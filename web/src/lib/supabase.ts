import { createClient } from "@supabase/supabase-js";
import type { Database } from "@/../lib/database.types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://iozdysrapznxefleqcfu.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "sb_publishable_VPVbNymUfDoW-dABTAQR8w_17Vih4je";

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false,
  },
});
