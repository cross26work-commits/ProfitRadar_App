import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const page = await readFile("src/app/onboarding/page.tsx", "utf8");
const profileService = await readFile(
  "src/services/profile/profileService.ts",
  "utf8",
);
const onboardingService = await readFile(
  "src/services/onboarding/onboardingService.ts",
  "utf8",
);

test("profile loading uses the deployed full_name column", () => {
  const queryStart = profileService.indexOf('.from("profiles")', profileService.indexOf("getCurrentAppProfile"));
  const queryEnd = profileService.indexOf('.eq("user_id"', queryStart);
  const profileQuery = profileService.slice(queryStart, queryEnd);

  assert.match(profileQuery, /user_id,\s+full_name,\s+role,/);
  assert.doesNotMatch(profileQuery, /user_id,\s+name,\s+role,/);
});

test("onboarding sends business consent and waits for readable profile", () => {
  assert.match(onboardingService, /business_use_confirmed:/);
  assert.match(page, /await refreshProfile\(\)/);
  assert.match(page, /completedProfile\?\.companyId/);
});

test("successful onboarding routes directly to dashboard", () => {
  assert.match(page, /router\.replace\("\/dashboard"\)/);
  assert.doesNotMatch(page, /router\.replace\("\/settings\/plan"\)/);
});

test("business-use consent is visible and incomplete input explains disabled submit", () => {
  assert.match(page, /bg-white/);
  assert.match(page, /text-slate-900/);
  assert.match(page, /focus-within:ring-2/);
  assert.match(page, /has-\[:checked\]:bg-emerald-50/);
  assert.match(page, /会社名、お名前、事業利用の確認をすべて入力すると開始できます。/);
});
