-- 0009: StockSense Pro subscriptions (one row per user), kept in sync with Stripe
-- by the backend (/api/billing/confirm and the Stripe webhook). Run once in the
-- Supabase SQL editor. Safe to re-run.

CREATE TABLE IF NOT EXISTS public.subscriptions (
    user_id                UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_customer_id     TEXT UNIQUE,
    stripe_subscription_id TEXT,
    status                 TEXT NOT NULL DEFAULT 'none',   -- Stripe status: active, trialing, past_due, canceled, incomplete...
    cancel_at_period_end   BOOLEAN NOT NULL DEFAULT FALSE,
    current_period_end     TIMESTAMP WITH TIME ZONE,
    simulated              BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Users may read their own row; only the backend (service role) writes.
DROP POLICY IF EXISTS "Read own subscription" ON public.subscriptions;
CREATE POLICY "Read own subscription" ON public.subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- Saved portfolios now belong to real Supabase accounts
DO $$ BEGIN
    ALTER TABLE public.user_portfolios
        ADD CONSTRAINT user_portfolios_user_fk FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
