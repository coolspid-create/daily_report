"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { createBrowserSupabase } from "@/lib/auth/supabase-browser";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const client = createBrowserSupabase();
      const { error: authError } = await client.auth.signInWithPassword({
        email: String(form.get("email")), password: String(form.get("password")),
      });
      if (authError) throw authError;
      router.replace("/admin");
      router.refresh();
    } catch {
      setError("로그인 정보 또는 관리자 권한을 확인해 주세요.");
      setPending(false);
    }
  }

  return (
    <form className="login-card" onSubmit={submit}>
      <label>이메일<input name="email" type="email" autoComplete="username" required /></label>
      <label>비밀번호<input name="password" type="password" autoComplete="current-password" required /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button type="submit" disabled={pending}>{pending ? "확인 중…" : "관리자 로그인"}</button>
    </form>
  );
}
