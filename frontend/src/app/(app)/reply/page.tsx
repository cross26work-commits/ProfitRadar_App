"use client";

import Link from "next/link";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { Button } from "@/components/ui/Button";
import { DashboardHeroSection } from "@/components/sections/DashboardHeroSection";
import { DangerLeadSection } from "@/components/sections/DangerLeadSection";
import { PageStack } from "@/components/sections/PageStack";
import { ReplyQueueSection } from "@/components/sections/ReplyQueueSection";
import { ReplyDraftForm } from "@/components/business/ReplyDraftForm";

import {
  apiGet,
  apiPost,
} from "@/lib/api";

import {
  getReplyDashboard,
  type ReplyDashboardData,
} from "@/services/profitRadarService";

type GmailCheckRepliesResponse = {
  checked: boolean;
  count?: number;
};

type GmailReplyAnalysis = {
  intent?: string;
  amount?: number | null;
  people_count?: number | null;
  target_day?: number | null;
  amount_ambiguous?: boolean;
  confidence?: string;
  risk_level?: string;
  next_action?: string;
  reason?: string;
  provider?: string;
};

type GmailReplyItem = {
  id: string;
  profit_event_id?: string | null;
  customer_id?: string | null;

  customer_name: string;
  customer_email: string;

  subject: string;
  body: string;
  received_at: string;

  event_title: string;
  next_action: string;

  estimated_profit: number;
  risk_level: string;

  analysis?: GmailReplyAnalysis | null;
};

type GmailRepliesResponse = {
  count: number;
  items: GmailReplyItem[];
};

function formatDate(value: string) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "ja-JP",
    {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  ).format(date);
}

export default function ReplyPage() {
  const [dashboard, setDashboard] =
    useState<ReplyDashboardData | null>(null);

  const [replies, setReplies] =
    useState<GmailReplyItem[]>([]);

  const [error, setError] =
    useState("");

  const [syncing, setSyncing] =
    useState(false);

  const [syncMessage, setSyncMessage] =
    useState("");

  const loadDashboard =
    useCallback(async () => {
      const data =
        await getReplyDashboard();

      setDashboard(data);
    }, []);

  const loadReplies =
    useCallback(async () => {
      const data =
        await apiGet<GmailRepliesResponse>(
          "/gmail/replies?limit=20"
        );

      setReplies(data.items || []);
    }, []);

  const reloadAll =
    useCallback(async () => {
      await Promise.all([
        loadDashboard(),
        loadReplies(),
      ]);
    }, [
      loadDashboard,
      loadReplies,
    ]);

  const syncGmail =
    useCallback(
      async (showMessage: boolean) => {
        setSyncing(true);
        setError("");

        if (showMessage) {
          setSyncMessage("");
        }

        try {
          const result =
            await apiPost<GmailCheckRepliesResponse>(
              "/gmail/check-replies",
              {
                max_events: 50,
              }
            );

          await reloadAll();

          if (showMessage) {
            const count =
              result.count ?? 0;

            setSyncMessage(
              count > 0
                ? `新しい返信を${count}件検知しました。`
                : "同期完了。新しい返信はありません。"
            );
          }
        } catch {
          console.error("Gmail reply sync failed");

          try {
            await reloadAll();

            if (showMessage) {
              setSyncMessage(
                "Gmail同期に失敗しましたが、保存済みの返信を表示しています。"
              );
            }
          } catch {
            console.error("Reply reload failed");
            setError("返信情報の取得に失敗しました。");
          }
        } finally {
          setSyncing(false);
        }
      },
      [reloadAll]
    );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void reloadAll().catch(() => {
        setError("返信情報の取得に失敗しました。");
        console.error("Reply queue load failed");
      });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [reloadAll]);

  if (error) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今すぐ返信"
          description="利益につながる返信と案件を確認します。"
        />

        <div className="rounded-3xl border border-red-200 bg-red-50 p-6 text-sm font-bold text-red-700">
          {error}
        </div>
      </PageStack>
    );
  }

  if (!dashboard) {
    return (
      <PageStack>
        <DashboardHeroSection
          title="今すぐ返信"
          description="利益につながる返信と案件を確認します。"
        />

        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-bold text-slate-500">
          Gmailと返信候補を確認しています...
        </div>
      </PageStack>
    );
  }

  return (
    <PageStack>
      <DashboardHeroSection
        title="今すぐ返信"
        description="受信したメールをAIが分析し、次の行動と返信案を提示します。"
      />

      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() => {
            void syncGmail(true);
          }}
          disabled={syncing}
          loading={syncing}
        >
          メールを更新
        </Button>

        {syncMessage ? (
          <p className="text-sm font-medium text-slate-600">
            {syncMessage}
          </p>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-bold text-slate-700">
            受信返信
          </p>

          <p className="mt-2 text-3xl font-black text-slate-950">
            {replies.length}件
          </p>

          <p className="mt-2 text-xs font-medium text-slate-500">
            Gmailで検知済み
          </p>
        </div>

        {dashboard.stats
          .slice(0, 2)
          .map((item, index) => (
            <div
              key={`${item.label}-${index}`}
              className="rounded-3xl border border-slate-200 bg-white p-5"
            >
              <p className="text-sm font-bold text-slate-700">
                {item.label}
              </p>

              <p className="mt-2 text-3xl font-black text-slate-950">
                {item.value}
              </p>
            </div>
          ))}
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-black text-slate-950">
            受信した返信
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            AI分析・返信案・送信までここで完結します。
          </p>
        </div>

        {replies.length === 0 ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm font-medium text-slate-500">
            まだ受信返信はありません。
          </div>
        ) : (
          <div className="space-y-6">
            {replies.map((reply) => (
              <article
                key={reply.id}
                className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                        返信あり
                      </span>

                      {reply.risk_level ? (
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                          優先度 {reply.risk_level}
                        </span>
                      ) : null}
                    </div>

                    <h3 className="mt-3 text-lg font-black text-slate-950">
                      {reply.subject}
                    </h3>

                    <p className="mt-1 text-sm font-semibold text-slate-700">
                      {reply.customer_name}
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      {reply.customer_email}
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      {formatDate(reply.received_at)}
                    </p>
                  </div>
                </div>

                <div className="mt-5 rounded-2xl bg-slate-50 p-5">
                  <p className="mb-2 text-xs font-bold text-slate-500">
                    相手からの返信
                  </p>

                  <p className="whitespace-pre-wrap text-sm font-medium leading-7 text-slate-800">
                    {reply.body}
                  </p>
                </div>

                {reply.analysis?.amount_ambiguous ? (
                  <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <p className="text-sm font-bold text-amber-800">
                      AIが確認事項を検出しました
                    </p>

                    <p className="mt-1 text-sm text-amber-700">
                      金額条件が曖昧です。返信時に確認してください。
                    </p>
                  </div>
                ) : null}

                {reply.profit_event_id ? (
                  <div className="mt-6 border-t border-slate-200 pt-6">
                    <ReplyDraftForm
                      eventId={reply.profit_event_id}
                      replyId={reply.id}
                      fallbackCustomerId={reply.customer_id}
                      fallbackCustomerName={reply.customer_name}
                      fallbackCustomerEmail={reply.customer_email}
                      fallbackEventTitle={
                        reply.subject || reply.event_title
                      }
                    />
                  </div>
                ) : null}

                {reply.profit_event_id ? (
                  <div className="mt-5">
                    <Link
                      href={`/leads/${reply.profit_event_id}`}
                      className="text-sm font-bold text-slate-700 underline underline-offset-4"
                    >
                      案件詳細を開く
                    </Link>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-black text-slate-950">
            その他の返信候補
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            AIが対応優先度の高い案件を表示します。
          </p>
        </div>

        <ReplyQueueSection
          leads={dashboard.leads}
        />
      </section>

      <DangerLeadSection
        title="AIの判断基準"
        risks={[
          "利益につながる可能性",
          "相手の受注意欲",
          "金額・人数・日付などの具体性",
        ]}
      />
    </PageStack>
  );
}
