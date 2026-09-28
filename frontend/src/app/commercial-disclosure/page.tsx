import Link from "next/link";

const value = (name: string) => process.env[name]?.trim() || "公開前のOWNER ACTIONで確定します";

export default function CommercialDisclosurePage() {
  const rows = [
    ["販売事業者", value("SELLER_NAME")], ["所在地", value("SELLER_ADDRESS")],
    ["電話番号", value("SUPPORT_PHONE")], ["メール", value("SUPPORT_EMAIL")],
    ["販売価格", "月額19,800円（税込）"],
    ["試用", "14日間。試用終了のみで自動課金されず、明示的な申込みが必要です。"],
    ["解約", value("CANCELLATION_POLICY")], ["返金", value("REFUND_POLICY")],
    ["アカウント削除", value("DATA_DELETION_POLICY")],
    ["データ保持", process.env.DATA_RETENTION_DAYS ? `${process.env.DATA_RETENTION_DAYS}日` : value("DATA_RETENTION_DAYS")],
    ["バックアップ保持", process.env.BACKUP_RETENTION_DAYS ? `${process.env.BACKUP_RETENTION_DAYS}日` : value("BACKUP_RETENTION_DAYS")],
    ["管轄", value("GOVERNING_COURT")],
  ];
  return <main className="min-h-screen bg-slate-50 px-5 py-12"><div className="mx-auto max-w-3xl">
    <Link href="/" className="text-sm font-semibold text-emerald-700">← トップへ戻る</Link>
    <section className="mt-6 rounded-3xl border bg-white p-6 shadow-sm md:p-10">
      <h1 className="text-3xl font-bold">特定商取引法に基づく表記</h1>
      <p className="mt-3 text-sm text-slate-600">未確定欄がある間は販売準備中であり、申込みを受け付けません。</p>
      <dl className="mt-8 divide-y">{rows.map(([label,content])=><div key={label} className="grid gap-2 py-4 md:grid-cols-3"><dt className="font-semibold">{label}</dt><dd className="md:col-span-2">{content}</dd></div>)}</dl>
    </section>
  </div></main>;
}
