-- FlowSync SaaS Growth Intelligence
-- PostgreSQL schema
-- Dataset snapshot date: 2026-08-31

DROP TABLE IF EXISTS experiments CASCADE;
DROP TABLE IF EXISTS ai_usage CASCADE;
DROP TABLE IF EXISTS customer_feedback CASCADE;
DROP TABLE IF EXISTS support_tickets CASCADE;
DROP TABLE IF EXISTS product_events CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS integrations CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

CREATE TABLE accounts (
    account_id VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(120),
    industry VARCHAR(80),
    company_size VARCHAR(30),
    country VARCHAR(60),
    acquisition_channel VARCHAR(50),
    signup_date DATE,
    account_segment VARCHAR(30)
);

CREATE TABLE users (
    user_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    user_role VARCHAR(30),
    signup_date DATE,
    last_active_date DATE,
    is_active INTEGER CHECK (is_active IN (0,1))
);

CREATE TABLE subscriptions (
    subscription_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    plan_name VARCHAR(30),
    monthly_price NUMERIC(12,2),
    subscription_start_date DATE,
    subscription_end_date DATE,
    status VARCHAR(30),
    previous_plan VARCHAR(30),
    billing_cycle VARCHAR(30)
);

CREATE TABLE integrations (
    integration_id VARCHAR(20) PRIMARY KEY,
    integration_name VARCHAR(60) UNIQUE,
    integration_category VARCHAR(50),
    plan_availability VARCHAR(40)
);

CREATE TABLE product_events (
    event_id VARCHAR(25) PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(user_id),
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    event_timestamp TIMESTAMP,
    event_type VARCHAR(50),
    feature_name VARCHAR(80),
    integration_name VARCHAR(60),
    success_flag INTEGER
);

CREATE TABLE support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    created_at DATE,
    resolved_at DATE,
    ticket_text TEXT,
    issue_category VARCHAR(80),
    product_area VARCHAR(80),
    priority VARCHAR(20),
    status VARCHAR(30),
    resolution_hours NUMERIC(10,2)
);

CREATE TABLE customer_feedback (
    feedback_id VARCHAR(20) PRIMARY KEY,
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    feedback_date DATE,
    feedback_type VARCHAR(40),
    score NUMERIC(6,2),
    feedback_text TEXT
);

CREATE TABLE ai_usage (
    usage_id VARCHAR(25) PRIMARY KEY,
    account_id VARCHAR(20) REFERENCES accounts(account_id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    usage_date DATE,
    requests INTEGER,
    successful_requests INTEGER,
    failed_requests INTEGER,
    tokens_used BIGINT,
    estimated_cost NUMERIC(12,2)
);

CREATE TABLE experiments (
    experiment_id VARCHAR(20) PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(user_id),
    experiment_name VARCHAR(80),
    variant VARCHAR(30),
    assignment_date DATE
);

-- Helpful indexes for analysis
CREATE INDEX idx_users_account ON users(account_id);
CREATE INDEX idx_subscriptions_account ON subscriptions(account_id);
CREATE INDEX idx_events_account_time ON product_events(account_id, event_timestamp);
CREATE INDEX idx_events_type ON product_events(event_type);
CREATE INDEX idx_support_account ON support_tickets(account_id);
CREATE INDEX idx_ai_account ON ai_usage(account_id);
