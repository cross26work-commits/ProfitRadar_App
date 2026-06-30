import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { Input } from "@/components/forms/Input";
import { Textarea } from "@/components/forms/Textarea";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { FormSection } from "@/components/sections/FormSection";
import { LeadOverviewSection } from "@/components/sections/LeadOverviewSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";
import { ActionBar } from "@/components/ui/ActionBar";
import { Button } from "@/components/ui/Button";
import { getLeadDetail } from "@/services/profitRadarService";

export default async function LeadDetailPage() {
  const lead = await getLeadDetail();

  return (
    <PageStack>
      <DashboardHeroSection
        title="見積のご確認について"
        description="案件詳細・AI判断・返信文・実利益を管理します。"
      />

      <ProfitSummarySection items={lead.stats} />

      <LeadOverviewSection />

      <AIAdviceCard title="AI分析">
        この案件は見積確認段階で停止しています。放置が続くと失注リスクが上がるため、
        相手の確認事項に対して短く明確に返信し、次の判断期限を提示してください。
      </AIAdviceCard>

      <FormSection
        title="返信文"
        description="送信前に内容を確認してください。現段階ではダミー表示です。"
      >
        <Textarea
          label="返信内容"
          defaultValue="お世話になっております。見積内容についてご確認ありがとうございます。条件面について改めて整理し、本日中にご連絡いたします。"
        />
        <ActionBar>
          <Button>送信する</Button>
          <Button variant="secondary">下書き保存</Button>
        </ActionBar>
      </FormSection>

      <FormSection title="実利益">
        <Input label="実回収額" placeholder="例：120000" />
        <ActionBar>
          <Button variant="secondary">保存する</Button>
        </ActionBar>
      </FormSection>

      <RecentActivitySection title="案件タイムライン" items={lead.timeline} />
    </PageStack>
  );
}
