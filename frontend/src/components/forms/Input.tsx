type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({
  label,
  className = "",
  ...props
}: InputProps) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-slate-700">{label}</span>
      <input
        {...props}
        className={`mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-green-500 ${className}`}
      />
    </label>
  );
}
