import { createClient } from '@supabase/supabase-js';

// NFR-2.1: only the public anon key is used client-side — never the service role key.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
