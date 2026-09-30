import { apiPost } from "@/lib/api";

export type OnboardingResponse = {
  success: boolean;
  result: Array<{
    created: boolean;
    company_id: string;
    profile_id: string;
  }>;
};

export async function completeOnboarding(params: {
  companyName: string;
  name: string;
  businessUseConfirmed: boolean;
}) {
  return apiPost<OnboardingResponse>("/onboarding", {
    company_name: params.companyName,
    name: params.name,
    business_use_confirmed: params.businessUseConfirmed,
  });
}
