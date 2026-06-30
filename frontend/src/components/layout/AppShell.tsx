import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { BottomNav } from "./BottomNav";

export function AppShell({
  children,
  title = "今日の利益",
  subtitle = "AIが今日の優先行動を整理します。",
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex">
        <Sidebar />
        <main className="min-w-0 flex-1 pb-20 lg:pb-0">
          <Header title={title} subtitle={subtitle} />
          <div className="px-4 py-6 lg:px-8">{children}</div>
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
