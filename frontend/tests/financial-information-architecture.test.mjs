import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(path, "utf8");
const [financial, dashboard, customers, results, financials, overview, danger, service, shell, nav] = await Promise.all([
  read("src/components/business/FinancialSummary.tsx"),
  read("src/app/(app)/dashboard/page.tsx"),
  read("src/app/(app)/customers/page.tsx"),
  read("src/app/(app)/results/page.tsx"),
  read("src/app/(app)/financials/page.tsx"),
  read("src/components/sections/DashboardOverviewSection.tsx"),
  read("src/components/sections/DangerLeadSection.tsx"),
  read("src/services/profitRadarService.ts"),
  read("src/components/layout/AppShell.tsx"),
  read("src/components/layout/BottomNav.tsx"),
]);

test("dashboard compact and results full use the shared financial summary source", () => {
  assert.match(financial, /variant\?: "full" \| "compact"/);
  assert.match(financial, /apiGet<Summary>\("\/financials\/summary"\)/);
  assert.match(dashboard, /<FinancialSummary variant="compact"/);
  assert.match(results, /<FinancialSummary variant="full"/);
  assert.match(financial, /value === null \? "未記録・不明"/);
  assert.doesNotMatch(dashboard, /<FinancialSummary \/>/);
});

test("customers are customer-first and no longer request unused result stats", () => {
  assert.doesNotMatch(customers, /FinancialSummary/);
  const customerLoader = service.slice(
    service.indexOf("export async function getCustomersDashboard"),
    service.indexOf("export async function getCustomerDetail"),
  );
  assert.match(customerLoader, /apiGet<ApiCustomerListResponse>\("\/customers"\)/);
  assert.doesNotMatch(customerLoader, /getDashboardStats/);
});

test("financials remains a recording workspace while results owns analysis", () => {
  assert.doesNotMatch(financials, /FinancialSummary/);
  assert.match(financials, /売上・入金・原価の記録/);
  assert.match(financials, /確認した金額を保存/);
  assert.match(results, /<FinancialSummary variant="full"/);
});

test("empty dashboard advice and actions reflect current data", () => {
  assert.match(dashboard, /現在、優先対応案件はありません/);
  assert.match(dashboard, /本日すぐ対応が必要な返信候補・危険案件はありません。/);
  assert.match(dashboard, /メールを更新・確認/);
  assert.doesNotMatch(dashboard, /decision="高利益案件から返信してください"/);
  assert.doesNotMatch(overview, /利益に直結する返信から処理/);
});

test("empty risks render nothing and mobile content clears the fixed nav", () => {
  assert.match(danger, /if \(risks\.length === 0\) return null/);
  assert.match(shell, /pb-\[calc\(6\.5rem\+env\(safe-area-inset-bottom\)\)\]/);
  assert.match(nav, /pb-\[env\(safe-area-inset-bottom\)\]/);
});
