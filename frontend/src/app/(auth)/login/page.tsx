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

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit() {
    setErrorMessage("");

    if (!email || !password) {
      setErrorMessage("メールアドレスとパスワードを入力してください。");
      return;
    }

    try {
      setIsSubmitting(true);
      await signInWithEmail(email, password);
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "ログインに失敗しました。"
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageStack>
      <PageHeader
        title="ログイン"
        description="Profit Radarへサインインします。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-4">
          {errorMessage ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <Input
            label="メールアドレス"
            type="email"
            placeholder="example@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <Input
            label="パスワード"
            type="password"
            placeholder="********"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <div className="grid gap-3">
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? "ログイン中..." : "ログイン"}
            </Button>

            <Link href="/register">
              <Button variant="secondary" className="w-full">
                新規登録
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </PageStack>
  );
}
