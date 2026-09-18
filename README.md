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


Fintech_Project/
├── README.md
├── docker-compose.yml
├── .gitignore
├── docs/
│   ├── PRD.md
│   └── tech-stack.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── explain.py
│   │   │       └── portfolio.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── cache.py
│   │   │   ├── fundamentals.py
│   │   │   ├── indicators.py
│   │   │   └── market_data.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── chat_prompt_builder.py
│   │   │   ├── chat_routes.py
│   │   │   ├── chat_session.py
│   │   │   ├── context_builder.py
│   │   │   ├── disclaimer.py
│   │   │   ├── fallback.py
│   │   │   └── groq_client.py
│   │   ├── optimization/
│   │   │   ├── __init__.py
│   │   │   ├── allocator.py
│   │   │   ├── discretize.py
│   │   │   └── performance.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── portfolio.py
│   │   └── signals/
│   │       ├── __init__.py
│   │       ├── pattern_detection.py
│   │       └── models/
│   │           ├── __init__.py
│   │           └── model_loader.py
│   └── tests/
│       ├── __init__.py
│       └── test_optimization.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── capacitor.config.ts
│   ├── .env.example
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api/
│       │   └── client.ts
│       ├── lib/
│       │   └── supabaseClient.ts
│       ├── hooks/
│       │   └── usePortfolio.ts
│       ├── components/
│       │   ├── AllocationTable.tsx
│       │   ├── ChatPanel.tsx
│       │   ├── PortfolioChart.tsx
│       │   ├── RiskToggle.tsx
│       │   ├── SectorFilter.tsx
│       │   └── Tooltip.tsx
│       └── pages/
│           ├── Dashboard.tsx
│           ├── Login.tsx
│           └── Settings.tsx
├── ml/
│   ├── requirements.txt
│   ├── train.py
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   └── trained_models/
│       ├── general_model.pkl
│       ├── healthcare_model.pkl
│       ├── renewable_model.pkl
│       └── tech_model.pkl
└── supabase/
    └── migrations/
        ├── 0001_init.sql
        ├── 0002_add_cache_tables.sql
        └── 0003_add_chat_history.sql
