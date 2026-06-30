import { DetailField } from "./DetailField";

type InfoItem = {
  label: string;
  value: string | number;
};

type InfoGridProps = {
  items: InfoItem[];
};

export function InfoGrid({ items }: InfoGridProps) {
  return (
    <div className="grid gap-4 text-sm md:grid-cols-2">
      {items.map((item) => (
        <DetailField key={item.label} label={item.label} value={item.value} />
      ))}
    </div>
  );
}
