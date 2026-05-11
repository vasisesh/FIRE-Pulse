import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse V2.3 Mastery", layout="wide")

# --- OBSIDIAN EMERALD STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    [data-testid="stMetricValue"] {
        color: #00E676 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00C853 , #B2FF59); }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS & CONFIG ---
FIRE_TARGET = 1000000
NW_TARGET = 2500000
RET_AGE = 50
CUR_AGE = 43
YEARS_TO_GO = RET_AGE - CUR_AGE
GROWTH_RATE = 0.07 # 7% Nominal Appreciation
SWR = 0.035 # 3.5% Safe Withdrawal Rate

# --- ENGINES ---
def calculate_dynamic_values():
    now = datetime.now()
    # 1. Home Equity (Roswell, GA)
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    # 2. Contributions
    biweekly_periods = max(0, (now - datetime(2026, 1, 1)).days // 14)
    total_401k = biweekly_periods * 1269.23
    hsa_p = (7750 + 8300 + 8300) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, total_401k, hsa_p

def load_all_pillars():
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
    data = [
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875, 'Pillar': 'Robinhood'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067, 'Pillar': 'Robinhood'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524, 'Pillar': 'Robinhood'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.0675, 'Pillar': 'Robinhood'},
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE'},
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement'},
        {'Name': 'WFSPX (401k)', 'Tkr': 'WFSPX', 'Qty': 157.092, 'Pillar': 'Retirement'},
        {'Name': 'JLGMX (401k)', 'Tkr': 'JLGMX', 'Qty': 641.562, 'Pillar': 'Retirement'},
        {'Name': 'Auto 401k Growth', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k},
        {'Name': 'VTSAX (College)', 'Tkr': 'VTSAX', 'Qty': 209.296, 'Pillar': 'College Fund'},
        {'Name': 'VTI (College)', 'Tkr': 'VTI', 'Qty': 222.203, 'Pillar': 'College Fund'},
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000},
        {'Name': 'HSA (VTSAX)', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India'},
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000},
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base': -m_bal}
    ]
    df = pd.DataFrame(data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    try:
        p_df = yf.download(tkrs, period="7d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base'], r['Base']
            valid = p_df[r['Tkr']].dropna()
            return valid.iloc[-1] * r['Qty'], valid.iloc[-2] * r['Qty']
        df[['Curr', 'Prev']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr'] = df.get('Base', 0); df['Prev'] = df['Curr']
    df['Chg_$'] = (df['Curr'] - df['Prev']).fillna(0)
    df['Chg_%'] = ((df['Curr'] / df['Prev'] - 1) * 100).fillna(0)
    return df

df = load_all_pillars()

# --- FORECASTING ENGINE ---
liquid_total = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()
def project_wealth(base, rate):
    months = YEARS_TO_GO * 12
    m_rate = (1 + rate)**(1/12) - 1
    b = [base]
    for _ in range(months): b.append((b[-1] * (1 + m_rate)) + 3600)
    return b

projection = project_wealth(liquid_total, GROWTH_RATE)
final_liquid_2035 = projection[-1]
future_runway = (final_liquid_2035 * SWR) / 12

# --- UI DASHBOARD ---
st.title("🛡️ THE VASIREDDY FORTRESS")
st.caption(f"Strategy: Retire at {RET_AGE} | 7% Growth Projection | Combined Master Control")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL NET WORTH", f"${df['Curr'].sum():,.0f}", delta=f"${df['Chg_$'].sum():,.2f}")
m2.metric("LIQUID FIRE (CURRENT)", f"${liquid_total:,.0f}")
m3.metric("GAP TO $2.5M NW", f"${max(0, NW_TARGET - df['Curr'].sum()):,.0f}")

st.divider()

# PREDICTIVE SECTION
st.subheader(f"2035 ROADMAP (AGE {RET_AGE})")
p1, p2 = st.columns([2, 1])
with p1:
    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(y=projection, fill='tozeroy', line=dict(color='#00E676', width=4), name="Wealth Path"))
    fig_fore.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=300)
    st.plotly_chart(fig_fore, use_container_width=True)
with p2:
    st.metric("PROJECTED ASSETS (2035)", f"${final_liquid_2035:,.0f}")
    st.metric("SAFE MONTHLY RUNWAY", f"${future_runway:,.0f}")
    st.progress(min(liquid_total/1000000, 1.0))
    st.caption("Progress to $1M Liquid Milestone")

st.divider()

# PILLAR & LEDGER
c_left, c_right = st.columns([1.2, 1])
with c_left:
    st.subheader("ASSET ALLOCATION")
    fig_pie = px.pie(df[df['Curr']>0], values='Curr', names='Pillar', hole=0.6, color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    st.plotly_chart(fig_pie, use_container_width=True)
with c_right:
    st.subheader("MASTER LEDGER")
    def color_chg(v):
        if v > 0: return 'color: #00E676'
        elif v < 0: return 'color: #FF5252'
        return 'color: white'
    st.dataframe(df[['Pillar', 'Name', 'Curr', 'Chg_%']].sort_values('Curr', ascending=False).style.format({'Curr': '${:,.0f}', 'Chg_%': '{:.2f}%'}).map(color_chg, subset=['Chg_%']), use_container_width=True, hide_index=True)
