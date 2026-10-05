"""Smoke + business-rule tests; run pytest -q from the repository root."""
import json
from pathlib import Path
import pandas as pd
from ai_voc import clean_result

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data'/'processed'
R=ROOT/'data'/'raw'

def test_source_dataset_keys_are_unique():
    for file,key in [('accounts','account_id'),('users','user_id'),('product_events','event_id'),('subscriptions','subscription_id')]:
        d=pd.read_csv(R/f'{file}.csv',usecols=[key]);assert d[key].is_unique

def test_event_user_accounts_match():
    u=pd.read_csv(R/'users.csv',usecols=['user_id','account_id'])
    e=pd.read_csv(R/'product_events.csv',usecols=['user_id','account_id'])
    z=e.merge(u,on='user_id',suffixes=('_event','_user'))
    assert len(z)==len(e)
    assert (z.account_id_event==z.account_id_user).all()

def test_snapshot_mrr_reconciles():
    s=json.loads((P/'summary.json').read_text())
    monthly=pd.read_csv(P/'monthly_mrr.csv')
    plans=pd.read_csv(P/'mrr_by_plan.csv')
    assert monthly.iloc[-1].mrr==s['mrr_inr']==plans.mrr.sum()
    assert int(monthly.iloc[-1].active_accounts)==s['active_paid_accounts']==plans.accounts.sum()

def test_funnel_is_nested_and_mature():
    f=pd.read_csv(P/'funnel.csv'); assert (f.accounts.diff().fillna(0)<=0).all()
    d=pd.read_csv(P/'account_metrics.csv');assert d.activated_7d.sum()<=d.step_success.sum()
    assert d.signup_date.max()<='2026-08-10'

def test_experiment_matches_assignments_and_precision():
    e=pd.read_csv(P/'experiment.csv');raw=pd.read_csv(R/'experiments.csv')
    assert int(e.assigned_accounts.sum())==len(raw)==raw.user_id.nunique()
    for _,row in e.iterrows():
        assert 0<=row.activated_7d<=row.assigned_accounts
        assert abs(100*row.activated_7d/row.assigned_accounts-row.activation_pct)<.01

def test_issue_exposure_deduplicates_accounts():
    tickets=pd.read_csv(R/'support_tickets.csv')
    accounts=pd.read_csv(P/'account_metrics.csv',usecols=['account_id','current_mrr'])
    expected=tickets[['issue_category','account_id']].drop_duplicates().merge(accounts,on='account_id').groupby('issue_category').current_mrr.sum()
    observed=pd.read_csv(P/'issue_impact.csv').set_index('issue_category').active_mrr_exposure
    assert expected.sort_index().equals(observed.sort_index())

def test_ai_output_requires_review_for_high_severity_and_low_confidence():
    d={'theme':'Salesforce Sync','product_area':'Integrations','sentiment':'negative','severity':'high','confidence':.94,'root_cause_hypothesis':'Possible mapping error'}
    assert clean_result(d)['requires_human_review']
    d.update(severity='medium',confidence=0.42)
    assert clean_result(d)['requires_human_review']
    d.update(confidence=.95)
    assert not clean_result(d)['requires_human_review']
    d.update(theme='Invalid',confidence=2)
    assert clean_result(d)['theme']=='Other'
    assert clean_result(d)['confidence_self_reported']==1

def test_live_ai_path_with_mock_not_network(monkeypatch):
    """Tests JSON parsing and review policy without spending tokens or calling an API."""
    from types import SimpleNamespace, ModuleType
    import sys
    from ai_voc import analyze_ticket
    fake_response=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
        'theme':'Salesforce Sync','product_area':'Integrations','sentiment':'negative','severity':'high',
        'root_cause_hypothesis':'Possibly a mapping issue; needs investigation','confidence':0.86})))])
    class FakeChat:
        completions=SimpleNamespace(create=lambda **kwargs:fake_response)
    class FakeClient:
        chat=FakeChat()
    mock_openai=ModuleType('openai')
    mock_openai.OpenAI=lambda **kwargs:FakeClient()
    monkeypatch.setitem(sys.modules,'openai',mock_openai)
    result=analyze_ticket('Salesforce fields are not syncing.', 'not-a-real-key')
    assert result['theme']=='Salesforce Sync'
    assert result['requires_human_review']
