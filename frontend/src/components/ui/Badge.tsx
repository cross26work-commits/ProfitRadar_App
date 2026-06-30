type Tone = "green" | "danger" | "warning" | "neutral";

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: Tone }) {
  const styles = {
    green: "bg-green-50 text-green-700",
    danger: "bg-red-50 text-red-700",
    warning: "bg-amber-50 text-amber-700",
    neutral: "bg-slate-100 text-slate-700",
  };

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${styles[tone]}`}>
      {children}
    </span>
  );
}
