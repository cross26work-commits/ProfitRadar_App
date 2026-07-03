import type { Lead, StatItem, Task } from "@/types/profit-radar";

export const homeStats: StatItem[] = [
  { label: "今日の利益候補", value: "¥128,000", sub: "未対応 4件" },
  { label: "今すぐ返信", value: "3件", sub: "高優先度 2件" },
  { label: "回収見込", value: "¥420,000", sub: "今月累計" },
  { label: "返信待ち", value: "7件", sub: "平均2.4日" },
];

export const homeTasks: Task[] = [
  {
    title: "株式会社サンプルへ見積フォロー",
    description: "返信遅延3日。回収見込が高いため、本日中の対応を推奨。",
  },
  {
    title: "山田商事の契約確認",
    description: "契約前の確認メールで停止中。温度は高く、放置リスクあり。",
  },
  {
    title: "田中様へ再提案",
    description: "前回提案から7日経過。条件調整による再提案余地あり。",
  },
];

export const homePriorityLeads: Lead[] = [
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
    priority: "中",
    delay: "2日放置",
  },
];

export const homeRisks = ["未返信フォロー遅延", "契約前停止", "請求確認漏れ"];
