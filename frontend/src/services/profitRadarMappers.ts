import type { Customer, CustomerProfile, Lead, LeadDetail, StatItem, Timeline } from "@/types/profit-radar";

export type ApiLeadItem = {
  id: number;
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
  id: number;
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
      sub: "API接続済み",
    },
    {
      label: "見込利益",
      value: formatYen(summary.estimated_profit),
      sub: "進行中案件",
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
  id: number;
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
  id: number;
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
