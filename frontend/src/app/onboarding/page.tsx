"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { supabase } from "@/lib/supabase/client";
import { useAuth } from "@/providers/AuthProvider";
import { completeOnboarding } from "@/services/onboarding/onboardingService";


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

  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);


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

    if (!cleanCompanyName || !cleanName) {
      setErrorMessage(
        "会社名とお名前を入力してください。"
      );
      return;
    }

    try {
      setIsSubmitting(true);

      await completeOnboarding({
        companyName: cleanCompanyName,
        name: cleanName,
      });

      await refreshProfile();

      router.replace("/dashboard");
      router.refresh();

    } catch {
      setErrorMessage("初期設定を確認できません。再読み込みして登録状態を確認してください。");

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
            <label className="text-sm font-medium text-slate-700">
              会社名・屋号
            </label>

            <input
              value={companyName}
              onChange={(event) =>
                setCompanyName(event.target.value)
              }
              placeholder="株式会社サンプル"
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            />
          </div>


          <div>
            <label className="text-sm font-medium text-slate-700">
              お名前
            </label>

            <input
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


          {errorMessage ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}


          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
          >
            {isSubmitting
              ? "設定中..."
              : "Profit Radarを開始"}
          </button>

        </div>
      </div>
    </main>
  );
}
