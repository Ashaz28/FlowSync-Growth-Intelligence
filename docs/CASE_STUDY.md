# FlowSync | SaaS Growth Intelligence — completed portfolio case study

**Type:** Independent simulated product-analytics case study | **Data:** reproducible synthetic B2B SaaS (NOT an actual customer or employer dataset)  
**Role demonstrated:** Product / Business Analyst with practical AI prototype  
**Snapshot:** 31 August 2026 | **Data:** 3,000 accounts, 14,963 users, 289,792 product events

## 1. Situation / decision to support

FlowSync is a fictional workflow-automation SaaS business. Leadership wants to diagnose why trial activity does not reliably become engaged paying customers, whether revenue growth is sustainable, which product issues matter commercially and whether an AI feature is worth its operating cost. A useful answer must link customer actions, recurring revenue and feedback—not just show disconnected charts.

## 2. Approach

I modeled nine linked tables, computed account-level activation from **observable and chronological** product events, reconstructed month-end paid subscription snapshots, and created reporting marts for funnels, channels, MRR, retention, support issues, AI usage, a descriptive customer-health score and one randomized **simulation** of an onboarding experiment. I delivered an interactive three-section Streamlit dashboard and an optional LLM ticket-classification component with JSON validation and human-review safeguards.

## 3. Key findings (calculated from the synthetic scenario)

| Finding | Measured result | Business interpretation |
|---|---:|---|
| End-to-end onboarding | 1,306 of 3,000 accounts ever achieved the ordered signup-to-success milestone (43.5%) | Reaching first value is a meaningful onboarding bottleneck. |
| Workspace → integration | 2,855 created a workspace; 1,708 progressed to integration (59.8% of workspace creators) | Integration setup deserves a targeted usability investigation. |
| Seven-day activation | 28.0% of signed-up accounts | Time-to-first-value should be a core product KPI. |
| Channel quality | Referral: 54.7% paid conversion across 351 signups; Paid Social: 21.5% across 543 signups | Evaluate acquisition using downstream conversion, not just signup counts; **cost effectiveness cannot be assessed without spend data**. |
| Recurring revenue | ₹1.67 Cr closing MRR from 897 active paid accounts; latest NRR 96.0% | Total MRR can rise while existing-customer revenue retention is below 100%. |
| Ticket opportunity | Workflow Failure affects active accounts representing ₹122.8 L current MRR across 547 active accounts | Investigate common reliability failures because a wide paying population is exposed. |
| High-value niche issue | Salesforce Sync has 500 tickets, affects 150 active accounts with ₹50.1 L MRR, and has 36% higher *average affected-active-account MRR* than UI/Usability | Examine severity, revenue segment and recurrence before prioritizing even lower-volume issues. |
| Simulated onboarding test | Control 22.9% (88/385), variant 36.1% (155/429); absolute lift +13.3 pp (approx. 95% CI +7.1 to +19.5 pp) | The modelled scenario supports further exploration; this **is not a real-company experimental result**. |

**Revenue definitions:** Current MRR equals the value of active paid subscriptions at the 31-Aug-2026 snapshot. ARR is annualized MRR, not booked annual contract value. NRR compares recurring revenue for the preceding month's paying cohort, net of expansion, contraction and churn. Revenue *exposure* is distinct active account MRR touched by an issue theme: it is neither lost revenue nor evidence that the issue caused churn, and overlaps across categories.

## 4. Decisions recommended to fictional leadership

**Product:** Investigate friction in integration setup via usability sessions and a guided setup prototype. Pilot integration-first onboarding under a fresh pre-registered production A/B test; monitor activation, support contact rate and downstream paid conversion before rollout. This synthetic experiment is not proof of a real uplift.

**Growth:** Revisit Paid Social lead quality by source/segment and follow through to paid conversion. Do not call a channel profitable without spend/CAC and contribution-margin inputs.

**Customer Success and Product:** Review workflow-reliability issues for reach, while separately examining Salesforce Sync for its larger average MRR per affected active account. Revenue exposure identifies investigation priorities, not expected savings.

**AI Product:** Monitor AI Assistant adoption, task completion and cost per adopter as an initial unit-economics layer. The source's illustrative costs are not real bills; a business decision also needs incremental retention or revenue evidence and human-reviewed AI quality results.

## 5. Implementation and evidence

- **Reproducible data:** `scripts/generate_dataset.py`, `data/raw/`, seed 42. These represent designed scenarios, not observed market relationships.
- **Analysis:** Eight business-question PostgreSQL queries in `sql/01_core_analysis.sql`; tested Python marts in `analytics/build_marts.py`, plus independently inspectable `data/processed/` reporting outputs.
- **Dashboard:** `app.py` — live local Streamlit executive, product, customer/AI views. A read-only screenshot and portfolio landing page are provided for quick recruiter review.
- **AI:** `ai_voc.py` — optional live structured LLM classification with output safeguards. Current revenue-exposure charts use the synthetic dataset's ground-truth labels, **not unrun LLM output**. See `AI_EVALUATION.md` before claiming AI model performance.
- **Checks:** Automated source-join, chronological funnel, revenue reconciliation, exposure deduplication, experiment-denominator and AI-human-review tests.

## 6. Limitations / claims to avoid

The generator intentionally makes early integration, channel and support-risk relationships visible. Therefore the measured associations and simulated experiment are useful for demonstrating analytical method, but **not evidence of real business impact or market behavior**. The account health score is a rules-based prioritization heuristic, **not** a measured churn probability. No production integration, published website, real Power BI `.pbix`, LLM accuracy measurement, cost savings or actual customer uplift is included.

## 7. What I would do next in a real company

Validate the data dictionary and event instrumentation with Product/Engineering; review customer feedback with Support to establish better ground-truth labels; collect CAC and gross margin for financial analysis; conduct a real production pilot; use representative, manually annotated tickets to evaluate AI; and audit any automated decisions before expanding deployment.
