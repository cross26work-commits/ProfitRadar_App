type PageHeaderProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
};

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">{title}</h1>
        {description && (
          <p className="mt-2 text-sm font-medium text-slate-500">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
