import { ChartCard } from "../ui/ChartCard";
import { DetailPanel } from "./DetailPanel";
import { ActionBar } from "../ui/ActionBar";
import { Badge } from "../ui/Badge";

type ResultsSummarySectionProps = {
  insights: string[];
};

export function ResultsSummarySection({ insights }: ResultsSummarySectionProps) {
  return (
    <>
      <ChartCard title="実回収推移" description="日別・週別の回収実績を表示予定。" />
      <ChartCard title="案件ステージ別利益" description="見積・契約・請求などの分類別に表示予定。" />

      <DetailPanel title="分析メモ">
        <ActionBar>
          {insights.map((insight) => (
            <Badge key={insight} tone="green">
              {insight}
            </Badge>
          ))}
        </ActionBar>
      </DetailPanel>
    </>
  );
}
