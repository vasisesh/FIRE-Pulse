import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. APP CONFIG & OBSIDIAN UI ---
st.set_page_config(page_title="FIRE Pulse V4: Mastery", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 0.85rem !important; letter-spacing: 1px; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 800 !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00C853 , #B2FF59); }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION & TARGETS ---
FIRE_TARGET = 1000000
NW_TARGET = 2500000

# --- 3. DYNAMIC VALUE ENGINES ---
def calculate_dynamic_values():
    now = datetime.now()
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    
    biweekly_periods = max(0, (now - datetime(2026, 1, 1)).days // 14)
    total_401k = biweekly_periods * 1269.23
    hsa_p = (24350) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, total_401k, hsa_p

def load_all_data():
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
    
    data = [
        # PILLAR 1: Robinhood (Consolidated Master Inventory - $150k Sync)
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.228, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMZN', 'Tkr': 'AMZN', 'Qty': 6.139, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'ANET', 'Tkr': 'ANET', 'Qty': 6.970, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AVGO', 'Tkr': 'AVGO', 'Qty': 17.692, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'CRWD', 'Tkr': 'CRWD', 'Qty': 6.730, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'DELL', 'Tkr': 'DELL', 'Qty': 7.151, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'ENPH', 'Tkr': 'ENPH', 'Qty': 10.657, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'GOOGL', 'Tkr': 'GOOGL', 'Qty': 42.149, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'META', 'Tkr': 'META', 'Qty': 8.317, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MSFT', 'Tkr': 'MSFT', 'Qty': 19.746, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NFLX', 'Tkr': 'NFLX', 'Qty': 77.977, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'SHOP', 'Tkr': 'SHOP', 'Qty': 42.621, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'UBER', 'Tkr': 'UBER', 'Qty': 42.189, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.067529, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'LRCX', 'Tkr': 'LRCX', 'Qty': 9.221, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MU', 'Tkr': 'MU', 'Qty': 6.941, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'WDC', 'Tkr': 'WDC', 'Qty': 8.910, 'Pillar': 'Robinhood', 'Risk': 'High'},
        
        # PILLAR 2: ETRADE
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE', 'Risk': 'High'},
        
        # PILLAR 3: Retirement
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'Auto 401k Growth', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k, 'Risk': 'Mid'},
        
        # PILLAR 5: Non-US/India & HSA
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
        {'Name': 'HSA (Invested)', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India', 'Risk': 'Mid'},
        
        # PILLAR 6: Cash
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
        
        # SYSTEM
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val, 'Risk': 'Low'},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base': -m_bal, 'Risk': 'Low'}
    ]
    df = pd.DataFrame(data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    
    try:
        # Optimization: Fetch 1 day of data for speed and reliability
        p_df = yf.download(tkrs, period="1d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base']
            if r['Tkr'] in p_df.columns:
                val = p_df[r['Tkr']].dropna().iloc[-1]
                return val * r['Qty']
            return 0
        df['Curr'] = df.apply(get_v, axis=1)
    except:
        # Fail-safe: Ensure baseline numbers show up even if yfinance is down
        df['Curr'] = df.apply(lambda r: r.get('Base', 100) if r['Tkr'] == 'FIXED' else 0, axis=1)
    
    return df

df = load_all_data()

# --- 4. CALCULATIONS ---
nw_curr = df['Curr'].sum()
liquid_total = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()
high_risk_val = df[df['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk_val / liquid_total) * 100 if liquid_total > 0 else 0
fire_progress = min(liquid_total / FIRE_TARGET, 1.0)
nw_progress = min(nw_curr / NW_TARGET, 1.0)

# --- 5. UI DASHBOARD ---
st.title("🛡️ THE VASIREDDY FORTRESS V4")
st.caption("Deployment Verified • High-Precision Sync • Obsidian UI")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL NET WORTH", f"${nw_curr:,.0f}")
m2.metric("LIQUID ASSETS", f"${liquid_total:,.0f}")
m3.metric("TECH CONCENTRATION", f"{risk_score:.1f}%")

st.divider()

# --- RISK GAUGE & MISSION ---
g_col, m_col = st.columns([1, 1])
with g_col:
    st.subheader("RISK TEMPERATURE")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = risk_score,
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': "#00E676"}, 'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(21, 101, 192, 0.3)'},
                {'range': [40, 75], 'color': 'rgba(255, 143, 0, 0.3)'},
                {'range': [75, 100], 'color': 'rgba(198, 40, 40, 0.3)'}
            ]
        }
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=280)
    st.plotly_chart(fig_gauge, use_container_width=True)

with m_col:
    st.subheader("CORE MISSION PROGRESS")
    st.write(f"**FIRE Goal ($1.0M Liquid):** {fire_progress:.1%}")
    st.progress(fire_progress)
    st.write(f"**Net Worth Goal ($2.5M Total):** {nw_progress:.1%}")
    st.progress(nw_progress)
    st.info(f"Robinhood Verification: **${df[df['Pillar']=='Robinhood']['Curr'].sum():,.0f}**")

st.divider()

# --- PILLAR PROGRESS ---
c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("Asset Distribution")
    fig_pie = px.pie(df[df['Curr']>0], values='Curr', names='Pillar', hole=0.6, color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)
with c2:
    st.subheader("Pillar Progress Summaries")
    p_sum = df.groupby('Pillar')['Curr'].sum()
    for p in ['Robinhood', 'ETRADE', 'Retirement', 'College Fund', 'Non-US/India', 'Cash']:
        val = p_sum.get(p, 0)
        st.markdown(f"**{p}** <span style='float:right; color:#00E676;'>${val:,.0f}</span>", unsafe_allow_html=True)
        st.progress(min(val/1200000, 1.0))

st.divider()

# --- MASTER LEDGER ---
st.subheader("MASTER ASSET LEDGER")
st.dataframe(
    df[['Pillar', 'Name', 'Curr']].sort_values(['Pillar', 'Curr'], ascending=False),
    use_container_width=True, hide_index=True
)
