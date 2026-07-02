import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn("Supabase env is not configured.");
}

export const supabase = createClient(
  supabaseUrl || "http://localhost:54321",
  supabaseAnonKey || "dev-placeholder"
);
