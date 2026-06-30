type MessageBoxProps = {
  children: React.ReactNode;
};

export function MessageBox({ children }: MessageBoxProps) {
  return (
    <p className="mt-3 rounded-2xl bg-slate-50 p-5 leading-8 text-slate-700">
      {children}
    </p>
  );
}
