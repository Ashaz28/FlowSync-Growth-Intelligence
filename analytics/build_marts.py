"""Turn the reproducible synthetic SaaS CSVs into simple decision-ready analytics marts.

Run: python analytics/build_marts.py
All money is illustrative INR; no causal or real-company impact claims.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
OUT=ROOT/'data'/'processed'
OUT.mkdir(parents=True,exist_ok=True)
SNAP=pd.Timestamp('2026-08-31')

def read(name,dates=()):
    return pd.read_csv(RAW/f'{name}.csv',parse_dates=list(dates))

def save(name,df):
    df.to_csv(OUT/f'{name}.csv',index=False,float_format='%.4f')
    print(f'{name:<20} {len(df):>5} rows')

def main():
    ac=read('accounts',['signup_date']); us=read('users',['signup_date']); sub=read('subscriptions',['subscription_start_date','subscription_end_date'])
    ev=read('product_events',['event_timestamp']); tickets=read('support_tickets',['created_at','resolved_at']); feedback=read('customer_feedback',['feedback_date']); ai=read('ai_usage',['usage_date']); exp=read('experiments',['assignment_date'])
    # Source integrity is explicitly checked before any claimed metrics.
    id_tables={'accounts':(ac,'account_id'),'users':(us,'user_id'),'subscriptions':(sub,'subscription_id'),'product_events':(ev,'event_id'),'support_tickets':(tickets,'ticket_id'),'customer_feedback':(feedback,'feedback_id'),'ai_usage':(ai,'usage_id'),'integrations':(read('integrations'),'integration_id')}
    checks={f'{name}_unique_id': bool(frame[key].is_unique) for name,(frame,key) in id_tables.items()}
    checks['users_all_accounts_exist']=bool(us.account_id.isin(ac.account_id).all())
    checks['events_all_users_exist']=bool(ev.user_id.isin(us.user_id).all())
    checks['events_user_account_match']=bool((ev[['user_id','account_id']].merge(us[['user_id','account_id']],on='user_id',suffixes=('_event','_user')).eval('account_id_event == account_id_user')).all())
    checks['support_all_accounts_exist']=bool(tickets.account_id.isin(ac.account_id).all())
    checks['events_within_snapshot']=bool(ev.event_timestamp.le(SNAP+pd.Timedelta(days=1)).all())
    checks['ai_usage_account_exists']=bool(ai.account_id.isin(ac.account_id).all())
    if not all(checks.values()):
        raise ValueError(f'Data integrity checks failed: {[k for k,v in checks.items() if not v]}')
    # Account-level funnel: first occurrence is trustworthy after generator chronology checks.
    first=ev.loc[ev.event_type.isin(['workspace_created','integration_connected','workflow_created','workflow_success'])].groupby(['account_id','event_type']).event_timestamp.min().unstack()
    x=ac.set_index('account_id').join(first)
    for c in ['workspace_created','integration_connected','workflow_created','workflow_success']:
        if c not in x.columns: x[c]=pd.NaT
    checks['success_not_before_integration']=bool((x.workflow_success.dropna() >= x.loc[x.workflow_success.notna(),'integration_connected']).all())
    if not checks['success_not_before_integration']:raise ValueError('Workflow success occurred before integration.')
    x['step_signup']=True
    x['step_workspace']=x.workspace_created.notna()
    x['step_integration']=x.step_workspace & x.integration_connected.ge(x.workspace_created)
    x['step_workflow']=x.step_integration & x.workflow_created.ge(x.integration_connected)
    x['step_success']=x.step_workflow & x.workflow_success.ge(x.workflow_created)
    x['activated_7d']=x.workflow_success.ge(x.signup_date) & x.workflow_success.lt(x.signup_date+pd.Timedelta(days=7))
    x['early_integration']=x.integration_connected.ge(x.signup_date) & x.integration_connected.lt(x.signup_date+pd.Timedelta(hours=72))
    paid=sub.loc[sub.plan_name.ne('Trial')]
    x['paid_ever']=x.index.isin(paid.account_id)
    x['churned']=x.index.isin(paid.loc[paid.status.eq('Cancelled'),'account_id'])
    current=paid.loc[(paid.subscription_start_date<=SNAP)&(paid.subscription_end_date>=SNAP)&paid.status.ne('Cancelled')].copy()
    assert current.account_id.is_unique, 'Multiple active subscriptions on snapshot'
    x['current_mrr']=current.set_index('account_id').monthly_price.reindex(x.index).fillna(0)
    x['current_plan']=current.set_index('account_id').plan_name.reindex(x.index).fillna('Not active')
    first_paid=paid.groupby('account_id').subscription_start_date.min()
    x['first_paid_date']=first_paid.reindex(x.index)
    # Team-adoption denominator only includes fully observed 30-day windows.
    members=us.merge(ac[['account_id','signup_date']],on='account_id',suffixes=('_user','_account'))
    early_member=members.loc[(members.signup_date_user>=members.signup_date_account)&(members.signup_date_user<=members.signup_date_account+pd.Timedelta(days=30))].groupby('account_id').user_id.nunique()
    x['early_team_users']=early_member.reindex(x.index).fillna(0).astype(int)
    x['early_team_mature']=x.signup_date.le(SNAP-pd.Timedelta(days=30))
    x['age_90d_paid']=x.first_paid_date.le(SNAP-pd.Timedelta(days=90))
    account_cols=['industry','company_size','country','acquisition_channel','signup_date','account_segment','current_mrr','current_plan','first_paid_date','paid_ever','churned','early_team_users','early_team_mature','age_90d_paid','early_integration','activated_7d','step_signup','step_workspace','step_integration','step_workflow','step_success']
    save('account_metrics',x[account_cols].reset_index())
    stages=[('Signups',x.step_signup.sum()),('Workspace',x.step_workspace.sum()),('Integration',x.step_integration.sum()),('Workflow created',x.step_workflow.sum()),('Successful workflow',x.step_success.sum())]
    save('funnel',pd.DataFrame(stages,columns=['stage','accounts']).assign(overall_pct=lambda d:100*d.accounts/d.accounts.iloc[0],step_pct=lambda d:100*d.accounts/d.accounts.shift().fillna(d.accounts.iloc[0])))
    # Early integration association: same observation window and account-level denominator.
    association=x.groupby('early_integration').agg(accounts=('activated_7d','size'),activated=('activated_7d','sum')).reset_index()
    association['activation_rate_pct']=100*association.activated/association.accounts
    save('early_integration',association)
    channels=x.groupby('acquisition_channel').agg(signups=('step_signup','sum'),activated_7d=('activated_7d','sum'),paid_accounts=('paid_ever','sum'),active_mrr=('current_mrr','sum')).reset_index()
    channels['activation_7d_pct']=100*channels.activated_7d/channels.signups
    channels['paid_conversion_pct']=100*channels.paid_accounts/channels.signups
    save('channels',channels.sort_values('paid_conversion_pct',ascending=False))
    # Current MRR by plan, no overlapping periods.
    plans=current.groupby('plan_name').agg(accounts=('account_id','nunique'),mrr=('monthly_price','sum')).reset_index().sort_values('mrr',ascending=False)
    plans['mrr_share_pct']=100*plans.mrr/plans.mrr.sum()
    save('mrr_by_plan',plans)
    # Revenue waterfall at month end; history is monthly subscription snapshot, not invoiced revenue.
    dates=pd.date_range('2025-09-30',SNAP,freq='ME'); months=[]; previous=pd.Series(dtype=float)
    for month in dates:
        active=paid.loc[(paid.subscription_start_date<=month)&(paid.subscription_end_date>=month)&~((paid.status=='Cancelled')&(paid.subscription_end_date<=month))]
        values=active.groupby('account_id').monthly_price.sum()
        mrr=float(values.sum())
        curr=values.reindex(previous.index.union(values.index),fill_value=0)
        prev=previous.reindex(curr.index,fill_value=0)
        new=float(curr.loc[(prev==0)&(curr>0)].sum())
        expansion=float((curr.loc[(prev>0)&(curr>prev)]-prev.loc[(prev>0)&(curr>prev)]).sum())
        contraction=float((prev.loc[(prev>0)&(curr>0)&(curr<prev)]-curr.loc[(prev>0)&(curr>0)&(curr<prev)]).sum())
        churn=float(prev.loc[(prev>0)&(curr==0)].sum())
        if len(months): assert abs(previous.sum()+new+expansion-contraction-churn-mrr)<0.001
        base=float(previous.sum())
        months.append({'month':month.date(),'mrr':mrr,'active_accounts':int((values>0).sum()),'new_mrr':new,'expansion_mrr':expansion,'contraction_mrr':contraction,'churned_mrr':churn,'nrr_pct':100*(base+expansion-contraction-churn)/base if base else np.nan,'grr_pct':100*(base-contraction-churn)/base if base else np.nan})
        previous=values
    save('monthly_mrr',pd.DataFrame(months))
    # Cohort retention: first paid month, reported only when full follow-up month has been observed.
    paid_start=first_paid.reset_index(); paid_start.columns=['account_id','first_paid_date']; paid_start['cohort']=paid_start.first_paid_date.dt.to_period('M')
    cohorts=[]
    for cohort,g in paid_start.groupby('cohort'):
        orig=set(g.account_id)
        for age in (0,1,2,3,4,5,6):
            at=(cohort+age).to_timestamp(how='end').normalize()
            if at>SNAP: continue
            ids=set(paid.loc[(paid.account_id.isin(orig))&(paid.subscription_start_date<=at)&(paid.subscription_end_date>=at)].account_id)
            cohorts.append({'cohort':str(cohort),'months_since_first_paid':age,'original_paid_accounts':len(orig),'retained_accounts':len(ids),'retention_pct':100*len(ids)/len(orig)})
    save('paid_cohort_retention',pd.DataFrame(cohorts))
    # Support revenue exposure deduplicates accounts per category and counts only current paid MRR.
    impact=tickets.groupby('issue_category').agg(tickets=('ticket_id','size'),affected_accounts=('account_id','nunique'),open_tickets=('status',lambda s:int(s.eq('Open').sum())),high_urgent=('priority',lambda s:int(s.isin(['High','Urgent']).sum()))).reset_index()
    unique_issue=tickets[['issue_category','account_id']].drop_duplicates().merge(x[['current_mrr']].reset_index(),on='account_id',how='left')
    exposure=unique_issue.groupby('issue_category').agg(active_mrr_exposure=('current_mrr','sum'),affected_active_accounts=('current_mrr',lambda s:int(s.gt(0).sum()))).reset_index()
    impact=impact.merge(exposure,on='issue_category');impact['avg_exposure_per_active_account']=np.where(impact.affected_active_accounts>0,impact.active_mrr_exposure/impact.affected_active_accounts,0)
    save('issue_impact',impact.sort_values('active_mrr_exposure',ascending=False))
    # Descriptive heuristic score, not a calibrated churn prediction.
    wins=ev.loc[ev.event_type.eq('workflow_success')].copy()
    wins['period']=np.where(wins.event_timestamp.ge(SNAP-pd.Timedelta(days=29)),'recent',np.where(wins.event_timestamp.ge(SNAP-pd.Timedelta(days=59)),'prior','older'))
    wins=wins.loc[wins.period.ne('older')]
    counts=wins.pivot_table(index='account_id',columns='period',values='event_id',aggfunc='size',fill_value=0)
    for k in ('recent','prior'):
        if k not in counts:counts[k]=0
    recent_user=ev.loc[(ev.event_timestamp>=SNAP-pd.Timedelta(days=29))&(ev.event_timestamp<SNAP+pd.Timedelta(days=1))].groupby('account_id').user_id.nunique()
    open_high=tickets.loc[(tickets.status.eq('Open'))&(tickets.priority.isin(['High','Urgent']))].groupby('account_id').ticket_id.size()
    health=x.loc[x.current_mrr.gt(0),['current_mrr','current_plan','account_segment']].copy()
    health['successful_runs_30d']=counts.recent.reindex(health.index).fillna(0).astype(int)
    health['successful_runs_prior_30d']=counts.prior.reindex(health.index).fillna(0).astype(int)
    health['active_users_30d']=recent_user.reindex(health.index).fillna(0).astype(int)
    health['unresolved_high_urgent_tickets']=open_high.reindex(health.index).fillna(0).astype(int)
    health['has_integration']=x.step_integration.reindex(health.index).astype(bool)
    trend_ratio=(health.successful_runs_30d+1)/(health.successful_runs_prior_30d+1)
    health['score_engagement']=np.select([health.successful_runs_30d.eq(0),trend_ratio.lt(.7),trend_ratio.lt(1.0),trend_ratio.ge(1.0)],[0,15,27,40],default=20)
    health['score_team']=np.select([health.active_users_30d.ge(3),health.active_users_30d.eq(2),health.active_users_30d.eq(1)],[25,15,6],default=0)
    health['score_setup']=health.has_integration.astype(int)*15
    health['score_support']=np.where(health.unresolved_high_urgent_tickets>0,0,20)
    health['health_score']=health[['score_engagement','score_team','score_setup','score_support']].sum(axis=1)
    health['attention_band']=pd.cut(health.health_score,bins=[-1,39,69,100],labels=['Priority review','Monitor','Healthy'])
    save('customer_health',health.reset_index())
    ai_account=ai.groupby('account_id').agg(requests=('requests','sum'),successful_requests=('successful_requests','sum'),tokens_used=('tokens_used','sum'),estimated_cost=('estimated_cost','sum')).reset_index()
    ai_account=ai_account.merge(x[['current_mrr','current_plan','paid_ever','activated_7d']].reset_index(),on='account_id',how='left')
    ai_account['success_pct']=100*ai_account.successful_requests/ai_account.requests
    save('ai_account_usage',ai_account)
    ai_plans=ai_account.groupby('current_plan').agg(ai_accounts=('account_id','nunique'),requests=('requests','sum'),successful_requests=('successful_requests','sum'),total_cost_inr=('estimated_cost','sum')).reset_index()
    ai_plans['task_success_pct']=100*ai_plans.successful_requests/ai_plans.requests
    ai_plans['cost_per_ai_account_inr']=ai_plans.total_cost_inr/ai_plans.ai_accounts
    save('ai_by_plan',ai_plans)
    # Experiment: one admin was assigned per eligible account; report observed lift, uncertainty.
    exa=exp.merge(us[['user_id','account_id']],on='user_id').merge(x[['workflow_success']].reset_index(),on='account_id')
    exa['activated_7d']=exa.workflow_success.ge(exa.assignment_date) & exa.workflow_success.lt(exa.assignment_date+pd.Timedelta(days=7))
    experiment=exa.groupby('variant').agg(assigned_accounts=('account_id','nunique'),activated_7d=('activated_7d','sum')).reset_index()
    experiment['activation_pct']=100*experiment.activated_7d/experiment.assigned_accounts
    save('experiment',experiment)
    ctl=experiment.set_index('variant').loc['Control'];var=experiment.set_index('variant').loc['Variant']
    n0,n1=float(ctl.assigned_accounts),float(var.assigned_accounts)
    p0,p1=float(ctl.activated_7d/n0),float(var.activated_7d/n1)
    diff=p1-p0; pooled=(float(ctl.activated_7d)+float(var.activated_7d))/(n0+n1)
    sep=float(np.sqrt(pooled*(1-pooled)*(1/n0+1/n1)));pval=float(2*norm.sf(abs(diff/sep))) if sep>0 else 1.
    seci=float(np.sqrt(p0*(1-p0)/n0+p1*(1-p1)/n1))
    exp_result={'control_n':int(n0),'variant_n':int(n1),'control_activated':int(ctl.activated_7d),'variant_activated':int(var.activated_7d),'control_rate_pct':round(100*p0,2),'variant_rate_pct':round(100*p1,2),'absolute_lift_pp':round(100*diff,2),'relative_lift_pct':round(100*diff/p0,2) if p0>0 else None,'p_value_two_sided':round(pval,8),'ci95_difference_pp':[round(100*(diff-1.96*seci),2),round(100*(diff+1.96*seci),2)],'statistically_significant_5pct':bool(pval<.05),'test':'two-sided two-proportion z-test; Wald confidence interval','caution':'Simulated randomized assignment and synthetic outcomes; illustrative, not proof of real-world uplift.'}
    (OUT/'experiment_summary.json').write_text(json.dumps(exp_result,indent=2))
    snapshot={'snapshot':'2026-08-31','source':'Synthetic scenario only','accounts':len(ac),'users':len(us),'events':len(ev),'support_tickets':len(tickets),'feedback':len(feedback),'active_paid_accounts':len(current),'mrr_inr':float(current.monthly_price.sum()),'arr_run_rate_inr':float(current.monthly_price.sum()*12),'paid_ever':int(x.paid_ever.sum()),'seven_day_activation_rate_pct':round(100*x.activated_7d.mean(),2),'data_quality':checks}
    (OUT/'summary.json').write_text(json.dumps(snapshot,indent=2))
    print('SUMMARY',json.dumps({k:v for k,v in snapshot.items() if k!='data_quality'},indent=2))
    print('EXPERIMENT',json.dumps(exp_result,indent=2))

if __name__=='__main__':main()
