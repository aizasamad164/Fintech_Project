# Portfolio Allocation App

An educational portfolio allocation simulator combining quantitative signal
generation (LightGBM/XGBoost + technical indicators), mean-variance
optimization, and LLM-generated plain-English explanations (Groq).

> **Disclaimer:** This is an educational simulation, not regulated financial advice.

## Project Structure

- `backend/` — FastAPI service: data ingestion, ML signals, portfolio
  optimization, and LLM explanation pipeline. See `docs/PRD.md` for the
  functional/non-functional requirements each module satisfies.
- `frontend/` — React + Tailwind + Capacitor app (Web, iOS, Android from one codebase).
- `supabase/` — Postgres schema, RLS policies, and migrations.
- `docs/` — Product requirements and tech stack references.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- A Supabase project (free tier is fine for MVP)
- API keys: Groq, Finnhub (or Polygon)

### Backend

```bash
cd backend
cp .env.example .env       # fill in your real keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
cp .env.example .env       # fill in Supabase URL + anon key, API base URL
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Mobile (Capacitor)

```bash
cd frontend
npm run build
npx cap add ios       # or android, one-time
npm run cap:sync
npm run cap:ios        # or cap:android
```

### Database

Apply migrations in `supabase/migrations/` via the Supabase CLI or dashboard SQL editor:

```bash
supabase db push
```

### Docker (optional, local full-stack)

```bash
docker-compose up
```

## Where things live

| What | Where |
|---|---|
| Third-party API keys (Groq, Finnhub) | `backend/.env` (git-ignored) — never in frontend |
| Your own REST API | `backend/app/api/routes/` |
| Live market data | Fetched on demand, held in in-memory cache (`backend/app/data/cache.py`), with a Supabase fallback table (`market_data_cache`) |
| Trained ML models | `backend/app/signals/models/*.pkl` (committed or pulled from object storage at startup) |
| Bulk training datasets | External storage, **not** committed to git |
| Frontend public config (Supabase anon key, API base URL) | `frontend/.env` (git-ignored, but contains only public-safe values) |

## Requirements Traceability

See `docs/PRD.md` for the full FRS. Code comments throughout `backend/app/`
reference the specific FR/NFR IDs each module implements (e.g. `# FR-2.3`).

## License

TBD.
