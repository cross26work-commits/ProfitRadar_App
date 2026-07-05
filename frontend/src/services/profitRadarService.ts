import type { Customer, CustomerProfile, Lead, LeadDetail, StatItem, Task, Timeline } from "@/types/profit-radar";
import { apiGet } from "@/lib/api";
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
  ApiSalesForecastResponse,
  ApiSelfEvaluationSummaryResponse,
  ApiResultSummaryResponse,
  ApiTimelineResponse,
  mapApiCustomerDetailToProfile,
  mapApiCustomerToCustomer,
  mapApiLeadDetailToLeadDetail,
  mapApiLeadToLead,
  mapApiTimelineToTimeline,
  mapResultSummaryToStats,
} from "@/services/profitRadarMappers";


type ApiDashboardHomeAction = {
  event_id: string;
  customer_id: string | null;
  company_id: string;
  title: string;
  customer_name: string;
  estimated_profit: number;
  recoverable_profit: number;
  risk_level: string;
  category: string;
  priority_score: number;
  reason: string;
  next_action: string;
  latest_timeline?: unknown;
  created_at: string;
};

type ApiDashboardHomeResponse = {
  company_id: string;
  summary: {
    top_action_count: number;
    total_estimated_profit: number;
    total_recoverable_profit: number;
    high_risk_count: number;
  };
  ai_message: string;
  top_actions: ApiDashboardHomeAction[];
  reply_queue: ApiDashboardHomeAction[];
  risks: {
    event_id: string;
    title: string;
    customer_name: string;
    risk_level: string;
    reason: string;
    estimated_profit: number;
    next_action: string;
  }[];
  recent_timeline: unknown[];
};

function yen(value: number | null | undefined): string {
  return `¥${Number(value ?? 0).toLocaleString("ja-JP")}`;
}

function mapActionToTask(action: ApiDashboardHomeAction): Task {
  return {
    id: action.event_id,
    title: `${action.customer_name || "顧客未設定"}：${action.next_action || action.title}`,
    description: `${action.title} / 期待利益 ${yen(action.estimated_profit)} / 優先度 ${action.priority_score}`,
    href: "/reply",
  };
}

function mapActionToLead(action: ApiDashboardHomeAction, index = 0): Lead {
  return {
    id: action.event_id,
    href: `/leads/${action.event_id}`,
    rank: index + 1,
    customer: action.customer_name || "顧客未設定",
    subject: action.title,
    profit: yen(action.estimated_profit),
    priority: action.risk_level || "未判定",
    delay: action.next_action || "状況確認",
    category: action.category || "未分類",
    status: "未対応",
    estimatedProfit: yen(action.estimated_profit),
    recoverableProfit: yen(action.recoverable_profit),
    delayDays: 0,
    nextAction: action.next_action || "状況確認",
  };
}

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
  forecast: ApiSalesForecastResponse | null;
  selfEvaluation: ApiSelfEvaluationSummaryResponse | null;
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
    const home = await apiGet<ApiDashboardHomeResponse>("/dashboard/home");

    return {
      stats: [
        {
          label: "今日やる営業",
          value: `${home.summary.top_action_count}件`,
          helper: "AIが優先順位付け",
        },
        {
          label: "期待利益",
          value: yen(home.summary.total_estimated_profit),
          helper: "TOP案件の合計",
        },
        {
          label: "回収可能利益",
          value: yen(home.summary.total_recoverable_profit),
          helper: "回収候補",
        },
        {
          label: "危険案件",
          value: `${home.summary.high_risk_count}件`,
          helper: "優先確認対象",
        },
      ],
      tasks: home.top_actions.map(mapActionToTask),
      priorityLeads: home.reply_queue.map(mapActionToLead),
      risks: home.risks.map((risk) =>
        `${risk.customer_name || "顧客未設定"}：${risk.title} / ${risk.risk_level} / ${risk.next_action}`,
      ),
    };
  } catch (error) {
    console.error("getHomeDashboard API failed:", error);
    throw error;
  }
}

export async function getReplyDashboard(): Promise<ReplyDashboardData> {
  try {
    const home = await apiGet<ApiDashboardHomeResponse>("/dashboard/home");

    return {
      stats: [
        {
          label: "返信候補",
          value: `${home.reply_queue.length}件`,
          sub: "AI優先順位",
        },
        {
          label: "期待利益",
          value: yen(home.summary.total_estimated_profit),
          sub: "返信候補合計",
        },
        {
          label: "危険案件",
          value: `${home.summary.high_risk_count}件`,
          sub: "優先確認",
        },
      ],
      leads: home.reply_queue.map(mapActionToLead),
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

export async function getCustomerDetail(customerId: string | number = 1): Promise<CustomerDetailData> {
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

export async function getLeadDetail(leadId: string | number = 1): Promise<LeadDetailData> {
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
    const [stats, insightsResponse, forecast, selfEvaluation] = await Promise.all([
      getDashboardStats(resultStats),
      apiGet<ApiResultInsightsResponse>("/results/insights"),
      apiGet<ApiSalesForecastResponse>("/sales-forecast/summary"),
      apiGet<ApiSelfEvaluationSummaryResponse>("/self-evaluation/summary"),
    ]);

    return {
      stats,
      insights: insightsResponse.items.length > 0 ? insightsResponse.items : resultInsights,
      forecast,
      selfEvaluation,
    };
  } catch {
    return {
      stats: resultStats,
      insights: resultInsights,
      forecast: null,
      selfEvaluation: null,
    };
  }
}
