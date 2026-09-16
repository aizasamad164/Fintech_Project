-- Initial schema.
-- Auth is handled by Supabase's built-in auth.users table; these are app-level tables.
-- Four core entities per the data dictionary: profiles [D1], market_cache [D2],
-- scores [D3], allocations [D4].


-- =========================================================
-- D1: profiles
-- FR-1.1/1.2/1.3/1.4 — user identity + saved budget/risk/sector preferences.
-- =========================================================
create table if not exists public.profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null unique,
    display_name text,
    budget numeric not null default 1000,
    risk_strategy text not null default 'balanced'
        check (risk_strategy in ('conservative', 'balanced', 'aggressive')),
    sectors text[] not null default array['combined'],
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
    on public.profiles for select
    using (auth.uid() = user_id);

create policy "Users can update their own profile"
    on public.profiles for update
    using (auth.uid() = user_id);

create policy "Users can insert their own profile"
    on public.profiles for insert
    with check (auth.uid() = user_id);


-- =========================================================
-- D2: market_cache
-- NFR-3.2 — fallback cache for daily OHLCV data, used when the live market
-- data feed (Finnhub/yfinance) is unresponsive. Durable backstop that sits
-- behind the in-memory cache (app/data/cache.py).
-- =========================================================
create table if not exists public.market_cache (
    ticker text not null,
    trade_date date not null,
    open numeric,
    high numeric,
    low numeric,
    close numeric not null,
    volume bigint,
    fetched_at timestamptz not null default now(),
    primary key (ticker, trade_date)
);

-- Read-only for authenticated clients; writes happen only via the backend
-- service role, never directly from the frontend (NFR-2.1).
alter table public.market_cache enable row level security;

create policy "Authenticated users can read cached market data"
    on public.market_cache for select
    using (auth.role() = 'authenticated');


-- =========================================================
-- D3: scores
-- FR-3.2/3.3 — ML-generated P(Bullish) confidence scores per candidate
-- stock, output by the sector-specialized LightGBM/XGBoost models.
-- =========================================================
create table if not exists public.scores (
    id uuid primary key default gen_random_uuid(),
    ticker text not null,
    sector text not null,
    p_bullish numeric not null check (p_bullish >= 0 and p_bullish <= 1),
    model_version text not null default 'v1',
    computed_at timestamptz not null default now()
);

create index if not exists idx_scores_ticker_sector
    on public.scores (ticker, sector, computed_at desc);

-- Read-only for authenticated clients; writes happen only via the backend
-- service role (scores are generated server-side, never client-side).
alter table public.scores enable row level security;

create policy "Authenticated users can read scores"
    on public.scores for select
    using (auth.role() = 'authenticated');


-- =========================================================
-- D4: allocations
-- FR-4.1/4.2/4.3 — generated portfolio allocation history, for
-- performance tracking / re-display, and as the context payload for
-- the LLM explanation layer (FR-5.1).
-- =========================================================
create table if not exists public.allocations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    budget numeric not null,
    risk_strategy text not null,
    sectors text[] not null,
    allocation jsonb not null,          -- {ticker: {weight, amount, shares}}
    one_year_performance_pct numeric,
    projected_return numeric,
    created_at timestamptz not null default now()
);

alter table public.allocations enable row level security;

create policy "Users can view their own allocations"
    on public.allocations for select
    using (auth.uid() = user_id);

create policy "Users can insert their own allocations"
    on public.allocations for insert
    with check (auth.uid() = user_id);