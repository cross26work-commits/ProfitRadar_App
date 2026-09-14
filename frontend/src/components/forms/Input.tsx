type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  helperText?: string;
  error?: string;
};

export function Input({
  label,
  helperText,
  error,
  className = "",
  ...props
}: InputProps) {
  return (
    <label className="block">
      <span className="text-sm font-semibold text-slate-700">
        {label}
      </span>

      <input
        {...props}
        className={`
          mt-2
          w-full
          rounded-xl
          border
          bg-white
          px-4
          py-3
          text-sm
          text-slate-900
          placeholder:text-slate-400
          outline-none
          transition
          ${
            error
              ? "border-red-400 focus:border-red-500 focus:ring-2 focus:ring-red-100"
              : "border-slate-300 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          }
          ${className}
        `}
      />

      {error ? (
        <p className="mt-2 text-xs font-medium text-red-700">
          {error}
        </p>
      ) : helperText ? (
        <p className="mt-2 text-xs text-slate-500">
          {helperText}
        </p>
      ) : null}
    </label>
  );
}
