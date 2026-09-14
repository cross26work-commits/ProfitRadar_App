"use client";

import { useEffect, useState } from "react";
import { FinancialSummary } from "@/components/business/FinancialSummary";
import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DashboardOverviewSection } from "@/components/sections/DashboardOverviewSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import {
  getHomeDashboard,
  type HomeDashboardData,
} from "@/services/profitRadarService";

export default function HomePage() {
  const [dashboard, setDashboard] = useState<HomeDashboardData | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    getHomeDashboard()
      .then(setDashboard)
      .catch((err) => {
        console.error("Dashboard load failed:", err);
        setError(err instanceof Error ? err.message : "Dashboard load failed");
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今日の利益"
          description="Dashboard APIの接続に失敗しました。"
        />
        <pre className="whitespace-pre-wrap rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-700">
          {error}
        </pre>
      </PageStack>
    );
  }

  if (!dashboard) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今日の利益"
          description="利益・今日やること・返信優先案件を確認します。"
        />
        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-bold text-slate-500">
          Dashboardを読み込み中...
        </div>
      </PageStack>
    );
  }

  return (
    <PageStack>
      <DashboardHeroSection
        title="今日の対応と収益"
        description="利益・今日やること・返信優先案件を確認します。"
      />

      <FinancialSummary />
      <p className="text-sm text-slate-500">以下の候補額は旧モデルの参考値で、確定収益ではありません。</p>
      <DashboardOverviewSection
        stats={dashboard.stats}
        tasks={dashboard.tasks}
      />

      <ReplyQueueSection title="今すぐ返信すべき案件" leads={dashboard.priorityLeads} />

      <AIAdviceCard
        title="今日の最優先判断"
        decision="高利益案件から返信してください"
        reason="返信遅延がある案件ほど、放置による失注リスクが上がります。"
        nextAction={dashboard.tasks[0]?.title ?? "本日すぐ対応すべき案件はありません。"}
      />

      <DangerLeadSection risks={dashboard.risks} />
    </PageStack>
  );
}
