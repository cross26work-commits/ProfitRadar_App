import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { ActualProfitForm } from "@/components/business/ActualProfitForm";
import { ReplyDraftForm } from "@/components/business/ReplyDraftForm";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { FormSection } from "@/components/sections/FormSection";
import { LeadOverviewSection } from "@/components/sections/LeadOverviewSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";
import { getLeadDetail } from "@/services/profitRadarService";

type LeadDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function LeadDetailPage({ params }: LeadDetailPageProps) {
  const { id } = await params;
  const lead = await getLeadDetail(id);

  return (
    <PageStack>
      <DashboardHeroSection
        title={lead.detail.subject}
        description="案件詳細・AI判断・返信文・実利益を管理します。"
      />

      <ProfitSummarySection items={lead.stats} />

      <LeadOverviewSection lead={lead.detail} />

      <AIAdviceCard title="AI分析">
        <div className="space-y-4 text-sm">

          <div>
            <p className="font-bold">AI判断</p>
            <p>{lead.detail.priority}</p>
          </div>

          <div>
            <p className="font-bold">カテゴリ</p>
            <p>{lead.detail.category}</p>
          </div>

          <div>
            <p className="font-bold">次の行動</p>
            <p>{lead.detail.nextAction}</p>
          </div>

        </div>
      </AIAdviceCard>

      <FormSection
        title="返信文"
        description="AIが案件情報から返信下書きを生成します。送信前に内容を確認してください。"
      >
        <ReplyDraftForm eventId={lead.detail.id} />
      </FormSection>

      <FormSection title="実利益">
        <ActualProfitForm eventId={lead.detail.id} />
      </FormSection>

      <RecentActivitySection title="案件タイムライン" items={lead.timeline} />
    </PageStack>
  );
}
