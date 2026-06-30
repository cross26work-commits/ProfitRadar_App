import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { ResultsSummarySection } from "@/components/sections/ResultsSummarySection";
import { getResultsDashboard } from "@/services/profitRadarService";

export default async function ResultsPage() {
  const results = await getResultsDashboard();

  return (
    <PageStack>
      <DashboardHeroSection
        title="実績"
        description="実回収・見込利益・対応結果を確認します。"
      />

      <ProfitSummarySection items={results.stats} />

      <ResultsSummarySection insights={results.insights} />
    </PageStack>
  );
}
