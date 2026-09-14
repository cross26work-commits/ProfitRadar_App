"use client";

import { useState } from "react";
import Link from "next/link";

import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";

import { requestPasswordReset } from "@/services/auth/authService";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [sent, setSent] = useState(false);

  async function handleSubmit() {
    setErrorMessage("");

    if (!email.trim()) {
      setErrorMessage(
        "メールアドレスを入力してください。"
      );
      return;
    }

    try {
      setLoading(true);

      await requestPasswordReset(
        email.trim()
      );

      setSent(true);
    } catch {
      setErrorMessage(
        "再設定メールを送信できませんでした。時間をおいて、もう一度お試しください。"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageStack>
      <PageHeader
        title="パスワードを再設定"
        description="登録済みのメールアドレスへ、パスワード再設定用のリンクを送信します。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-5">
          {sent ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4">
              <p className="text-sm font-semibold text-emerald-800">
                再設定メールを送信しました。
              </p>

              <p className="mt-2 text-xs leading-5 text-emerald-700">
                メールが届いた場合は、本文のリンクから新しいパスワードを設定してください。
              </p>
            </div>
          ) : (
            <>
              {errorMessage ? (
                <div
                  role="alert"
                  className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
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
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    void handleSubmit();
                  }
                }}
              />

              <Button
                onClick={handleSubmit}
                loading={loading}
                className="w-full"
              >
                再設定メールを送信
              </Button>
            </>
          )}

          <Link
            href="/login"
            className="block text-center text-sm font-semibold text-emerald-700 hover:underline"
          >
            ログインへ戻る
          </Link>
        </div>
      </Card>
    </PageStack>
  );
}
