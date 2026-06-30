import { DetailPanel } from "./DetailPanel";
import { Badge } from "../ui/Badge";
import { DetailField } from "../ui/DetailField";
import { InfoGrid } from "../ui/InfoGrid";

export function CustomerProfileSection() {
  return (
    <DetailPanel title="顧客情報">
      <InfoGrid
        items={[
          { label: "担当者", value: "佐藤様" },
          { label: "メール", value: "sample@example.com" },
          { label: "次の行動", value: "本日中に再フォロー" },
        ]}
      />
      <DetailField label="状態" value={<Badge tone="green">商談中</Badge>} />
    </DetailPanel>
  );
}
