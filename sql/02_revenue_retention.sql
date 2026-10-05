-- Optional follow-up queries for SQL interview depth.
-- These match the dashboard's definitions as of each month end.
-- A paid subscription is in force if it begins on/before the snapshot and has not yet ended.
-- A cancellation effective ON month end is excluded from that month's closing MRR.
WITH months AS (
    SELECT (DATE_TRUNC('month', month_start) + INTERVAL '1 month - 1 day')::date AS month_end
    FROM GENERATE_SERIES(DATE '2025-09-01', DATE '2026-08-01', INTERVAL '1 month') AS t(month_start)
), paid_accounts AS (
    SELECT m.month_end, s.account_id, SUM(s.monthly_price) AS account_mrr
    FROM months m
    JOIN subscriptions s
      ON s.plan_name <> 'Trial'
     AND s.subscription_start_date <= m.month_end
     AND s.subscription_end_date >= m.month_end
     AND NOT (s.status = 'Cancelled' AND s.subscription_end_date = m.month_end)
    GROUP BY 1, 2
)
SELECT month_end, COUNT(*) AS active_paid_accounts, SUM(account_mrr) AS month_end_mrr
FROM paid_accounts
GROUP BY month_end
ORDER BY month_end;
-- Note: Python analytics/build_marts.py handles new/expansion/contraction/churn MRR
-- and reconciliation with clearer intermediate account-level snapshots.
