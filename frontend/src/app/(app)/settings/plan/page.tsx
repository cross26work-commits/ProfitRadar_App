"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Billing = {
  status: string;
  allowed: boolean;
  trial_ends_at: string;
  paid_until: string | null;
  test_mode?: boolean;
};
const labels: Record<string, string> = {
  trial: "試用中",
  trial_expired: "試用終了",
  active: "有料利用中",
  past_due: "支払い確認が必要",
  canceled: "解約済み",
  unpaid: "支払い未完了",
  incomplete: "契約手続き未完了",
  incomplete_expired: "契約手続き期限切れ",
  paused: "契約一時停止中",
};
export default function PlanPage() {
  const [data, setData] = useState<Billing | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const testMode = data?.test_mode !== false;
  const canStartCheckout = data !== null &&
    ["trial", "trial_expired", "canceled", "incomplete_expired"].includes(data.status);
  useEffect(() => {
    let active = true;
    apiGet<Billing>("/billing/status")
      .then((value) => {
        if (active) setData(value);
      })
      .catch(() => {
        if (active)
          setError(
            "契約状態を取得できませんでした。時間を置いて再読み込みしてください。",
          );
      });
    return () => {
      active = false;
    };
  }, []);
  async function checkout() {
    if (!canStartCheckout || !agreed || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await apiPost<{ url: string }>("/billing/checkout", {expected_mode: testMode ? "test" : "live"});
      const url = new URL(result.url);
      if (url.protocol !== "https:" || url.hostname !== "checkout.stripe.com")
        throw new Error();
      window.location.assign(url.toString());
    } catch {
      setError("申込み受付を確認できませんでした。新しい契約を重ねず、契約状態を確認して再試行してください。");
      setBusy(false);
    }
  }
  async function cancel() {
    if (!window.confirm("支払済み期間の末日で解約しますか？")) return;
    setBusy(true);
    try {
      await apiPost("/billing/cancel", {});
      setError("期間末解約を受け付けました。契約状態の反映までお待ちください。");
    } catch {
      setError("解約受付を確認できませんでした。完了とは扱っていません。再確認してください。");
    } finally { setBusy(false); }
  }
  return (
    <main className="mx-auto max-w-3xl space-y-6 p-4 pb-16">
      <Link href="/settings">← 設定</Link>
      <h1 className="text-3xl font-bold">試用・契約</h1>
      {error && (
        <p role="alert" className="rounded-xl bg-amber-50 p-4">
          {error}
        </p>
      )}
      <section className="rounded-2xl border bg-white p-6">
        <h2 className="font-semibold">現在の状態</h2>
        <p className="mt-3 text-xl">
          {data
            ? labels[data.status] || "状態を確認してください"
            : error
              ? "取得できません"
              : "読み込み中…"}
        </p>
        {data && (
          <>
            <p className="mt-3">
              試用期限: {new Date(data.trial_ends_at).toLocaleString("ja-JP", {timeZone: "Asia/Tokyo"})}（日本時間）
            </p>
            <p>
              機能利用: {data.allowed ? "利用可能" : "利用期間の確認が必要"}
            </p>
          </>
        )}
      </section>
      <section className="space-y-4 rounded-2xl border bg-white p-6">
        <h2 className="text-2xl font-bold">月額19,800円（税込）</h2>
        <p>
          14日間の試用終了だけでは課金されません。継続には明示的な有料申込みが必要です。
        </p>
        <p className="rounded-lg bg-amber-50 p-3">
          {testMode ? "現在はテストモードです。本番の支払い・有料契約は行えません。" : "お申込み内容と次のStripe画面の料金をご確認ください。試用終了だけでは課金されません。"}
        </p>
        {data && !canStartCheckout && (
          <p role="status" className="rounded-lg bg-amber-50 p-3">
            既存の契約があります。二重契約を防ぐため新規申込みは停止しています。
            支払い・契約状態の確認は初期設定支援担当へご連絡ください。
          </p>
        )}
        <label className="flex items-start gap-3">
          <input
            className="mt-1 h-5 w-5"
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          <span>
            料金と
            <Link href="/terms" className="underline">
              利用条件
            </Link>
            を確認し、{testMode ? "テスト申込み" : "有料申込み"}画面へ進みます。
          </span>
        </label>
        <button
          disabled={!agreed || busy || !canStartCheckout}
          onClick={checkout}
          className="rounded-xl bg-indigo-700 px-5 py-3 text-white disabled:opacity-40"
        >
          {busy ? "移動中…" : testMode ? "Stripeテスト申込みへ" : "有料申込みへ（月額19,800円）"}
        </button>
        <p className="text-sm text-slate-500">
          <button onClick={cancel} disabled={busy || !data || data.status === "trial" || data.status === "trial_expired"} className="mb-4 block rounded-lg border px-4 py-3 disabled:opacity-40">期間末で解約する{testMode ? "（テスト）" : ""}</button>
          解約・データ保持については利用条件をご確認ください。未確定の条件では本番契約を受け付けません。
        </p>
      </section>
    </main>
  );
}
