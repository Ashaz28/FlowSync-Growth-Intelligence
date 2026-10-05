"""FlowSync Growth Intelligence: streamlit run app.py"""
from __future__ import annotations
import json
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from ai_voc import analyze_ticket

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data'/'processed'
RAW=ROOT/'data'/'raw'
st.set_page_config(page_title='FlowSync · SaaS Growth Intelligence',page_icon='📈',layout='wide')
st.markdown('''<style>
.block-container{max-width:1260px;padding-top:1.5rem}h1,h2,h3{letter-spacing:-0.025em}
div[data-testid="stMetric"]{background:#f3f7fb;border:1px solid #e1eaf2;padding:15px 18px;border-radius:13px}
.pill{font-size:.8rem;font-weight:700;color:#155c5f;background:#e5f4f1;border-radius:30px;padding:5px 10px;display:inline-block;margin-bottom:8px}
.muted{color:#536174;font-size:.9rem}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def csv(name,processed=True):return pd.read_csv((OUT if processed else RAW)/f'{name}.csv')
@st.cache_data(show_spinner=False)
def obj(name):return json.loads((OUT/name).read_text())

def money(val):
    if abs(val)>=10_000_000:return f'₹{val/10_000_000:.2f} Cr'
    if abs(val)>=100_000:return f'₹{val/100_000:.1f} L'
    return f'₹{val:,.0f}'

def plotly(fig,height=360):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=5,r=5,t=38,b=5),font=dict(family='Arial',size=12),legend_title_text='')
    st.plotly_chart(fig,use_container_width=True)

s=obj('summary.json');exp=obj('experiment_summary.json'); ac=csv('account_metrics'); mrr=csv('monthly_mrr');f=csv('funnel')
st.markdown('<span class="pill">PORTFOLIO CASE STUDY · SYNTHETIC DATA</span>',unsafe_allow_html=True)
st.title('FlowSync | SaaS Growth Intelligence')
st.write('**Business question:** Where is customer growth leaking—and which product and customer actions should leadership prioritize?')
st.caption('Fictional B2B SaaS scenario • data as of 31 Aug 2026 • simulated outcomes, not real-company results')
tabs=st.tabs(['01  Executive overview','02  Product growth & experiment','03  Customer insights & AI'])
with tabs[0]:
    now=mrr.iloc[-1];before=mrr.iloc[-2]
    a,b,c,d=st.columns(4)
    a.metric('Current MRR',money(s['mrr_inr']),f"{(now.mrr/before.mrr-1)*100:+.1f}% MoM")
    b.metric('Active paid accounts',f"{s['active_paid_accounts']:,}")
    c.metric('7-day activation',f"{s['seven_day_activation_rate_pct']:.1f}%")
    d.metric('Latest NRR',f"{now.nrr_pct:.1f}%")
    l,r=st.columns([1.55,1])
    with l:
        fig=px.line(mrr,x='month',y='mrr',markers=True,title='Monthly recurring revenue',labels={'month':'Month','mrr':'MRR (₹)'})
        plotly(fig)
    with r:
        plans=csv('mrr_by_plan'); fig=px.bar(plans,x='plan_name',y='mrr',text='accounts',title='Current MRR by plan',labels={'plan_name':'Plan','mrr':'MRR (₹)','accounts':'Paid accounts'})
        plotly(fig)
    l,r=st.columns(2)
    with l:
        fig=px.bar(f,x='stage',y='accounts',text='overall_pct',title='Account onboarding funnel',labels={'stage':'Milestone','accounts':'Accounts'})
        fig.update_traces(texttemplate='%{text:.0f}%')
        plotly(fig)
    with r:
        channel=csv('channels').sort_values('paid_conversion_pct')
        fig=px.bar(channel,x='paid_conversion_pct',y='acquisition_channel',orientation='h',title='Paid conversion by acquisition channel',labels={'paid_conversion_pct':'Converted to paid (%)','acquisition_channel':'Channel'})
        plotly(fig)
    st.info('Interpretation: funnel and channel comparisons are observational. Signups and recurring revenue are different outcomes; leadership should optimize quality, not volume alone.')
with tabs[1]:
    st.subheader('Which onboarding behaviours connect to activation?')
    a,b=st.columns(2)
    with a:
        early=csv('early_integration');early['Group']=early.early_integration.map({True:'Within 72 hours',False:'Not within 72 hours','True':'Within 72 hours','False':'Not within 72 hours'})
        plotly(px.bar(early,x='Group',y='activation_rate_pct',text='activation_rate_pct',title='7-day activation by integration timing',labels={'activation_rate_pct':'Activated within 7 days (%)'}))
        st.caption('**Association, not causation.** The dataset intentionally models early integration as a driver; do not represent this gap as real-world evidence.')
    with b:
        cohort=csv('paid_cohort_retention'); pivot=cohort.pivot(index='cohort',columns='months_since_first_paid',values='retention_pct')
        fig=px.imshow(pivot,aspect='auto',text_auto='.0f',zmin=0,zmax=100,title='Paid account cohort retention (%)',labels={'x':'Months since first paid','y':'Paid cohort','color':'Retention %'})
        plotly(fig,400)
        st.caption('Missing cells represent cohorts that have not aged enough for that follow-up month.')
    st.subheader('Integration-first onboarding experiment')
    ex=csv('experiment');a,b,c=st.columns(3)
    a.metric('Control activation',f"{exp['control_rate_pct']:.1f}%",f"{exp['control_n']} accounts")
    b.metric('Variant activation',f"{exp['variant_rate_pct']:.1f}%",f"{exp['variant_n']} accounts")
    c.metric('Observed absolute lift',f"{exp['absolute_lift_pp']:+.1f} pp")
    plotly(px.bar(ex,x='variant',y='activation_pct',text='activated_7d',title='Observed 7-day activation by test group',labels={'variant':'Assignment','activation_pct':'Activation (%)','activated_7d':'Activated accounts'}),315)
    verdict='passes' if exp['statistically_significant_5pct'] else 'does not pass'
    st.info(f"In this simulation, observed lift {verdict} a 5% two-sided threshold. 95% approximate CI: {exp['ci95_difference_pp'][0]:+.1f} to {exp['ci95_difference_pp'][1]:+.1f} percentage points. Synthetic outcomes are not evidence of actual customer impact.")
with tabs[2]:
    issues=csv('issue_impact');health=csv('customer_health');ai=csv('ai_by_plan');
    st.subheader('Voice of customer meets account-level revenue')
    a,b=st.columns([1.25,1])
    with a:
        plotly(px.bar(issues.sort_values('active_mrr_exposure'),x='active_mrr_exposure',y='issue_category',orientation='h',title='Active MRR represented by affected accounts',labels={'active_mrr_exposure':'Affected-account current MRR (₹)','issue_category':'Issue'}))
    with b:
        shown=issues[['issue_category','tickets','affected_active_accounts','avg_exposure_per_active_account']].copy();shown.columns=['Issue','Tickets','Active accounts affected','Avg MRR / affected active account']
        st.dataframe(shown,use_container_width=True,hide_index=True)
        st.caption('**Revenue exposure ≠ revenue lost or saved.** A single account may appear under multiple themes; do not sum exposures across themes.')
    st.divider()
    a,b=st.columns(2)
    with a:
        st.subheader('Customer-success prioritization')
        bands=health.attention_band.value_counts().reset_index();bands.columns=['Attention band','Accounts']
        plotly(px.bar(bands,x='Attention band',y='Accounts',title='Transparent heuristic health bands'),300)
        st.dataframe(health.loc[health.attention_band.eq('Priority review'),['account_id','current_mrr','health_score','active_users_30d','unresolved_high_urgent_tickets']].sort_values(['health_score','current_mrr'],ascending=[True,False]).head(12),hide_index=True,use_container_width=True)
        st.caption('Descriptive score, not a validated churn-probability model. Review with Customer Success before acting.')
    with b:
        st.subheader('AI Workflow Assistant economics')
        if not ai.empty:
            plotly(px.bar(ai.loc[ai.current_plan.ne('Not active')],x='current_plan',y='cost_per_ai_account_inr',title='Illustrative AI cost per adopting account',labels={'current_plan':'Plan','cost_per_ai_account_inr':'Cost per AI adopter (₹)'}),300)
        st.caption('Costs are synthetic illustrative estimates, not actual API invoices. Different plan/customer cohorts are not directly comparable without controls.')
    st.divider()
    st.subheader('Live AI Voice-of-Customer prototype')
    st.write('Classify a support message into a structured theme, severity, sentiment and a tentative root-cause hypothesis. **Requires your own API key**; no external call happens otherwise.')
    sample=csv('support_tickets',processed=False)[['ticket_text','issue_category']].drop_duplicates('ticket_text').head(30)
    choice=st.selectbox('Optional synthetic sample', ['Type my own']+sample.ticket_text.tolist())
    typed=st.text_area('Ticket text',value='' if choice=='Type my own' else choice,height=105,max_chars=2500)
    api_key=st.text_input('OpenAI API key (not stored)',type='password',value=os.getenv('OPENAI_API_KEY',''))
    st.caption('Use synthetic/anonymized text only. Never paste real customer PII into a demo.')
    if st.button('Analyze ticket with AI',type='primary'):
        if not api_key:st.warning('Provide your own API key to run live LLM analysis. The existing issue charts above come from dataset labels, not LLM-generated results.')
        else:
            try:
                with st.spinner('Classifying and validating output...'):
                    result=analyze_ticket(typed,api_key)
                st.json(result)
                if result['requires_human_review']:st.warning('Human review is required before taking action.')
                else:st.success('Structured result available for review; do not automatically change the product roadmap.')
            except Exception as err:st.error(f'Live analysis unavailable: {err}')
st.divider()
st.caption('Methodology, SQL, AI evaluation plan and limitation disclosures: see the repository docs/ directory. This demo does not assert real business impact.')
