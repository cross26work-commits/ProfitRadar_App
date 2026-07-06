"use client";

import { useEffect, useState } from "react";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import {
  getReplyDashboard,
  type ReplyDashboardData,
} from "@/services/profitRadarService";

export default function ReplyPage() {
  const [dashboard, setDashboard] =
    useState<ReplyDashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getReplyDashboard()
      .then(setDashboard)
      .catch((err) => {
        console.error("Reply load failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Reply load failed",
        );
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今すぐ返信"
          description="返信候補の取得に失敗しました。"
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
          title="今すぐ返信"
          description="利益に直結する返信候補を優先順に表示します。"
        />
        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-bold text-slate-500">
          返信候補を読み込み中...
        </div>
      </PageStack>
    );
  }

  return (
    <PageStack>
      <DashboardHeroSection
        title="今すぐ返信"
        description="利益に直結する返信候補を優先順に表示します。"
      />

      <ProfitSummarySection items={dashboard.stats} />

      <ReplyQueueSection leads={dashboard.leads} />

      <DangerLeadSection
        title="返信判断ルール"
        risks={[
          "利益見込が高い",
          "放置日数が長い",
          "契約・見積・請求に近い",
        ]}
      />
    </PageStack>
  );
}
