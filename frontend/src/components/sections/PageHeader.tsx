type PageHeaderProps = {
  title: string;
  description?: string;
};

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-2">
      <h1 className="text-3xl font-black tracking-tight text-slate-950">{title}</h1>
      {description && (
        <p className="mt-2 text-sm font-medium leading-6 text-slate-500">
          {description}
        </p>
      )}
    </div>
  );
}
