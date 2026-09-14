import Link from "next/link";

export default function GuidePage() {
  return <main className="mx-auto max-w-3xl space-y-8 p-6 py-12 text-slate-900"><Link href="/">← Profit Radar</Link><h1 className="text-3xl font-bold">はじめてのProfit Radar</h1><ol className="list-decimal space-y-6 pl-6"><li>登録・ログイン後、会社名と氏名を入力します。試用終了だけでは課金されません。</li><li>設定 → Gmail接続から、仕事に利用する1つのアカウントを選択します。接続が切れた場合は同じ画面で再接続してください。</li><li>同期後、案件一覧から対象を選び、元メールと判断理由を確認します。何も表示されない場合は未接続・同期状態を確認してください。</li><li>返信案は必ず事実を確認して編集してください。「下書きを保存」で保持できます。</li><li>送信先・対象顧客・件名・本文を確認して送信します。結果不明の場合は再送せず「送信済み照合」を使います。見つからなくても未送信とは断定しません。</li><li>確定した成果は根拠とともに記録します。不明な金額を推測で確定しないでください。</li><li>有料継続を希望する場合のみプラン画面で申し込みます。準備中・テストモードの表示中は本番契約できません。</li></ol><p className="rounded-xl bg-amber-50 p-4">送信結果不明が続く場合は運営担当へ相談してください。別タブや本文変更での再送も避けてください。</p></main>;
}
