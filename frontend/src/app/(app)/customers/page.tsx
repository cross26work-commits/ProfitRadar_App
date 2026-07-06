"use client";

import { useEffect, useState } from "react";
import { CustomerListSection } from "@/components/sections/CustomerListSection";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import {
  getCustomersDashboard,
  type CustomersDashboardData,
} from "@/services/profitRadarService";

export default function CustomersPage() {
  const [dashboard, setDashboard] =
    useState<CustomersDashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getCustomersDashboard()
      .then(setDashboard)
      .catch((err) => {
        console.error("Customers load failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Customers load failed",
        );
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="顧客"
          description="顧客データの取得に失敗しました。"
        />
        <pre className="whitespace-pre-wrap rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-700">
          {error}
        </pre>
      </PageStack>
    );
  }

  if (!dashboard) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="顧客"
          description="顧客ごとの案件・利益・最終対応を確認します。"
        />
        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-bold text-slate-500">
          顧客データを読み込み中...
        </div>
      </PageStack>
    );
  }

  return (
    <PageStack>
      <DashboardHeroSection
        title="顧客"
        description="顧客ごとの案件・利益・最終対応を確認します。"
      />

      <ProfitSummarySection items={dashboard.stats} />

      <CustomerListSection
        title="顧客一覧"
        customers={dashboard.customers}
      />
    </PageStack>
  );
}
