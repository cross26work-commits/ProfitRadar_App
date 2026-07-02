import { apiGet } from "@/lib/api";

export type AuthMeResponse = {
  authenticated: boolean;
  user: unknown;
};

export async function getAuthMe() {
  return apiGet<AuthMeResponse>("/auth/me");
}
