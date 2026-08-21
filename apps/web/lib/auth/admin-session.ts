import type { User } from "@supabase/supabase-js";
import { createServerSupabase } from "./supabase-server";

function allowedByEmail(user: User): boolean {
  const allowed = (process.env.ADMIN_ALLOWED_EMAILS ?? "")
    .split(",")
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean);
  return Boolean(user.email && allowed.includes(user.email.toLowerCase()));
}

export async function getAdminUser(): Promise<User | null> {
  const supabase = await createServerSupabase();
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) return null;
  const role = data.user.app_metadata?.role;
  return role === "admin" || allowedByEmail(data.user) ? data.user : null;
}
