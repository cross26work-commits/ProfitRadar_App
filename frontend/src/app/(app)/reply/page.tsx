import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import { getReplyDashboard } from "@/services/profitRadarService";

export default async function ReplyPage() {
  const dashboard = await getReplyDashboard();

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
        risks={["利益見込が高い", "放置日数が長い", "契約・見積・請求に近い"]}
      />
    </PageStack>
  );
}
