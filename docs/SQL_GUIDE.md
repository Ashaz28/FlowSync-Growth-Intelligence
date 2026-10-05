# FlowSync SQL Guide — Business First

## Why SQL is in this project
You are not using SQL to present yourself as a database engineer. SQL is the tool used to combine customer, product, subscription, and support data so management questions can be answered with evidence.

## What you should be able to explain in an interview
You should understand these ideas rather than memorize every line of syntax:

1. **JOIN** — connects tables using identifiers such as `account_id`.
2. **GROUP BY** — summarizes many rows into business-level metrics such as accounts by channel or MRR by plan.
3. **CASE WHEN** — turns business rules into flags, such as whether a customer activated.
4. **CTE (`WITH`)** — breaks a larger analysis into understandable steps.
5. **Window function** — used sparingly when we need the latest subscription or comparisons across groups.

## Definitions used in the project
- **Dataset snapshot:** 31 Aug 2026.
- **Activation:** an account achieves at least one successful workflow. For time-bound onboarding analysis, activation means a successful workflow within 7 days.
- **Early integration:** first integration connected within 72 hours of signup.
- **Paid conversion:** account has at least one non-Trial subscription.
- **Current MRR:** sum of `monthly_price` for subscription rows marked `Active` at the dataset snapshot.
- **Churned paid account:** a paid subscription history contains a row marked `Cancelled`.

## How to talk about Query 3
Do not say: “Integrations cause activation.”
Say: “Accounts connecting an integration within the first 72 hours showed a higher activation rate. I treated that as an association and used the onboarding experiment to test whether changing the onboarding experience could improve activation.”

That distinction makes the analysis much more credible.

## Recommended learning order
1. Run the row-count query.
2. Understand the onboarding funnel.
3. Learn the early-integration query line by line.
4. Compare acquisition channels.
5. Understand MRR calculation.
6. Compare early team adoption with churn (using users added in the first 30 days).
7. Prioritize support issues using revenue exposure.
8. Evaluate the onboarding experiment.

You do not need advanced SQL before moving to Power BI. The goal is to understand why each query exists and what decision it supports.
