# FlowSync SaaS Growth Intelligence — Synthetic Dataset

## Purpose
This is a realistic synthetic B2B SaaS dataset designed for a Product / Business / Growth Analytics portfolio project. It is intentionally business-first: the data contains a few controlled behavioural relationships that can be discovered and quantified with SQL, dashboards, and basic statistics.

**Data period:** 2025-09-01 to 2026-08-31  
**Random seed:** 42  
**Accounts:** 3,000  
**Users:** 14,963  
**Product events:** 289,792  
**Support tickets:** 4,790  
**Customer feedback rows:** 2,417  

## Business scenario
FlowSync is a fictional B2B workflow-automation SaaS company. Signups are growing, but management wants to understand why activation, retention, and recurring revenue are not improving at the same pace. The company also wants to know whether its AI Workflow Assistant creates enough product value to justify its cost.

## Controlled business patterns
The generator encodes *probability differences*, not final answers:

1. Accounts connecting an integration within 72 hours have a higher probability of activation and conversion.
2. Multi-user accounts tend to retain better than single-user accounts.
3. Paid Social produces many signups but lower-quality activation/conversion than Referral or Partner channels.
4. Business/Enterprise accounts are more likely to depend on Salesforce. Salesforce issues therefore affect fewer accounts but disproportionately high MRR.
5. Usage declines before churn for many churned accounts.
6. Support-risk accounts experience more tickets and slower resolution.
7. AI Workflow Assistant adoption is higher in Growth/Business/Enterprise plans. Heavy AI users create higher model cost.
8. The integration-first onboarding experiment modestly increases early integration and therefore activation.

These patterns should be *measured later through analysis*. Do not quote a number on a resume until your SQL/analysis actually calculates it.

## Quick generation sanity checks
- Activated accounts (latent generator state): 1,306
- Early-integration accounts (latent generator state): 1,160
- Converted paid accounts: 1,097
- Churned paid accounts: 200
- AI-adopting paid accounts: 480
- Experiment assignments: {'Control': 385, 'Variant': 429}

The latent states above are only generator diagnostics and are intentionally **not columns in `accounts.csv`**. In the project, you should derive activation, churn, engagement, and similar concepts from observable tables.

## Tables
- `accounts.csv` — account/company attributes
- `users.csv` — users belonging to accounts
- `subscriptions.csv` — trial and paid subscription periods; can contain multiple paid periods when a plan changes
- `product_events.csv` — event-level product activity used for funnels, retention, feature adoption, and engagement
- `support_tickets.csv` — structured ticket metadata plus unstructured text for the later Voice-of-Customer AI step
- `customer_feedback.csv` — NPS, cancellation comments, and feature requests
- `ai_usage.csv` — monthly-ish AI usage observations; `estimated_cost` is a **fictional blended internal cost in INR**
- `experiments.csv` — onboarding experiment assignment for eligible new users
- `integrations.csv` — integration reference table

## Recommended first SQL questions
1. What is the signup → workspace → integration → workflow → success activation funnel?
2. Does connecting an integration within 72 hours relate to higher activation?
3. Which acquisition channels bring high volume but weak conversion?
4. How does retention differ for single-user vs multi-user accounts?
5. What are monthly MRR movements and churn?
6. Which support issue categories affect the most MRR?
7. Does Salesforce reliability affect high-value accounts disproportionately?
8. How do AI adopters differ from non-adopters on engagement/retention?
9. What is the AI cost per account and which cohort drives the highest cost?
10. Did the integration-first onboarding variant improve activation?

## Interview framing
A good explanation is:

> I created a realistic synthetic SaaS dataset instead of using an overused churn CSV. I encoded a few business assumptions as probability differences — for example, early integration should improve activation — and then treated those assumptions as hypotheses. The actual metrics and conclusions are derived later through SQL and analysis rather than hard-coded into the resume story.
