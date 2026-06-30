type PageStackProps = {
  children: React.ReactNode;
};

export function PageStack({ children }: PageStackProps) {
  return <div className="space-y-8">{children}</div>;
}
