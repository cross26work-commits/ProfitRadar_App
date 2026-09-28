"use client";

export default function AppError({retry}: {retry: () => void}) {
  return <section role="alert" className="relative z-10 space-y-4 rounded-2xl border bg-white p-6 text-slate-900">
    <h1 className="text-xl font-bold">データを表示できませんでした</h1>
    <p>接続状態を確認して再読み込みしてください。送信や保存を自動で再実行することはありません。</p>
    <button type="button" className="relative z-10 inline-flex min-h-11 cursor-pointer items-center rounded-xl bg-indigo-700 px-4 py-3 font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700" onClick={retry}>再読み込み</button>
  </section>;
}
