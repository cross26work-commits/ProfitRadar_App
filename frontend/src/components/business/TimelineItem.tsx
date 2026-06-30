export function TimelineItem({
  type,
  title,
  body,
  time,
}: {
  type: string;
  title: string;
  body: string;
  time: string;
}) {
  return (
    <div className="flex gap-4 border-b border-slate-100 pb-5 last:border-0">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-green-50 text-xs font-black text-green-700">
        {type}
      </div>
      <div>
        <p className="font-black text-slate-900">{title}</p>
        <p className="mt-2 leading-7 text-slate-600">{body}</p>
        <p className="mt-1 text-xs font-bold text-slate-400">{time}</p>
      </div>
    </div>
  );
}
