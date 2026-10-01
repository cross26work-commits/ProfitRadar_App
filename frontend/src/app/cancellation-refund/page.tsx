import Link from "next/link";
import { LegalBackLink } from "@/components/legal/LegalBackLink";

export default function CancellationRefundPage() {
  return <main className="min-h-screen bg-slate-50 px-5 py-12 text-slate-900">
    <article className="mx-auto max-w-3xl space-y-5 rounded-3xl border border-slate-200 bg-white p-6 text-slate-800 shadow-sm sm:p-8">
      <LegalBackLink />
      <h1 className="text-3xl font-bold text-slate-950">解約・返金ポリシー</h1>
      <p className="leading-7 text-slate-700">Profit Radarは法人・個人事業主等の事業用途向けサービスです。</p>
      <h2 className="text-xl font-bold text-slate-950">無料期間</h2>
      <p className="leading-7 text-slate-700">カード登録時の請求は0円です。7日間の無料期間中に解約すれば初回請求はありません。解約されない場合は表示された日時に月額19,800円（税込）が課金され、以後1か月ごとに自動更新します。</p>
      <h2 className="text-xl font-bold text-slate-950">解約</h2>
      <p className="leading-7 text-slate-700">設定画面からいつでも解約できます。有料開始後は原則として支払済み期間末まで利用できます。</p>
      <h2 className="text-xl font-bold text-slate-950">返金</h2>
      <p className="leading-7 text-slate-700">利用者都合の返金および日割返金はありません。二重請求、重大障害その他COROS WORKが返金相当と判断する場合は個別に対応します。</p>
      <Link className="font-semibold text-emerald-800 underline underline-offset-4" href="/contact">請求・解約について問い合わせる</Link>
    </article>
  </main>;
}
