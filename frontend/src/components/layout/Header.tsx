"use client";

import Link from "next/link";

import { useAuth } from "@/providers/AuthProvider";

export function Header() {
  const { profile } = useAuth();

  const companyName = profile?.companyName || "会社未設定";

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-4 px-5 py-4 md:px-8 lg:px-10">
        <div className="hidden flex-1 md:block">
          <Link href="/leads" className="inline-block rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700">
            対応案件の一覧を見る
          </Link>
        </div>

        <Link
          href="/settings/plan"
          className="ml-auto flex items-center gap-3 rounded-xl px-3 py-2 text-right transition hover:bg-slate-50"
        >
          <div>
            <p className="max-w-[180px] truncate text-sm font-bold text-slate-900">
              {companyName}
            </p>

            <p className="text-xs text-slate-500">
              試用・契約状態を確認
            </p>
          </div>

          <span className="text-slate-400">›</span>
        </Link>
      </div>
    </header>
  );
}
