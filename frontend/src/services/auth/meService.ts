import { apiGet } from "@/lib/api";

export type AuthMeResponse = {
  authenticated: boolean;
  user: unknown;
  company_id: string | null;
  onboarding_completed: boolean;
};

export async function getAuthMe() {
  return apiGet<AuthMeResponse>("/auth/me");
}
