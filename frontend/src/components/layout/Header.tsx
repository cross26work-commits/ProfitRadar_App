"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import { Button } from "@/components/ui/Button";
import { getAuthMe } from "@/services/auth/meService";

export function Header({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  const router = useRouter();
  const { session, profile, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.replace("/login");
    router.refresh();
  }

  async function handleAuthMeTest() {
    const result = await getAuthMe();
    console.log("AUTH ME:", result);
    alert("JWT認証OK: /auth/me");
  }

  const userLabel = profile?.name ?? session?.user.email ?? "未取得";
  const companyLabel = profile?.companyName ?? "未設定";
  const planLabel = profile?.plan ?? "free";

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-5 py-5 md:px-8 lg:px-10">
        <div>
          <p className="text-2xl font-black tracking-tight text-slate-950">{title}</p>
          <p className="mt-1 text-sm font-medium text-slate-500">{subtitle}</p>
        </div>

        <div className="hidden w-full max-w-sm rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-400 md:block">
          顧客名・案件名で検索...
        </div>

        <div className="hidden items-center gap-3 lg:flex">
          <div className="text-right">
            <p className="text-xs font-bold text-slate-500">
              {companyLabel} / {planLabel}
            </p>
            <p className="max-w-[180px] truncate text-sm font-black text-slate-900">
              {userLabel}
            </p>
          </div>

          <Button variant="secondary" onClick={handleAuthMeTest}>
            認証確認
          </Button>

          <Button variant="secondary" onClick={handleLogout}>
            ログアウト
          </Button>
        </div>
      </div>
    </header>
  );
}
