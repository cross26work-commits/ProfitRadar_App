import { PageHeader } from "./PageHeader";

type DashboardHeroSectionProps = {
  title: string;
  description: string;
};

export function DashboardHeroSection({ title, description }: DashboardHeroSectionProps) {
  return <PageHeader title={title} description={description} />;
}
