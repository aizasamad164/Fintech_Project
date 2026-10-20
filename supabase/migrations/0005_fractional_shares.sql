-- =====================================================================
-- 0005_fractional_shares.sql
--
-- /api/v1/recommend returns fractional share counts (e.g. 0.3333 shares),
-- but allocation_items.shares was an integer. Widen it so saved allocations
-- keep the exact share count. Safe to run more than once.
-- The existing check (shares >= 0) is untouched.
-- =====================================================================

alter table public.allocation_items
    alter column shares type numeric(18, 6);
