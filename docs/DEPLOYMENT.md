# Deploy the Streamlit dashboard

The project already runs locally. Deployment is optional but useful because a recruiter can open a live link without installing anything.

## Streamlit Community Cloud

1. Push the repository to GitHub first.
2. Sign in to Streamlit Community Cloud using GitHub.
3. Create a new app and select the repository `flowsync-saas-growth-intelligence`.
4. Set the main file path to `app.py`.
5. Deploy. The dashboard itself does **not** require an API key.
6. Open the public URL and verify all three dashboard sections load.

## Optional AI Voice-of-Customer demo

The live AI classifier is intentionally separated from the core dashboard. If you want to demo it publicly, add `OPENAI_API_KEY` through the deployment platform's private secrets/settings rather than committing it to GitHub. Never add the key to `.env`, README screenshots, code, or repository history.

Before saying the AI feature is personally tested, run one or more synthetic ticket examples and confirm the structured fields and human-review flag behave as expected.

## Resume rule

A local dashboard + GitHub repository is already a valid portfolio project. A public deployment is an enhancement, not a requirement. Only add a live-demo URL to your resume after opening it yourself and confirming it works.
