import Link from "next/link";

import { publicationReady } from "../../../config/publication";

const sections = [
  {
    title: "1. 取得する情報",
    body: [
      "Profit Radarでは、アカウント情報として氏名、会社名・屋号、メールアドレス、認証に必要な情報等を取得します。",
      "メール連携を利用する場合、連携したメールアカウントに関連するメール本文、件名、送受信者、日時、スレッド情報、添付ファイルに関する情報その他分析に必要な情報を取り扱う場合があります。",
      "また、顧客情報、案件情報、営業履歴、利益情報、返信履歴、ユーザーが入力した内容、サービスの利用履歴、端末・ブラウザ・アクセスログその他サービス提供に必要な技術情報を取得する場合があります。",
    ],
  },
  {
    title: "2. 利用目的",
    body: [
      "本サービスの提供、本人確認、認証、アカウント管理のため。",
      "営業メール、顧客、案件、営業履歴等を解析し、利益機会、返信優先度、失注リスク、推奨アクション等を提示するため。",
      "AIによる返信文案、分類、要約、予測その他の支援機能を提供するため。",
      "本サービスの改善、障害調査、セキュリティ確保、不正利用防止のため。",
      "ユーザーからのお問い合わせへの対応および重要なお知らせを行うため。",
      "料金請求、契約管理その他有料サービスの提供に必要な処理を行うため。",
    ],
  },
  {
    title: "3. AIによる情報処理",
    body: [
      "本サービスでは、メール、顧客情報、案件情報その他の入力データをAIにより解析する場合があります。",
      "AIの処理対象、保存範囲、利用する外部AIサービスその他の詳細は、実際の提供構成に応じて本ポリシーまたはサービス上で明示します。",
      "本サービスは、ユーザーのデータを本サービス提供と無関係な目的で利用しない方針とします。",
    ],
  },
  {
    title: "4. 外部サービスとの連携",
    body: [
      "初期提供では、利用者が許可したGoogleアカウントのGmailと連携します。",
      "外部サービスから取得する情報は、ユーザーが許可した権限の範囲内で取り扱います。",
      "外部サービスとの接続を解除した場合でも、法令上の保存義務またはサービス運営上必要な範囲で一定期間情報を保持する場合があります。",
    ],
  },
  {
    title: "5. 第三者提供",
    body: [
      "法令に基づく場合その他法令上認められる場合を除き、本人の同意なく個人データを第三者へ提供しません。",
      "サービス提供に必要な業務委託先への情報提供については、法令に従い適切な管理を行います。",
    ],
  },
  {
    title: "6. 業務委託",
    body: [
      "本サービスでは、クラウド、データベース、認証、AI処理、決済、メール送信、監視その他のサービス提供に必要な業務を外部事業者へ委託する場合があります。",
      "委託先を利用する場合、必要な範囲で情報を取り扱わせ、適切な安全管理を行います。",
    ],
  },
  {
    title: "7. 安全管理",
    body: [
      "個人情報、認証情報その他の重要情報について、不正アクセス、漏えい、滅失、毀損等を防止するため、アクセス制御、認証、通信の保護、ログ管理その他合理的な安全管理措置を講じます。",
      "メールサービス等の認証情報は、必要性を最小限にし、安全な認証方式を優先します。",
    ],
  },
  {
    title: "8. 保存期間および削除",
    body: [
      "取得した情報は、利用目的の達成に必要な期間または法令上必要な期間保存します。",
      "アカウント削除後は、法令上保存が必要な場合、バックアップその他直ちに消去できない合理的な理由がある場合を除き、所定の手順に従い削除または利用できない状態にします。",
      "通常サービスデータは退会後原則30日以内に削除または匿名化し、バックアップは原則90日以内のローテーションにより削除します。請求・契約・問い合わせ等の法令または紛争対応上必要な記録は目的に必要な期間を分離して保持します。",
    ],
  },
  {
    title: "9. 開示・訂正・利用停止等",
    body: [
      "本人から、保有個人データについて開示、訂正、追加、削除、利用停止、消去その他法令上認められる請求を受けた場合、本人確認を行ったうえで法令に従い対応します。",
      "具体的な申請方法および問い合わせ窓口は、正式公開までに本ページまたはお問い合わせページへ掲載します。",
    ],
  },
  {
    title: "10. Cookie・アクセス解析",
    body: [
      "本サービスでは、ログイン状態の維持、セキュリティ、利用状況の把握、サービス改善等のためCookieその他類似技術を使用する場合があります。",
      "アクセス解析サービスを導入する場合は、実際の利用サービスに応じて本ポリシーへ追記します。",
    ],
  },
  {
    title: "11. 海外にある事業者の利用",
    body: [
      "クラウド、AIその他の外部サービスにより、データが日本国外で取り扱われる可能性がある場合には、実際のサービス構成および適用法令に応じて必要な対応と表示を行います。",
    ],
  },
  {
    title: "12. 本ポリシーの変更",
    body: [
      "法令、本サービス内容、利用する外部サービス等の変更に応じて、本ポリシーを改定する場合があります。",
      "重要な変更がある場合は、本サービス上その他適切な方法により通知します。",
    ],
  },
  {
    title: "13. お問い合わせ",
    body: [
      "個人情報の取扱い、開示、削除等のお問い合わせは、本サービスの問い合わせページから受け付けます。",
    ],
  },
];

export default function PrivacyPage() {
  const ready = publicationReady(process.env);
  return (
    <main className="min-h-screen bg-slate-50 px-5 py-12">
      <div className="mx-auto w-full max-w-3xl">
        <Link
          href="/register"
          className="text-sm font-semibold text-emerald-700 hover:underline"
        >
          ← 新規登録へ戻る
        </Link>

        <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-10">
          <div className="border-b border-slate-200 pb-6">
            <p className="text-sm font-bold text-emerald-700">
              Profit Radar
            </p>

            <h1 className="mt-2 text-3xl font-bold text-slate-950">
              プライバシーポリシー
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              Profit Radarにおける個人情報およびサービスデータの取扱いについて定めます。
            </p>

            <p className="mt-3 text-xs text-slate-500">
              制定日：2026年9月6日
            </p>
          </div>

          <div className="mt-8 space-y-9">
            {sections.map((section) => (
              <section key={section.title}>
                <h2 className="text-lg font-bold text-slate-900">
                  {section.title}
                </h2>

                <div className="mt-3 space-y-3">
                  {section.body.map((paragraph) => (
                    <p
                      key={paragraph}
                      className="text-sm leading-7 text-slate-700"
                    >
                      {paragraph}
                    </p>
                  ))}
                </div>
              </section>
            ))}
          </div>

          <div className="mt-10 border-t border-slate-200 pt-6">
            <p className="text-xs leading-6 text-slate-500">
              {ready
                ? `問い合わせ: ${process.env.PRIVACY_CONTACT} / 通常データ保持: ${process.env.DATA_RETENTION_DAYS}日 / バックアップ保持: ${process.env.BACKUP_RETENTION_DAYS}日。国外移転・外部サービス: ${process.env.INTERNATIONAL_TRANSFER_DISCLOSURE}`
                : "※ 正式公開前に、事業者情報、問い合わせ窓口、委託先、国外移転、保存期間等の実際の運用内容を確定して反映します。"}
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
