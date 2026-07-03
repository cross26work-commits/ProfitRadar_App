export type StatItem = {
  label: string;
  value: string;
  sub?: string;
  helper?: string;
  tone?: string;
};

export type Lead = {
  id: string | number;
  href?: string;
  rank: number;
  customer: string;
  subject: string;
  profit: string;
  priority: string;
  delay: string;
  category?: string;
  status?: string;
  estimatedProfit?: string;
  recoverableProfit?: string;
  delayDays?: number;
  nextAction?: string;
};

export type Customer = {
  id?: string | number;
  href?: string;
  name: string;
  leads: number;
  profit: string;
  last: string;
};

export type Timeline = {
  type: string;
  title: string;
  body: string;
  time: string;
};

export type Task = {
  id?: string | number;
  title: string;
  description: string;
  href?: string;
};


export type CustomerProfile = {
  id: string | number;
  name: string;
  contact: string;
  email: string;
  status: string;
  nextAction: string;
};


export type LeadDetail = {
  id: string | number;
  customer: string;
  subject: string;
  priority: string;
  category: string;
  status: string;
  estimatedProfit: string;
  recoverableProfit: string;
  delayDays: number;
  nextAction: string;
  body: string;
};
