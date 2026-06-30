import { ReactNode } from "react";

type Variant = "primary" | "secondary" | "danger";

export function Button({
  children,
  variant = "primary",
}: {
  children: ReactNode;
  variant?: Variant;
}) {
  const styles = {
    primary: "bg-green-600 text-white hover:bg-green-700",
    secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };

  return (
    <button className={`rounded-xl px-4 py-2 text-sm font-bold transition ${styles[variant]}`}>
      {children}
    </button>
  );
}
