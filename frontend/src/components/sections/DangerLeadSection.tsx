import { DetailPanel } from "./DetailPanel";
import { ActionBar } from "../ui/ActionBar";
import { Badge } from "../ui/Badge";

type DangerLeadSectionProps = {
  title?: string;
  risks: string[];
};

export function DangerLeadSection({ title = "現在の注意点", risks }: DangerLeadSectionProps) {
  if (risks.length === 0) return null;

  return (
    <DetailPanel title={title}>
      <ActionBar>
        {risks.map((risk) => (
          <Badge key={risk} tone="warning">
            {risk}
          </Badge>
        ))}
      </ActionBar>
    </DetailPanel>
  );
}
