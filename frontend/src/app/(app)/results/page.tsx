"use client";

import { useEffect, useState } from "react";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { PageStack } from "@/components/sections/PageStack";
import { ProfitSummarySection } from "@/components/sections/ProfitSummarySection";
import { ResultsSummarySection } from "@/components/sections/ResultsSummarySection";
import { SalesForecastSection } from "@/components/sections/SalesForecastSection";
import { SelfEvaluationSection } from "@/components/sections/SelfEvaluationSection";
import {
  getResultsDashboard,
  type ResultsDashboardData,
} from "@/services/profitRadarService";

export default function ResultsPage() {
  const [results, setResults] =
    useState<ResultsDashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getResultsDashboard()
      .then(setResults)
      .catch((err) => {
        console.error("Results load failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Results load failed",
        );
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="実績"
          description="実績データの取得に失敗しました。"
        />
        <pre className="whitespace-pre-wrap rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-700">
          {error}
        </pre>
      </PageStack>
    );
  }

  if (!results) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="実績"
          description="実回収・見込利益・対応結果を確認します。"
        />
        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-bold text-slate-500">
          実績データを読み込み中...
        </div>
      </PageStack>
    );
  }

  return (
    <PageStack>
      <DashboardHeroSection
        title="実績"
        description="実回収・見込利益・対応結果を確認します。"
      />

      <ProfitSummarySection items={results.stats} />

      <SalesForecastSection forecast={results.forecast} />

      <SelfEvaluationSection evaluation={results.selfEvaluation} />

      <ResultsSummarySection insights={results.insights} />
    </PageStack>
  );
}
