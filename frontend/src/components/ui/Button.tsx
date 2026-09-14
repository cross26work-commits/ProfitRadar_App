type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "danger";
  loading?: boolean;
};

export function Button({
  children,
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  const styles = {
    primary:
      "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-slate-200 disabled:text-slate-500",
    secondary:
      "bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 disabled:bg-slate-100 disabled:text-slate-400",
    danger:
      "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-100 disabled:text-red-400",
  };

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`
        rounded-xl
        px-5
        py-3
        text-sm
        font-semibold
        transition
        disabled:cursor-not-allowed
        ${styles[variant]}
        ${className}
      `}
    >
      {loading ? "処理中..." : children}
    </button>
  );
}
