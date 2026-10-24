#!/usr/bin/env python
"""
Checks that this project is really connected to your Supabase project.
It never prints your keys.

Run it from the backend folder (with your virtualenv active):

    python scripts/check_supabase.py               # config + read-only live checks
    python scripts/check_supabase.py --write-test  # also proves the candle/feature upserts work
    python scripts/check_supabase.py --offline     # only the checks that need no internet

--write-test adds ONE temporary stock (ticker ZZCONNTEST) with a few rows, checks
that re-sending them updates instead of duplicating, then deletes everything it added.

Exit code is 0 if nothing FAILED (warnings are fine), 1 otherwise.
"""
import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
os.chdir(BACKEND)  # the backend reads backend/.env relative to the working directory
sys.path.insert(0, str(BACKEND))

# Every table the app expects, in the public schema.
TABLES = [
    "profiles", "stocks", "ohlcv_daily", "technical_features", "chart_patterns",
    "ml_signals", "market_data_cache", "allocation_requests", "allocation_items",
    "portfolio_performance", "llm_explanations",
]
# Columns the backend code writes; a missing one would make every save fail.
CODE_COLUMNS = {
    "stocks": "id,ticker,name,sector",
    "ohlcv_daily": "stock_id,trade_date,open,high,low,close,volume",
    "technical_features": "stock_id,trade_date,rsi_14,macd,macd_signal,macd_hist,ema_50,ema_200,sma_50,sma_200,atr,volatility_20",
}
# Tables a logged-out visitor must NOT be able to read (checked when they contain rows).
RLS_TABLES = ["stocks", "profiles", "ohlcv_daily", "technical_features", "allocation_requests"]
TEST_TICKER = "ZZCONNTEST"

_results: list[tuple[str, str]] = []


def report(status: str, label: str, hint: str = "") -> None:
    _results.append((status, label))
    print(f"  [{status}] {label}")
    if hint and status in ("FAIL", "WARN"):
        print(f"         -> {hint}")


def short(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:150]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def read_env(path: Path):
    if not path.exists():
        return None
    from dotenv import dotenv_values
    return {k: (v or "").strip() for k, v in dotenv_values(path).items()}


def jwt_claims(token: str):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001
        return None


def project_ref(url: str):
    m = re.match(r"^https://([a-z0-9]+)\.supabase\.co/?$", url)
    return m.group(1) if m else None


PLACEHOLDER = re.compile(r"replace|your[-_ ]|changeme|example|<.*>|xxxx", re.I)


def is_set(v: str) -> bool:
    return bool(v) and not PLACEHOLDER.search(v)


def describe_key(token: str):
    """Returns (role, ref, expired, kind). kind is 'jwt' (legacy) or 'new' (sb_...)."""
    if token.startswith("sb_secret_"):
        return "service_role", None, False, "new"
    if token.startswith("sb_publishable_"):
        return "anon", None, False, "new"
    c = jwt_claims(token)
    if not c:
        return None, None, False, "unknown"
    exp = c.get("exp")
    return c.get("role"), c.get("ref"), bool(exp and exp < time.time()), "jwt"


def check_key(name: str, token: str, want_role: str, ref: str | None) -> None:
    role, key_ref, expired, kind = describe_key(token)
    if kind == "unknown":
        report("FAIL", f"{name} is a valid Supabase key", "it doesn't look like a Supabase key - re-copy it from Project Settings -> API")
        return
    if role != want_role:
        hint = "keys are swapped or wrong: paste the service_role key in SERVICE_ROLE, the anon/publishable key in ANON"
        report("FAIL", f"{name} has role '{want_role}' (found '{role}')", hint)
        return
    if expired:
        report("FAIL", f"{name} is not expired", "generate a new key in the dashboard")
        return
    if kind == "jwt" and ref and key_ref != ref:
        report("FAIL", f"{name} belongs to the same project as SUPABASE_URL", "the key is from a different Supabase project")
        return
    extra = ""
    if kind == "new":
        extra = " (new-style key; needs supabase-py 2.16+, see note at the end)"
    report("PASS", f"{name}: role '{want_role}', same project as the URL{extra}" if kind == "jwt" else f"{name}: role '{want_role}'{extra}")


# --------------------------------------------------------------------------
# A. local configuration (no internet needed)
# --------------------------------------------------------------------------
def section_config(ctx: dict) -> None:
    print("\nA. Project files")
    benv = read_env(BACKEND / ".env")
    fenv = read_env(ROOT / "frontend" / ".env")
    if benv is None:
        report("FAIL", "backend/.env exists", "copy backend/.env.example to backend/.env and fill it in")
        return
    report("PASS", "backend/.env exists")
    if fenv is None:
        report("WARN", "frontend/.env exists", "copy frontend/.env.example to frontend/.env (needed for login)")
    else:
        report("PASS", "frontend/.env exists")

    url = benv.get("SUPABASE_URL", "")
    ref = project_ref(url)
    if not is_set(url):
        report("FAIL", "SUPABASE_URL is set", "add it to backend/.env (Project Settings -> API -> Project URL)")
        return
    if ref is None:
        report("FAIL", "SUPABASE_URL looks like https://<project-ref>.supabase.co", "no trailing path or slash, e.g. no /rest/v1")
        return
    report("PASS", "SUPABASE_URL is well formed")

    for name in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY"):
        if not is_set(benv.get(name, "")):
            report("FAIL", f"{name} is set", "add it to backend/.env")
    svc, anon = benv.get("SUPABASE_SERVICE_ROLE_KEY", ""), benv.get("SUPABASE_ANON_KEY", "")
    if is_set(svc):
        check_key("SUPABASE_SERVICE_ROLE_KEY", svc, "service_role", ref)
    if is_set(anon):
        check_key("SUPABASE_ANON_KEY", anon, "anon", ref)

    if fenv is not None:
        fkey = fenv.get("VITE_SUPABASE_ANON_KEY", "")
        if fenv.get("VITE_SUPABASE_URL", "") != url:
            report("FAIL", "frontend VITE_SUPABASE_URL matches the backend URL", "the two apps point at different projects")
        else:
            report("PASS", "frontend VITE_SUPABASE_URL matches the backend URL")
        role, _, _, _ = describe_key(fkey) if fkey else (None, None, False, "")
        if not is_set(fkey):
            report("FAIL", "frontend VITE_SUPABASE_ANON_KEY is set", "add the anon/publishable key to frontend/.env")
        elif role == "service_role":
            report("FAIL", "frontend uses the anon key, NOT the service-role key",
                   "the service-role key in frontend/.env would be public in the browser bundle. Replace it and rotate that key NOW")
        elif fkey != anon:
            report("WARN", "frontend anon key equals the backend anon key", "not harmful, but they should normally be the same key")
        else:
            report("PASS", "frontend uses the same anon key as the backend")

    link = ROOT / "supabase" / ".temp" / "project-ref"
    if link.exists():
        linked = link.read_text().strip()
        if linked == ref:
            report("PASS", "Supabase CLI link (supabase/.temp) points at the same project")
        else:
            report("FAIL", "Supabase CLI link points at the same project as SUPABASE_URL",
                   "you linked the CLI to a different project; run 'supabase link --project-ref " + ref + "'")
    else:
        report("SKIP", "Supabase CLI link", "not linked; only matters if you use the supabase CLI")

    try:
        for k, v in benv.items():
            os.environ.setdefault(k, v)
        from app.config import settings  # noqa: F401
        report("PASS", "backend settings load (app/config.py)")
        ctx["settings_ok"] = True
    except Exception as exc:  # noqa: BLE001
        report("FAIL", "backend settings load (app/config.py)", short(exc))
        ctx["settings_ok"] = False

    ctx.update(url=url, ref=ref, svc=svc, anon=anon, config_ok=all(s != "FAIL" for s, _ in _results))


# --------------------------------------------------------------------------
# B. live checks, service-role key (read only)
# --------------------------------------------------------------------------
def count_rows(client, table: str, **eq) -> int:
    q = client.table(table).select("*", count="exact")
    for col, val in eq.items():
        q = q.eq(col, val)
    return q.limit(1).execute().count or 0


def section_live(ctx: dict) -> None:
    from supabase import create_client
    print("\nB. Live database (service-role key, read only)")
    try:
        client = create_client(ctx["url"], ctx["svc"])
        count_rows(client, "stocks")
    except Exception as exc:  # noqa: BLE001
        report("FAIL", "connect to Supabase with the service-role key", short(exc))
        ctx["live_ok"] = False
        return
    report("PASS", "connected to Supabase with the service-role key")
    ctx["client"] = client

    counts = {}
    for table in TABLES:
        try:
            counts[table] = count_rows(client, table)
        except Exception as exc:  # noqa: BLE001
            report("FAIL", f"table public.{table} is reachable", short(exc) + " (does the table exist? run 0001_init.sql)")
    ok_tables = [t for t in TABLES if t in counts]
    if len(ok_tables) == len(TABLES):
        report("PASS", f"all {len(TABLES)} tables exist and are reachable")
    ctx["counts"] = counts
    print("         row counts: " + ", ".join(f"{t}={counts[t]}" for t in ok_tables))

    for table, cols in CODE_COLUMNS.items():
        try:
            client.table(table).select(cols).limit(1).execute()
            report("PASS", f"{table} has the columns the backend writes")
        except Exception as exc:  # noqa: BLE001
            report("FAIL", f"{table} has the columns the backend writes ({cols})", short(exc))

    if counts.get("stocks", 0) == 0:
        report("WARN", "public.stocks contains tickers",
               "it's empty, so /api/market/ingest returns 404 for every ticker until you add some")
    else:
        report("PASS", f"public.stocks contains {counts['stocks']} ticker(s)")
    ctx["live_ok"] = True


# --------------------------------------------------------------------------
# C. live checks, anon key (what a logged-out visitor can see)
# --------------------------------------------------------------------------
def section_anon(ctx: dict) -> None:
    from supabase import create_client
    print("\nC. What the anon key can see (should be nothing without a login)")
    try:
        anon = create_client(ctx["url"], ctx["anon"])
        anon.table("stocks").select("id").limit(1).execute()
    except Exception as exc:  # noqa: BLE001
        report("FAIL", "connect to Supabase with the anon key", short(exc))
        return
    report("PASS", "the anon key is accepted by Supabase")
    for table in RLS_TABLES:
        have = ctx.get("counts", {}).get(table, 0)
        if have == 0:
            report("SKIP", f"row-level security on {table}", "table is empty, so there's nothing to hide yet")
            continue
        try:
            seen = len(anon.table(table).select("*").limit(5).execute().data or [])
        except Exception as exc:  # noqa: BLE001
            report("PASS", f"{table} is protected from logged-out visitors ({short(exc)[:60]})")
            continue
        if seen:
            report("FAIL", f"{table} is protected from logged-out visitors", "anon can read rows: enable RLS on this table")
        else:
            report("PASS", f"{table} is protected from logged-out visitors")


# --------------------------------------------------------------------------
# D. write test (opt-in, cleans up after itself)
# --------------------------------------------------------------------------
def section_write(ctx: dict) -> None:
    print(f"\nD. Write test (temporary stock {TEST_TICKER}, removed at the end)")
    if not ctx.get("settings_ok"):
        report("SKIP", "write test", "backend settings did not load")
        return
    from app.data.supabase_client import get_supabase, upsert_in_chunks
    client = get_supabase()

    def cleanup() -> None:
        rows = client.table("stocks").select("id").eq("ticker", TEST_TICKER).execute().data or []
        for r in rows:
            for child in ("ohlcv_daily", "technical_features"):
                client.table(child).delete().eq("stock_id", r["id"]).execute()
        client.table("stocks").delete().eq("ticker", TEST_TICKER).execute()

    try:
        cleanup()  # leftovers from an interrupted earlier run
        stock = client.table("stocks").insert(
            {"ticker": TEST_TICKER, "name": "Connection test", "sector": "technology"}
        ).execute().data[0]
        sid = stock["id"]
        report("PASS", "can insert into public.stocks")

        today = date.today().isoformat()
        candle = {"stock_id": sid, "trade_date": today, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100}
        feature = {"stock_id": sid, "trade_date": today, "rsi_14": 50.0, "macd": 0.1, "macd_signal": 0.05,
                   "ema_50": 1.4, "ema_200": 1.3, "atr": 0.2}
        for table, rec, changed in (("ohlcv_daily", candle, {"close": 9.9}), ("technical_features", feature, {"rsi_14": 77.0})):
            try:
                upsert_in_chunks(table, [rec])
                upsert_in_chunks(table, [{**rec, **changed}])  # same day again: must UPDATE, not duplicate
                n = count_rows(client, table, stock_id=sid)
                if n == 1:
                    report("PASS", f"{table}: saving the same day twice updates it (unique constraint works)")
                else:
                    report("FAIL", f"{table}: saving the same day twice updates it", f"found {n} rows; missing UNIQUE (stock_id, trade_date)")
            except Exception as exc:  # noqa: BLE001
                report("FAIL", f"{table}: upsert works", short(exc))
    except Exception as exc:  # noqa: BLE001
        report("FAIL", "write test could not run", short(exc))
    finally:
        try:
            cleanup()
            left = count_rows(client, "stocks", ticker=TEST_TICKER)
            report("PASS" if left == 0 else "WARN", "temporary test data removed",
                   f"delete the row with ticker {TEST_TICKER} from public.stocks by hand")
        except Exception as exc:  # noqa: BLE001
            report("WARN", "temporary test data removed", f"delete ticker {TEST_TICKER} from public.stocks by hand ({short(exc)})")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="only run checks that need no internet")
    ap.add_argument("--write-test", action="store_true", help="also run the temporary write/cleanup test")
    args = ap.parse_args()

    print("Supabase connection check (keys are never printed)")
    ctx: dict = {}
    section_config(ctx)

    if not args.offline:
        if not ctx.get("config_ok"):
            print("\nSkipping the live checks: fix the FAIL lines above first.")
        else:
            section_live(ctx)
            if ctx.get("live_ok"):
                section_anon(ctx)
                if args.write_test:
                    section_write(ctx)
                else:
                    print("\n(Run again with --write-test to also prove that saving candles/features works.)")

    fails = [l for s, l in _results if s == "FAIL"]
    warns = [l for s, l in _results if s == "WARN"]
    passed = sum(1 for s, _ in _results if s == "PASS")
    print(f"\nSUMMARY: {passed} passed, {len(warns)} warning(s), {len(fails)} failed")
    if any("new-style key" in l for _, l in _results):
        print("NOTE: new-style keys (sb_...) need a newer client: set supabase==2.16.0 in requirements.txt and remove the httpx==0.27.2 line.")
    if fails:
        print("NOT fully connected yet. Fix these:")
        for l in fails:
            print("  -", l)
        return 1
    if args.offline:
        print("Project files look right. The live connection was NOT tested (you used --offline).")
        return 0
    print("Connected." + (" (Warnings above are things to do next, not errors.)" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())