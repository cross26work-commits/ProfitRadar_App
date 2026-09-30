type Environment = Record<string, string | undefined>;

const required = [
  "SELLER_NAME", "SUPPORT_EMAIL",
  "REFUND_POLICY", "CANCELLATION_POLICY", "PRIVACY_CONTACT",
  "INTERNATIONAL_TRANSFER_DISCLOSURE", "DATA_DELETION_POLICY", "GOVERNING_COURT",
  "TERMS_EFFECTIVE_DATE", "DATA_RETENTION_DAYS", "BACKUP_RETENTION_DAYS",
] as const;

function placeholder(value: string): boolean {
  return /(?:TODO|TBD|未定|未入力|placeholder|example\.com|example\.invalid)/i.test(value);
}

export function publicationReady(env: Environment): boolean {
  if (env.SALES_PUBLICATION_APPROVED !== "true" || env.LEGAL_REVIEW_APPROVED !== "true" ||
      env.COMMERCIAL_DISCLOSURE_APPROVED !== "true") return false;
  for (const name of required) {
    const value = env[name]?.trim() ?? "";
    if (!value || placeholder(value)) return false;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(env.SUPPORT_EMAIL ?? "")) return false;
  if (env.SELLER_ADDRESS_DISCLOSURE_MODE !== "request" || env.SELLER_PHONE_DISCLOSURE_MODE !== "request") return false;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(env.TERMS_EFFECTIVE_DATE ?? "")) return false;
  for (const name of ["DATA_RETENTION_DAYS", "BACKUP_RETENTION_DAYS"] as const) {
    const days = Number(env[name]);
    if (!Number.isInteger(days) || days < 1 || days > 3650) return false;
  }
  if (env.DATA_RETENTION_DAYS !== "30" || env.BACKUP_RETENTION_DAYS !== "90") return false;
  return true;
}

export function validatePublication(env: Environment): void {
  // Local production builds remain possible for regression. An actual deploy
  // must explicitly declare APP_ENV=production, which activates this gate.
  if (env.APP_ENV === "production" && !publicationReady(env)) {
    throw new Error("Production publication settings are incomplete or unapproved");
  }
}
