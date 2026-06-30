import { Badge } from "../ui/Badge";
import { MiniPanel } from "../ui/MiniPanel";

type ConnectionStatusProps = {
  label: string;
  connected: boolean;
  description?: string;
};

export function ConnectionStatus({
  label,
  connected,
  description,
}: ConnectionStatusProps) {
  return (
    <MiniPanel className="flex items-center justify-between gap-4">
      <div>
        <p className="font-black text-slate-900">{label}</p>
        {description && (
          <p className="mt-1 text-sm font-medium text-slate-500">
            {description}
          </p>
        )}
      </div>
      <Badge tone={connected ? "green" : "danger"}>
        {connected ? "接続済み" : "未接続"}
      </Badge>
    </MiniPanel>
  );
}
