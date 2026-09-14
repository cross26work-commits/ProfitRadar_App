"use client";

export default function AppError({retry}: {retry: () => void}) {
  return <section role="alert" className="space-y-4 rounded-2xl border bg-white p-6">
    <h1 className="text-xl font-bold">データを表示できませんでした</h1>
    <p>接続状態を確認して再読み込みしてください。送信や保存を自動で再実行することはありません。</p>
    <button className="rounded-xl bg-indigo-700 px-4 py-3 text-white" onClick={retry}>再読み込み</button>
  </section>;
}
