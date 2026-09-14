"use client";

import { useEffect, useState } from "react";

import { Textarea } from "@/components/forms/Textarea";
import { ActionBar } from "@/components/ui/ActionBar";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { ApiError, apiGet, apiPost } from "@/lib/api";

type ReplyDraftFormProps = {
  eventId: string | number;
};

type ReplyCustomer = {
  id?: string;
  name?: string | null;
  email?: string | null;
};

type ReplyEvent = {
  customer_id?: string | null;
  title?: string | null;
};

type ReplyAnalysis = {
  is_lead?: boolean;
  intent?: string;
  estimated_profit?: number | null;
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

type ReplyDraftResponse = {
  send_status?: string;
  subject?: string;
  draft?: string;
  draft_provider?: string;
  draft_model?: string;
  event?: ReplyEvent | null;
  customer?: ReplyCustomer | null;
  analysis?: ReplyAnalysis | null;
};

function formatYen(value?: number | null) {
  if (value == null) {
    return "未確定";
  }

  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 0,
  }).format(value);
}

function buildSubject(title?: string | null) {
  const value = (title || "").trim();

  if (!value) {
    return "Re: Profit Radar";
  }

  if (/^re:/i.test(value)) {
    return value;
  }

  return `Re: ${value}`;
}

export function ReplyDraftForm({
  eventId,
}: ReplyDraftFormProps) {
  const [draft, setDraft] = useState("");
  const [customerId, setCustomerId] =
    useState<string | null>(null);

  const [customerName, setCustomerName] =
    useState("");

  const [toEmail, setToEmail] =
    useState("");

  const [subject, setSubject] =
    useState("Re: Profit Radar");

  const [analysis, setAnalysis] =
    useState<ReplyAnalysis | null>(null);

  const [draftProvider, setDraftProvider] =
    useState("");

  const [draftModel, setDraftModel] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [sending, setSending] =
    useState(false);
  const [saving, setSaving] = useState(false);
  const [sendStatus, setSendStatus] = useState("");

  const [confirmOpen, setConfirmOpen] =
    useState(false);

  const [message, setMessage] =
    useState("");

  useEffect(() => {
    async function loadDraft() {
      setLoading(true);
      setMessage("");

      try {
        const data =
          await apiGet<ReplyDraftResponse>(
            `/reply/${eventId}/draft`
          );

        setDraft(data.draft || "");

        setDraftProvider(
          data.draft_provider || ""
        );

        setDraftModel(
          data.draft_model || ""
        );

        setAnalysis(
          data.analysis || null
        );

        setCustomerId(
          data.event?.customer_id ?? null
        );

        setCustomerName(
          data.customer?.name || ""
        );

        setToEmail(
          data.customer?.email || ""
        );

        setSendStatus(data.send_status || "");
        if (data.send_status === "unknown" || data.send_status === "sending") setMessage("送信結果不明・確認中です。再送せず、送信済み照合を行ってください。");
        if (data.send_status === "sent") setMessage("送信済みです。履歴を確認してください。");
        setSubject(
          data.subject ?? buildSubject(
            data.event?.title
          )
        );
      } catch (error) {
        void error;

        setMessage(
          "AI返信案を取得できませんでした。"
        );
      } finally {
        setLoading(false);
      }
    }

    void loadDraft();
  }, [eventId]);

  function requestSend() {
    if (loading || sending || saving || sendStatus) return;
    setMessage("");

    if (!toEmail) {
      setMessage(
        "顧客のメールアドレスが登録されていません。"
      );
      return;
    }

    if (!draft.trim()) {
      setMessage(
        "返信内容を入力してください。"
      );
      return;
    }

    setConfirmOpen(true);
  }

  async function saveDraft() {
    setSaving(true);
    setMessage("");
    try {
      await apiPost(`/reply/${eventId}/draft`, { body: draft, subject });
      setMessage("下書きを保存しました。");
    } catch {
      setMessage("下書きを保存できませんでした。入力内容はこの画面に残っています。");
    } finally {
      setSaving(false);
    }
  }

  async function generateDraft() {
    if (draft.trim() && !window.confirm("画面上の返信案を新しく生成します。未保存の編集は置き換わります。よろしいですか？")) return;
    setSaving(true); setMessage("");
    try {
      const result = await apiPost<ReplyDraftResponse>(`/reply/${eventId}/generate`, {});
      setDraft(result.draft || ""); setAnalysis(result.analysis || null);
      setDraftProvider(result.draft_provider || ""); setDraftModel(result.draft_model || "");
      setMessage("返信案を生成しました。根拠と内容を確認し、必要なら下書きを保存してください。");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "生成できませんでした。入力内容は保持しています。");
    } finally { setSaving(false); }
  }

  async function sendDraft() {
    if (sending || saving || sendStatus || !confirmOpen) return;
    setSending(true);
    setMessage("");

    try {
      const result = await apiPost<{ sent: boolean; status: string }>(
        `/reply/${eventId}/send`,
        {
          customer_id: customerId,
          to_email: toEmail,
          subject,
          body: draft,
        }
      );

      setConfirmOpen(false);
      setSendStatus(result.status);
      setMessage(result.sent ? "送信済みです。返信待ちとして追跡します。" : "送信結果を確認できません。再送せず、送信済み照合を行ってください。");
    } catch (error) {
      void error;
      setSendStatus("unknown");
      setConfirmOpen(false);

      setMessage(
        "送信結果を確認できません。再送せず、送信済み照合を行ってください。"
      );
    } finally {
      setSending(false);
    }
  }

  async function reconcileSend() {
    setSending(true);
    try {
      const result = await apiPost<{ sent: boolean; status: string }>(`/reply/${eventId}/reconcile`, {});
      setSendStatus(result.status);
      setMessage(result.sent ? "送信済みを確認し、履歴を保存しました。" : "送信結果はまだ不明です。再送せず、時間を置いて照合してください。");
    } catch {
      setMessage("照合できませんでした。Gmail接続状態を確認してください。再送は行っていません。");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-5">
      {analysis ? (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-black text-slate-950">
              AI判断
            </p>

            {analysis.risk_level ? (
              <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-bold text-white">
                優先度 {analysis.risk_level}
              </span>
            ) : null}

            {draftProvider ? (
              <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-500">
                {draftProvider === "openai"
                  ? draftModel
                    ? `OpenAI生成 / ${draftModel}`
                    : "OpenAI生成"
                  : draftProvider === "gemini"
                    ? "Gemini生成"
                    : draftProvider === "validator_fallback"
                      ? "安全確認Fallback"
                      : "Fallback生成"}
              </span>
            ) : null}
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs font-bold text-slate-500">
                意図
              </p>
              <p className="mt-1 text-sm font-bold text-slate-900">
                {analysis.intent || "要確認"}
              </p>
            </div>

            <div>
              <p className="text-xs font-bold text-slate-500">
                金額
              </p>
              <p className="mt-1 text-sm font-bold text-slate-900">
                {formatYen(analysis.amount)}
              </p>
            </div>

            <div>
              <p className="text-xs font-bold text-slate-500">
                人数
              </p>
              <p className="mt-1 text-sm font-bold text-slate-900">
                {analysis.people_count
                  ? `${analysis.people_count}名`
                  : "未確認"}
              </p>
            </div>

            <div>
              <p className="text-xs font-bold text-slate-500">
                希望日
              </p>
              <p className="mt-1 text-sm font-bold text-slate-900">
                {analysis.target_day
                  ? `${analysis.target_day}日`
                  : "未確認"}
              </p>
            </div>
          </div>

          {analysis.amount_ambiguous ? (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-bold text-amber-800">
                金額条件が曖昧です。
              </p>
              <p className="mt-1 text-sm text-amber-700">
                1名あたりの金額か、全体の合計金額か確認が必要です。
              </p>
            </div>
          ) : null}

          {analysis.reason && <div className="mt-4"><p className="text-xs font-bold text-slate-500">判断理由（根拠メールと照合してください）</p><p className="mt-1 whitespace-pre-wrap text-sm">{analysis.reason}</p></div>}
          {analysis.next_action ? (
            <div className="mt-4">
              <p className="text-xs font-bold text-slate-500">
                次の行動
              </p>
              <p className="mt-1 text-sm font-bold leading-6 text-slate-900">
                {analysis.next_action}
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <p className="text-xs font-medium text-slate-500">
          送信先
        </p>

        <p className="mt-1 text-sm font-semibold text-slate-900">
          {customerName || "顧客名未設定"}
        </p>

        <p className="mt-1 break-all text-sm text-slate-700">
          {toEmail || "メールアドレス未登録"}
        </p>

        <p className="mt-4 text-xs font-medium text-slate-500">
          件名
        </p>

        <p className="mt-1 text-sm font-semibold text-slate-900">
          {subject}
        </p>
      </div>

      <Textarea
        label={
          loading
            ? "保存済み返信案を読み込み中..."
            : "AI返信案"
        }
        value={draft}
        onChange={(event) =>
          setDraft(event.target.value)
        }
      />

      <p className="text-xs text-slate-500">
        送信前に内容を確認・編集できます。
      </p>

      <ActionBar>
        <Button onClick={generateDraft} disabled={loading || saving || sending}>返信案を生成</Button>
        <Button onClick={reconcileSend} disabled={loading || sending}>送信済み照合</Button>
        <Button onClick={saveDraft} disabled={loading || sending || saving}>
          {saving ? "保存中..." : "下書きを保存"}
        </Button>
        <Button
          onClick={requestSend}
          disabled={
            loading ||
            saving ||
            Boolean(sendStatus) ||
            sending ||
            !draft.trim() ||
            !toEmail
          }
        >
          Gmailで送信
        </Button>
      </ActionBar>

      {message ? (
        <p role="status" className="text-sm font-medium text-slate-600">
          {message}
        </p>
      ) : null}

      <Dialog
        open={confirmOpen}
        title="このメールを送信しますか？"
        description={`送信先: ${toEmail || "未設定"}`}
        confirmLabel="Gmailで送信"
        cancelLabel="キャンセル"
        loading={sending}
        onConfirm={sendDraft}
        onCancel={() => {
          if (!sending) {
            setConfirmOpen(false);
          }
        }}
      >
        <dl className="space-y-2 text-sm"><dt>対象顧客</dt><dd>{customerName}</dd><dt>件名</dt><dd>{subject}</dd><dt>本文</dt><dd className="max-h-56 overflow-y-auto whitespace-pre-wrap rounded-lg border p-3">{draft}</dd></dl>
      </Dialog>
    </div>
  );
}
