-- Profit Radar Core Schema
-- Phase4: PostgreSQL real data foundation

create extension if not exists "uuid-ossp";

-- companies
create table if not exists companies (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    plan text default 'free',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- profiles
create table if not exists profiles (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null unique,
    company_id uuid not null references companies(id) on delete cascade,
    email text not null,
    full_name text,
    role text not null default 'member',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- customers
create table if not exists customers (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    name text not null,
    email text,
    phone text,
    company_name text,
    status text not null default 'active',
    total_estimated_profit bigint not null default 0,
    total_actual_profit bigint not null default 0,
    last_contact_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_customers_company_id on customers(company_id);

-- messages
create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    channel text not null default 'gmail',
    direction text not null,
    sender text,
    recipient text,
    subject text,
    body text,
    external_id text,
    thread_id text,
    sent_at timestamptz,
    received_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_messages_company_id on messages(company_id);
create index if not exists idx_messages_customer_id on messages(customer_id);
create index if not exists idx_messages_thread_id on messages(thread_id);

-- profit_events
create table if not exists profit_events (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    source_message_id uuid references messages(id) on delete set null,
    title text not null,
    status text not null default 'open',
    category text,
    estimated_profit bigint not null default 0,
    actual_profit bigint not null default 0,
    opportunity_score integer not null default 0,
    roi_score integer not null default 0,
    hot_lead boolean not null default false,
    risk_level text not null default 'medium',
    next_action text,
    due_at timestamptz,
    closed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_profit_events_company_id on profit_events(company_id);
create index if not exists idx_profit_events_customer_id on profit_events(customer_id);
create index if not exists idx_profit_events_status on profit_events(status);

-- timeline
create table if not exists timeline (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    profit_event_id uuid references profit_events(id) on delete set null,
    event_type text not null,
    channel text,
    title text not null,
    description text,
    amount bigint default 0,
    occurred_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_timeline_company_id on timeline(company_id);
create index if not exists idx_timeline_customer_id on timeline(customer_id);
create index if not exists idx_timeline_profit_event_id on timeline(profit_event_id);

-- reply_logs
create table if not exists reply_logs (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    profit_event_id uuid references profit_events(id) on delete set null,
    message_id uuid references messages(id) on delete set null,
    channel text not null default 'gmail',
    reply_body text,
    reply_at timestamptz,
    detected_at timestamptz not null default now(),
    external_id text,
    thread_id text,
    created_at timestamptz not null default now()
);

create index if not exists idx_reply_logs_company_id on reply_logs(company_id);
create index if not exists idx_reply_logs_thread_id on reply_logs(thread_id);

-- ai_judgements
create table if not exists ai_judgements (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    profit_event_id uuid references profit_events(id) on delete set null,
    provider text not null default 'rule_based',
    score integer not null default 0,
    priority text not null default 'medium',
    risk text,
    reason text,
    next_action text,
    raw_input jsonb not null default '{}'::jsonb,
    raw_output jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_ai_judgements_company_id on ai_judgements(company_id);
create index if not exists idx_ai_judgements_profit_event_id on ai_judgements(profit_event_id);

-- learning_logs
create table if not exists learning_logs (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    profit_event_id uuid references profit_events(id) on delete set null,
    event_type text not null,
    input_data jsonb not null default '{}'::jsonb,
    result_data jsonb not null default '{}'::jsonb,
    success boolean,
    actual_profit bigint default 0,
    created_at timestamptz not null default now()
);

create index if not exists idx_learning_logs_company_id on learning_logs(company_id);
create index if not exists idx_learning_logs_event_type on learning_logs(event_type);

-- calendar_events
create table if not exists calendar_events (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    customer_id uuid references customers(id) on delete set null,
    profit_event_id uuid references profit_events(id) on delete set null,
    provider text not null default 'google_calendar',
    title text not null,
    description text,
    meeting_url text,
    external_id text,
    starts_at timestamptz,
    ends_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_calendar_events_company_id on calendar_events(company_id);

-- gmail_connections
create table if not exists gmail_connections (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid not null references companies(id) on delete cascade,
    profile_id uuid references profiles(id) on delete cascade,
    email text not null,
    token_json jsonb not null default '{}'::jsonb,
    status text not null default 'connected',
    last_synced_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_gmail_connections_company_id on gmail_connections(company_id);
