import type { CustomerProfile } from "@/types/profit-radar";
import { DetailPanel } from "./DetailPanel";
import { Badge } from "../ui/Badge";
import { DetailField } from "../ui/DetailField";
import { InfoGrid } from "../ui/InfoGrid";

type CustomerProfileSectionProps = {
  profile: CustomerProfile;
};

export function CustomerProfileSection({ profile }: CustomerProfileSectionProps) {
  return (
    <DetailPanel title="顧客情報">
      <InfoGrid
        items={[
          { label: "担当者", value: profile.contact },
          { label: "メール", value: profile.email },
          { label: "次の行動", value: profile.nextAction },
        ]}
      />
      <DetailField label="状態" value={<Badge tone="green">{profile.status}</Badge>} />
    </DetailPanel>
  );
}
