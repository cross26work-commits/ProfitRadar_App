// Isolated UI fixture only. CSP forbids external transport; no Auth/DB is contacted.
import { chromium } from "playwright";
import { existsSync } from "node:fs";

const edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync(edge) ? edge : undefined);
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const routes = [
  ["/dashboard", "normal"],
  ["/dashboard", "empty"],
  ["/customers", "empty"],
  ["/results", "normal"],
  ["/results", "empty"],
  ["/financials", "normal"],
  ["/reply", "empty"],
  ["/settings", "normal"],
];
const reports = [];

try {
  for (const [route, state] of routes) {
    const params = new URLSearchParams({ page: route, state });
    await page.goto(`http://127.0.0.1:3190/?${params}`);
    await page.waitForTimeout(400);
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    reports.push(await page.evaluate(({ route, state }) => {
      const text = document.body.innerText;
      const nav = document.querySelector("nav.fixed");
      const stack = document.querySelector("main > div > div");
      const last = stack?.lastElementChild;
      const main = document.querySelector("main");
      const financialHeading = [...document.querySelectorAll("h2")].find((node) =>
        node.textContent?.includes("今月の簡易実績") || node.textContent?.includes("今月の売上・入金・原価・粗利"),
      );
      const financialSection = financialHeading?.closest("section");
      return {
        route,
        state,
        bodyText: text,
        horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        navOverlap: Boolean(nav && last && last.getBoundingClientRect().bottom > nav.getBoundingClientRect().top + 1),
        dateInputs: document.querySelectorAll('input[type="date"]').length,
        mainPaddingBottom: main ? getComputedStyle(main).paddingBottom : "missing",
        financialMetrics: financialSection ? [...financialSection.querySelectorAll("dl > div")].slice(0, 4).map((node) => ({
          label: node.querySelector("dt")?.textContent?.trim(),
          value: node.querySelector("dd")?.textContent?.trim(),
        })) : [],
      };
    }, { route, state }));
  }
} finally {
  await browser.close();
}

const find = (route, state) => reports.find((item) => item.route === route && item.state === state);
const dashboard = find("/dashboard", "empty");
const dashboardNormal = find("/dashboard", "normal");
const customers = find("/customers", "empty");
const results = find("/results", "empty");
const resultsNormal = find("/results", "normal");
const financials = find("/financials", "normal");
const failures = [];

for (const item of reports) {
  if (item.horizontalOverflow) failures.push(`${item.route} (${item.state}): horizontal overflow`);
  if (item.navOverlap) failures.push(`${item.route} (${item.state}): bottom nav overlap`);
}
if (dashboard.dateInputs !== 0) failures.push("dashboard contains financial period inputs");
if (!dashboard.bodyText.includes("今月の簡易実績") || !dashboard.bodyText.includes("実績の詳細を見る")) failures.push("dashboard compact summary missing");
if (!dashboard.bodyText.includes("現在、優先対応案件はありません") || !dashboard.bodyText.includes("メールを更新・確認")) failures.push("dashboard empty advice/CTA mismatch");
if (dashboard.bodyText.includes("現在の注意点")) failures.push("empty danger section rendered");
if (!customers.bodyText.includes("顧客一覧") || customers.bodyText.includes("今月の売上・入金・原価・粗利")) failures.push("customers information architecture mismatch");
if (results.dateInputs !== 2 || !results.bodyText.includes("顧客別の集計") || !results.bodyText.includes("売上・入金・原価を記録する")) failures.push("results full financial UI missing");
if ((dashboard.bodyText.match(/未記録・不明/g) ?? []).length < 4) failures.push("dashboard null values were not preserved");
if (JSON.stringify(dashboardNormal.financialMetrics) !== JSON.stringify(resultsNormal.financialMetrics)) failures.push("dashboard/results current-month financial values differ");
if (JSON.stringify(dashboard.financialMetrics) !== JSON.stringify(results.financialMetrics)) failures.push("dashboard/results unknown financial states differ");
if (financials.financialMetrics.length !== 0 || !financials.bodyText.includes("売上・入金・原価の記録") || !financials.bodyText.includes("確認した金額を保存")) failures.push("financials is not limited to the recording workflow");

console.log(JSON.stringify({
  checks: reports.map((item) => ({
    route: item.route,
    state: item.state,
    horizontalOverflow: item.horizontalOverflow,
    navOverlap: item.navOverlap,
    dateInputs: item.dateInputs,
    mainPaddingBottom: item.mainPaddingBottom,
    financialMetrics: item.financialMetrics,
  })),
  dashboardUnknownCount: (dashboard.bodyText.match(/未記録・不明/g) ?? []).length,
  failures,
}, null, 2));

if (failures.length) process.exitCode = 1;
