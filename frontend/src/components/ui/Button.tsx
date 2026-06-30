type ButtonProps = {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "danger";
};

export function Button({ children, variant = "primary" }: ButtonProps) {
  const styles = {
    primary: "bg-green-600 text-white hover:bg-green-700",
    secondary: "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };

  return (
    <button className={`rounded-2xl px-5 py-3 text-sm font-black transition ${styles[variant]}`}>
      {children}
    </button>
  );
}
