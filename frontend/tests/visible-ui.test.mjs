import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(path, "utf8");
const [plan, mail, chart, legacyChart, results, mapper, mock] = await Promise.all([
  read("src/app/(app)/settings/plan/page.tsx"),
  read("src/app/(app)/settings/mail/page.tsx"),
  read("src/components/ui/ChartCard.tsx"),
  read("src/components/sections/ResultChartPlaceholder.tsx"),
  read("src/components/sections/ResultsSummarySection.tsx"),
  read("src/services/profitRadarMappers.ts"),
  read("src/data/mock.ts"),
]);

test("plan copy stays readable while only unavailable controls look disabled", () => {
  assert.match(plan, /text-slate-900/);
  assert.match(plan, /border-slate-300 bg-white/);
  assert.match(plan, /disabled:bg-slate-300 disabled:text-slate-700/);
  assert.doesNotMatch(plan, /disabled:opacity-/);
  assert.match(plan, /申込みには、上の5項目を確認してチェックしてください。/);
  assert.match(plan, /解約できる有効な契約はありません。/);
});

test("results use customer-facing empty states instead of development placeholders", () => {
  assert.doesNotMatch(chart, /グラフ表示エリア/);
  assert.doesNotMatch(legacyChart, /Chart Placeholder/);
  assert.doesNotMatch(results, /表示予定/);
  assert.doesNotMatch(mapper, /API接続済み/);
  assert.match(chart, /まだ推移を表示できるデータがありません。/);
  assert.match(legacyChart, /まだ推移を表示できるデータがありません。/);
});

test("customer-facing fixture branding uses COROS WORK", () => {
  assert.match(mock, /COROS WORK/);
  assert.doesNotMatch(mock, /CROSS WORK/);
});

test("Google connection errors distinguish local config and provider failures", () => {
  assert.match(mail, /ローカル・テスト環境ではGoogle OAuthが設定されていません/);
  assert.match(mail, /Google連携の本番設定が完了していません/);
  assert.match(mail, /一時的な接続障害の可能性があります/);
  assert.doesNotMatch(mail, /console\.error/);
  assert.doesNotMatch(mail, /Microsoft Graphによる接続に対応予定/);
  assert.doesNotMatch(mail, /IMAP\/SMTP対応サービス向けの接続方式/);
});
