type MiniPanelProps = {
  title?: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
};

export function MiniPanel({ title, description, children, className = "" }: MiniPanelProps) {
  return (
    <div className={`rounded-2xl bg-slate-50 p-4 ${className}`}>
      {title && <p className="font-black text-slate-900">{title}</p>}
      {description && (
        <p className="mt-1 text-sm font-medium text-slate-500">{description}</p>
      )}
      {children}
    </div>
  );
}
