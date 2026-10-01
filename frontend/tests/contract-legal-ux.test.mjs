import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";
import { build } from "esbuild";

async function loadTypeScriptModule(path) {
  const result = await build({
    entryPoints: [path],
    bundle: true,
    format: "esm",
    platform: "node",
    write: false,
  });
  const source = result.outputFiles[0].text;
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

const [{ getBillingPresentation }, { resolveLegalReturn }] = await Promise.all([
  loadTypeScriptModule("src/lib/billingPresentation.ts"),
  loadTypeScriptModule("src/lib/legalReturn.ts"),
]);

test("billing presentation does not claim a date before checkout completes", () => {
  const pending = getBillingPresentation({
    status: "trial_pending",
    first_billing_at: "2026-10-07T00:00:00Z",
    paid_until: null,
    trial_days: 7,
  });
  assert.equal(pending.statusLabel, "カード登録待ち");
  assert.equal(pending.scheduleAt, null);
  assert.equal(pending.scheduleKind, "unconfirmed");
  assert.match(pending.scheduleMessage, /課金日時はまだ確定していません/);
  assert.equal(pending.canStartCheckout, true);
  assert.equal(pending.canCancel, false);
});

test("billing presentation separates trialing, active, failed, and canceled states", () => {
  const input = {
    first_billing_at: "2026-10-07T00:00:00Z",
    paid_until: "2026-11-07T00:00:00Z",
    trial_days: 7,
  };
  const trialing = getBillingPresentation({ ...input, status: "trialing" });
  assert.equal(trialing.scheduleKind, "first_billing");
  assert.equal(trialing.scheduleAt, input.first_billing_at);
  assert.equal(trialing.canCancel, true);

  const active = getBillingPresentation({ ...input, status: "active" });
  assert.equal(active.scheduleKind, "renewal");
  assert.equal(active.scheduleAt, input.paid_until);

  assert.equal(getBillingPresentation({ ...input, status: "trialing", first_billing_at: null }).scheduleAt, null);
  assert.equal(getBillingPresentation({ ...input, status: "active", paid_until: null }).scheduleAt, null);

  for (const status of ["incomplete", "past_due", "unpaid", "paused", "canceled"]) {
    const presentation = getBillingPresentation({ ...input, status });
    assert.equal(presentation.scheduleAt, null, `${status} must not claim an exact billing date`);
  }
});

test("legal return targets accept only exact internal allowlisted paths", () => {
  assert.deepEqual(resolveLegalReturn("/settings/plan", true), {
    href: "/settings/plan",
    label: "← 試用・契約へ戻る",
  });
  assert.deepEqual(resolveLegalReturn("/register", false), {
    href: "/register",
    label: "← 新規登録へ戻る",
  });
  for (const unsafe of [
    "https://evil.example",
    "//evil.example",
    "/settings/plan?next=https://evil.example",
    "/settings/../admin",
    "/settings/plan/",
  ]) {
    assert.deepEqual(resolveLegalReturn(unsafe, true), {
      href: "/settings",
      label: "← 設定へ戻る",
    });
    assert.deepEqual(resolveLegalReturn(unsafe, false), {
      href: "/register",
      label: "← 新規登録へ戻る",
    });
  }
});

test("plan and signup legal links preserve a safe return context", async () => {
  const [plan, register, refund] = await Promise.all([
    readFile("src/app/(app)/settings/plan/page.tsx", "utf8"),
    readFile("src/app/(auth)/register/page.tsx", "utf8"),
    readFile("src/app/cancellation-refund/page.tsx", "utf8"),
  ]);
  assert.match(plan, /\/terms\?returnTo=%2Fsettings%2Fplan/);
  assert.match(plan, /\/privacy\?returnTo=%2Fsettings%2Fplan/);
  assert.match(plan, /\/cancellation-refund\?returnTo=%2Fsettings%2Fplan/);
  assert.match(register, /\/terms\?returnTo=%2Fregister/);
  assert.match(register, /\/privacy\?returnTo=%2Fregister/);
  assert.match(refund, /bg-white/);
  assert.match(refund, /text-slate-950/);
  assert.match(refund, /text-slate-800/);
  assert.match(refund, /text-emerald-800/);
});

test("customer-facing frontend source contains no legacy cross work branding", async () => {
  async function walk(path) {
    const entries = await readdir(path, { withFileTypes: true });
    const files = await Promise.all(entries.map((entry) => {
      const child = `${path}/${entry.name}`;
      return entry.isDirectory() ? walk(child) : [child];
    }));
    return files.flat();
  }
  const files = (await walk("src")).filter((path) => /\.(?:ts|tsx|js|jsx|css)$/.test(path));
  const matches = [];
  for (const path of files) {
    const source = await readFile(path, "utf8");
    if (/cross[ -]?work/i.test(source)) matches.push(path);
  }
  assert.deepEqual(matches, []);
});
