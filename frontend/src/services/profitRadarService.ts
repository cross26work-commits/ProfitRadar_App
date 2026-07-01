import type { Customer, Lead, StatItem, Task, Timeline } from "@/types/profit-radar";
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
  ApiCustomerListResponse,
  ApiLeadListResponse,
  ApiResultSummaryResponse,
  mapApiCustomerToCustomer,
  mapApiLeadToLead,
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

export async function getCustomerDetail(): Promise<CustomerDetailData> {
  return {
    stats: customerDetailStats,
    leads: customerDetailLeads,
    timeline: customerTimeline,
  };
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
