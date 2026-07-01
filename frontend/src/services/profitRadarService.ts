import type { Customer, CustomerProfile, Lead, StatItem, Task, Timeline } from "@/types/profit-radar";
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
  ApiLeadListResponse,
  ApiResultSummaryResponse,
  ApiTimelineResponse,
  mapApiCustomerDetailToProfile,
  mapApiCustomerToCustomer,
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
    const [leadsResponse, apiStats] = await Promise.all([
      apiGet<ApiLeadListResponse>("/leads"),
      getDashboardStats(homeStats),
    ]);

    const apiLeads = leadsResponse.items.map(mapApiLeadToLead);

    return {
      stats: apiStats.length > 0 ? apiStats : homeStats,
      tasks: homeTasks,
      priorityLeads: apiLeads.length > 0 ? apiLeads : homePriorityLeads,
      risks: homeRisks,
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

export async function getLeadDetail(): Promise<LeadDetailData> {
  return {
    stats: leadDetailStats,
    timeline: leadTimeline,
  };
}

export async function getResultsDashboard(): Promise<ResultsDashboardData> {
  try {
    return {
      stats: await getDashboardStats(resultStats),
      insights: resultInsights,
    };
  } catch {
    return {
      stats: resultStats,
      insights: resultInsights,
    };
  }
}
