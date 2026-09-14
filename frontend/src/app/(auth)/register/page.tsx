"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";

import { signUpWithEmail } from "@/services/auth/authService";
import { completeOnboarding } from "@/services/onboarding/onboardingService";

function getRegisterErrorMessage(error: unknown) {
  const message =
    error instanceof Error ? error.message.toLowerCase() : "";

  if (
    message.includes("already registered") ||
    message.includes("already been registered") ||
    message.includes("user already registered")
  ) {
    return "このメールアドレスはすでに登録されています。";
  }

  if (message.includes("password")) {
    return "パスワードの条件を確認してください。";
  }

  if (
    message.includes("failed to fetch") ||
    message.includes("network")
  ) {
    return "通信に失敗しました。インターネット接続を確認してください。";
  }

  return "アカウントを作成できませんでした。入力内容を確認して、もう一度お試しください。";
}

export default function RegisterPage() {
  const router = useRouter();

  const [companyName, setCompanyName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] =
    useState("");

  const [acceptedTerms, setAcceptedTerms] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit() {
    setErrorMessage("");

    if (
      !companyName.trim() ||
      !name.trim() ||
      !email.trim() ||
      !password ||
      !passwordConfirmation
    ) {
      setErrorMessage("すべての必須項目を入力してください。");
      return;
    }

    if (password !== passwordConfirmation) {
      setErrorMessage("パスワードが一致していません。");
      return;
    }

    if (!acceptedTerms) {
      setErrorMessage(
        "利用規約とプライバシーポリシーへの同意が必要です。"
      );
      return;
    }

    try {
      setIsSubmitting(true);

      const authData = await signUpWithEmail({
        email: email.trim(),
        password,
        companyName: companyName.trim(),
        name: name.trim(),
      });

      if (!authData.session) {
        router.push("/login");
        return;
      }

      await completeOnboarding({
        companyName: companyName.trim(),
        name: name.trim(),
      });

      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(getRegisterErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageStack>
      <PageHeader
        title="新規登録"
        description="Profit Radarのアカウントを作成します。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-5">
          {errorMessage ? (
            <div
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700"
            >
              {errorMessage}
            </div>
          ) : null}

          <Input
            label="会社名・屋号"
            placeholder="株式会社サンプル"
            value={companyName}
            onChange={(event) =>
              setCompanyName(event.target.value)
            }
          />

          <Input
            label="お名前"
            autoComplete="name"
            placeholder="山田 太郎"
            value={name}
            onChange={(event) =>
              setName(event.target.value)
            }
          />

          <Input
            label="メールアドレス"
            type="email"
            autoComplete="email"
            placeholder="example@company.com"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
          />

          <Input
            label="パスワード"
            type="password"
            autoComplete="new-password"
            placeholder="パスワードを入力"
            helperText="安全性の高いパスワードを設定してください。"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />

          <Input
            label="パスワード（確認）"
            type="password"
            autoComplete="new-password"
            placeholder="もう一度入力"
            value={passwordConfirmation}
            onChange={(event) =>
              setPasswordConfirmation(event.target.value)
            }
          />

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <input
              type="checkbox"
              checked={acceptedTerms}
              onChange={(event) =>
                setAcceptedTerms(event.target.checked)
              }
              className="mt-0.5 h-4 w-4 accent-emerald-600"
            />

            <span className="text-xs leading-5 text-slate-600">
              <Link
                href="/terms"
                className="font-semibold text-emerald-700 hover:underline"
              >
                利用規約
              </Link>
              {" "}と{" "}
              <Link
                href="/privacy"
                className="font-semibold text-emerald-700 hover:underline"
              >
                プライバシーポリシー
              </Link>
              に同意します。
            </span>
          </label>

          <div className="grid gap-3">
            <Button
              onClick={handleSubmit}
              loading={isSubmitting}
              className="w-full"
            >
              アカウントを作成
            </Button>

            <Link
              href="/login"
              className="block"
            >
              <Button
                variant="secondary"
                className="w-full"
              >
                ログインへ戻る
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </PageStack>
  );
}
