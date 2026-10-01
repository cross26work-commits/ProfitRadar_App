export type LegalReturnTarget = { href: string; label: string };

const allowedTargets: Record<string, string> = {
  "/settings/plan": "← 試用・契約へ戻る",
  "/settings": "← 設定へ戻る",
  "/register": "← 新規登録へ戻る",
};

export function resolveLegalReturn(returnTo: string | null, authenticated: boolean): LegalReturnTarget {
  if (returnTo && Object.hasOwn(allowedTargets, returnTo)) {
    return { href: returnTo, label: allowedTargets[returnTo] };
  }
  const href = authenticated ? "/settings" : "/register";
  return { href, label: allowedTargets[href] };
}
