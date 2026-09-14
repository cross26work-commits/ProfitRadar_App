import "server-only";

import { apiGetServer } from "@/lib/api.server";

import {
  ApiLeadDetailResponse,
  ApiResultSummaryResponse,
  ApiTimelineResponse,
  mapApiLeadDetailToLeadDetail,
  mapApiTimelineToTimeline,
  mapResultSummaryToStats,
} from "@/services/profitRadarMappers";

export async function getLeadDetailServer(
  leadId: string | number
) {
  const [
    detailResponse,
    timelineResponse,
    statsResponse,
  ] = await Promise.all([
    apiGetServer<ApiLeadDetailResponse>(
      `/leads/${leadId}`
    ),

    apiGetServer<ApiTimelineResponse>(
      `/leads/${leadId}/timeline`
    ),

    apiGetServer<ApiResultSummaryResponse>(
      "/results/summary"
    ),
  ]);

  return {
    detail: mapApiLeadDetailToLeadDetail(detailResponse),
    stats: mapResultSummaryToStats(statsResponse),
    timeline: timelineResponse.items.map(
      mapApiTimelineToTimeline
    ),
  };
}