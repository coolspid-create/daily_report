import { LoginForm } from "@/features/admin-review/components/login-form";

export default function AdminLoginPage() {
  return (
    <main className="login-shell">
      <div><p className="eyebrow">CURATION ADMIN</p><h1>관리자 로그인</h1><p>승인된 운영자 계정만 검수 작업대에 접근할 수 있습니다.</p></div>
      <LoginForm />
    </main>
  );
}
