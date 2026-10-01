"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FinancialSummary } from "@/components/business/FinancialSummary";
import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DashboardOverviewSection } from "@/components/sections/DashboardOverviewSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import { Button } from "@/components/ui/Button";
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
      .catch(() => {
        setError("データを取得できませんでした。接続状態を確認して再読み込みしてください。");
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今日の利益"
          description="Dashboard APIの接続に失敗しました。"
        />
        <p role="alert" className="rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-800">
          {error}
        </p>
        <button type="button" className="relative z-10 rounded-xl bg-indigo-700 px-4 py-3 font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700" onClick={() => window.location.reload()}>再読み込み</button>
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

  const priorityLead = dashboard.priorityLeads[0];
  const hasPriorityLead = Boolean(priorityLead);
  const hasRisk = dashboard.risks.length > 0;
  const advice = hasPriorityLead
    ? {
        decision: `${priorityLead.customer}の案件を優先してください`,
        reason: `${priorityLead.subject} / 期待値 ${priorityLead.profit} / 優先度 ${priorityLead.priority}`,
        nextAction: priorityLead.nextAction ?? "案件内容を確認して返信してください。",
      }
    : hasRisk
      ? {
          decision: "注意が必要な案件を確認してください",
          reason: dashboard.risks[0],
          nextAction: "注意点を確認し、必要な対応を判断してください。",
        }
      : {
          decision: "現在、優先対応案件はありません",
          reason: "本日すぐ対応が必要な返信候補・危険案件はありません。",
          nextAction: "メールを更新して新着を確認するか、新しい営業機会の確認を進めてください。",
        };

  return (
    <PageStack>
      <DashboardHeroSection
        title="今日の利益"
        description="利益・今日やること・返信優先案件を確認します。"
      />

      <DashboardOverviewSection
        stats={dashboard.stats}
        tasks={dashboard.tasks}
      />
      <p className="text-sm text-slate-500">上記の候補額は旧モデルの参考値で、確定収益ではありません。</p>

      <ReplyQueueSection title="今すぐ返信すべき案件" leads={dashboard.priorityLeads} />

      <AIAdviceCard
        title="今日の最優先判断"
        decision={advice.decision}
        reason={advice.reason}
        nextAction={advice.nextAction}
      />

      <div>
        <Link href="/reply">
          <Button>{hasPriorityLead ? "今すぐ返信へ" : "メールを更新・確認"}</Button>
        </Link>
      </div>

      {hasRisk ? <DangerLeadSection risks={dashboard.risks} /> : null}

      <FinancialSummary variant="compact" />
    </PageStack>
  );
}
