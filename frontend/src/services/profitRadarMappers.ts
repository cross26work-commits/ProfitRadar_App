import type { Customer, CustomerProfile, Lead, LeadDetail, StatItem, Timeline } from "@/types/profit-radar";

export type ApiLeadItem = {
  id: string | number;
  customer: string;
  subject: string;
  priority: string;
  status: string;
  estimated_profit: number;
  recoverable_profit: number;
  delay_days: number;
  href?: string | null;
};

export type ApiLeadListResponse = {
  items: ApiLeadItem[];
  message: string;
};

export type ApiCustomerItem = {
  id: string | number;
  name: string;
  leads: number;
  profit: number;
  last: string;
  href?: string | null;
};

export type ApiCustomerListResponse = {
  items: ApiCustomerItem[];
  message: string;
};

export type ApiResultSummaryResponse = {
  actual_profit: number;
  estimated_profit: number;
  action_count: number;
  recovery_rate: number;
  message: string;
};

export function formatYen(value: number): string {
  return `¥${value.toLocaleString("ja-JP")}`;
}

export function mapPriority(priority: string): string {
  if (priority === "high") return "高";
  if (priority === "medium") return "中";
  if (priority === "low") return "低";
  return priority;
}

export function mapApiLeadToLead(item: ApiLeadItem, index: number): Lead {
  return {
    id: String(item.id),
    href: item.href ?? `/leads/${item.id}`,
    rank: index + 1,
    customer: item.customer,
    subject: item.subject,
    profit: formatYen(item.estimated_profit),
    priority: mapPriority(item.priority),
    delay: `${item.delay_days}日放置`,
  };
}

export function mapApiCustomerToCustomer(item: ApiCustomerItem): Customer {
  return {
    id: item.id,
    href: item.href ?? `/customers/${item.id}`,
    name: item.name,
    leads: item.leads,
    profit: formatYen(item.profit),
    last: item.last,
  };
}

export function mapResultSummaryToStats(summary: ApiResultSummaryResponse): StatItem[] {
  return [
    {
      label: "今月実回収",
      value: formatYen(summary.actual_profit),
      sub: "記録済みデータから集計",
    },
    {
      label: "受注見込額",
      value: formatYen(summary.estimated_profit),
      sub: "原価未入力のため利益とは区別",
    },
    {
      label: "対応件数",
      value: `${summary.action_count}件`,
      sub: "今月累計",
    },
    {
      label: "回収率",
      value: `${summary.recovery_rate}%`,
      sub: "実回収 / 見込",
    },
  ];
}


export type ApiCustomerDetailResponse = {
  id: string | number;
  name: string;
  contact: string;
  email: string;
  status: string;
  next_action: string;
};

export type ApiTimelineItem = {
  type: string;
  title: string;
  body: string;
  time: string;
};

export type ApiTimelineResponse = {
  items: ApiTimelineItem[];
};

export function mapApiCustomerDetailToProfile(item: ApiCustomerDetailResponse): CustomerProfile {
  return {
    id: item.id,
    name: item.name,
    contact: item.contact,
    email: item.email,
    status: item.status,
    nextAction: item.next_action,
  };
}

export function mapApiTimelineToTimeline(item: ApiTimelineItem): Timeline {
  return {
    type: item.type,
    title: item.title,
    body: item.body,
    time: item.time,
  };
}


export type ApiLeadDetailResponse = {
  id: string | number;
  customer: string;
  subject: string;
  priority: string;
  category: string;
  status: string;
  estimated_profit: number;
  recoverable_profit: number;
  delay_days: number;
  next_action: string;
  body: string;
};

export function mapApiLeadDetailToLeadDetail(item: ApiLeadDetailResponse): LeadDetail {
  return {
    id: item.id,
    customer: item.customer,
    subject: item.subject,
    priority: mapPriority(item.priority),
    category: item.category,
    status: item.status,
    estimatedProfit: formatYen(item.estimated_profit),
    recoverableProfit: formatYen(item.recoverable_profit),
    delayDays: item.delay_days,
    nextAction: item.next_action,
    body: item.body,
  };
}


export type ApiResultInsightsResponse = {
  items: string[];
  message: string;
};

/* ===========================
   Dashboard Summary
=========================== */

export type ApiDashboardSummary = {
  company_id: string;
  metrics: {
    estimated_profit: number;
    actual_profit: number;
    recoverable_profit: number;
    customer_count: number;
    open_event_count: number;
    hot_lead_count: number;
  };
  top_actions: unknown[];
  recent_timeline: unknown[];
};

export function mapDashboardSummaryToStats(
  summary: ApiDashboardSummary,
): StatItem[] {
  return [
    {
      label: "今日の利益",
      value: formatYen(summary.metrics.actual_profit),
      sub: "実利益",
    },
    {
      label: "見込利益",
      value: formatYen(summary.metrics.estimated_profit),
      sub: "AI分析",
    },
    {
      label: "回収可能",
      value: formatYen(summary.metrics.recoverable_profit),
      sub: "未回収",
    },
    {
      label: "顧客",
      value: `${summary.metrics.customer_count}件`,
      sub: "管理中",
    },
  ];
}


export type ApiSalesForecastResponse = {
  company_id: string;
  actual_profit: number;
  estimated_profit: number;
  open_profit: number;
  closed_profit: number;
  hot_open_profit: number;
  forecast: {
    conservative: number;
    standard: number;
    aggressive: number;
  };
  message: string;
};


export type ApiSelfEvaluationSummaryResponse = {
  company_id: string;
  count: number;
  success_count: number;
  avg_accuracy: number;
  message: string;
};
