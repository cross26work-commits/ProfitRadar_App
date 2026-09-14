"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { supabase } from "@/lib/supabase/client";
import { useAuth } from "@/providers/AuthProvider";
import { deleteCurrentAccount } from "@/services/account/accountService";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/forms/Input";
import { Dialog } from "@/components/ui/Dialog";

function getDeleteErrorMessage(error: unknown) {
  const message =
    error instanceof Error ? error.message.toLowerCase() : "";

  if (
    message.includes("invalid login credentials") ||
    message.includes("invalid password")
  ) {
    return "パスワードが正しくありません。";
  }

  if (
    message.includes("failed to fetch") ||
    message.includes("network")
  ) {
    return "通信に失敗しました。もう一度お試しください。";
  }

  return "削除完了を確認できません。契約中は先に期間末解約してください。削除開始後のエラーは運営者へ復旧を依頼してください。";
}

export default function SettingsPage() {
  const router = useRouter();
  const { profile } = useAuth();

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const [isDeleting, setIsDeleting] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    try {
      setIsLoggingOut(true);

      await supabase.auth.signOut();

      router.replace("/login");
      router.refresh();
    } finally {
      setIsLoggingOut(false);
    }
  }

  async function handleDeleteAccount() {
    setErrorMessage("");

    if (!password) {
      setErrorMessage("現在のパスワードを入力してください。");
      return;
    }

    if (confirmation !== "削除") {
      setErrorMessage(
        "確認欄に「削除」と入力してください。"
      );
      return;
    }

    try {
      setIsDeleting(true);

      await deleteCurrentAccount({
        password,
        confirmation,
      });

      await supabase.auth.signOut();

      router.replace("/login");
      router.refresh();
    } catch (error) {
      setErrorMessage(getDeleteErrorMessage(error));
    } finally {
      setIsDeleting(false);
    }
  }

  function closeDeleteModal() {
    if (isDeleting) return;

    setDeleteOpen(false);
    setPassword("");
    setConfirmation("");
    setErrorMessage("");
  }

  return (
    <div className="mx-auto w-full max-w-4xl space-y-8 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          設定
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          アカウント、会社情報、プラン、セッションを管理します。
        </p>
      </div>

      <Card className="p-6">
        <h2 className="text-base font-bold text-slate-900">
          アカウント
        </h2>

        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium text-slate-500">
              お名前
            </p>

            <p className="mt-1 text-sm font-semibold text-slate-900">
              {profile?.name || "未設定"}
            </p>
          </div>

          <div>
            <p className="text-xs font-medium text-slate-500">
              メールアドレス
            </p>

            <p className="mt-1 break-all text-sm font-semibold text-slate-900">
              {profile?.email || "未設定"}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              会社情報
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              {profile?.companyName || "会社情報が未設定です。"}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              メール連携
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              営業メールの接続と同期状態を管理します。
            </p>
          </div>

          <Link
            href="/settings/mail"
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
          >
            メール連携を管理
          </Link>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              プラン
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              現在：
              <span className="ml-1 font-semibold capitalize text-slate-900">
                {profile?.plan || "free"}
              </span>
            </p>
          </div>

          <Link href="/settings/plan">
            <Button variant="secondary">
              プランを確認
            </Button>
          </Link>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-base font-bold text-slate-900">
          セッション
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          この端末からProfit Radarをログアウトします。
        </p>

        <div className="mt-5">
          <Button
            variant="secondary"
            onClick={handleLogout}
            loading={isLoggingOut}
          >
            ログアウト
          </Button>
        </div>
      </Card>

      <section className="rounded-2xl border border-red-200 bg-red-50/50 p-6">
        <h2 className="text-base font-bold text-red-700">
          危険な操作
        </h2>

        <div className="mt-4 rounded-xl border border-red-200 bg-white p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-semibold text-slate-900">
                アカウントを完全に削除
              </p>

              <p className="mt-1 max-w-xl text-sm leading-6 text-slate-600">
                アカウントや関連データを削除します。契約中は先に期間末解約し、契約終了後に操作してください。削除監査と請求参照・バックアップは所定の保持期間後に消去します。
                この操作は取り消せません。
              </p>
            </div>

            <Button
              variant="danger"
              onClick={() => setDeleteOpen(true)}
              className="shrink-0"
            >
              アカウントを削除
            </Button>
          </div>
        </div>
      </section>

      <Dialog
        open={deleteOpen}
        title="本当にアカウントを削除しますか？"
        description="削除したアカウントは元に戻せません。本人確認のため、現在のパスワードと確認文字を入力してください。"
        confirmLabel="完全に削除する"
        cancelLabel="キャンセル"
        variant="danger"
        loading={isDeleting}
        onConfirm={handleDeleteAccount}
        onCancel={closeDeleteModal}
      >
        <div className="space-y-5">
          <Input
            label="現在のパスワード"
            type="password"
            autoComplete="current-password"
            placeholder="現在のパスワード"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />

          <Input
            label="確認"
            placeholder="削除"
            helperText="続行するには「削除」と入力してください。"
            value={confirmation}
            onChange={(event) =>
              setConfirmation(event.target.value)
            }
          />

          {errorMessage ? (
            <div
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700"
            >
              {errorMessage}
            </div>
          ) : null}
        </div>
      </Dialog>
    </div>
  );
}
