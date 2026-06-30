type DetailFieldProps = {
  label: string;
  value: React.ReactNode;
};

export function DetailField({ label, value }: DetailFieldProps) {
  return (
    <div>
      <p className="font-bold text-slate-500">{label}</p>
      <div className="mt-1 font-black text-slate-900">{value}</div>
    </div>
  );
}
