"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { PageStack } from "@/components/sections/PageStack";
import { PageHeader } from "@/components/sections/PageHeader";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/forms/Input";
import { Button } from "@/components/ui/Button";

import { supabase } from "@/lib/supabase/client";
import { updatePassword } from "@/services/auth/authService";

export default function ResetPasswordPage() {
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");

  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);

  const [errorMessage, setErrorMessage] = useState("");
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function checkSession() {
      const { data } =
        await supabase.auth.getSession();

      if (
        mounted &&
        data.session
      ) {
        setReady(true);
      }
    }

    void checkSession();

    const {
      data: subscription,
    } =
      supabase.auth.onAuthStateChange(
        (event, session) => {
          if (
            event === "PASSWORD_RECOVERY" &&
            session &&
            mounted
          ) {
            setReady(true);
          }
        }
      );

    return () => {
      mounted = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  async function handleSubmit() {
    setErrorMessage("");

    if (!ready) {
      setErrorMessage(
        "再設定リンクが無効、または有効期限が切れている可能性があります。"
      );
      return;
    }

    if (!password) {
      setErrorMessage(
        "新しいパスワードを入力してください。"
      );
      return;
    }

    if (password.length < 8) {
      setErrorMessage(
        "パスワードは8文字以上で設定してください。"
      );
      return;
    }

    if (password !== confirmation) {
      setErrorMessage(
        "パスワードが一致していません。"
      );
      return;
    }

    try {
      setLoading(true);

      await updatePassword(password);

      setCompleted(true);

      window.setTimeout(() => {
        router.replace("/login");
      }, 1200);
    } catch {
      setErrorMessage(
        "パスワードを更新できませんでした。再設定リンクをもう一度発行してください。"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageStack>
      <PageHeader
        title="新しいパスワードを設定"
        description="新しいパスワードを入力してください。"
      />

      <Card className="mx-auto w-full max-w-md p-6">
        <div className="space-y-5">
          {completed ? (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4">
              <p className="text-sm font-semibold text-emerald-800">
                パスワードを変更しました。
              </p>

              <p className="mt-2 text-xs text-emerald-700">
                ログイン画面へ移動します。
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

              {!ready ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  再設定リンクを確認しています。
                </div>
              ) : null}

              <Input
                label="新しいパスワード"
                type="password"
                autoComplete="new-password"
                placeholder="8文字以上"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
              />

              <Input
                label="新しいパスワード（確認）"
                type="password"
                autoComplete="new-password"
                placeholder="もう一度入力"
                value={confirmation}
                onChange={(event) =>
                  setConfirmation(event.target.value)
                }
              />

              <Button
                onClick={handleSubmit}
                loading={loading}
                disabled={!ready}
                className="w-full"
              >
                パスワードを変更
              </Button>
            </>
          )}

          <Link
            href="/forgot-password"
            className="block text-center text-xs font-semibold text-slate-600 hover:text-emerald-700 hover:underline"
          >
            再設定メールをもう一度送る
          </Link>
        </div>
      </Card>
    </PageStack>
  );
}
