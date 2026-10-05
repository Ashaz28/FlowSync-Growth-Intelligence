from __future__ import annotations

import csv
import math
import random
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
rng = random.Random(SEED)

OUT_DIR = Path(__file__).resolve().parents[1] / 'data' / 'raw'
if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
OUT_DIR.mkdir(parents=True, exist_ok=True)

START = date(2025, 9, 1)
END = date(2026, 8, 31)
N_ACCOUNTS = 3000

PLAN_PRICE = {
    'Trial': 0,
    'Starter': 2999,
    'Growth': 9999,
    'Business': 24999,
    'Enterprise': 69999,
}

CHANNELS = ['Organic Search', 'Paid Search', 'Paid Social', 'Partner', 'Referral', 'Content']
CHANNEL_WEIGHTS = [0.24, 0.20, 0.18, 0.10, 0.12, 0.16]
CHANNEL_QUALITY = {
    'Organic Search': 0.03,
    'Paid Search': -0.02,
    'Paid Social': -0.10,
    'Partner': 0.07,
    'Referral': 0.10,
    'Content': 0.02,
}

INDUSTRIES = ['SaaS', 'E-commerce', 'Professional Services', 'Education', 'Healthcare', 'Manufacturing', 'FinTech']
COUNTRIES = ['India', 'United States', 'United Kingdom', 'Singapore', 'UAE', 'Australia']
SIZE_BANDS = ['1-10', '11-50', '51-200', '201-500', '501+']
SIZE_WEIGHTS = [0.28, 0.34, 0.22, 0.11, 0.05]

INTEGRATIONS = [
    ('INT_001', 'Salesforce', 'CRM', 'Business+'),
    ('INT_002', 'HubSpot', 'CRM', 'Growth+'),
    ('INT_003', 'Slack', 'Collaboration', 'Starter+'),
    ('INT_004', 'Google Sheets', 'Productivity', 'Starter+'),
    ('INT_005', 'Microsoft Teams', 'Collaboration', 'Growth+'),
    ('INT_006', 'Zendesk', 'Support', 'Business+'),
]

SUPPORT_TEMPLATES = {
    'Salesforce Sync': [
        'Salesforce records are not syncing and our workflow keeps failing.',
        'The Salesforce connector stopped updating opportunities after yesterday.',
        'Our CRM automation is delayed and Salesforce fields are not mapping correctly.',
        'Salesforce sync failures are blocking an important sales workflow.',
    ],
    'Workflow Failure': [
        'A workflow that used to run successfully is now failing without a clear reason.',
        'Our automation fails at the final step and we cannot identify the issue.',
        'Several workflow runs are failing intermittently this week.',
    ],
    'Billing': [
        'We were charged for a plan change and need clarification on the invoice.',
        'The billing page is confusing and we cannot reconcile this month’s charge.',
        'Please explain why our subscription amount changed this month.',
    ],
    'AI Assistant': [
        'The AI workflow assistant generated steps that did not match our request.',
        'AI suggestions are useful but the generated workflow needs too many edits.',
        'The AI assistant failed to create a valid workflow from our prompt.',
    ],
    'User Management': [
        'We are having trouble inviting new team members to the workspace.',
        'A team member cannot access the workspace even after being invited.',
        'User permissions are unclear for managers and members.',
    ],
    'UI / Usability': [
        'It takes too many clicks to find recent workflow runs.',
        'The dashboard is difficult to navigate when we have many workflows.',
        'We would like a simpler way to filter and search workflows.',
    ],
}

FEEDBACK_TEMPLATES = {
    'positive': [
        'Automation has saved our team time and the product is easy to use.',
        'Integrations work well and we have expanded usage across the team.',
        'The workflow builder is intuitive and has become part of our daily process.',
    ],
    'neutral': [
        'The product is useful but onboarding could explain integrations more clearly.',
        'We like the core workflows but some settings are difficult to discover.',
        'Good overall experience, although setup takes longer than expected.',
    ],
    'negative': [
        'We are seeing too many workflow failures and support has not resolved them quickly.',
        'The integration issues are making it hard to rely on the product.',
        'We expected faster setup and more reliable automation.',
    ],
    'salesforce': [
        'Salesforce sync is unreliable and it is affecting an important revenue workflow.',
        'We like the product but the Salesforce connector needs to be more stable.',
        'Salesforce integration reliability is the main reason we may reconsider renewal.',
    ],
    'ai': [
        'The AI workflow assistant is helpful but generated steps sometimes need manual correction.',
        'AI setup is fast, but we need more predictable output for complex workflows.',
        'The AI assistant saves time for simple automations and could improve for edge cases.',
    ],
}


def clamp(x, low=0.0, high=1.0):
    return max(low, min(high, x))


def rand_date(start: date, end: date) -> date:
    if end <= start:
        return start
    return start + timedelta(days=rng.randint(0, (end - start).days))


def iso(d):
    return d.isoformat() if d else ''


def size_to_segment(size_band: str) -> str:
    if size_band in ('1-10', '11-50'):
        return 'SMB'
    if size_band == '51-200':
        return 'Mid-Market'
    return 'Enterprise'


def base_plan(size_band: str) -> str:
    options = {
        '1-10': [('Starter', 0.82), ('Growth', 0.18)],
        '11-50': [('Starter', 0.42), ('Growth', 0.50), ('Business', 0.08)],
        '51-200': [('Growth', 0.46), ('Business', 0.48), ('Enterprise', 0.06)],
        '201-500': [('Business', 0.68), ('Enterprise', 0.32)],
        '501+': [('Business', 0.28), ('Enterprise', 0.72)],
    }
    roll = rng.random()
    cum = 0.0
    for p, w in options[size_band]:
        cum += w
        if roll <= cum:
            return p
    return options[size_band][-1][0]


def choose_integration(plan: str, enterprise_bias=False) -> str:
    if enterprise_bias:
        names = ['Salesforce', 'HubSpot', 'Slack', 'Google Sheets', 'Microsoft Teams', 'Zendesk']
        weights = [0.38, 0.18, 0.10, 0.08, 0.12, 0.14]
    elif plan == 'Starter':
        names = ['Slack', 'Google Sheets', 'HubSpot']
        weights = [0.38, 0.46, 0.16]
    elif plan == 'Growth':
        names = ['HubSpot', 'Slack', 'Google Sheets', 'Microsoft Teams', 'Salesforce']
        weights = [0.28, 0.22, 0.22, 0.14, 0.14]
    else:
        names = ['Salesforce', 'HubSpot', 'Slack', 'Google Sheets', 'Microsoft Teams', 'Zendesk']
        weights = [0.32, 0.18, 0.12, 0.08, 0.14, 0.16]
    return rng.choices(names, weights=weights, k=1)[0]


def daterange_months(start_d: date, end_d: date):
    y, m = start_d.year, start_d.month
    current = date(y, m, 1)
    end_m = date(end_d.year, end_d.month, 1)
    while current <= end_m:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def month_end(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1) - timedelta(days=1)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)


def write_csv(name, rows, fieldnames):
    path = OUT_DIR / name
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


# -------------------------
# 1) Account-level behavior
# -------------------------
accounts = []
account_state = {}
experiment_rows = []

for i in range(1, N_ACCOUNTS + 1):
    aid = f'ACC_{i:05d}'
    signup = rand_date(START, date(2026, 8, 10))
    size = rng.choices(SIZE_BANDS, weights=SIZE_WEIGHTS, k=1)[0]
    segment = size_to_segment(size)
    channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
    industry = rng.choice(INDUSTRIES)
    country = rng.choices(COUNTRIES, weights=[0.42, 0.20, 0.12, 0.08, 0.09, 0.09], k=1)[0]
    target_plan = base_plan(size)

    # The onboarding experiment runs May-Jul 2026 for new accounts.
    exp_variant = None
    if date(2026, 5, 1) <= signup <= date(2026, 7, 31):
        exp_variant = 'Variant' if rng.random() < 0.5 else 'Control'

    # Early integration is the key activation driver.
    early_integration_p = 0.34 + CHANNEL_QUALITY[channel]
    if target_plan in ('Business', 'Enterprise'):
        early_integration_p += 0.08
    if exp_variant == 'Variant':
        early_integration_p += 0.11
    early_integration = rng.random() < clamp(early_integration_p, 0.12, 0.75)

    # Expected team breadth before we generate users.
    multi_user_p = {'1-10': 0.34, '11-50': 0.56, '51-200': 0.72, '201-500': 0.82, '501+': 0.90}[size]
    multi_user = rng.random() < multi_user_p

    activation_p = 0.26 + (0.34 if early_integration else 0) + (0.08 if multi_user else 0) + CHANNEL_QUALITY[channel]
    if exp_variant == 'Variant':
        activation_p += 0.03  # Total experiment lift comes mostly through early integration.
    activated = rng.random() < clamp(activation_p, 0.08, 0.91)

    convert_p = 0.12 + (0.48 if activated else 0) + CHANNEL_QUALITY[channel]
    if target_plan in ('Business', 'Enterprise'):
        convert_p += 0.06
    converted = rng.random() < clamp(convert_p, 0.04, 0.86)

    # Some high-value accounts depend on Salesforce; this later creates a revenue-heavy pain point.
    salesforce_dependency_p = 0.06
    if target_plan == 'Growth':
        salesforce_dependency_p = 0.14
    elif target_plan == 'Business':
        salesforce_dependency_p = 0.34
    elif target_plan == 'Enterprise':
        salesforce_dependency_p = 0.48
    salesforce_dependency = converted and rng.random() < salesforce_dependency_p

    support_risk = rng.random() < (0.12 + (0.16 if salesforce_dependency else 0) + (0.08 if not early_integration else 0))

    churn_p = 0.11
    churn_p += 0.16 if not early_integration else -0.04
    churn_p += 0.10 if not multi_user else -0.05
    churn_p += 0.11 if support_risk else 0
    churn_p += -CHANNEL_QUALITY[channel] * 0.45
    churn_p += 0.04 if target_plan == 'Starter' else 0
    churned = converted and rng.random() < clamp(churn_p, 0.035, 0.52)

    trial_end = signup + timedelta(days=14)
    paid_start = trial_end if converted else None
    churn_date = None
    if churned and paid_start:
        min_churn = paid_start + timedelta(days=55)
        if min_churn <= END:
            churn_date = rand_date(min_churn, END)
        else:
            churned = False

    active_end = churn_date or END

    accounts.append({
        'account_id': aid,
        'company_name': f'FlowSync Customer {i:04d}',
        'industry': industry,
        'company_size': size,
        'country': country,
        'acquisition_channel': channel,
        'signup_date': iso(signup),
        'account_segment': segment,
    })

    account_state[aid] = {
        'signup': signup,
        'size': size,
        'segment': segment,
        'channel': channel,
        'industry': industry,
        'country': country,
        'target_plan': target_plan,
        'exp_variant': exp_variant,
        'early_integration': early_integration,
        'multi_user': multi_user,
        'activated': activated,
        'converted': converted,
        'salesforce_dependency': salesforce_dependency,
        'support_risk': support_risk,
        'churned': churned,
        'churn_date': churn_date,
        'trial_end': trial_end,
        'paid_start': paid_start,
        'active_end': active_end,
    }

# -------------------------
# 2) Users + experiment rows
# -------------------------
users = []
account_users = defaultdict(list)
user_counter = 1

for aid, st in account_state.items():
    size = st['size']
    if size == '1-10':
        n_users = rng.randint(1, 5)
    elif size == '11-50':
        n_users = rng.randint(2, 10)
    elif size == '51-200':
        n_users = rng.randint(4, 14)
    elif size == '201-500':
        n_users = rng.randint(6, 18)
    else:
        n_users = rng.randint(9, 25)

    if not st['multi_user']:
        n_users = 1

    for j in range(n_users):
        uid = f'USR_{user_counter:06d}'
        user_counter += 1
        role = 'Admin' if j == 0 else rng.choices(['Manager', 'Member'], weights=[0.25, 0.75], k=1)[0]
        join_delay = 0 if j == 0 else rng.randint(1, min(75, max(2, (st['active_end'] - st['signup']).days + 1)))
        user_signup = min(st['signup'] + timedelta(days=join_delay), st['active_end'])

        # Churned/risky accounts tend to lose activity before cancellation.
        if st['churned']:
            last_active = max(user_signup, st['active_end'] - timedelta(days=rng.randint(7, 32)))
            is_active = False
        else:
            inactivity = rng.randint(0, 20 if st['activated'] else 55)
            last_active = max(user_signup, END - timedelta(days=inactivity))
            is_active = inactivity <= 30

        users.append({
            'user_id': uid,
            'account_id': aid,
            'user_role': role,
            'signup_date': iso(user_signup),
            'last_active_date': iso(last_active),
            'is_active': '1' if is_active else '0',
        })
        account_users[aid].append(uid)

        if j == 0 and st['exp_variant']:
            experiment_rows.append({
                'experiment_id': 'EXP_001',
                'user_id': uid,
                'experiment_name': 'integration_first_onboarding',
                'variant': st['exp_variant'],
                'assignment_date': iso(st['signup']),
            })

# -------------------------
# 3) Subscription periods
# -------------------------
subscriptions = []
sub_counter = 1
for aid, st in account_state.items():
    # Everyone begins with a 14-day trial record.
    subscriptions.append({
        'subscription_id': f'SUB_{sub_counter:06d}',
        'account_id': aid,
        'plan_name': 'Trial',
        'monthly_price': 0,
        'subscription_start_date': iso(st['signup']),
        'subscription_end_date': iso(min(st['trial_end'], END)),
        'status': 'Converted' if st['converted'] else 'Expired',
        'previous_plan': '',
        'billing_cycle': 'Trial',
    })
    sub_counter += 1

    if not st['converted'] or st['paid_start'] > END:
        continue

    plan1 = st['target_plan']
    paid_end = st['churn_date'] or END
    duration_days = (paid_end - st['paid_start']).days

    # A minority of retained accounts upgrade/downgrade after enough tenure.
    change_date = None
    plan2 = None
    if duration_days >= 120 and rng.random() < (0.23 if st['activated'] else 0.08):
        change_date = st['paid_start'] + timedelta(days=rng.randint(90, max(91, duration_days - 20)))
        ladder = ['Starter', 'Growth', 'Business', 'Enterprise']
        idx = ladder.index(plan1)
        if rng.random() < 0.78 and idx < len(ladder)-1:
            plan2 = ladder[idx+1]
        elif idx > 0:
            plan2 = ladder[idx-1]
        else:
            plan2 = plan1

    if change_date and plan2 and plan2 != plan1:
        subscriptions.append({
            'subscription_id': f'SUB_{sub_counter:06d}',
            'account_id': aid,
            'plan_name': plan1,
            'monthly_price': PLAN_PRICE[plan1],
            'subscription_start_date': iso(st['paid_start']),
            'subscription_end_date': iso(change_date - timedelta(days=1)),
            'status': 'Plan Changed',
            'previous_plan': 'Trial',
            'billing_cycle': 'Monthly',
        })
        sub_counter += 1
        subscriptions.append({
            'subscription_id': f'SUB_{sub_counter:06d}',
            'account_id': aid,
            'plan_name': plan2,
            'monthly_price': PLAN_PRICE[plan2],
            'subscription_start_date': iso(change_date),
            'subscription_end_date': iso(paid_end),
            'status': 'Cancelled' if st['churned'] else 'Active',
            'previous_plan': plan1,
            'billing_cycle': 'Monthly',
        })
        st['final_plan'] = plan2
        sub_counter += 1
    else:
        subscriptions.append({
            'subscription_id': f'SUB_{sub_counter:06d}',
            'account_id': aid,
            'plan_name': plan1,
            'monthly_price': PLAN_PRICE[plan1],
            'subscription_start_date': iso(st['paid_start']),
            'subscription_end_date': iso(paid_end),
            'status': 'Cancelled' if st['churned'] else 'Active',
            'previous_plan': 'Trial',
            'billing_cycle': 'Monthly',
        })
        st['final_plan'] = plan1
        sub_counter += 1

# -------------------------
# 4) Product events
# -------------------------
product_events = []
event_counter = 1

EVENT_MIX = ['workflow_run', 'workflow_success', 'dashboard_viewed', 'workflow_created', 'integration_connected', 'team_member_invited']
EVENT_WEIGHTS = [0.34, 0.26, 0.18, 0.10, 0.06, 0.06]

for aid, st in account_state.items():
    uids = account_users[aid]
    admin = uids[0]
    signup_dt = st['signup']

    def add_event(uid, d, etype, feature='', integration='', success=''):
        nonlocal_dummy = None
        global event_counter
        product_events.append({
            'event_id': f'EVT_{event_counter:08d}',
            'user_id': uid,
            'account_id': aid,
            'event_timestamp': f"{d.isoformat()} { {'signup':8, 'workspace_created':9, 'integration_connected':11, 'workflow_created':13, 'workflow_run':15, 'workflow_success':16, 'team_member_invited':17}.get(etype, 18):02d}:{rng.randint(0,59):02d}:00",
            'event_type': etype,
            'feature_name': feature,
            'integration_name': integration,
            'success_flag': success,
        })
        event_counter += 1

    # Enforce plausible onboarding order instead of independent random timestamps.
    add_event(admin, signup_dt, 'signup', 'Onboarding')
    has_workspace = st['activated'] or st['early_integration'] or rng.random() < 0.87
    workspace_day = signup_dt + timedelta(days=rng.randint(0, 1))
    if has_workspace:
        add_event(admin, workspace_day, 'workspace_created', 'Workspace')

    primary_integration = None
    integration_day = None
    if st['early_integration'] and has_workspace:
        integration_day = workspace_day + timedelta(days=rng.randint(0, 1))
        primary_integration = 'Salesforce' if st['salesforce_dependency'] else choose_integration(st['target_plan'])
        add_event(admin, integration_day, 'integration_connected', 'Integrations', primary_integration, '1')
    elif st['activated'] and has_workspace:
        # Successful workflows require an integration, even for slower adopters.
        integration_day = signup_dt + timedelta(days=rng.randint(4, 9))
        primary_integration = 'Salesforce' if st['salesforce_dependency'] else choose_integration(st['target_plan'])
        add_event(admin, integration_day, 'integration_connected', 'Integrations', primary_integration, '1')

    first_success_day = None
    if st['activated']:
        wf_day = integration_day + timedelta(days=rng.randint(0, 2))
        first_success_day = min(wf_day + timedelta(days=1), st['active_end'])
        add_event(admin, wf_day, 'workflow_created', 'Workflow Builder')
        add_event(admin, first_success_day, 'workflow_run', 'Workflow Engine', primary_integration or '', '1')
        add_event(admin, first_success_day, 'workflow_success', 'Workflow Engine', primary_integration or '', '1')
        if len(uids) >= 2:
            add_event(admin, min(first_success_day + timedelta(days=1), st['active_end']), 'team_member_invited', 'Team Management')
    elif has_workspace and rng.random() < 0.26:
        # Some non-activated accounts try the builder but never complete a workflow.
        add_event(admin, min(workspace_day + timedelta(days=2), st['active_end']), 'workflow_created', 'Workflow Builder')

    active_start = signup_dt
    active_end = st['active_end']
    months = list(daterange_months(active_start, active_end))
    plan = st.get('final_plan', st['target_plan']) if st['converted'] else 'Trial'
    base_monthly = {'Trial': 4, 'Starter': 13, 'Growth': 24, 'Business': 38, 'Enterprise': 55}[plan]
    engagement_mult = 1.30 if st['activated'] else 0.45
    if st['early_integration']:
        engagement_mult *= 1.18
    if len(uids) >= 3:
        engagement_mult *= 1.12

    for month_start in months:
        m_end = min(month_end(month_start), active_end, END)
        m_start = max(month_start, active_start, (first_success_day + timedelta(days=1)) if first_success_day else active_start)
        if m_start > m_end:
            continue
        monthly_events = max(1, int(rng.gauss(base_monthly * engagement_mult, max(2, base_monthly * 0.18))))

        # In the month leading into churn, usage visibly declines.
        if st['churned'] and (st['churn_date'] - m_start).days <= 45:
            monthly_events = max(1, int(monthly_events * 0.42))

        for _ in range(monthly_events):
            d = rand_date(m_start, m_end)
            etype = rng.choices(EVENT_MIX if st['activated'] else ['dashboard_viewed','workflow_run','team_member_invited'], weights=EVENT_WEIGHTS if st['activated'] else [0.8,0.15,0.05], k=1)[0]
            uid = rng.choice(uids)
            integration = ''
            feature = 'Workflow Engine'
            success = ''

            if etype == 'workflow_run':
                success_prob = (0.94 - (0.12 if st['support_risk'] else 0)) if st['activated'] else 0.0
                success = '1' if rng.random() < success_prob else '0'
            elif etype == 'workflow_success':
                success = '1'
            elif etype == 'dashboard_viewed':
                feature = 'Analytics Dashboard'
            elif etype == 'workflow_created':
                feature = 'Workflow Builder'
            elif etype == 'integration_connected':
                feature = 'Integrations'
                integration = 'Salesforce' if st['salesforce_dependency'] and rng.random() < 0.55 else choose_integration(plan if plan != 'Trial' else 'Starter')
                success = '1'
            elif etype == 'team_member_invited':
                feature = 'Team Management'

            add_event(uid, d, etype, feature, integration, success)

# -------------------------
# 5) Support tickets
# -------------------------
support_tickets = []
ticket_counter = 1
for aid, st in account_state.items():
    if not st['converted']:
        ticket_lambda = 0.7 if st['activated'] else 0.35
    else:
        plan = st.get('final_plan', st['target_plan'])
        ticket_lambda = {'Starter': 2.0, 'Growth': 3.4, 'Business': 5.6, 'Enterprise': 7.5}[plan]
        if st['support_risk']:
            ticket_lambda *= 1.6

    n_tickets = max(0, int(rng.gauss(ticket_lambda, max(0.8, ticket_lambda * 0.35))))
    for _ in range(n_tickets):
        if st['salesforce_dependency'] and rng.random() < 0.42:
            category = 'Salesforce Sync'
        else:
            category = rng.choices(
                ['Workflow Failure', 'Billing', 'AI Assistant', 'User Management', 'UI / Usability'],
                weights=[0.30, 0.18, 0.16, 0.14, 0.22],
                k=1,
            )[0]

        created = rand_date(st['signup'], st['active_end'])
        high_risk = category in ('Salesforce Sync', 'Workflow Failure')
        priority = rng.choices(['Low', 'Medium', 'High', 'Urgent'], weights=[0.14, 0.48, 0.28 if high_risk else 0.22, 0.10 if high_risk else 0.04], k=1)[0]
        unresolved_p = 0.05 + (0.09 if st['support_risk'] else 0) + (0.07 if category == 'Salesforce Sync' else 0)
        unresolved = rng.random() < unresolved_p and created > END - timedelta(days=35)
        if unresolved:
            resolved = None
            status = 'Open'
            resolution_hours = ''
        else:
            mean_hours = {'Low': 18, 'Medium': 14, 'High': 9, 'Urgent': 5}[priority]
            if st['support_risk']:
                mean_hours *= 1.35
            hours = max(1.0, rng.gauss(mean_hours, mean_hours * 0.35))
            resolved_dt = datetime.combine(created, datetime.min.time()) + timedelta(hours=hours)
            resolved = min(resolved_dt.date(), END)
            status = 'Resolved'
            resolution_hours = round(hours, 1)

        product_area = {
            'Salesforce Sync': 'Integrations',
            'Workflow Failure': 'Workflow Engine',
            'Billing': 'Billing',
            'AI Assistant': 'AI Workflow Assistant',
            'User Management': 'Team Management',
            'UI / Usability': 'Dashboard',
        }[category]

        support_tickets.append({
            'ticket_id': f'TKT_{ticket_counter:06d}',
            'account_id': aid,
            'created_at': iso(created),
            'resolved_at': iso(resolved),
            'ticket_text': (rng.choice(SUPPORT_TEMPLATES[category]) + ' It affects our ' + rng.choice(['sales','operations','reporting','customer success','finance']) + ' workflow; ' + rng.choice(['the issue started this week','it has affected multiple runs','our team needs clearer guidance','we noticed it during setup','the problem recurs intermittently']) + '; ' + rng.choice(['the handoff is delayed','a teammate reported an error','the latest run needs review','we need an ETA','a manager raised a concern','it is disrupting a daily task','our team has tried retrying','a scheduled job was interrupted','a critical handoff was missed','we checked our configuration']) + '.'),
            'issue_category': category,
            'product_area': product_area,
            'priority': priority,
            'status': status,
            'resolution_hours': resolution_hours,
        })
        ticket_counter += 1

# -------------------------
# 6) Customer feedback
# -------------------------
feedback_rows = []
feedback_counter = 1
for aid, st in account_state.items():
    if rng.random() < (0.78 if st['converted'] else 0.42):
        # NPS-like score tied to experience, not randomly independent.
        base_score = 7.1
        base_score += 1.0 if st['early_integration'] else -0.6
        base_score += 0.7 if st['multi_user'] else -0.3
        base_score += -1.5 if st['support_risk'] else 0
        base_score += -0.9 if st['churned'] else 0
        score = max(0, min(10, round(rng.gauss(base_score, 1.25))))
        if st['salesforce_dependency'] and st['support_risk']:
            text = rng.choice(FEEDBACK_TEMPLATES['salesforce'])
        elif score >= 8:
            text = rng.choice(FEEDBACK_TEMPLATES['positive'])
        elif score >= 6:
            text = rng.choice(FEEDBACK_TEMPLATES['neutral'])
        else:
            text = rng.choice(FEEDBACK_TEMPLATES['negative'])
        feedback_rows.append({
            'feedback_id': f'FDB_{feedback_counter:06d}',
            'account_id': aid,
            'feedback_date': iso(rand_date(st['signup'], st['active_end'])),
            'feedback_type': 'NPS',
            'score': score,
            'feedback_text': text,
        })
        feedback_counter += 1

    if st['churned']:
        reason_pool = FEEDBACK_TEMPLATES['salesforce'] if st['salesforce_dependency'] else FEEDBACK_TEMPLATES['negative']
        feedback_rows.append({
            'feedback_id': f'FDB_{feedback_counter:06d}',
            'account_id': aid,
            'feedback_date': iso(st['churn_date']),
            'feedback_type': 'Cancellation',
            'score': '',
            'feedback_text': rng.choice(reason_pool),
        })
        feedback_counter += 1

    if st['converted'] and rng.random() < 0.48:
        if rng.random() < 0.30:
            text = rng.choice(FEEDBACK_TEMPLATES['ai'])
        elif st['salesforce_dependency'] and rng.random() < 0.35:
            text = rng.choice(FEEDBACK_TEMPLATES['salesforce'])
        else:
            text = rng.choice([
                'Please add better workflow history filters for larger teams.',
                'We need more templates for common sales and support workflows.',
                'A simpler approval step would help managers review automations.',
                'We would like more control over notifications and workflow alerts.',
            ])
        feedback_rows.append({
            'feedback_id': f'FDB_{feedback_counter:06d}',
            'account_id': aid,
            'feedback_date': iso(rand_date(st['paid_start'], st['active_end'])),
            'feedback_type': 'Feature Request',
            'score': '',
            'feedback_text': text,
        })
        feedback_counter += 1

# -------------------------
# 7) AI usage
# -------------------------
ai_usage = []
ai_counter = 1
for aid, st in account_state.items():
    if not st['converted']:
        continue
    plan = st.get('final_plan', st['target_plan'])
    adopt_p = {'Starter': 0.18, 'Growth': 0.42, 'Business': 0.55, 'Enterprise': 0.61}[plan]
    adopt_p += 0.08 if st['activated'] else -0.08
    ai_adopter = rng.random() < clamp(adopt_p, 0.05, 0.78)
    st['ai_adopter'] = ai_adopter
    if not ai_adopter:
        continue

    monthly_requests_base = {'Starter': 8, 'Growth': 18, 'Business': 34, 'Enterprise': 50}[plan]
    uids = account_users[aid]
    for month_start in daterange_months(st['paid_start'], st['active_end']):
        m_start = max(month_start, st['paid_start'])
        m_end = min(month_end(month_start), st['active_end'], END)
        if m_start > m_end:
            continue
        requests = max(1, int(rng.gauss(monthly_requests_base, monthly_requests_base * 0.25)))
        # Heavy users are a visible cost cohort.
        if rng.random() < 0.10:
            requests = int(requests * rng.uniform(2.2, 3.2))
        success_rate = clamp(rng.gauss(0.86 if st['activated'] else 0.76, 0.05), 0.60, 0.96)
        successes = int(round(requests * success_rate))
        failures = requests - successes
        avg_tokens = rng.randint(900, 1700)
        tokens = requests * avg_tokens
        # Fictional blended internal cost in INR, documented in README.
        estimated_cost = round(tokens / 1000 * 0.55, 2)
        ai_usage.append({
            'usage_id': f'AIU_{ai_counter:07d}',
            'account_id': aid,
            'user_id': rng.choice(uids),
            'usage_date': iso(rand_date(m_start, m_end)),
            'requests': requests,
            'successful_requests': successes,
            'failed_requests': failures,
            'tokens_used': tokens,
            'estimated_cost': estimated_cost,
        })
        ai_counter += 1

# -------------------------
# 8) Integration reference
# -------------------------
integrations_rows = [
    {'integration_id': x[0], 'integration_name': x[1], 'integration_category': x[2], 'plan_availability': x[3]}
    for x in INTEGRATIONS
]

# -------------------------
# 9) Save CSVs
# -------------------------
write_csv('accounts.csv', accounts, ['account_id','company_name','industry','company_size','country','acquisition_channel','signup_date','account_segment'])
write_csv('users.csv', users, ['user_id','account_id','user_role','signup_date','last_active_date','is_active'])
write_csv('subscriptions.csv', subscriptions, ['subscription_id','account_id','plan_name','monthly_price','subscription_start_date','subscription_end_date','status','previous_plan','billing_cycle'])
write_csv('product_events.csv', product_events, ['event_id','user_id','account_id','event_timestamp','event_type','feature_name','integration_name','success_flag'])
write_csv('support_tickets.csv', support_tickets, ['ticket_id','account_id','created_at','resolved_at','ticket_text','issue_category','product_area','priority','status','resolution_hours'])
write_csv('customer_feedback.csv', feedback_rows, ['feedback_id','account_id','feedback_date','feedback_type','score','feedback_text'])
write_csv('ai_usage.csv', ai_usage, ['usage_id','account_id','user_id','usage_date','requests','successful_requests','failed_requests','tokens_used','estimated_cost'])
write_csv('experiments.csv', experiment_rows, ['experiment_id','user_id','experiment_name','variant','assignment_date'])
write_csv('integrations.csv', integrations_rows, ['integration_id','integration_name','integration_category','plan_availability'])

# Generator lives in scripts/; do not overwrite the repository files.

# -------------------------
# 10) README / documentation
# -------------------------
channel_counts = Counter(r['acquisition_channel'] for r in accounts)
variant_counts = Counter(r['variant'] for r in experiment_rows)
converted_count = sum(1 for st in account_state.values() if st['converted'])
churned_count = sum(1 for st in account_state.values() if st['churned'])
activated_count = sum(1 for st in account_state.values() if st['activated'])
early_count = sum(1 for st in account_state.values() if st['early_integration'])
ai_adopters = sum(1 for st in account_state.values() if st.get('ai_adopter'))

readme = f"""# FlowSync SaaS Growth Intelligence — Synthetic Dataset\n\n## Purpose\nThis is a realistic synthetic B2B SaaS dataset designed for a Product / Business / Growth Analytics portfolio project. It is intentionally business-first: the data contains a few controlled behavioural relationships that can be discovered and quantified with SQL, dashboards, and basic statistics.\n\n**Data period:** {START.isoformat()} to {END.isoformat()}  \n**Random seed:** {SEED}  \n**Accounts:** {len(accounts):,}  \n**Users:** {len(users):,}  \n**Product events:** {len(product_events):,}  \n**Support tickets:** {len(support_tickets):,}  \n**Customer feedback rows:** {len(feedback_rows):,}  \n\n## Business scenario\nFlowSync is a fictional B2B workflow-automation SaaS company. Signups are growing, but management wants to understand why activation, retention, and recurring revenue are not improving at the same pace. The company also wants to know whether its AI Workflow Assistant creates enough product value to justify its cost.\n\n## Controlled business patterns\nThe generator encodes *probability differences*, not final answers:\n\n1. Accounts connecting an integration within 72 hours have a higher probability of activation and conversion.\n2. Multi-user accounts tend to retain better than single-user accounts.\n3. Paid Social produces many signups but lower-quality activation/conversion than Referral or Partner channels.\n4. Business/Enterprise accounts are more likely to depend on Salesforce. Salesforce issues therefore affect fewer accounts but disproportionately high MRR.\n5. Usage declines before churn for many churned accounts.\n6. Support-risk accounts experience more tickets and slower resolution.\n7. AI Workflow Assistant adoption is higher in Growth/Business/Enterprise plans. Heavy AI users create higher model cost.\n8. The integration-first onboarding variant probabilistically increases early integration and short-term activation; observed effect varies by simulated sample.\n\nThese patterns should be *measured later through analysis*. Do not quote a number on a resume until your SQL/analysis actually calculates it.\n\n## Quick generation sanity checks\n- Activated accounts (latent generator state): {activated_count:,}\n- Early-integration accounts (latent generator state): {early_count:,}\n- Converted paid accounts: {converted_count:,}\n- Churned paid accounts: {churned_count:,}\n- AI-adopting paid accounts: {ai_adopters:,}\n- Experiment assignments: {dict(variant_counts)}\n\nThe latent states above are only generator diagnostics and are intentionally **not columns in `accounts.csv`**. In the project, you should derive activation, churn, engagement, and similar concepts from observable tables.\n\n## Tables\n- `accounts.csv` — account/company attributes\n- `users.csv` — users belonging to accounts\n- `subscriptions.csv` — trial and paid subscription periods; can contain multiple paid periods when a plan changes\n- `product_events.csv` — event-level product activity used for funnels, retention, feature adoption, and engagement\n- `support_tickets.csv` — structured ticket metadata plus unstructured text for the later Voice-of-Customer AI step\n- `customer_feedback.csv` — NPS, cancellation comments, and feature requests\n- `ai_usage.csv` — monthly-ish AI usage observations; `estimated_cost` is a **fictional blended internal cost in INR**\n- `experiments.csv` — onboarding experiment assignment for eligible new users\n- `integrations.csv` — integration reference table\n\n## Recommended first SQL questions\n1. What is the signup → workspace → integration → workflow → success activation funnel?\n2. Does connecting an integration within 72 hours relate to higher activation?\n3. Which acquisition channels bring high volume but weak conversion?\n4. How does retention differ for single-user vs multi-user accounts?\n5. What are monthly MRR movements and churn?\n6. Which support issue categories affect the most MRR?\n7. Does Salesforce reliability affect high-value accounts disproportionately?\n8. How do AI adopters differ from non-adopters on engagement/retention?\n9. What is the AI cost per account and which cohort drives the highest cost?\n10. Did the integration-first onboarding variant improve activation?\n\n## Interview framing\nA good explanation is:\n\n> I created a realistic synthetic SaaS dataset instead of using an overused churn CSV. I encoded a few business assumptions as probability differences — for example, early integration should improve activation — and then treated those assumptions as hypotheses. The actual metrics and conclusions are derived later through SQL and analysis rather than hard-coded into the resume story.\n"""
(OUT_DIR / 'DATASET_NOTES.md').write_text(readme, encoding='utf-8')

# A concise schema reference.
schema_md = """# Data Model\n\n`accounts` 1→many `users`  \n`accounts` 1→many `subscriptions`  \n`accounts` 1→many `support_tickets`  \n`accounts` 1→many `customer_feedback`  \n`users` 1→many `product_events`  \n`users` 1→many `ai_usage`  \n`users` 1→many `experiments`  \n\nThe common business-level key is `account_id`. `user_id` supports user-level product analysis. Integration usage appears in `product_events.integration_name` and can be joined conceptually to `integrations.integration_name`.\n"""
(OUT_DIR / 'DATA_MODEL.md').write_text(schema_md, encoding='utf-8')

# Create a simple manifest for easy verification.
manifest = {
    'accounts.csv': len(accounts),
    'users.csv': len(users),
    'subscriptions.csv': len(subscriptions),
    'product_events.csv': len(product_events),
    'support_tickets.csv': len(support_tickets),
    'customer_feedback.csv': len(feedback_rows),
    'ai_usage.csv': len(ai_usage),
    'experiments.csv': len(experiment_rows),
    'integrations.csv': len(integrations_rows),
}
with (OUT_DIR / 'MANIFEST.txt').open('w', encoding='utf-8') as f:
    for k, v in manifest.items():
        f.write(f'{k}: {v:,} rows\n')

# The repository archive is built separately after dashboards and docs are generated.
print('Generated synthetic CSV files at:', OUT_DIR)
for k, v in manifest.items():
    print(f'{k:24s} {v:>10,}')
print(f'Converted accounts: {converted_count:,}')
print(f'Churned accounts:   {churned_count:,}')
print(f'Activated accounts: {activated_count:,}')
print('Experiment:', dict(variant_counts))
