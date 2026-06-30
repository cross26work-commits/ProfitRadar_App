export function Header({
  title,
  subtitle,
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-5 py-5 md:px-8 lg:px-10">
        <div>
          <p className="text-2xl font-black tracking-tight text-slate-950">{title}</p>
          <p className="mt-1 text-sm font-medium text-slate-500">{subtitle}</p>
        </div>

        <div className="hidden w-full max-w-sm rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-400 md:block">
          顧客名・案件名で検索...
        </div>
      </div>
    </header>
  );
}
