// Isolated UI fixture only. CSP forbids external transport; no Auth/DB/Stripe is contacted.
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { existsSync } from "node:fs";

const edge = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync(edge) ? edge : undefined);
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
const viewports = [
  { name: "desktop", width: 1280, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];
const scenarios = [
  { route: "/settings/plan", state: "normal", expected: "カード登録待ち" },
  { route: "/settings/plan", state: "trialing", expected: "初回課金予定" },
  { route: "/terms", state: "normal", returnTo: "/settings/plan", expected: "← 試用・契約へ戻る" },
  { route: "/privacy", state: "normal", returnTo: "/settings/plan", expected: "← 試用・契約へ戻る" },
  { route: "/cancellation-refund", state: "normal", returnTo: "/settings/plan", expected: "← 試用・契約へ戻る" },
  { route: "/terms", state: "unauthenticated", expected: "← 新規登録へ戻る" },
  { route: "/terms", state: "normal", returnTo: "https://evil.example", expected: "← 設定へ戻る" },
];
const failures = [];
const reports = [];

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    for (const scenario of scenarios) {
      const params = new URLSearchParams({ page: scenario.route, state: scenario.state });
      if (scenario.returnTo) params.set("returnTo", scenario.returnTo);
      await page.goto(`http://127.0.0.1:3190/?${params}`);
      await page.waitForTimeout(250);
      const report = await page.evaluate(({ route, state, expected }) => {
        const text = document.body.innerText;
        return {
          route,
          state,
          text,
          expectedFound: text.includes(expected),
          horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
          bottomNavPresent: Boolean(document.querySelector("nav.fixed")),
          externalHrefPresent: [...document.querySelectorAll("a")].some((link) => /evil\.example/.test(link.href)),
        };
      }, scenario);
      if (scenario.route === "/cancellation-refund") {
        const accessibility = await new AxeBuilder({ page }).include("article").withRules(["color-contrast"]).analyze();
        report.contrastViolations = accessibility.violations.length;
      }
      reports.push({ viewport: viewport.name, ...report });
      if (!report.expectedFound) failures.push(`${viewport.name} ${scenario.route}: expected copy missing`);
      if (report.horizontalOverflow) failures.push(`${viewport.name} ${scenario.route}: horizontal overflow`);
      if (scenario.route.startsWith("/settings/") === false && scenario.route !== "/settings/plan" && report.bottomNavPresent) {
        failures.push(`${viewport.name} ${scenario.route}: public legal page has BottomNav`);
      }
      if (report.externalHrefPresent) failures.push(`${viewport.name} ${scenario.route}: external returnTo was rendered`);
      if (scenario.route === "/settings/plan" && scenario.state === "normal") {
        if (!report.text.includes("課金日時はまだ確定していません")) failures.push(`${viewport.name} plan: unconfirmed schedule copy missing`);
        if (report.text.includes("初回課金予定:")) failures.push(`${viewport.name} plan: exact date shown before checkout`);
      }
      if ((report.contrastViolations ?? 0) > 0) failures.push(`${viewport.name} refund: color contrast violation`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}

console.log(JSON.stringify({ reports: reports.map((report) => ({ ...report, text: undefined })), failures }, null, 2));
if (failures.length) process.exitCode = 1;
