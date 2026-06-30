import { Card } from "@/components/ui/Card";

type FormSectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function FormSection({ title, description, children }: FormSectionProps) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-base font-black text-slate-900">{title}</h2>
        {description && (
          <p className="mt-1 text-sm font-medium text-slate-500">{description}</p>
        )}
      </div>

      <Card className="space-y-4 p-5">{children}</Card>
    </section>
  );
}
