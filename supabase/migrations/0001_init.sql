-- =====================================================================
-- 0001_init.sql  —  BASELINE SNAPSHOT of the live Supabase database
--
-- This file was generated from the live schema (tables, constraints, RLS,
-- functions, triggers). It documents what already exists in Supabase.
--
--   * Do NOT run this on your existing Supabase project — everything here
--     is already there and it would fail with "already exists".
--   * DO run it on a brand-new / empty Supabase project to rebuild the DB.
--   * Run 0002 after it (0002 is safe on both new and existing databases).
--
-- Note: the duplicate RLS policies (an "old style" and a "new style" one on
-- each table) are reproduced here exactly as they exist live; 0002 removes
-- the old-style ones.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Enum types
-- ---------------------------------------------------------------------
create type public.pattern_type      as enum ('support', 'resistance', 'breakout');
create type public.risk_strategy     as enum ('conservative', 'balanced', 'aggressive');
create type public.sector_type       as enum ('technology', 'healthcare', 'renewable_energy');
create type public.subscription_tier as enum ('free', 'pro');


-- ---------------------------------------------------------------------
-- Reference data: candidate stocks (must be seeded before ingesting data)
-- ---------------------------------------------------------------------
create table public.stocks (
    id          uuid        not null default gen_random_uuid(),
    ticker      text        not null,
    name        text        not null,
    sector      sector_type not null,
    market_cap  numeric,
    pe_ratio    numeric,
    is_active   boolean     not null default true,
    updated_at  timestamptz not null default now(),
    constraint stocks_pkey       primary key (id),
    constraint stocks_ticker_key unique (ticker)
);
create index idx_stocks_sector on public.stocks using btree (sector);


-- ---------------------------------------------------------------------
-- Users: one profile per auth user (row is created by a trigger, see below)
-- ---------------------------------------------------------------------
create table public.profiles (
    id                 uuid              not null,
    email              text              not null,
    subscription_tier  subscription_tier not null default 'free',
    created_at         timestamptz       not null default now(),
    updated_at         timestamptz       not null default now(),
    constraint profiles_pkey    primary key (id),
    constraint profiles_id_fkey foreign key (id) references auth.users (id) on delete cascade
);


-- ---------------------------------------------------------------------
-- Market data (written by the backend with the service-role key)
-- NOTE: every bigint "id" below is GENERATED ALWAYS AS IDENTITY in the live DB
-- (confirmed from the Supabase schema view). The database numbers the rows
-- itself and rejects any insert that tries to supply an id, so code must never
-- send "id".
-- ---------------------------------------------------------------------
create table public.ohlcv_daily (
    id          bigint      generated always as identity,
    stock_id    uuid        not null,
    trade_date  date        not null,
    open        numeric     not null,
    high        numeric     not null,
    low         numeric     not null,
    close       numeric     not null,
    volume      bigint      not null,
    created_at  timestamptz not null default now(),
    constraint ohlcv_daily_pkey                  primary key (id),
    constraint ohlcv_daily_stock_id_trade_date_key unique (stock_id, trade_date),
    constraint ohlcv_daily_stock_id_fkey         foreign key (stock_id) references public.stocks (id) on delete cascade
);
create index idx_ohlcv_stock_date on public.ohlcv_daily using btree (stock_id, trade_date desc);

create table public.technical_features (
    id          bigint      generated always as identity,
    stock_id    uuid        not null,
    trade_date  date        not null,
    rsi_14      numeric,
    macd        numeric,
    macd_signal numeric,
    ema_50      numeric,
    ema_200     numeric,
    atr         numeric,
    created_at  timestamptz not null default now(),
    constraint technical_features_pkey                    primary key (id),
    constraint technical_features_stock_id_trade_date_key unique (stock_id, trade_date),
    constraint technical_features_stock_id_fkey           foreign key (stock_id) references public.stocks (id) on delete cascade
);
create index idx_technical_features_stock_date on public.technical_features using btree (stock_id, trade_date desc);

create table public.chart_patterns (
    id            bigint       generated always as identity,
    stock_id      uuid         not null,
    trade_date    date         not null,
    pattern_type  pattern_type not null,
    price_level   numeric      not null,
    detected_at   timestamptz  not null default now(),
    constraint chart_patterns_pkey          primary key (id),
    constraint chart_patterns_stock_id_fkey foreign key (stock_id) references public.stocks (id) on delete cascade
);
create index idx_chart_patterns_stock_date on public.chart_patterns using btree (stock_id, trade_date desc);

create table public.ml_signals (
    id                   bigint      generated always as identity,
    stock_id             uuid        not null,
    model_name           text        not null,
    sector               sector_type,
    probability_bullish  numeric     not null,
    generated_at         timestamptz not null default now(),
    trade_date           date        not null default now(),
    constraint ml_signals_pkey                        primary key (id),
    constraint ml_signals_probability_bullish_check   check (probability_bullish >= 0 and probability_bullish <= 1),
    constraint ml_signals_unique_signal               unique (stock_id, model_name, trade_date),
    constraint ml_signals_stock_id_fkey               foreign key (stock_id) references public.stocks (id) on delete cascade
);
create index idx_ml_signals_stock_generated on public.ml_signals using btree (stock_id, generated_at desc);

-- Per-ticker JSON cache with an expiry time (purge expired rows periodically).
create table public.market_data_cache (
    ticker      text        not null,
    data        jsonb       not null,
    cached_at   timestamptz not null default now(),
    expires_at  timestamptz,
    constraint market_data_cache_pkey        primary key (ticker),
    constraint market_data_cache_ticker_fkey foreign key (ticker) references public.stocks (ticker) on delete cascade
);


-- ---------------------------------------------------------------------
-- User activity: allocation requests and their results
-- ---------------------------------------------------------------------
create table public.allocation_requests (
    id            uuid          not null default gen_random_uuid(),
    user_id       uuid          not null,
    budget        numeric       not null,
    risk_strategy risk_strategy not null,
    sectors       sector_type[] not null,
    is_combined   boolean       not null default false,
    created_at    timestamptz   not null default now(),
    constraint allocation_requests_pkey         primary key (id),
    constraint allocation_requests_budget_check check (budget > 0),
    -- As it exists live. Known flaw: a non-combined request with an EMPTY
    -- sectors array slips through (array_length is NULL, and a NULL check
    -- result counts as "pass"). 0002 replaces it with a correct version.
    constraint allocation_requests_sector_logic_check check (
        (is_combined = true  and array_length(sectors, 1) is null)
        or
        (is_combined = false and array_length(sectors, 1) > 0)
    ),
    constraint allocation_requests_user_id_fkey foreign key (user_id) references public.profiles (id) on delete cascade
);
create index idx_allocation_requests_user_created on public.allocation_requests using btree (user_id, created_at desc);

create table public.allocation_items (
    id          bigint      generated always as identity,
    request_id  uuid        not null,
    stock_id    uuid        not null,
    weight      numeric     not null,
    amount      numeric     not null,
    shares      integer     not null,
    created_at  timestamptz not null default now(),
    constraint allocation_items_pkey         primary key (id),
    constraint allocation_items_amount_check check (amount >= 0),
    constraint allocation_items_shares_check check (shares >= 0),
    constraint allocation_items_weight_check check (weight >= 0 and weight <= 1),
    constraint allocation_items_request_id_fkey foreign key (request_id) references public.allocation_requests (id) on delete cascade,
    constraint allocation_items_stock_id_fkey   foreign key (stock_id)   references public.stocks (id)
);
create index idx_allocation_items_request on public.allocation_items using btree (request_id);

create table public.portfolio_performance (
    id                       bigint      generated always as identity,
    request_id               uuid        not null,
    one_year_return_pct      numeric,
    projected_return_amount  numeric,
    computed_at              timestamptz not null default now(),
    constraint portfolio_performance_pkey           primary key (id),
    constraint portfolio_performance_request_id_key unique (request_id),
    constraint portfolio_performance_request_id_fkey foreign key (request_id) references public.allocation_requests (id) on delete cascade
);

create table public.llm_explanations (
    id            bigint      generated always as identity,
    request_id    uuid        not null,
    bullet_points text[]      not null,
    disclaimer    text        not null default 'This is an educational simulation, not regulated financial advice.',
    model_used    text,
    is_fallback   boolean     not null default false,
    created_at    timestamptz not null default now(),
    constraint llm_explanations_pkey           primary key (id),
    constraint llm_explanations_request_id_key unique (request_id),
    constraint llm_explanations_request_id_fkey foreign key (request_id) references public.allocation_requests (id) on delete cascade
);


-- ---------------------------------------------------------------------
-- Functions and triggers
-- ---------------------------------------------------------------------

-- Creates a profile row whenever someone signs up via Supabase Auth.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$function$;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $function$
begin
  new.updated_at = now();
  return new;
end;
$function$;

create trigger trg_on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

create trigger trg_profiles_updated_at
    before update on public.profiles
    for each row execute function public.set_updated_at();


-- ---------------------------------------------------------------------
-- Row Level Security
-- The backend uses the service-role key, which bypasses RLS, so it needs no
-- policies. These policies only govern what logged-in users can read
-- directly from the frontend.
-- ---------------------------------------------------------------------
alter table public.allocation_items      enable row level security;
alter table public.allocation_requests   enable row level security;
alter table public.chart_patterns        enable row level security;
alter table public.llm_explanations      enable row level security;
alter table public.market_data_cache     enable row level security;
alter table public.ml_signals            enable row level security;
alter table public.ohlcv_daily           enable row level security;
alter table public.portfolio_performance enable row level security;
alter table public.profiles              enable row level security;
alter table public.stocks                enable row level security;
alter table public.technical_features    enable row level security;

-- allocation_items
create policy "Users can view own allocation items" on public.allocation_items
    as permissive for select to public
    using (request_id in (select allocation_requests.id from allocation_requests where allocation_requests.user_id = auth.uid()));
create policy allocation_items_select_own on public.allocation_items
    as permissive for select to authenticated
    using (exists (select 1 from allocation_requests r where r.id = allocation_items.request_id and r.user_id = auth.uid()));

-- allocation_requests
create policy "Users can view own allocation requests" on public.allocation_requests
    as permissive for select to public
    using (auth.uid() = user_id);
create policy allocation_requests_select_own on public.allocation_requests
    as permissive for select to authenticated
    using (user_id = auth.uid());
create policy allocation_requests_insert_own on public.allocation_requests
    as permissive for insert to authenticated
    with check (user_id = auth.uid());
create policy allocation_requests_delete_own on public.allocation_requests
    as permissive for delete to authenticated
    using (user_id = auth.uid());

-- chart_patterns
create policy "Authenticated users can read chart_patterns" on public.chart_patterns
    as permissive for select to public
    using (auth.role() = 'authenticated');
create policy chart_patterns_select_authenticated on public.chart_patterns
    as permissive for select to authenticated
    using (true);

-- llm_explanations
create policy "Users can view own explanations" on public.llm_explanations
    as permissive for select to public
    using (request_id in (select allocation_requests.id from allocation_requests where allocation_requests.user_id = auth.uid()));
create policy llm_explanations_select_own on public.llm_explanations
    as permissive for select to authenticated
    using (exists (select 1 from allocation_requests r where r.id = llm_explanations.request_id and r.user_id = auth.uid()));

-- market_data_cache
create policy market_data_cache_select_authenticated on public.market_data_cache
    as permissive for select to authenticated
    using (true);

-- ml_signals
create policy "Authenticated users can read ml_signals" on public.ml_signals
    as permissive for select to public
    using (auth.role() = 'authenticated');
create policy ml_signals_select_authenticated on public.ml_signals
    as permissive for select to authenticated
    using (true);

-- ohlcv_daily
create policy "Authenticated users can read ohlcv_daily" on public.ohlcv_daily
    as permissive for select to public
    using (auth.role() = 'authenticated');
create policy ohlcv_daily_select_authenticated on public.ohlcv_daily
    as permissive for select to authenticated
    using (true);

-- portfolio_performance
create policy "Users can view own portfolio performance" on public.portfolio_performance
    as permissive for select to public
    using (request_id in (select allocation_requests.id from allocation_requests where allocation_requests.user_id = auth.uid()));
create policy portfolio_performance_select_own on public.portfolio_performance
    as permissive for select to authenticated
    using (exists (select 1 from allocation_requests r where r.id = portfolio_performance.request_id and r.user_id = auth.uid()));

-- profiles
create policy "Users can view own profile" on public.profiles
    as permissive for select to public
    using (auth.uid() = id);
create policy profiles_select_own on public.profiles
    as permissive for select to authenticated
    using (id = auth.uid());
create policy profiles_update_own on public.profiles
    as permissive for update to authenticated
    using (id = auth.uid())
    with check (id = auth.uid());

-- stocks
create policy "Authenticated users can read stocks" on public.stocks
    as permissive for select to public
    using (auth.role() = 'authenticated');
create policy stocks_select_authenticated on public.stocks
    as permissive for select to authenticated
    using (true);

-- technical_features
create policy "Authenticated users can read technical_features" on public.technical_features
    as permissive for select to public
    using (auth.role() = 'authenticated');
create policy technical_features_select_authenticated on public.technical_features
    as permissive for select to authenticated
    using (true);
