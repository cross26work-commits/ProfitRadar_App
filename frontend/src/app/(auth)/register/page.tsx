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
import { createCompanyAndProfile } from "@/services/profile/profileService";

export default function RegisterPage() {
  const router = useRouter();

  const [companyName, setCompanyName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit() {
    setErrorMessage("");

    if (!companyName || !name || !email || !password || !passwordConfirmation) {
      setErrorMessage("すべての項目を入力してください。");
      return;
    }

    if (password !== passwordConfirmation) {
      setErrorMessage("パスワードが一致していません。");
      return;
    }

    try {
      setIsSubmitting(true);
      const authData = await signUpWithEmail({
        email,
        password,
        companyName,
        name,
      });

      if (authData.user) {
        await createCompanyAndProfile({
          userId: authData.user.id,
          companyName,
          name,
        });
      }

      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "アカウント作成に失敗しました。"
      );
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
        <div className="space-y-4">
          {errorMessage ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          ) : null}

          <Input
            label="会社名"
            placeholder="株式会社サンプル"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
          />

          <Input
            label="お名前"
            placeholder="山田 太郎"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />

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

          <Input
            label="パスワード（確認）"
            type="password"
            placeholder="********"
            value={passwordConfirmation}
            onChange={(event) => setPasswordConfirmation(event.target.value)}
          />

          <div className="grid gap-3">
            <Button onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? "作成中..." : "アカウントを作成"}
            </Button>

            <Link href="/login">
              <Button variant="secondary" className="w-full">
                ログインへ戻る
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </PageStack>
  );
}
