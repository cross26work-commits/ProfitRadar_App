import Link from "next/link";

const value = (name: string) => process.env[name]?.trim() || "公開前のOWNER ACTIONで確定します";

export default function CommercialDisclosurePage() {
  const rows = [
    ["運営ブランド", "COROS WORK"], ["販売事業者", value("SELLER_NAME")],
    ["所在地", "請求があった場合、遅滞なく開示します。"],
    ["電話番号", "請求があった場合、遅滞なく開示します。"], ["問い合わせ", value("SUPPORT_EMAIL")],
    ["販売価格", "月額19,800円（税込）"],
    ["試用・支払時期", "カード登録時の請求は0円。7日間の無料期間終了までに解約されない場合、月額19,800円（税込）を自動課金し、以後1か月ごとに自動更新します。"],
    ["解約", "いつでも可能です。無料期間中の解約は初回請求なし。有料開始後は原則として支払済み期間末まで利用できます。"],
    ["返金", "利用者都合の返金および日割返金はありません。二重請求、重大障害その他COROS WORKが返金相当と判断する場合は個別に対応します。"],
    ["アカウント削除", value("DATA_DELETION_POLICY")],
    ["データ保持", "退会後、通常サービスデータは原則30日以内に削除または匿名化します。"],
    ["バックアップ保持", "バックアップは原則90日以内のローテーションで削除します。"],
    ["管轄", value("GOVERNING_COURT")],
  ];
  return <main className="min-h-screen bg-slate-50 px-5 py-12"><div className="mx-auto max-w-3xl">
    <Link href="/" className="text-sm font-semibold text-emerald-700">← トップへ戻る</Link>
    <section className="mt-6 rounded-3xl border bg-white p-6 shadow-sm md:p-10">
      <h1 className="text-3xl font-bold">特定商取引法に基づく表記</h1>
      <p className="mt-3 text-sm text-slate-600">未確定欄がある間は販売準備中であり、申込みを受け付けません。</p>
      <p className="mt-3 text-sm"><Link href="/contact" className="font-semibold text-emerald-700">事業者情報の開示を請求する</Link></p>
      <dl className="mt-8 divide-y">{rows.map(([label,content])=><div key={label} className="grid gap-2 py-4 md:grid-cols-3"><dt className="font-semibold">{label}</dt><dd className="md:col-span-2">{content}</dd></div>)}</dl>
    </section>
  </div></main>;
}
