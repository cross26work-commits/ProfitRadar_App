import type { Customer, CustomerProfile, Lead, LeadDetail, StatItem, Task, Timeline } from "@/types/profit-radar";
import { apiGet } from "@/lib/api";
import { homePriorityLeads, homeRisks, homeStats, homeTasks } from "@/data/mock/home";
import { replyLeads, replyStats } from "@/data/mock/reply";
import {
  customerDetailLeads,
  customerDetailStats,
  customers,
  customerStats,
  customerTimeline,
} from "@/data/mock/customers";
import { leadDetailStats, leadTimeline } from "@/data/mock/leads";
import { resultInsights, resultStats } from "@/data/mock/results";
import {
  ApiCustomerDetailResponse,
  ApiCustomerListResponse,
  ApiLeadDetailResponse,
  ApiLeadListResponse,
  ApiResultInsightsResponse,
  ApiDashboardSummary,
  mapDashboardSummaryToStats,
  ApiResultSummaryResponse,
  ApiTimelineResponse,
  mapApiCustomerDetailToProfile,
  mapApiCustomerToCustomer,
  mapApiLeadDetailToLeadDetail,
  mapApiLeadToLead,
  mapApiTimelineToTimeline,
  mapResultSummaryToStats,
} from "@/services/profitRadarMappers";

export type HomeDashboardData = {
  stats: StatItem[];
  tasks: Task[];
  priorityLeads: Lead[];
  risks: string[];
};

export type ReplyDashboardData = {
  stats: StatItem[];
  leads: Lead[];
};

export type CustomersDashboardData = {
  stats: StatItem[];
  customers: Customer[];
};

export type CustomerDetailData = {
  profile: CustomerProfile;
  stats: StatItem[];
  leads: Lead[];
  timeline: Timeline[];
};

export type LeadDetailData = {
  detail: LeadDetail;
  stats: StatItem[];
  timeline: Timeline[];
};

export type ResultsDashboardData = {
  stats: StatItem[];
  insights: string[];
};

async function getDashboardStats(fallbackStats: StatItem[]): Promise<StatItem[]> {
  try {
    const response = await apiGet<ApiResultSummaryResponse>("/results/summary");
    const apiStats = mapResultSummaryToStats(response);

    return apiStats.length > 0 ? apiStats : fallbackStats;
  } catch {
    return fallbackStats;
  }
}

export async function getHomeDashboard(): Promise<HomeDashboardData> {
  try {
    const summary = await apiGet<ApiDashboardSummary>("/dashboard/summary");

    return {
      stats: mapDashboardSummaryToStats(summary),
      tasks: [],
      priorityLeads: [],
      risks: [],
    };
  } catch {
    return {
      stats: homeStats,
      tasks: homeTasks,
      priorityLeads: homePriorityLeads,
      risks: homeRisks,
    };
  }
}

export async function getReplyDashboard(): Promise<ReplyDashboardData> {
  try {
    const [leadsResponse, apiStats] = await Promise.all([
      apiGet<ApiLeadListResponse>("/leads"),
      getDashboardStats(homeStats),
    ]);

    const apiLeads = leadsResponse.items.map(mapApiLeadToLead);

    return {
      stats: apiStats.length > 0 ? apiStats : replyStats,
      leads: apiLeads.length > 0 ? apiLeads : replyLeads,
    };
  } catch {
    return {
      stats: replyStats,
      leads: replyLeads,
    };
  }
}

export async function getCustomersDashboard(): Promise<CustomersDashboardData> {
  try {
    const [customersResponse, apiStats] = await Promise.all([
      apiGet<ApiCustomerListResponse>("/customers"),
      getDashboardStats(customerStats),
    ]);

    const apiCustomers = customersResponse.items.map(mapApiCustomerToCustomer);

    return {
      stats: apiStats.length > 0 ? apiStats : customerStats,
      customers: apiCustomers.length > 0 ? apiCustomers : customers,
    };
  } catch {
    return {
      stats: customerStats,
      customers,
    };
  }
}

export async function getCustomerDetail(customerId = 1): Promise<CustomerDetailData> {
  try {
    const [profileResponse, leadsResponse, timelineResponse, apiStats] = await Promise.all([
      apiGet<ApiCustomerDetailResponse>(`/customers/${customerId}`),
      apiGet<ApiLeadListResponse>(`/customers/${customerId}/leads`),
      apiGet<ApiTimelineResponse>(`/customers/${customerId}/timeline`),
      getDashboardStats(customerDetailStats),
    ]);

    const apiLeads = leadsResponse.items.map(mapApiLeadToLead);
    const apiTimeline = timelineResponse.items.map(mapApiTimelineToTimeline);

    return {
      profile: mapApiCustomerDetailToProfile(profileResponse),
      stats: apiStats.length > 0 ? apiStats : customerDetailStats,
      leads: apiLeads.length > 0 ? apiLeads : customerDetailLeads,
      timeline: apiTimeline.length > 0 ? apiTimeline : customerTimeline,
    };
  } catch {
    return {
      profile: {
        id: 1,
        name: "株式会社サンプル",
        contact: "佐藤様",
        email: "sample@example.com",
        status: "商談中",
        nextAction: "本日中に再フォロー",
      },
      stats: customerDetailStats,
      leads: customerDetailLeads,
      timeline: customerTimeline,
    };
  }
}

export async function getLeadDetail(leadId = 1): Promise<LeadDetailData> {
  try {
    const [detailResponse, timelineResponse, apiStats] = await Promise.all([
      apiGet<ApiLeadDetailResponse>(`/leads/${leadId}`),
      apiGet<ApiTimelineResponse>(`/leads/${leadId}/timeline`),
      getDashboardStats(leadDetailStats),
    ]);

    const apiTimeline = timelineResponse.items.map(mapApiTimelineToTimeline);

    return {
      detail: mapApiLeadDetailToLeadDetail(detailResponse),
      stats: apiStats.length > 0 ? apiStats : leadDetailStats,
      timeline: apiTimeline.length > 0 ? apiTimeline : leadTimeline,
    };
  } catch {
    return {
      detail: {
        id: 1,
        customer: "株式会社サンプル",
        subject: "見積のご確認について",
        priority: "高",
        category: "見積",
        status: "waiting_reply",
        estimatedProfit: "¥120,000",
        recoverableProfit: "¥100,000",
        delayDays: 3,
        nextAction: "本日中に確認フォロー",
        body: "お世話になっております。先日いただいた見積内容について確認させてください。条件面を再度確認したうえで、進行可否をご連絡いたします。",
      },
      stats: leadDetailStats,
      timeline: leadTimeline,
    };
  }
}

export async function getResultsDashboard(): Promise<ResultsDashboardData> {
  try {
    const [stats, insightsResponse] = await Promise.all([
      getDashboardStats(resultStats),
      apiGet<ApiResultInsightsResponse>("/results/insights"),
    ]);

    return {
      stats,
      insights: insightsResponse.items.length > 0 ? insightsResponse.items : resultInsights,
    };
  } catch {
    return {
      stats: resultStats,
      insights: resultInsights,
    };
  }
}
