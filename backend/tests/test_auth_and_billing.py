"""
Sign-in protection and Stripe billing, with Supabase and Stripe replaced by
stand-ins (no network, no keys).

    cd backend
    python -m pytest tests/test_auth_and_billing.py -q
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import billing as billing_routes
from app.api.routes import portfolio as portfolio_routes
from app.billing import gateway, store
from app.config import settings
from app.data import portfolio_store

ALICE = deps.CurrentUser(id=str(uuid.uuid4()), email="alice@example.com")
BOB = deps.CurrentUser(id=str(uuid.uuid4()), email="bob@example.com")
TOKENS = {"alice-token": ALICE, "bob-token": BOB}
POSITIONS = [{"ticker": "AAPL", "sector": "Technology", "shares_held": 2, "buy_price": 150}]


@pytest.fixture
def client(tmp_path, monkeypatch):
    # data stays in temp files; never touches a real Supabase project
    monkeypatch.setattr(portfolio_store, "LOCAL_FILE", tmp_path / "portfolios.json")
    monkeypatch.setattr(store, "LOCAL_FILE", tmp_path / "billing.json")
    monkeypatch.setattr(portfolio_store, "_supabase_configured", lambda: False)
    deps._token_cache.clear()
    from app.main import app
    return TestClient(app)


@pytest.fixture
def supabase_auth(monkeypatch):
    """Pretend Supabase Auth is on and knows two users."""
    for mod in (deps, portfolio_routes, billing_routes):
        monkeypatch.setattr(mod, "auth_mode", lambda: "supabase")
    monkeypatch.setattr(deps, "_verify_with_supabase", lambda token: TOKENS.get(token))


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ── auth ─────────────────────────────────────────────────────────────────────
def test_demo_mode_uses_user_id(client):
    assert client.get("/api/auth/mode").json() == {"mode": "demo"}
    assert client.get("/api/portfolio/list").status_code == 401
    uid = str(uuid.uuid4())
    assert client.get("/api/portfolio/list", params={"user_id": uid}).status_code == 200


def test_signed_in_routes_need_a_valid_token(client, supabase_auth):
    assert client.get("/api/portfolio/list").status_code == 401
    assert client.get("/api/portfolio/list", headers=bearer("forged")).status_code == 401
    # a user_id query param is NOT accepted once real accounts are on
    assert client.get("/api/portfolio/list", params={"user_id": ALICE.id}).status_code == 401
    me = client.get("/api/auth/me", headers=bearer("alice-token")).json()
    assert me == {"id": ALICE.id, "email": ALICE.email, "demo": False}


def test_users_only_see_their_own_portfolios(client, supabase_auth):
    saved = client.post("/api/portfolio/save", headers=bearer("alice-token"),
                        json={"initial_investment": 300, "positions": POSITIONS,
                              "user_id": BOB.id})   # trying to save as someone else is ignored
    assert saved.status_code == 200, saved.text
    pid = saved.json()["portfolio"]["id"]
    assert saved.json()["portfolio"]["user_id"] == ALICE.id

    assert [p["id"] for p in client.get("/api/portfolio/list", headers=bearer("alice-token")).json()["portfolios"]] == [pid]
    assert client.get("/api/portfolio/list", headers=bearer("bob-token")).json()["portfolios"] == []
    assert client.delete(f"/api/portfolio/{pid}", headers=bearer("bob-token")).status_code == 404
    assert client.delete(f"/api/portfolio/{pid}", headers=bearer("alice-token")).status_code == 200


def test_save_requires_sign_in(client, supabase_auth):
    r = client.post("/api/portfolio/save", json={"initial_investment": 300, "positions": POSITIONS})
    assert r.status_code == 401


# ── billing without Stripe keys ──────────────────────────────────────────────
def test_billing_without_stripe_offers_only_a_simulated_upgrade(client, supabase_auth, monkeypatch):
    monkeypatch.setattr(gateway, "configured", lambda: False)
    assert client.get("/api/billing/config").json()["configured"] is False
    assert client.post("/api/billing/subscribe", headers=bearer("alice-token")).status_code == 503
    assert client.get("/api/billing/status", headers=bearer("alice-token")).json()["is_pro"] is False

    up = client.post("/api/billing/demo-upgrade", headers=bearer("alice-token")).json()
    assert up["is_pro"] is True and up["simulated"] is True
    # Pro belongs to Alice only
    assert client.get("/api/billing/status", headers=bearer("bob-token")).json()["is_pro"] is False


# ── billing with Stripe (stand-in) ───────────────────────────────────────────
@pytest.fixture
def fake_stripe(monkeypatch):
    subs = {}

    def create_subscription(customer_id, user_id):
        sid = f"sub_{len(subs) + 1}"
        subs[sid] = {"id": sid, "customer": customer_id, "status": "incomplete", "cancel_at_period_end": False,
                     "items": {"data": [{"current_period_end": 1893456000}]}, "metadata": {"user_id": user_id}}
        return {"subscription_id": sid, "client_secret": f"{sid}_secret", "status": "incomplete"}

    monkeypatch.setattr(gateway, "configured", lambda: True)
    monkeypatch.setattr(gateway, "ensure_customer", lambda existing, user_id, email: existing or f"cus_{user_id[:8]}")
    monkeypatch.setattr(gateway, "create_subscription", create_subscription)
    monkeypatch.setattr(gateway, "retrieve_subscription", lambda sid: subs[sid])
    monkeypatch.setattr(gateway, "cancel_at_period_end", lambda sid, cancel=True: {**subs[sid], "cancel_at_period_end": True})
    return subs


def test_subscribe_then_confirm_grants_pro(client, supabase_auth, fake_stripe):
    start = client.post("/api/billing/subscribe", headers=bearer("alice-token"))
    assert start.status_code == 200, start.text
    sid = start.json()["subscription_id"]
    assert start.json()["client_secret"] == f"{sid}_secret"

    # Payment not completed yet -> no Pro
    pending = client.post("/api/billing/confirm", headers=bearer("alice-token"), json={"subscription_id": sid}).json()
    assert pending["is_pro"] is False and pending["status"] == "incomplete"

    fake_stripe[sid]["status"] = "active"   # Stripe marks it paid
    done = client.post("/api/billing/confirm", headers=bearer("alice-token"), json={"subscription_id": sid}).json()
    assert done["is_pro"] is True and done["current_period_end"].startswith("2030")

    # A second subscription is refused, and simulated upgrades are off when Stripe is on
    assert client.post("/api/billing/subscribe", headers=bearer("alice-token")).status_code == 409
    assert client.post("/api/billing/demo-upgrade", headers=bearer("bob-token")).status_code == 403

    cancelled = client.post("/api/billing/cancel", headers=bearer("alice-token")).json()
    assert cancelled["is_pro"] is True and cancelled["cancel_at_period_end"] is True


def test_cannot_claim_someone_elses_subscription(client, supabase_auth, fake_stripe):
    sid = client.post("/api/billing/subscribe", headers=bearer("alice-token")).json()["subscription_id"]
    fake_stripe[sid]["status"] = "active"
    client.post("/api/billing/subscribe", headers=bearer("bob-token"))   # Bob gets his own customer
    r = client.post("/api/billing/confirm", headers=bearer("bob-token"), json={"subscription_id": sid})
    assert r.status_code == 403
    assert client.get("/api/billing/status", headers=bearer("bob-token")).json()["is_pro"] is False


def test_webhook_updates_status(client, monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    store.upsert(ALICE.id, stripe_customer_id="cus_alice", status="active")
    event = {"type": "customer.subscription.deleted",
             "data": {"object": {"id": "sub_9", "customer": "cus_alice", "status": "canceled", "metadata": {}}}}
    monkeypatch.setattr(gateway, "construct_event", lambda payload, sig: event)
    assert client.post("/api/billing/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=x"}).status_code == 200
    assert store.is_pro(store.get(ALICE.id)) is False

    def bad(payload, sig):
        raise ValueError("bad signature")
    monkeypatch.setattr(gateway, "construct_event", bad)
    assert client.post("/api/billing/webhook", content=b"{}").status_code == 400


def test_gateway_reads_new_and_old_stripe_shapes():
    new = {"latest_invoice": {"confirmation_secret": {"client_secret": "new_secret"}}}
    old = {"latest_invoice": {"payment_intent": {"client_secret": "old_secret"}}}
    assert gateway._client_secret(new) == "new_secret"
    assert gateway._client_secret(old) == "old_secret"
    s = gateway.summarize({"id": "sub_1", "customer": {"id": "cus_1"}, "status": "active",
                           "current_period_end": 1893456000})
    assert s["stripe_customer_id"] == "cus_1" and s["current_period_end"].startswith("2030")
