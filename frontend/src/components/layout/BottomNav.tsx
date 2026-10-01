"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItems } from "@/lib/constants";

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-20 grid grid-cols-5 border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] lg:hidden">
      {navItems.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);

        return (
          <Link
            key={item.label}
            href={item.href}
            className={`py-3 text-center text-[11px] font-bold ${
              active ? "text-green-700" : "text-slate-500"
            }`}
          >
            <div className="mx-auto mb-1 h-1.5 w-1.5 rounded-full bg-current" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
