import Link from "next/link";
import { publicationReady } from "../../config/publication";

export default function RootPage() {
  const seller = process.env.SELLER_NAME;
  const contact = process.env.SUPPORT_EMAIL;
  const ready = publicationReady(process.env);
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="mx-auto flex max-w-6xl items-center justify-between p-6"><span className="text-xl font-black">Profit Radar</span><Link className="rounded-lg border px-4 py-2" href="/login">ログイン</Link></nav>
      <section className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <p className="text-sm font-semibold text-indigo-700">小規模サービス会社の、Gmail営業を支える</p>
        <h1 className="mt-5 max-w-3xl text-4xl font-bold leading-tight md:text-6xl"><span className="inline-block">次に返すべき</span><span className="inline-block">商談を、</span><br />見失わない。</h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">未返信、見積もり後の放置、追客忘れを確認し、返信案の編集から結果の記録まで。送信する宛先と本文は、必ずあなたが確認します。</p>
        {!ready && <p role="status" className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4">有料提供の準備中です。販売開始前に動作検証・販売者情報・Google審査を確認します。この画面から課金は発生しません。</p>}
        <div className="mt-8 flex flex-wrap gap-4"><Link href="/register" className="rounded-xl bg-indigo-700 px-6 py-4 font-semibold text-white">{ready ? "7日間の無料試用を始める" : "検証用アカウントを登録"}</Link><Link href="/terms" className="rounded-xl border px-6 py-4">利用条件を確認</Link></div>
      </section>
      <section className="mx-auto grid max-w-6xl gap-5 px-6 pb-16 md:grid-cols-3">
        {[['1. 接続・確認','Gmailを接続し、対応が必要な案件と元メールを確認します。'],['2. 編集・確認送信','返信案を編集・保存。宛先と本文を確認した後にだけ送信します。'],['3. 結果を記録','見込みと確定した成果を分けて記録します。AIによる売上増加を保証するものではありません。']].map(([title,body])=><article key={title} className="rounded-2xl border bg-white p-6"><h2 className="font-bold">{title}</h2><p className="mt-3 leading-7 text-slate-600">{body}</p></article>)}
      </section>
      <section className="mx-auto max-w-3xl rounded-2xl border bg-white p-8"><h2 className="text-2xl font-bold">事業者向けプラン</h2><p className="mt-5 text-4xl font-bold">19,800円<span className="text-base font-normal"> / 月（税込）</span></p><p className="mt-4 leading-7">1社1ユーザー・Gmail 1アカウント・日本語。カード登録時は0円、7日間無料です。期間中に解約されない場合は月額料金を自動課金し、以後1か月ごとに自動更新します。</p><p className="mt-4 text-sm text-slate-500">法人・個人事業主等の事業用途向けです。初回課金日時、解約・返金条件は申込直前にも明示します。</p></section>
      <footer className="mx-auto max-w-6xl space-y-3 px-6 py-12 text-sm text-slate-600"><p>運営ブランド: COROS WORK / 販売者: {seller || "公開前に入力が必要"} / 問い合わせ: {contact || "公開前に入力が必要"}</p><div className="flex flex-wrap gap-6"><Link href="/terms">利用条件</Link><Link href="/privacy">プライバシー</Link><Link href="/commercial-disclosure">特商法表記</Link><Link href="/cancellation-refund">解約・返金</Link><Link href="/data-retention">データ保持</Link><Link href="/google-data-use">Googleデータ利用</Link><Link href="/contact">問い合わせ</Link><Link href="/guide">利用ガイド</Link></div></footer>
    </main>
  );
}
