"use client";

import { useEffect, useState } from "react";
import { Textarea } from "@/components/forms/Textarea";
import { ActionBar } from "@/components/ui/ActionBar";
import { Button } from "@/components/ui/Button";

type ReplyDraftFormProps = {
  eventId: string | number;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const COMPANY_ID =
  process.env.NEXT_PUBLIC_DEMO_COMPANY_ID ??
  "517a5d5a-3488-4ece-91be-99034929143a";

export function ReplyDraftForm({ eventId }: ReplyDraftFormProps) {
  const [draft, setDraft] = useState("");
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadDraft() {
      setLoading(true);
      setMessage("");

      try {
        const response = await fetch(
          `${API_BASE_URL}/reply/${eventId}/draft`,
          {
            headers: {
              "x-company-id": COMPANY_ID,
            },
          },
        );

        if (!response.ok) {
          throw new Error(await response.text());
        }

        const data = await response.json();
        setDraft(data.draft || "");
        setCustomerId(data.event?.customer_id ?? null);
      } catch (error) {
        console.error(error);
        setMessage("返信下書きの取得に失敗しました。");
      } finally {
        setLoading(false);
      }
    }

    loadDraft();
  }, [eventId]);

  async function saveDraft() {
    setSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/reply/${eventId}/save-draft`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-company-id": COMPANY_ID,
          },
          body: JSON.stringify({
            customer_id: customerId,
            body: draft,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setMessage("返信下書きを保存しました。TimelineとLearningへ反映済みです。");
    } catch (error) {
      console.error(error);
      setMessage("返信下書きの保存に失敗しました。");
    } finally {
      setSaving(false);
    }
  }

  async function sendDraftMock() {
    setSending(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/reply/${eventId}/send`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-company-id": COMPANY_ID,
          },
          body: JSON.stringify({
            customer_id: customerId,
            to_email: "demo@example.com",
            subject: "Profit Radar 返信",
            body: draft,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setMessage("返信を疑似送信しました。TimelineとLearningへ反映済みです。");
    } catch (error) {
      console.error(error);
      setMessage("返信の疑似送信に失敗しました。");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-4">
      <Textarea
        label={loading ? "返信内容を生成中..." : "返信内容"}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />

      <ActionBar>
        <Button onClick={saveDraft} disabled={loading || saving || sending}>
          {saving ? "保存中..." : "下書き保存"}
        </Button>
        <Button onClick={sendDraftMock} disabled={loading || saving || sending || !draft}>
          {sending ? "送信中..." : "疑似送信"}
        </Button>
      </ActionBar>

      {message && (
        <p className="text-sm font-bold text-slate-600">{message}</p>
      )}
    </div>
  );
}
