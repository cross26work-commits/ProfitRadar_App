import { CustomerListSection } from "@/components/sections/CustomerListSection";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { getCustomersDashboard } from "@/services/profitRadarService";

export default async function CustomersPage() {
  const dashboard = await getCustomersDashboard();

  return (
    <PageStack>
      <DashboardHeroSection
        title="顧客"
        description="顧客ごとの案件・利益・最終対応を確認します。"
      />

      <ProfitSummarySection items={dashboard.stats} />

      <CustomerListSection title="顧客一覧" customers={dashboard.customers} />
    </PageStack>
  );
}
