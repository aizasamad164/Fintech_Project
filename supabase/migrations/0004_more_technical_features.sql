-- =====================================================================
-- 0004_more_technical_features.sql
--
-- Adds the extra indicator columns the backend now writes to
-- public.technical_features: MACD histogram, simple moving averages and
-- 20-day annualised volatility.
--
-- RUN THIS BEFORE the updated backend saves features, otherwise every
-- save fails with "column ... does not exist".
-- Safe to run more than once.
-- =====================================================================

alter table public.technical_features
    add column if not exists macd_hist     numeric,
    add column if not exists sma_50        numeric,
    add column if not exists sma_200       numeric,
    add column if not exists volatility_20 numeric;
