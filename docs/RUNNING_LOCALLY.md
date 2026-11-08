# Running StockSense locally

Two terminals: one for the backend (FastAPI, port 8000), one for the frontend (Vite, port 5173).
On Windows, `start.bat` in the project folder opens both and the browser.

**Python 3.12 is required** (scipy and pandas-ta in `requirements.txt` don't install on 3.11).
Install it with `winget install Python.Python.3.12`. If you already have a `backend\venv` made with
an older Python, delete that folder and create it again as below.

## 1. Backend (first time)

```
cd backend
py -3.12 -m venv venv            # macOS/Linux: python3.12 -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
```

Edit `backend/.env`:

| Key | Needed for | Without it |
|---|---|---|
| `GROQ_API_KEY` | Advisor chat, AI-written explanations | Chat says it isn't configured; dashboard uses rule-based bullets |
| `GROQ_MODEL` / `GROQ_EXPLAIN_MODEL` | Which Groq models to use | Defaults: `openai/gpt-oss-120b` / `openai/gpt-oss-20b` |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Real accounts (the backend checks each sign-in token with Supabase), saving portfolios, subscriptions and chat history in the cloud DB | **Demo mode**: no accounts, each browser gets a random id, data goes to `backend/.local_*.json` |
| `STRIPE_SECRET_KEY` | Taking card payments for Pro (use the `sk_test_...` key) | Checkout offers only a simulated upgrade |
| `STRIPE_WEBHOOK_SECRET` | Renewals, failed payments and cancellations made in Stripe | Pro status is still updated right after checkout and on cancel |
| `STRIPE_PRICE_ID` | Optional: use an existing Stripe price | A "StockSense Pro" $9/month price is created in your Stripe account on first checkout |

Check which models your Groq key can use: `python check_models.py`

Run it:

```
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/health (shows models found, Groq and storage status)
- API docs: http://localhost:8000/docs

## 2. Accounts and database (once, only if using Supabase)

1. In the Supabase SQL editor, run `supabase/migrations/0008_portfolio_tracking.sql`, then
   `0009_subscriptions.sql` (skip any earlier ones your project already has).
2. **Authentication → URL Configuration**: Site URL `http://localhost:5173`, and add
   `http://localhost:5173` to Redirect URLs (used by confirmation and password-reset emails).
3. Optional, for "Continue with Google": **Authentication → Providers → Google**, paste a Google
   OAuth client id and secret.
4. **Project Settings → API**: copy the Project URL, the `anon` key (frontend) and the
   `service_role` key (backend only, never put it in the frontend).

By default Supabase asks new users to confirm their email before they can sign in. The app says so
after sign-up. For quick testing you can turn that off under **Authentication → Providers → Email**.

## 3. Payments (optional, Stripe test mode)

1. Make a free Stripe account, stay in **Test mode**, open **Developers → API keys**.
2. `sk_test_...` goes in `backend/.env` as `STRIPE_SECRET_KEY`;
   `pk_test_...` goes in `frontend/.env` as `VITE_STRIPE_PUBLISHABLE_KEY`.
3. Pay with test card `4242 4242 4242 4242`, any future date, any CVC and postcode.
   `4000 0025 0000 3155` tests the bank-verification (3-D Secure) step.
4. Optional webhook while developing, with the Stripe CLI:
   `stripe listen --forward-to localhost:8000/api/billing/webhook`, then put the `whsec_...` it prints
   in `backend/.env` as `STRIPE_WEBHOOK_SECRET`.

Card details are typed into Stripe's own form inside the page and go straight to Stripe; they never
reach our backend. Pro is granted only after the backend re-checks the subscription with Stripe.

## 4. Frontend

```
cd frontend
npm install
```

`frontend/.env`:

```
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Leave the Supabase lines out to run in demo mode (the login screen shows "Continue in demo mode").
Set them in **both** `.env` files or neither: the backend decides demo vs real accounts from its own keys.

(`VITE_USE_MOCK=true` runs the whole UI on mock data with no backend.)

```
npm run dev
```

Open http://localhost:5173

## Tests

```
cd backend
python -m pytest tests -q          # offline: uses synthetic prices, no keys needed
cd ../frontend
npm run typecheck
```

## API at a glance

| Method | Path | What it does |
|---|---|---|
| POST | `/api/portfolio/rebalance` | Build a 3-5 holding portfolio + explanation |
| POST | `/api/portfolio/save` | Save an accepted portfolio (signed in) |
| GET | `/api/portfolio/list` | Your saved portfolios (signed in) |
| GET | `/api/portfolio/{id}/performance` | Live P&L (signed in) |
| DELETE | `/api/portfolio/{id}` | Remove a saved portfolio (signed in) |
| GET | `/api/portfolio/shariah/universe` | Shariah screening list and sources |
| GET | `/api/auth/mode`, `/api/auth/me` | Demo or real accounts; who is signed in |
| GET | `/api/billing/status` | Does this account have Pro |
| POST | `/api/billing/subscribe`, `/confirm`, `/cancel` | Stripe subscription for Pro |
| POST | `/api/billing/webhook` | Stripe events |
| GET | `/api/news/{ticker}?limit=3` | Headlines (yfinance, Google News RSS fallback) |
| GET | `/api/insights` | Best strategy per sector, ranked |
| POST | `/api/chat/message` | Advisor agent (Groq + tools) |

"Signed in" means the request carries `Authorization: Bearer <Supabase access token>`; the frontend
adds it automatically. In demo mode the same routes take `?user_id=<uuid>` instead.

## Known gaps

- `News_Sentiment` is fed as 0 to the models: training used a `sentiment_engine` module that isn't in the repo.
- There is no General model file, so "General" falls back to the ticker's own sector model.
- `api/routes/market.py` is not mounted: it imports `fetch_ohlcv`, which no longer exists in `data/market_data.py`.
