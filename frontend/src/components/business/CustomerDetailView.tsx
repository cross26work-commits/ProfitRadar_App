import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { CustomerProfileSection } from "@/components/sections/CustomerProfileSection";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { LeadListSection } from "@/components/sections/LeadListSection";
import { PageStack } from "@/components/sections/PageStack";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";
import type { ServerCustomerDetailData } from "@/services/serverProfitRadarService";
export function CustomerDetailView({customer}: {customer: ServerCustomerDetailData}) {
  return (
    <PageStack>
      <DashboardHeroSection
        title={customer.profile.name}
        description="顧客情報・タイムライン・利益・次の行動を一画面で確認します。"
      />

      <CustomerProfileSection profile={customer.profile} />

      <AIAdviceCard title="次の行動">{customer.profile.nextAction || "関連案件の根拠メールを確認してください。"}</AIAdviceCard>

      <LeadListSection title="関連案件" leads={customer.leads} />

      <RecentActivitySection title="タイムライン" items={customer.timeline} />
    </PageStack>
  );
}
