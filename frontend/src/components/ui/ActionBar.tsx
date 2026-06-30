type ActionBarProps = {
  children: React.ReactNode;
};

export function ActionBar({ children }: ActionBarProps) {
  return <div className="flex flex-wrap gap-2">{children}</div>;
}
