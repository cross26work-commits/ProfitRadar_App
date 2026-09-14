import { LeadDetailView } from "@/components/business/LeadDetailView";
import { getLeadDetailServer } from "@/services/profitRadarServerService";

export default async function Page({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  const lead = await getLeadDetailServer(id);
  return <LeadDetailView lead={lead} />;
}
