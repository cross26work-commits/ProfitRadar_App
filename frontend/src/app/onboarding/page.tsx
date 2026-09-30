"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { supabase } from "@/lib/supabase/client";
import { useAuth } from "@/providers/AuthProvider";
import { completeOnboarding } from "@/services/onboarding/onboardingService";
import { ApiError } from "@/lib/api";


export default function OnboardingPage() {
  const router = useRouter();

  const {
    session,
    profile,
    loading,
    refreshProfile,
  } = useAuth();

  const [companyName, setCompanyName] = useState("");
  const [name, setName] = useState("");
  const [businessUseConfirmed, setBusinessUseConfirmed] = useState(false);

  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const canSubmit = companyName.trim().length > 0 && name.trim().length > 0 && businessUseConfirmed;


  useEffect(() => {
    if (loading) return;

    if (!session) {
      router.replace("/login");
      return;
    }

    if (profile?.companyId) {
      router.replace("/dashboard");
      return;
    }

    async function loadMetadata() {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) return;

      const metadata = user.user_metadata ?? {};

      if (typeof metadata.company_name === "string") {
        setCompanyName(metadata.company_name);
      }

      if (typeof metadata.name === "string") {
        setName(metadata.name);
      }
    }

    loadMetadata();
  }, [
    loading,
    session,
    profile,
    router,
  ]);


  async function handleSubmit() {
    setErrorMessage("");

    const cleanCompanyName = companyName.trim();
    const cleanName = name.trim();

    if (!cleanCompanyName || !cleanName || !businessUseConfirmed) {
      setErrorMessage(
        "会社名、お名前、事業利用の確認が必要です。"
      );
      return;
    }

    try {
      setIsSubmitting(true);

      await completeOnboarding({
        companyName: cleanCompanyName,
        name: cleanName,
        businessUseConfirmed,
      });

      const completedProfile = await refreshProfile();
      if (!completedProfile?.companyId) {
        throw new Error("Onboarding profile did not become readable");
      }

      router.replace("/dashboard");
      router.refresh();

    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "初期設定を保存できませんでした。入力内容と通信状態を確認して、もう一度お試しください。"
      );

    } finally {
      setIsSubmitting(false);
    }
  }


  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">
          読み込み中...
        </p>
      </div>
    );
  }


  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-12">
      <div className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">

        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-600 font-bold text-white">
            P
          </div>

          <div>
            <p className="font-bold text-slate-900">
              PROFIT RADAR
            </p>

            <p className="text-xs text-slate-500">
              AI Sales OS
            </p>
          </div>
        </div>


        <h1 className="mt-8 text-2xl font-bold text-slate-900">
          初期設定
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Profit Radarを利用するための基本情報を設定します。
        </p>


        <div className="mt-7 space-y-5">

          <div>
            <label htmlFor="onboarding-company-name" className="text-sm font-medium text-slate-700">
              会社名・屋号
            </label>

            <input
              id="onboarding-company-name"
              value={companyName}
              onChange={(event) =>
                setCompanyName(event.target.value)
              }
              placeholder="株式会社サンプル"
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </div>


          <div>
            <label htmlFor="onboarding-owner-name" className="text-sm font-medium text-slate-700">
              お名前
            </label>

            <input
              id="onboarding-owner-name"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="山田 太郎"
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </div>


          {session?.user?.email ? (
            <div>
              <p className="text-xs text-slate-500">
                ログイン中のメールアドレス
              </p>

              <p className="mt-1 text-sm font-medium text-slate-800">
                {session.user.email}
              </p>
            </div>
          ) : null}

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-400 bg-white p-4 text-sm leading-6 text-slate-900 transition hover:border-emerald-600 hover:bg-emerald-50 focus-within:border-emerald-600 focus-within:ring-2 focus-within:ring-emerald-200 has-[:checked]:border-emerald-600 has-[:checked]:bg-emerald-50">
            <input
              type="checkbox"
              checked={businessUseConfirmed}
              onChange={(event) => setBusinessUseConfirmed(event.target.checked)}
              className="mt-0.5 h-5 w-5 shrink-0 accent-emerald-600 outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:ring-offset-2"
            />
            <span className="font-medium">私は法人または個人事業主等として、本サービスを事業目的で利用します。</span>
          </label>


          {errorMessage ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}


          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !canSubmit}
            aria-describedby="onboarding-submit-help"
            className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600"
          >
            {isSubmitting
              ? "設定中..."
              : "Profit Radarを開始"}
          </button>

          <p id="onboarding-submit-help" className="text-xs leading-5 text-slate-600" aria-live="polite">
            {isSubmitting
              ? "初期設定を保存しています。"
              : canSubmit
                ? "入力内容を保存してダッシュボードへ進みます。"
                : "会社名、お名前、事業利用の確認をすべて入力すると開始できます。"}
          </p>

        </div>
      </div>
    </main>
  );
}
