import type { StatItem } from "@/types/profit-radar";

export const resultStats: StatItem[] = [
  { label: "今月実回収", value: "¥240,000", sub: "前月比 +18%" },
  { label: "見込利益", value: "¥820,000", sub: "進行中案件" },
  { label: "対応件数", value: "31件", sub: "今月累計" },
  { label: "回収率", value: "29.2%", sub: "実回収 / 見込" },
];

export const resultInsights = [
  "見積案件の回収率が高い",
  "3日以上放置で成約率低下",
  "請求確認メールは即日対応が有効",
];
