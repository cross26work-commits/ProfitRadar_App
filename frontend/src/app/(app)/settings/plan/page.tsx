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
  trial_days: number;
  monthly_price_jpy: number;
  today_due_jpy: number;
  first_billing_at: string;
  automatic_trial_charge: boolean;
  automatic_renewal: boolean;
};
const labels: Record<string, string> = {
  trial: "試用中",
  trialing: "試用中",
  trial_pending: "カード登録待ち",
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
  const [confirmations, setConfirmations] = useState({business:false,renewal:false,terms:false,privacy:false,refund:false});
  const agreed = Object.values(confirmations).every(Boolean);
  const testMode = data?.test_mode !== false;
  const canStartCheckout = data !== null &&
    ["trial_pending", "trial", "trial_expired", "canceled", "incomplete_expired"].includes(data.status);
  const canCancel = data !== null &&
    ["trialing", "active", "past_due", "unpaid", "paused"].includes(data.status);
  const checkoutHelp = !data
    ? "契約状態を確認しています。"
    : !canStartCheckout
      ? "既存の契約があるため、新しい申込みはできません。"
      : !agreed
        ? "申込みには、上の5項目を確認してチェックしてください。"
        : "Stripeの安全な申込み画面へ進みます。";
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
      const result = await apiPost<{ url: string }>("/billing/checkout", {
        expected_mode: testMode ? "test" : "live",
        business_use_confirmed:true, automatic_renewal_confirmed:true,
        terms_confirmed:true, privacy_confirmed:true, refund_policy_confirmed:true,
      });
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
    <main className="mx-auto max-w-3xl space-y-6 p-4 pb-16 text-slate-900 sm:p-6">
      <Link href="/settings" className="font-semibold text-emerald-700 hover:underline">← 設定</Link>
      <h1 className="text-3xl font-bold text-slate-950">試用・契約</h1>
      {error && (
        <p role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 font-medium text-amber-950">
          {error}
        </p>
      )}
      <section className="rounded-2xl border border-slate-300 bg-white p-5 text-slate-900 sm:p-6">
        <h2 className="font-semibold text-slate-950">現在の状態</h2>
        <p className="mt-3 text-xl font-medium text-slate-900">
          {data
            ? labels[data.status] || "状態を確認してください"
            : error
              ? "取得できません"
              : "読み込み中…"}
        </p>
        {data && (
          <>
            <p className="mt-3 text-slate-800">初回課金予定: {new Date(data.first_billing_at).toLocaleString("ja-JP", {timeZone: "Asia/Tokyo"})}（日本時間）</p>
            <p className="text-slate-800">
              機能利用: {data.allowed ? "利用可能" : "利用期間の確認が必要"}
            </p>
          </>
        )}
      </section>
      <section className="space-y-4 rounded-2xl border border-slate-300 bg-white p-5 text-slate-900 sm:p-6">
        <h2 className="text-2xl font-bold text-slate-950">月額19,800円（税込）</h2>
        <p className="leading-7 text-slate-900">
          本日の請求額は<strong>0円</strong>です。カード登録後7日間は無料です。
          無料期間中に解約しない場合、上記の初回課金予定日時に月額19,800円（税込）が自動課金され、以後1か月ごとに自動更新されます。
        </p>
        <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 font-medium text-amber-950">
          {testMode ? "現在はテストモードです。本番の支払い・有料契約は行えません。" : "Stripe画面でカードを登録しても本日の請求は0円です。無料期間終了日時と自動更新条件を必ず確認してください。"}
        </p>
        {data && !canStartCheckout && (
          <p role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-3 font-medium text-amber-950">
            既存の契約があります。二重契約を防ぐため新規申込みは停止しています。
            支払い・契約状態の確認は初期設定支援担当へご連絡ください。
          </p>
        )}
        {[
          ["business","私は法人または個人事業主等として、本サービスを事業目的で利用します。"],
          ["renewal","本日0円、7日後に月額19,800円（税込）が自動課金され、その後1か月ごとに自動更新されることを確認しました。"],
          ["terms","利用規約を確認し同意します。"],
          ["privacy","プライバシーポリシーを確認し同意します。"],
          ["refund","無料期間中は初回請求前に解約でき、有料開始後は利用者都合・日割りの返金がないことを確認しました。"],
        ].map(([key,label]) => <label key={key} className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-300 bg-white p-3 text-slate-900 transition hover:border-indigo-500 hover:bg-indigo-50 focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-200 has-[:checked]:border-indigo-600 has-[:checked]:bg-indigo-50"><input className="mt-0.5 h-5 w-5 shrink-0 accent-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-700 focus-visible:ring-offset-2" type="checkbox" checked={confirmations[key as keyof typeof confirmations]} onChange={(e)=>setConfirmations(v=>({...v,[key]:e.target.checked}))}/><span className="font-medium leading-6">{label}</span></label>)}
        <p className="text-sm font-medium text-slate-800"><Link href="/terms" className="text-indigo-800 underline underline-offset-2">利用規約</Link> / <Link href="/privacy" className="text-indigo-800 underline underline-offset-2">プライバシーポリシー</Link> / <Link href="/cancellation-refund" className="text-indigo-800 underline underline-offset-2">解約・返金ポリシー</Link></p>
        <button
          disabled={!agreed || busy || !canStartCheckout}
          onClick={checkout}
          aria-describedby="checkout-help"
          className="w-full rounded-xl bg-indigo-700 px-5 py-3 font-semibold text-white transition hover:bg-indigo-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-700 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-700 sm:w-auto"
        >
          {busy ? "移動中…" : testMode ? "Stripeテスト申込みへ" : "有料申込みへ（月額19,800円）"}
        </button>
        <p id="checkout-help" role="status" className="text-sm font-medium text-slate-700">{checkoutHelp}</p>
        <div className="text-sm leading-6 text-slate-700">
          <button onClick={cancel} disabled={busy || !canCancel} aria-describedby="cancel-help" className="mb-3 block rounded-lg border border-slate-400 bg-white px-4 py-3 font-semibold text-slate-900 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-700 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-100 disabled:text-slate-600">期間末で解約する{testMode ? "（テスト）" : ""}</button>
          <p id="cancel-help" className="mb-3 font-medium text-slate-700">{canCancel ? "解約後も、原則として支払済み期間末まで利用できます。" : "解約できる有効な契約はありません。"}</p>
          Trial期間中は初回請求前に解約できます。いつでも解約でき、有料開始後は支払済み期間末まで原則利用できます。利用者都合・日割りの返金はありません。
        </div>
      </section>
    </main>
  );
}
