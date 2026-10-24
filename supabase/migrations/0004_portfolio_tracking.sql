-- 0004: Saved portfolios + live tracking (report Appendix A) and chat history.
-- Run once in the Supabase SQL editor. Safe to re-run (IF NOT EXISTS / DROP POLICY IF EXISTS).
--
-- Changes vs. the report's draft DDL (see report section 7):
--   * TIMESTAMP WITH TIME ZONE (the draft's "WITH TIMEZONE" is invalid Postgres)
--   * Row-level security on every table: a signed-in user can only see their own rows.
--     The FastAPI backend uses the service-role key, which bypasses RLS by design.
--   * chat_history created here because 0003_add_chat_history.sql is empty.

-- 1. Master portfolio record ------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_portfolios (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL,
    portfolio_name     VARCHAR(100) DEFAULT 'My Advisory Portfolio',
    target_sector      VARCHAR(50)  DEFAULT 'All',
    risk_strategy      VARCHAR(20)  DEFAULT 'balanced',
    initial_investment NUMERIC(12, 2) NOT NULL,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_portfolios_user ON public.user_portfolios (user_id, created_at DESC);

-- 2. Individual positions (deleted automatically with their portfolio) -----
CREATE TABLE IF NOT EXISTS public.portfolio_positions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES public.user_portfolios(id) ON DELETE CASCADE,
    ticker       VARCHAR(10) NOT NULL,
    sector       VARCHAR(50) NOT NULL,
    shares_held  NUMERIC(12, 4) NOT NULL,
    buy_price    NUMERIC(12, 2) NOT NULL,
    cost_basis   NUMERIC(12, 2) NOT NULL,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON public.portfolio_positions (portfolio_id);

-- 3. Chat history used by app/llm/chat_session.py --------------------------
CREATE TABLE IF NOT EXISTS public.chat_history (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    metadata   JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON public.chat_history (session_id, created_at);

-- 4. Row-level security ------------------------------------------------------
ALTER TABLE public.user_portfolios     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history        ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Own portfolios" ON public.user_portfolios;
CREATE POLICY "Own portfolios" ON public.user_portfolios
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Own positions" ON public.portfolio_positions;
CREATE POLICY "Own positions" ON public.portfolio_positions
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.user_portfolios p
                WHERE p.id = portfolio_id AND p.user_id = auth.uid())
    ) WITH CHECK (
        EXISTS (SELECT 1 FROM public.user_portfolios p
                WHERE p.id = portfolio_id AND p.user_id = auth.uid())
    );
-- chat_history: no client policies; only the backend (service role) reads/writes it.
