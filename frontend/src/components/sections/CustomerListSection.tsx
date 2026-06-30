import { CustomerCard } from "@/components/business/CustomerCard";
import { EmptyState } from "@/components/feedback/EmptyState";

type Customer = {
  href?: string;
  name: string;
  leads: number;
  profit: string;
  last: string;
};

type CustomerListSectionProps = {
  title: string;
  customers: Customer[];
};

export function CustomerListSection({ title, customers }: CustomerListSectionProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-base font-black text-slate-900">{title}</h2>

      {customers.length === 0 ? (
        <EmptyState title="顧客がありません" description="表示できる顧客データはまだありません。" />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {customers.map((customer) => (
            <CustomerCard key={customer.name} {...customer} />
          ))}
        </div>
      )}
    </section>
  );
}
