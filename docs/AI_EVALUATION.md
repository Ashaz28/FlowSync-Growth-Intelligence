# Voice-of-Customer AI: design, evaluation and safeguards

**Business use case.** Convert unstructured support tickets into reviewable themes, sentiment, severity and *tentative* root-cause hypotheses. Connect those themes with active customer MRR to prioritize investigation rather than counting requests alone.

**Current implemented scope.** `ai_voc.py` contains a working optional OpenAI API call, JSON request, output validation and deterministic human-review rules. The Streamlit demo lets an operator provide a key and test synthetic ticket text. The aggregate issue charts use the dataset's **pre-existing synthetic issue labels**, not classifications produced by the LLM; do not confuse them.

**Input → process → output.** Synthetic, PII-free ticket text → LLM returns structured JSON → category validation/guardrail check → human review for high severity, unknown themes or self-reported confidence below 0.75 → attach approved labels to customer/account data for prioritization. Confidence is self-reported by the model, **not calibrated**; use it only as a coarse review flag, not an accuracy guarantee.

**Before claiming model performance**, create a labeled holdout of 50–100 paraphrased, human-reviewed examples (not templates duplicated from our generator). Evaluate theme accuracy, macro F1, root-cause unsupported-claim rate, severity agreement and high-severity false negatives; manually inspect every false negative. Compare with a simple rule-based baseline. The live LLM has **not** been run or validated as part of this packaged demo: no accuracy, savings or successful-deployment claim is made.

**Risks and mitigations.** Synthetic templated text is easier than messy real support data; LLMs can hallucinate a root cause; category taxonomy can drift; customer text may contain prompt injection/PII; revenue exposure is not revenue saved. The prompt treats ticket text as untrusted data and validates returned categories, but production would additionally need consent, PII redaction, rate limits, audit logs, monitoring, and a written retention policy.

**Decision boundary.** AI produces a suggestion. A Product/Support owner validates the classification and investigates the issue. It never cancels subscriptions, edits invoices, prioritizes a roadmap unilaterally or sends customer messages automatically.
