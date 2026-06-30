import { Card } from "@/components/ui/Card";

type SettingsSectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function SettingsSection({ title, description, children }: SettingsSectionProps) {
  return (
    <Card className="p-5">
      <div className="mb-5">
        <h2 className="text-base font-black text-slate-900">{title}</h2>
        {description && (
          <p className="mt-1 text-sm font-medium text-slate-500">{description}</p>
        )}
      </div>

      <div className="space-y-4">{children}</div>
    </Card>
  );
}
