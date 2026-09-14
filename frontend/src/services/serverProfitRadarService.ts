import type {
  CustomerProfile,
  Lead,
  StatItem,
  Timeline,
} from "@/types/profit-radar";

import { serverApiGet } from "@/lib/server-api";

import {
  ApiCustomerDetailResponse,
  ApiLeadListResponse,
  ApiResultSummaryResponse,
  ApiTimelineResponse,
  mapApiCustomerDetailToProfile,
  mapApiLeadToLead,
  mapApiTimelineToTimeline,
  mapResultSummaryToStats,
} from "@/services/profitRadarMappers";

export type ServerCustomerDetailData = {
  profile: CustomerProfile;
  stats: StatItem[];
  leads: Lead[];
  timeline: Timeline[];
};

export async function getServerCustomerDetail(
  customerId: string | number
): Promise<ServerCustomerDetailData> {
  const [
    profileResponse,
    leadsResponse,
    timelineResponse,
    resultSummary,
  ] = await Promise.all([
    serverApiGet<ApiCustomerDetailResponse>(
      `/customers/${customerId}`
    ),

    serverApiGet<ApiLeadListResponse>(
      `/customers/${customerId}/leads`
    ),

    serverApiGet<ApiTimelineResponse>(
      `/customers/${customerId}/timeline`
    ),

    serverApiGet<ApiResultSummaryResponse>(
      "/results/summary"
    ),
  ]);

  const leads =
    (leadsResponse.items || []).map(
      mapApiLeadToLead
    );

  const timeline =
    (timelineResponse.items || []).map(
      mapApiTimelineToTimeline
    );

  return {
    profile:
      mapApiCustomerDetailToProfile(
        profileResponse
      ),

    stats:
      mapResultSummaryToStats(
        resultSummary
      ),

    leads,
    timeline,
  };
}
