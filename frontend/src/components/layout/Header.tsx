export function Header({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 px-4 py-4 backdrop-blur lg:px-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        </div>
        <div className="hidden w-80 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-400 md:block">
          顧客名・案件名で検索...
        </div>
      </div>
    </header>
  );
}
