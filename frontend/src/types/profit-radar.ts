export type StatItem = {
  label: string;
  value: string;
  sub: string;
  tone?: string;
};

export type Lead = {
  href?: string;
  rank: number;
  customer: string;
  subject: string;
  profit: string;
  priority: string;
  delay: string;
};

export type Customer = {
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
};


export type CustomerProfile = {
  id: number;
  name: string;
  contact: string;
  email: string;
  status: string;
  nextAction: string;
};


export type LeadDetail = {
  id: number;
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
