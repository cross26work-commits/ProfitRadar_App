"use client";

import { useEffect, useState } from "react";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { LeadListSection } from "@/components/sections/LeadListSection";
import { PageStack } from "@/components/sections/PageStack";
import { apiGet } from "@/lib/api";
import { mapApiLeadToLead, type ApiLeadListResponse } from "@/services/profitRadarMappers";
import type { Lead } from "@/types/profit-radar";

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    void apiGet<ApiLeadListResponse>("/leads")
      .then((response) => setLeads((response.items || []).map(mapApiLeadToLead)))
      .catch(() => setError(true));
  }, []);

  return (
    <PageStack>
      <DashboardHeroSection title="案件" description="受注見込額と次の対応を確認します。" />
      {error ? <p className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">案件を取得できませんでした。</p> : null}
      {leads === null && !error ? <p className="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500">案件を読み込み中...</p> : null}
      {leads ? <LeadListSection title="案件一覧" leads={leads} /> : null}
    </PageStack>
  );
}
