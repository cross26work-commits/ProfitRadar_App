import type { Customer, Lead, StatItem, Timeline } from "@/types/profit-radar";

export const customerStats: StatItem[] = [
  { label: "顧客数", value: "12社", sub: "今月接触あり" },
  { label: "進行中案件", value: "18件", sub: "未対応 4件" },
  { label: "見込利益", value: "¥820,000", sub: "全顧客合計" },
  { label: "実回収", value: "¥240,000", sub: "今月累計" },
];

export const customers: Customer[] = [
  { href: "/customers/1", name: "株式会社サンプル", leads: 4, profit: "¥320,000", last: "今日" },
  { href: "/customers/2", name: "山田商事", leads: 3, profit: "¥210,000", last: "1日前" },
  { href: "/customers/3", name: "田中様", leads: 2, profit: "¥90,000", last: "3日前" },
];

export const customerDetailStats: StatItem[] = [
  { label: "見込利益", value: "¥320,000", sub: "進行中案件合計" },
  { label: "実回収", value: "¥120,000", sub: "今月累計" },
  { label: "案件数", value: "4件", sub: "未対応 2件" },
  { label: "最終連絡", value: "今日", sub: "返信待ちあり" },
];

export const customerDetailLeads: Lead[] = [
  {
    href: "/leads/1",
    rank: 1,
    customer: "株式会社サンプル",
    subject: "見積のご確認について",
    profit: "¥120,000",
    priority: "高",
    delay: "3日放置",
  },
  {
    href: "/leads/2",
    rank: 2,
    customer: "株式会社サンプル",
    subject: "追加依頼の確認",
    profit: "¥80,000",
    priority: "中",
    delay: "1日放置",
  },
];

export const customerTimeline: Timeline[] = [
  {
    type: "MAIL",
    title: "見積確認メールを送信",
    body: "見積内容の確認と、次回打ち合わせ候補日の確認を送信しました。",
    time: "今日 10:20",
  },
  {
    type: "AI",
    title: "対応優先度を高に判定",
    body: "利益見込が高く、返信遅延が発生しているため、本日中の再フォローを推奨。",
    time: "今日 10:21",
  },
  {
    type: "SMS",
    title: "SMS送信予定",
    body: "メール未返信が続く場合、短文SMSで確認する余地があります。",
    time: "予定",
  },
];
