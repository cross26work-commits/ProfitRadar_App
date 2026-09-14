"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";
import { signInWithEmail } from "@/services/auth/authService";

function getLoginErrorMessage(error: unknown) {
  const message =
    error instanceof Error ? error.message.toLowerCase() : "";

  if (
    message.includes("invalid login credentials") ||
    message.includes("invalid credentials")
  ) {
    return "メールアドレスまたはパスワードが正しくありません。";
  }

  if (message.includes("email not confirmed")) {
    return "メールアドレスの確認が完了していません。確認メールをご確認ください。";
  }

  if (
    message.includes("failed to fetch") ||
    message.includes("network")
  ) {
    return "通信に失敗しました。インターネット接続を確認して、もう一度お試しください。";
  }

  return "ログインできませんでした。入力内容を確認して、もう一度お試しください。";
}

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit() {
    setErrorMessage("");

    if (!email.trim() || !password) {
      setErrorMessage(
        "メールアドレスとパスワードを入力してください。"
      );
      return;
    }

    try {
      setIsSubmitting(true);

      await signInWithEmail(email.trim(), password);

      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(getLoginErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageStack>
      <PageHeader
        title="ログイン"
        description="Profit Radarにログインします。"
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
            label="メールアドレス"
            type="email"
            autoComplete="email"
            placeholder="example@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <Input
            label="パスワード"
            type="password"
            autoComplete="current-password"
            placeholder="パスワードを入力"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                void handleSubmit();
              }
            }}
          />

          <div className="grid gap-3">
            <Button
              onClick={handleSubmit}
              loading={isSubmitting}
              className="w-full"
            >
              ログイン
            </Button>

            <Link
              href="/register"
              className="block"
            >
              <Button
                variant="secondary"
                className="w-full"
              >
                新規登録
              </Button>
            </Link>
          </div>

          <Link
            href="/forgot-password"
            className="block text-center text-sm font-semibold text-emerald-700 hover:underline"
          >
            パスワードを忘れた方
          </Link>
        </div>
      </Card>
    </PageStack>
  );
}
