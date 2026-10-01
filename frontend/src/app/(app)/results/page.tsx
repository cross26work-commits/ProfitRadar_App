"use client";

import { useEffect, useState } from "react";
import { FinancialSummary } from "@/components/business/FinancialSummary";
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
      .catch(() => {
        setError("実績データを取得できませんでした。接続状態を確認して再読み込みしてください。");
      });
  }, []);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="実績"
          description="実績データの取得に失敗しました。"
        />
        <p role="alert" className="rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-800">
          {error}
        </p>
        <button type="button" className="relative z-10 rounded-xl bg-indigo-700 px-4 py-3 font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700" onClick={() => window.location.reload()}>再読み込み</button>
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

      <FinancialSummary variant="full" />
      <p className="text-sm text-slate-500">以下は旧モデルの参考値です。上記の手動確定収益とは別集計です。</p>
      <ProfitSummarySection items={results.stats} />

      <SalesForecastSection forecast={results.forecast} />

      <SelfEvaluationSection evaluation={results.selfEvaluation} />

      <ResultsSummarySection insights={results.insights} />
    </PageStack>
  );
}
