import Link from "next/link";
export default function MissingResource() {
  return <section className="space-y-4 p-6"><h1 className="text-xl font-bold">情報が見つかりません</h1><p>削除されたか、閲覧できない情報です。</p><Link href="/leads" className="underline">案件一覧へ戻る</Link></section>;
}
