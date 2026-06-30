import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import { TaskListSection } from "@/components/sections/TaskListSection";
import { getHomeDashboard } from "@/services/profitRadarService";

export default async function HomePage() {
  const dashboard = await getHomeDashboard();

  return (
    <PageStack>
      <DashboardHeroSection
        title="今日の利益"
        description="本日見るべき利益候補と、優先対応を整理します。"
      />

      <ProfitSummarySection items={dashboard.stats} />

      <AIAdviceCard title="今日の最優先判断">
        利益見込が高く、返信遅延が発生している案件から対応してください。
        特に株式会社サンプルは本日中にフォローすることで、回収確度を維持できます。
      </AIAdviceCard>

      <TaskListSection title="今日やること" tasks={dashboard.tasks} />

      <ReplyQueueSection title="優先案件" leads={dashboard.priorityLeads} />

      <DangerLeadSection risks={dashboard.risks} />
    </PageStack>
  );
}
