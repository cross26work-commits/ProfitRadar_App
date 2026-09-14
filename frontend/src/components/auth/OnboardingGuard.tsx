"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/providers/AuthProvider";


export function OnboardingGuard({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();

  const {
    session,
    profile,
    loading,
  } = useAuth();


  const onboardingRequired =
    !loading &&
    !!session &&
    (!profile || !profile.companyId);


  useEffect(() => {
    if (onboardingRequired) {
      router.replace("/onboarding");
    }
  }, [onboardingRequired, router]);


  if (loading || onboardingRequired) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600" />

          <p className="mt-4 text-sm text-slate-500">
            アカウント情報を確認しています...
          </p>
        </div>
      </div>
    );
  }


  return <>{children}</>;
}
