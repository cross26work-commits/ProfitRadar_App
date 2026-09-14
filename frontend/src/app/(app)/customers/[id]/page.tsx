import { CustomerDetailView } from "@/components/business/CustomerDetailView";
import { getServerCustomerDetail } from "@/services/serverProfitRadarService";

export default async function Page({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  const customer = await getServerCustomerDetail(id);
  return <CustomerDetailView customer={customer} />;
}
