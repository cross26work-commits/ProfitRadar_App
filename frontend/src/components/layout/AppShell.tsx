import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { BottomNav } from "./BottomNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F6F8FA]">
      <div className="flex min-h-screen">
        <Sidebar />

        <main className="min-w-0 flex-1 pb-[calc(6.5rem+env(safe-area-inset-bottom))] lg:pb-0">
          <Header />

          <div className="mx-auto w-full max-w-6xl px-5 py-7 md:px-8 lg:px-10">
            {children}
          </div>
        </main>
      </div>

      <BottomNav />
    </div>
  );
}
