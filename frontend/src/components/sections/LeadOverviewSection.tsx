import { DetailPanel } from "./DetailPanel";
import { ActionBar } from "../ui/ActionBar";
import { Badge } from "../ui/Badge";
import { DetailField } from "../ui/DetailField";
import { InfoGrid } from "../ui/InfoGrid";
import { MessageBox } from "../ui/MessageBox";

export function LeadOverviewSection() {
  return (
    <DetailPanel title="案件情報">
      <ActionBar>
        <Badge tone="danger">高優先度</Badge>
        <Badge tone="green">見積</Badge>
        <Badge>3日放置</Badge>
      </ActionBar>

      <InfoGrid
        items={[
          { label: "顧客", value: "株式会社サンプル" },
          { label: "次の行動", value: "本日中に確認フォロー" },
        ]}
      />

      <DetailField
        label="メール本文"
        value={
          <MessageBox>
            お世話になっております。先日いただいた見積内容について確認させてください。
            条件面を再度確認したうえで、進行可否をご連絡いたします。
          </MessageBox>
        }
      />
    </DetailPanel>
  );
}
