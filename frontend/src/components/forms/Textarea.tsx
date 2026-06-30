export function Textarea({
  label,
  placeholder,
  defaultValue,
}: {
  label: string;
  placeholder?: string;
  defaultValue?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-slate-700">{label}</span>
      <textarea
        placeholder={placeholder}
        defaultValue={defaultValue}
        className="mt-2 min-h-40 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 leading-7 text-slate-900 outline-none transition focus:border-green-500"
      />
    </label>
  );
}
