-- =====================================================================
-- 0002_cleanup_policies_and_sector_check.sql
--
-- RUN THIS ONE on your existing Supabase database (SQL Editor -> paste -> Run).
-- It is safe to run more than once, and safe on a fresh database after 0001.
--
-- 1) Removes duplicate RLS policies. Every table currently has two SELECT
--    policies that do the same thing (an old "Users can view ..." one and a
--    newer "*_select_own / *_select_authenticated" one). Permissive policies
--    are OR-ed together, so the duplicates change nothing except clutter.
--    The newer ones stay; nothing gets more or less access.
--
-- 2) Fixes allocation_requests_sector_logic_check. The old version let a
--    non-combined request with an EMPTY sectors array through, because
--    array_length('{}', 1) is NULL and a CHECK that evaluates to NULL passes.
--    Rule enforced now:
--       is_combined = true   ->  sectors must be empty  ('{}')
--       is_combined = false  ->  sectors must have at least one entry
-- =====================================================================

-- 1) Duplicate policies ------------------------------------------------
drop policy if exists "Users can view own allocation items"            on public.allocation_items;
drop policy if exists "Users can view own allocation requests"         on public.allocation_requests;
drop policy if exists "Authenticated users can read chart_patterns"    on public.chart_patterns;
drop policy if exists "Users can view own explanations"                on public.llm_explanations;
drop policy if exists "Authenticated users can read ml_signals"        on public.ml_signals;
drop policy if exists "Authenticated users can read ohlcv_daily"       on public.ohlcv_daily;
drop policy if exists "Users can view own portfolio performance"       on public.portfolio_performance;
drop policy if exists "Users can view own profile"                     on public.profiles;
drop policy if exists "Authenticated users can read stocks"            on public.stocks;
drop policy if exists "Authenticated users can read technical_features" on public.technical_features;

-- 2) Sector check ------------------------------------------------------
-- One statement, so it is all-or-nothing: if any existing row breaks the new
-- rule the whole ALTER fails and the old constraint stays in place.
alter table public.allocation_requests
    drop constraint if exists allocation_requests_sector_logic_check,
    add constraint allocation_requests_sector_logic_check
    check (
        (is_combined     and coalesce(cardinality(sectors), 0) = 0)
        or
        (not is_combined and coalesce(cardinality(sectors), 0) > 0)
    );
