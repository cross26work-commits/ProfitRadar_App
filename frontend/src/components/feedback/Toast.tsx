type ToastProps = {
  title: string;
  description?: string;
  tone?: "success" | "warning" | "danger" | "neutral";
};

const styles = {
  success: "border-green-200 bg-green-50 text-green-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-red-200 bg-red-50 text-red-800",
  neutral: "border-slate-200 bg-white text-slate-800",
};

export function Toast({ title, description, tone = "neutral" }: ToastProps) {
  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${styles[tone]}`}>
      <p className="font-black">{title}</p>
      {description && <p className="mt-1 text-sm font-medium">{description}</p>}
    </div>
  );
}
