import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { CustomerProfileSection } from "@/components/sections/CustomerProfileSection";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { LeadListSection } from "@/components/sections/LeadListSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";
import { getCustomerDetail } from "@/services/profitRadarService";

export default async function CustomerDetailPage() {
  const customer = await getCustomerDetail();

  return (
    <PageStack>
      <DashboardHeroSection
        title="株式会社サンプル"
        description="顧客情報・タイムライン・利益・次の行動を一画面で確認します。"
      />

      <ProfitSummarySection items={customer.stats} />

      <CustomerProfileSection />

      <AIAdviceCard title="次の行動">
        見積確認で停止しているため、まずメールで軽く再確認してください。
        返信がなければSMSで短文確認に切り替える流れが妥当です。
      </AIAdviceCard>

      <LeadListSection title="関連案件" leads={customer.leads} />

      <RecentActivitySection title="タイムライン" items={customer.timeline} />
    </PageStack>
  );
}
