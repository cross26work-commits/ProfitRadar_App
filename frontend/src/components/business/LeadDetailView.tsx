import { AIAdviceCard } from "@/components/business/AIAdviceCard";
import { ReplyDraftForm } from "@/components/business/ReplyDraftForm";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { FormSection } from "@/components/sections/FormSection";
import { LeadOverviewSection } from "@/components/sections/LeadOverviewSection";
import { PageStack } from "@/components/sections/PageStack";
import { RecentActivitySection } from "@/components/sections/RecentActivitySection";

import Link from "next/link";
import type { getLeadDetailServer } from "@/services/profitRadarServerService";
export function LeadDetailView({lead}: {lead: Awaited<ReturnType<typeof getLeadDetailServer>>}) {
  return (
    <PageStack>
      <DashboardHeroSection
        title={lead.detail.subject}
        description="案件の詳細、AI判断、返信内容、実績を確認・管理します。"
      />

      <LeadOverviewSection lead={lead.detail} />

      <AIAdviceCard title="AI判断">
        <div className="space-y-4 text-sm">
          <div>
            <p className="font-bold text-slate-900">
              優先度
            </p>
            <p className="mt-1 text-slate-700">
              {lead.detail.priority}
            </p>
          </div>

          <div>
            <p className="font-bold text-slate-900">
              カテゴリ
            </p>
            <p className="mt-1 text-slate-700">
              {lead.detail.category}
            </p>
          </div>

          <div>
            <p className="font-bold text-slate-900">
              次の行動
            </p>
            <p className="mt-1 text-slate-700">
              {lead.detail.nextAction}
            </p>
          </div>
        </div>
      </AIAdviceCard>

      <FormSection
        title="返信文"
        description="AIが案件情報をもとに返信下書きを生成します。送信前に内容を確認してください。"
      >
        <ReplyDraftForm eventId={lead.detail.id} />
      </FormSection>

      <FormSection title="実績">
        <Link className="inline-block rounded-xl bg-indigo-700 px-4 py-3 text-white" href="/financials">売上・入金・原価を記録する</Link><p className="mt-2 text-sm">対象案件を選択し、受注額と入金・原価を区別して記録します。</p>
      </FormSection>

      <RecentActivitySection
        title="案件タイムライン"
        items={lead.timeline}
      />
    </PageStack>
  );
}
