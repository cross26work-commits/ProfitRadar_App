import { Card } from "@/components/ui/Card";

type DetailPanelProps = {
  title: string;
  children: React.ReactNode;
};

export function DetailPanel({ title, children }: DetailPanelProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-base font-black text-slate-900">{title}</h2>
      <Card className="p-5">{children}</Card>
    </section>
  );
}
