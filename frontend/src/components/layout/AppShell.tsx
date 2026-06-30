import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { BottomNav } from "./BottomNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F6F8FA]">
      <div className="flex min-h-screen">
        <Sidebar />

        <main className="min-w-0 flex-1 pb-20 lg:pb-0">
          <Header
            title="Profit Radar"
            subtitle="3秒で利益と今日やることを把握します。"
          />

          <div className="mx-auto w-full max-w-6xl px-5 py-7 md:px-8 lg:px-10">
            {children}
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
