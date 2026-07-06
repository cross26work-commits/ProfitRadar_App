"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ActionBar } from "@/components/ui/ActionBar";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/forms/Input";
import { apiPatch } from "@/lib/api";

type ActualProfitFormProps = {
  eventId: string | number;
  defaultValue?: number;
};

export function ActualProfitForm({
  eventId,
  defaultValue = 0,
}: ActualProfitFormProps) {
  const router = useRouter();
  const [actualProfit, setActualProfit] = useState(String(defaultValue || ""));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSave() {
    setSaving(true);
    setMessage("");

    try {
      await apiPatch(`/profit-events/${eventId}/actual-profit`, {
        actual_profit: Number(actualProfit || 0),
        status: "closed",
      });

      setMessage("実利益を保存しました。Resultsへ反映済みです。");
      router.refresh();
    } catch (error) {
      console.error(error);
      setMessage("保存に失敗しました。ターミナルまたはAPIログを確認してください。");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <Input
        label="実回収額"
        placeholder="例：200000"
        value={actualProfit}
        onChange={(event) => setActualProfit(event.target.value)}
      />

      <ActionBar>
        <Button variant="secondary" onClick={handleSave} disabled={saving}>
          {saving ? "保存中..." : "保存する"}
        </Button>
      </ActionBar>

      {message && (
        <p className="text-sm font-bold text-slate-600">{message}</p>
      )}
    </div>
  );
}
