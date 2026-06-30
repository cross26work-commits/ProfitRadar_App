import type { StatItem, Timeline } from "@/types/profit-radar";

export const leadDetailStats: StatItem[] = [
  { label: "見込利益", value: "¥120,000", sub: "高優先度" },
  { label: "放置日数", value: "3日", sub: "本日対応推奨" },
  { label: "状態", value: "未対応", sub: "返信待ち" },
  { label: "確度", value: "高", sub: "見積確認中" },
];

export const leadTimeline: Timeline[] = [
  {
    type: "MAIL",
    title: "相手から見積確認メール",
    body: "見積内容について確認したい旨のメールを受信しました。",
    time: "3日前",
  },
  {
    type: "AI",
    title: "利益候補として検出",
    body: "見積・契約に近い内容のため、高優先度案件として判定しました。",
    time: "3日前",
  },
];
