"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { apiPost, ApiError } from "@/lib/api";

import {
  disconnectGmail,
  getGmailAuthUrl,
  getGmailStatus,
  type GmailStatusResponse,
} from "@/services/mailService";

function formatDate(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function MailSettingsPage() {
  const searchParams = useSearchParams();

  const [gmail, setGmail] =
    useState<GmailStatusResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing,setSyncing]=useState(false);

  async function syncNow() {
    if(syncing)return;setSyncing(true);setErrorMessage("");
    try {await apiPost("/gmail/check-replies",{});await loadStatus();}
    catch(error){setErrorMessage(error instanceof ApiError?error.message:"同期に失敗しました。時間をおいて再試行してください。");}
    finally{setSyncing(false);}
  }
  const [disconnecting, setDisconnecting] =
    useState(false);

  const [disconnectOpen, setDisconnectOpen] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");

  async function loadStatus() {
    try {
      setLoading(true);
      setErrorMessage("");

      const result = await getGmailStatus();

      setGmail(result);
    } catch {
      setErrorMessage(
        "メール接続状態を取得できませんでした。"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadStatus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function connectGoogle() {
    try {
      setConnecting(true);
      setErrorMessage("");

      const result = await getGmailAuthUrl();

      window.location.assign(result.auth_url);
    } catch (error) {
      if (error instanceof ApiError && error.status === 501) {
        setErrorMessage("このローカル・テスト環境ではGoogle OAuthが設定されていません。実際のGoogle接続は、専用のテスト設定がある環境で確認してください。");
      } else if (error instanceof ApiError && error.status === 424) {
        setErrorMessage("Google連携の本番設定が完了していません。設定が確認されるまで接続は開始されません。運営担当へお問い合わせください。");
      } else if (error instanceof ApiError && error.status === 502) {
        setErrorMessage("Googleの認証画面を準備できませんでした。一時的な接続障害の可能性があります。時間を置いて再試行してください。");
      } else {
        setErrorMessage(error instanceof ApiError ? error.message : "Google連携を開始できませんでした。通信状態を確認して、時間を置いて再試行してください。");
      }

      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    try {
      setDisconnecting(true);
      setErrorMessage("");

      await disconnectGmail();

      setDisconnectOpen(false);

      await loadStatus();
    } catch {
      setErrorMessage(
        "Googleとの接続を解除できませんでした。"
      );
    } finally {
      setDisconnecting(false);
    }
  }

  const gmailResult =
    searchParams.get("gmail");

  return (
    <div className="mx-auto w-full max-w-4xl space-y-8 pb-16">
      <div>
        <Link
          href="/settings"
          className="text-sm font-semibold text-emerald-700 hover:underline"
        >
          ← 設定へ戻る
        </Link>

        <h1 className="mt-5 text-2xl font-bold text-slate-900">
          メール連携
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Profit Radarが営業メールを分析するために使用する
          メールアカウントを管理します。
        </p>
      </div>

      {gmailResult === "connected" ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">
          Googleアカウントとの接続が完了しました。
        </div>
      ) : null}

      {gmailResult === "cancelled" ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          Googleアカウントとの接続はキャンセルされました。
        </div>
      ) : null}

      {gmailResult === "error" || gmailResult === "oauth_failed" ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          Googleアカウントとの接続に失敗しました。
        </div>
      ) : null}

      {errorMessage ? (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700"
        >
          {errorMessage}
        </div>
      ) : null}

      <Card className="p-6">
        {!loading&&gmail?.connected&&<div className="mb-6 space-y-2 rounded-xl border p-4 text-slate-900">
          <p>最終同期完了：{formatDate(gmail.sync?.last_successful_sync)}</p>
          <p>同期状態：{gmail.last_run?.status==="failed"?"同期失敗。再試行してください。":gmail.last_run?.status==="running"?"同期中":gmail.sync?.mode==="full"?"初回取得を継続中":"次の同期を待機中"}</p>
          <Button onClick={syncNow} loading={syncing} disabled={loading||disconnecting}>今すぐ同期</Button>
          <p className="text-xs text-slate-600">初回は過去30日分を順次取得します。件数が多い場合は複数回に分けて継続します。</p>
        </div>}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-bold text-slate-900">
                Google
              </h2>

              {loading ? (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  確認中
                </span>
              ) : gmail?.connected ? (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                  接続済み
                </span>
              ) : (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  未接続
                </span>
              )}
            </div>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              Gmail / Google Workspace
            </p>

            {gmail?.connected && gmail.connection ? (
              <div className="mt-5 space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    接続メールアドレス
                  </p>

                  <p className="mt-1 break-all text-sm font-semibold text-slate-900">
                    {gmail.connection.email}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-500">
                    接続日時
                  </p>

                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {formatDate(
                      gmail.connection.created_at
                    )}
                  </p>
                </div>
              </div>
            ) : null}

            <p className="mt-4 max-w-xl text-xs leading-5 text-slate-500">
              Profit Radarは営業メールの分析・返信支援に必要な範囲で、
              Gmailの閲覧権限と送信権限を利用します。
            </p>
          </div>

          <div className="flex shrink-0 flex-col gap-2">
            <Button
              onClick={connectGoogle}
              loading={connecting}
              disabled={loading}
            >
              {gmail?.connected
                ? "Googleを再接続"
                : "Googleで接続"}
            </Button>

            {gmail?.connected ? (
              <Button
                variant="secondary"
                onClick={() =>
                  setDisconnectOpen(true)
                }
              >
                接続を解除
              </Button>
            ) : null}
          </div>
        </div>
      </Card>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <h2 className="text-sm font-bold text-slate-900">
          メールデータの取扱い
        </h2>

        <p className="mt-2 text-xs leading-6 text-slate-600">
          接続したメールの情報は、利益機会の検出、
          返信支援、案件状況の分析などProfit Radarの
          機能提供のために利用します。
        </p>

        <Link
          href="/privacy"
          className="mt-3 inline-block text-xs font-semibold text-emerald-700 hover:underline"
        >
          プライバシーポリシーを確認
        </Link>
      </div>

      <Dialog
        open={disconnectOpen}
        title="Googleとの接続を解除しますか？"
        description="Profit RadarからGoogleアカウントとの接続情報を削除します。再度利用する場合は、もう一度Google認証が必要です。"
        confirmLabel="接続を解除"
        cancelLabel="キャンセル"
        variant="danger"
        loading={disconnecting}
        onConfirm={handleDisconnect}
        onCancel={() =>
          setDisconnectOpen(false)
        }
      />
    </div>
  );
}
