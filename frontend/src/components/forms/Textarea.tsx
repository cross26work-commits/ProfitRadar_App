import type { ChangeEvent } from "react";

type TextareaProps = {
  label: string;
  placeholder?: string;
  defaultValue?: string;
  value?: string;
  onChange?: (event: ChangeEvent<HTMLTextAreaElement>) => void;
};

export function Textarea({
  label,
  placeholder,
  defaultValue,
  value,
  onChange,
}: TextareaProps) {
  return (
    <label className="grid gap-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <textarea
        className="min-h-32 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-4 focus:ring-slate-100"
        placeholder={placeholder}
        defaultValue={defaultValue}
        value={value}
        onChange={onChange}
      />
    </label>
  );
}
