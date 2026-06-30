type PageStackProps = {
  children: React.ReactNode;
};

export function PageStack({ children }: PageStackProps) {
  return <div className="space-y-7">{children}</div>;
}
