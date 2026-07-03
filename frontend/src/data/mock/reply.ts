import type { Lead, StatItem } from "@/types/profit-radar";

export const replyStats: StatItem[] = [
  { label: "要返信", value: "3件", sub: "本日対応推奨" },
  { label: "高優先度", value: "2件", sub: "利益影響大" },
  { label: "平均放置", value: "3.1日", sub: "返信遅延あり" },
  { label: "見込利益", value: "¥260,000", sub: "要返信合計" },
];

export const replyLeads: Lead[] = [
  {
    id: "1",
    href: "/leads/1",
    rank: 1,
    customer: "株式会社サンプル",
    subject: "見積のご確認について",
    profit: "¥120,000",
    priority: "高",
    delay: "3日放置",
  },
  {
    id: "2",
    href: "/leads/2",
    rank: 2,
    customer: "山田商事",
    subject: "契約前確認",
    profit: "¥80,000",
    priority: "高",
    delay: "2日放置",
  },
  {
    id: "3",
    href: "/leads/3",
    rank: 3,
    customer: "田中様",
    subject: "再提案について",
    profit: "¥60,000",
    priority: "中",
    delay: "7日放置",
  },
];
