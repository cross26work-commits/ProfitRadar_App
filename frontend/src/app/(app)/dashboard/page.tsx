import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DashboardOverviewSection } from "@/components/sections/DashboardOverviewSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import { getHomeDashboard } from "@/services/profitRadarService";

export default async function HomePage() {
  const dashboard = await getHomeDashboard();

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

      <ReplyQueueSection title="今すぐ返信すべき案件" leads={dashboard.priorityLeads} />

      <AIAdviceCard
        title="今日の最優先判断"
        decision="高利益案件から返信してください"
        reason="返信遅延がある案件ほど、放置による失注リスクが上がります。"
        nextAction="株式会社サンプルへ本日中にフォロー。"
      />

      <DangerLeadSection risks={dashboard.risks} />
    </PageStack>
  );
}
