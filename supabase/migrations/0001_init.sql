-- Initial schema.
-- Auth is handled by Supabase's built-in auth.users table; these are app-level tables.

-- FR-1.2/1.3/1.4: store each user's saved preferences
create table if not exists public.user_preferences (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    budget numeric not null default 1000,
    risk_strategy text not null default 'balanced'
        check (risk_strategy in ('conservative', 'balanced', 'aggressive')),
    sectors text[] not null default array['combined'],
    updated_at timestamptz not null default now()
);

alter table public.user_preferences enable row level security;

create policy "Users can view their own preferences"
    on public.user_preferences for select
    using (auth.uid() = user_id);

create policy "Users can update their own preferences"
    on public.user_preferences for update
    using (auth.uid() = user_id);

create policy "Users can insert their own preferences"
    on public.user_preferences for insert
    with check (auth.uid() = user_id);


-- NFR-3.2: fallback cache table for daily close prices, used when the
-- live market data feed (Finnhub/yfinance) is unresponsive. This is a
-- durable backstop that sits behind the in-memory cache (app/data/cache.py).
create table if not exists public.market_data_cache (
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
alter table public.market_data_cache enable row level security;

create policy "Authenticated users can read cached market data"
    on public.market_data_cache for select
    using (auth.role() = 'authenticated');


-- Generated portfolio history, for FR-4.3 performance tracking / re-display.
create table if not exists public.portfolio_snapshots (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    budget numeric not null,
    risk_strategy text not null,
    sectors text[] not null,
    allocation jsonb not null,          -- {ticker: {weight, amount, shares}}
    one_year_performance_pct numeric,
    created_at timestamptz not null default now()
);

alter table public.portfolio_snapshots enable row level security;

create policy "Users can view their own portfolio snapshots"
    on public.portfolio_snapshots for select
    using (auth.uid() = user_id);

create policy "Users can insert their own portfolio snapshots"
    on public.portfolio_snapshots for insert
    with check (auth.uid() = user_id);
