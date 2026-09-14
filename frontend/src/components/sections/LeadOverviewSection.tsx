import type { LeadDetail } from "@/types/profit-radar";

import { DetailPanel } from "./DetailPanel";
import { ActionBar } from "../ui/ActionBar";
import { Badge } from "../ui/Badge";
import { DetailField } from "../ui/DetailField";
import { InfoGrid } from "../ui/InfoGrid";
import { MessageBox } from "../ui/MessageBox";

type LeadOverviewSectionProps = {
  lead: LeadDetail;
};

export function LeadOverviewSection({
  lead,
}: LeadOverviewSectionProps) {
  return (
    <DetailPanel title="案件情報">
      <ActionBar>
        <Badge tone="danger">
          {lead.priority} 優先度
        </Badge>

        <Badge tone="green">
          {lead.category}
        </Badge>

        <Badge>
          {lead.delayDays}日 経過
        </Badge>
      </ActionBar>

      <InfoGrid
        items={[
          {
            label: "顧客",
            value: lead.customer,
          },
          {
            label: "旧モデル候補額（参考）",
            value: lead.estimatedProfit,
          },
          {
            label: "旧モデル回収候補（参考）",
            value: lead.recoverableProfit,
          },
          {
            label: "次の行動",
            value: lead.nextAction,
          },
        ]}
      />

      <DetailField
        label="メール本文"
        value={
          <MessageBox>
            {lead.body}
          </MessageBox>
        }
      />
    </DetailPanel>
  );
}
