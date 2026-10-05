-- FlowSync: Core SQL Analysis
-- Goal: answer business questions, not demonstrate complicated SQL for its own sake.
-- Snapshot date: 2026-08-31

/* ---------------------------------------------------------
1) DATA CHECK: are all tables loaded as expected?
Business purpose: verify the dataset before drawing conclusions.
--------------------------------------------------------- */
SELECT 'accounts' AS table_name, COUNT(*) AS row_count FROM accounts
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL SELECT 'product_events', COUNT(*) FROM product_events
UNION ALL SELECT 'support_tickets', COUNT(*) FROM support_tickets
UNION ALL SELECT 'customer_feedback', COUNT(*) FROM customer_feedback
UNION ALL SELECT 'ai_usage', COUNT(*) FROM ai_usage
UNION ALL SELECT 'experiments', COUNT(*) FROM experiments
UNION ALL SELECT 'integrations', COUNT(*) FROM integrations
ORDER BY table_name;

/* ---------------------------------------------------------
2) ONBOARDING FUNNEL
Business question: where do new accounts drop before reaching value?
Activation definition for this project: at least one successful workflow.
--------------------------------------------------------- */
WITH first_steps AS (
    SELECT
        a.account_id,
        MIN(pe.event_timestamp) FILTER (WHERE pe.event_type = 'workspace_created') AS workspace_at,
        MIN(pe.event_timestamp) FILTER (WHERE pe.event_type = 'integration_connected') AS integration_at,
        MIN(pe.event_timestamp) FILTER (WHERE pe.event_type = 'workflow_created') AS workflow_created_at,
        MIN(pe.event_timestamp) FILTER (WHERE pe.event_type = 'workflow_success') AS workflow_success_at
    FROM accounts a
    LEFT JOIN product_events pe ON a.account_id = pe.account_id
    GROUP BY a.account_id
),
account_steps AS (
    SELECT
        account_id,
        1 AS signed_up,
        CASE WHEN workspace_at IS NOT NULL THEN 1 ELSE 0 END AS workspace_created,
        CASE WHEN workspace_at IS NOT NULL
                  AND integration_at >= workspace_at THEN 1 ELSE 0 END AS integration_connected,
        CASE WHEN workspace_at IS NOT NULL
                  AND integration_at >= workspace_at
                  AND workflow_created_at >= integration_at THEN 1 ELSE 0 END AS workflow_created,
        CASE WHEN workspace_at IS NOT NULL
                  AND integration_at >= workspace_at
                  AND workflow_created_at >= integration_at
                  AND workflow_success_at >= workflow_created_at THEN 1 ELSE 0 END AS activated
    FROM first_steps
)
SELECT
    COUNT(*) AS signups,
    SUM(workspace_created) AS workspace_created,
    SUM(integration_connected) AS integration_connected,
    SUM(workflow_created) AS workflow_created,
    SUM(activated) AS activated,
    ROUND(100.0 * SUM(activated) / COUNT(*), 1) AS overall_activation_rate_pct
FROM account_steps;

/* ---------------------------------------------------------
3) EARLY INTEGRATION VS ACTIVATION
Business question: is connecting an integration early associated with activation?
Early integration = within 72 hours of account signup.
Activation = successful workflow within first 7 days.
Important: this shows association, not proof of causation.
--------------------------------------------------------- */
WITH first_integration AS (
    SELECT account_id, MIN(event_timestamp) AS first_integration_at
    FROM product_events
    WHERE event_type = 'integration_connected'
    GROUP BY account_id
),
first_success AS (
    SELECT account_id, MIN(event_timestamp) AS first_success_at
    FROM product_events
    WHERE event_type = 'workflow_success'
    GROUP BY account_id
),
account_flags AS (
    SELECT
        a.account_id,
        a.signup_date,
        CASE
            WHEN fi.first_integration_at < a.signup_date::timestamp + INTERVAL '72 hours' THEN 'Early integration'
            ELSE 'No early integration'
        END AS integration_group,
        CASE
            WHEN fs.first_success_at < a.signup_date::timestamp + INTERVAL '7 days' THEN 1
            ELSE 0
        END AS activated_7d
    FROM accounts a
    LEFT JOIN first_integration fi ON a.account_id = fi.account_id
    LEFT JOIN first_success fs ON a.account_id = fs.account_id
)
SELECT
    integration_group,
    COUNT(*) AS accounts,
    SUM(activated_7d) AS activated_accounts,
    ROUND(100.0 * AVG(activated_7d), 1) AS activation_rate_pct
FROM account_flags
GROUP BY integration_group
ORDER BY activation_rate_pct DESC;

/* ---------------------------------------------------------
4) ACQUISITION CHANNEL QUALITY
Business question: which channels bring users who actually activate and pay?
Paid account = account with any non-Trial subscription row.
--------------------------------------------------------- */
WITH activation AS (
    SELECT
        a.account_id,
        MAX(CASE WHEN pe.event_type = 'workflow_success' THEN 1 ELSE 0 END) AS activated
    FROM accounts a
    LEFT JOIN product_events pe ON a.account_id = pe.account_id
    GROUP BY a.account_id
),
paid_accounts AS (
    SELECT account_id, 1 AS became_paid
    FROM subscriptions
    WHERE plan_name <> 'Trial'
    GROUP BY account_id
)
SELECT
    a.acquisition_channel,
    COUNT(*) AS signups,
    ROUND(100.0 * AVG(act.activated), 1) AS activation_rate_pct,
    ROUND(100.0 * AVG(COALESCE(pa.became_paid,0)), 1) AS paid_conversion_rate_pct
FROM accounts a
JOIN activation act ON a.account_id = act.account_id
LEFT JOIN paid_accounts pa ON a.account_id = pa.account_id
GROUP BY a.acquisition_channel
ORDER BY paid_conversion_rate_pct DESC;

/* ---------------------------------------------------------
5) CURRENT MRR BY PLAN
Business question: where does recurring revenue currently come from?
Current = active subscriptions in the dataset snapshot (2026-08-31).
--------------------------------------------------------- */
SELECT
    plan_name,
    COUNT(DISTINCT account_id) AS active_accounts,
    SUM(monthly_price) AS mrr,
    ROUND(100.0 * SUM(monthly_price) / SUM(SUM(monthly_price)) OVER (), 1) AS share_of_mrr_pct
FROM subscriptions
WHERE status = 'Active'
  AND plan_name <> 'Trial'
GROUP BY plan_name
ORDER BY mrr DESC;

/* ---------------------------------------------------------
6) EARLY TEAM ADOPTION VS CHURN
Business question: do accounts that adopt FlowSync with a broader team retain better?
Early team adoption = number of users added within 30 days of account signup.
We use early adoption instead of current active users to avoid measuring a churn outcome as a cause.
--------------------------------------------------------- */
WITH early_team AS (
    SELECT
        a.account_id,
        COUNT(u.user_id) FILTER (
            WHERE u.signup_date <= a.signup_date + INTERVAL '30 days'
        ) AS users_first_30d
    FROM accounts a
    LEFT JOIN users u ON a.account_id = u.account_id
    GROUP BY a.account_id
),
paid_accounts AS (
    SELECT DISTINCT account_id
    FROM subscriptions
    WHERE plan_name <> 'Trial'
),
churn AS (
    SELECT account_id,
           MAX(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS churned
    FROM subscriptions
    WHERE plan_name <> 'Trial'
    GROUP BY account_id
)
SELECT
    CASE
        WHEN et.users_first_30d >= 3 THEN '3+ users in first 30d'
        ELSE '1-2 users in first 30d'
    END AS adoption_group,
    COUNT(*) AS paid_accounts,
    ROUND(100.0 * AVG(COALESCE(c.churned,0)), 1) AS churn_rate_pct
FROM early_team et
JOIN paid_accounts pa ON et.account_id = pa.account_id
LEFT JOIN churn c ON et.account_id = c.account_id
GROUP BY adoption_group
ORDER BY churn_rate_pct;

/* ---------------------------------------------------------
7) SUPPORT PROBLEMS BY REVENUE EXPOSURE
Business question: which issues touch the most current recurring revenue?
Deduplicate account/category so repeat tickets do not multiply the same MRR.
Exposure is NOT revenue lost, saved or causally attributable to the issue.
--------------------------------------------------------- */
WITH active_paid AS (
    SELECT account_id, monthly_price
    FROM subscriptions
    WHERE status = 'Active' AND plan_name <> 'Trial'
),
issue_accounts AS (
    SELECT DISTINCT issue_category, account_id
    FROM support_tickets
),
issue_exposure AS (
    SELECT ia.issue_category,
           SUM(COALESCE(ap.monthly_price,0)) AS active_mrr_exposure,
           COUNT(*) FILTER (WHERE ap.account_id IS NOT NULL) AS active_affected_accounts
    FROM issue_accounts ia
    LEFT JOIN active_paid ap ON ia.account_id = ap.account_id
    GROUP BY ia.issue_category
),
issue_counts AS (
    SELECT issue_category,
           COUNT(*) AS tickets,
           COUNT(DISTINCT account_id) AS affected_accounts
    FROM support_tickets
    GROUP BY issue_category
)
SELECT c.issue_category, c.tickets, c.affected_accounts,
       e.active_affected_accounts, e.active_mrr_exposure,
       ROUND(e.active_mrr_exposure / NULLIF(e.active_affected_accounts,0),0) AS avg_exposure_per_active_account
FROM issue_counts c
JOIN issue_exposure e USING (issue_category)
ORDER BY e.active_mrr_exposure DESC;

/* ---------------------------------------------------------
8) ONBOARDING A/B TEST
Business question: did integration-first onboarding improve activation?
Activation measured within 7 days of experiment assignment.
This query gives the observed lift; statistical significance comes next.
--------------------------------------------------------- */
WITH experiment_users AS (
    SELECT
        e.user_id,
        e.variant,
        e.assignment_date,
        u.account_id
    FROM experiments e
    JOIN users u ON e.user_id = u.user_id
    WHERE e.experiment_name = 'integration_first_onboarding'
),
results AS (
    SELECT
        eu.user_id,
        eu.variant,
        MAX(CASE
            WHEN pe.event_type = 'workflow_success'
             AND pe.event_timestamp >= eu.assignment_date::timestamp
             AND pe.event_timestamp < eu.assignment_date::timestamp + INTERVAL '7 days'
            THEN 1 ELSE 0 END
        ) AS activated_7d
    FROM experiment_users eu
    LEFT JOIN product_events pe ON eu.account_id = pe.account_id
    GROUP BY eu.user_id, eu.variant
)
SELECT
    variant,
    COUNT(*) AS users,
    SUM(activated_7d) AS activated_users,
    ROUND(100.0 * AVG(activated_7d), 1) AS activation_rate_pct
FROM results
GROUP BY variant
ORDER BY variant;
