"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_NAME, navItems } from "@/lib/constants";
import { useAuth } from "@/providers/AuthProvider";

export function Sidebar() {
  const pathname = usePathname();
  const { session, profile } = useAuth();

  const userName =
    profile?.name ||
    session?.user.user_metadata?.full_name ||
    session?.user.email?.split("@")[0] ||
    "ユーザー";

  const email = session?.user.email ?? "";

  return (
    <aside className="relative hidden h-screen w-64 shrink-0 border-r border-slate-200 bg-white px-4 py-6 lg:block">
      <div className="mb-10 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-green-600 text-lg font-black text-white">
          P
        </div>

        <div>
          <p className="text-lg font-black tracking-tight text-slate-900">
            {APP_NAME}
          </p>
          <p className="text-xs font-medium text-slate-500">
            AI Sales OS
          </p>
        </div>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition ${
                active
                  ? "bg-green-50 text-green-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <span className="h-2 w-2 rounded-full bg-current" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-6 left-4 right-4 border-t border-slate-200 pt-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
            {userName.slice(0, 1).toUpperCase()}
          </div>

          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-slate-900">
              {userName}
            </p>

            {email && (
              <p className="truncate text-xs text-slate-500">
                {email}
              </p>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}