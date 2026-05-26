import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Browser client only — safe to use in client components
export function createClient() {
  return createBrowserClient(supabaseUrl, supabaseAnonKey)
}
