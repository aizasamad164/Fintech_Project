# Running StockSense locally

Two terminals: one for the backend (FastAPI, port 8000), one for the frontend (Vite, port 5173).

## 1. Backend (first time)

```
cd backend
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
```

Edit `backend/.env`:

| Key | Needed for | Without it |
|---|---|---|
| `GROQ_API_KEY` | Advisor chat, AI-written explanations | Chat says it isn't configured; dashboard uses rule-based bullets |
| `GROQ_MODEL` / `GROQ_EXPLAIN_MODEL` | Which Groq models to use | Defaults: `openai/gpt-oss-120b` / `openai/gpt-oss-20b` |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Saving portfolios + chat history in the cloud DB | Saved portfolios go to `backend/.local_portfolios.json`; chat history is kept in memory |

Check which models your Groq key can use: `python check_models.py`

Run it:

```
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/health (shows models found, Groq and storage status)
- API docs: http://localhost:8000/docs

## 2. Database (once, only if using Supabase)

Open the Supabase SQL editor and run `supabase/migrations/0004_portfolio_tracking.sql`.
It creates `user_portfolios`, `portfolio_positions` and `chat_history` with row-level security.

## 3. Frontend

```
cd frontend
npm install
```

`frontend/.env`:

```
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
```

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
| POST | `/api/portfolio/save` | Save an accepted portfolio |
| GET | `/api/portfolio/list?user_id=` | A user's saved portfolios |
| GET | `/api/portfolio/{id}/performance?user_id=` | Live P&L |
| DELETE | `/api/portfolio/{id}?user_id=` | Remove a saved portfolio |
| GET | `/api/news/{ticker}?limit=3` | Headlines (yfinance, Google News RSS fallback) |
| GET | `/api/insights` | Best strategy per sector, ranked |
| POST | `/api/chat/message` | Advisor agent (Groq + tools) |

## Known gaps

- Login is still a mock. Each browser gets a random user id (`utils/userId.ts`) until Supabase auth is wired in.
- `News_Sentiment` is fed as 0 to the models: training used a `sentiment_engine` module that isn't in the repo.
- There is no General model file, so "General" falls back to the ticker's own sector model.
- `api/routes/market.py` is not mounted: it imports `fetch_ohlcv`, which no longer exists in `data/market_data.py`.
