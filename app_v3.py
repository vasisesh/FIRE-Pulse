import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="FIRE Pulse V3", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: monospace; }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC ENGINES ---
def get_dynamics():
    now = datetime.now()
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    
    biweekly = max(0, (now - datetime(2026, 1, 1)).days // 14)
    ret_auto = biweekly * 1269.23
    hsa_auto = (24350) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, ret_auto, hsa_auto

def load_v3_data():
    h_val, m_bal, ret_p, hsa_p = get_dynamics()
    data = [
        # Robinhood - High Risk
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.87, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.22, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMZN', 'Tkr': 'AMZN', 'Qty': 6.13, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.06, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NFLX', 'Tkr': 'NFLX', 'Qty': 77.97, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.52, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.067, 'Pillar': 'Robinhood', 'Risk': 'High'},
        # ETRADE - Mid Risk
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.77, 'Pillar': 'ETRADE', 'Risk': 'High'},
        # Retirement & Assets
        {'Name': 'VTSAX (Roth)', 'Tkr': 'VTSAX', 'Qty': 3318.5, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'Auto 401k', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': ret_p, 'Risk': 'Mid'},
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
        {'Name': 'HSA', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India', 'Risk': 'Mid'},
        {'Name': 'HYSA', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
        {'Name': 'Home Equity', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val - m_bal, 'Risk': 'Low'}
    ]
    df = pd.DataFrame(data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    try:
        p_df = yf.download(tkrs, period="1d", progress=False)['Close']
        df['Curr'] = df.apply(lambda r: p_df[r['Tkr']].iloc[-1] * r['Qty'] if r['Tkr'] != 'FIXED' else r['Base'], axis=1)
    except:
        df['Curr'] = df.apply(lambda r: r.get('Base', 100), axis=1) # Fallback
    return df

df = load_v3_data()
liquid_df = df[df['Pillar'] != 'Real Estate']
total_liq = liquid_df['Curr'].sum()
high_risk_val = liquid_df[liquid_df['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk_val / total_liq) * 100

# --- 3. UI ---
st.title("🛡️ FORTRESS MISSION CONTROL V3")
st.caption("Active Concentration & Multi-Pillar Sync")

m1, m2, m3 = st.columns(3)
m1.metric("LIQUID CAPITAL", f"${total_liq:,.0f}")
m2.metric("TECH EXPOSURE", f"${high_risk_val:,.0f}")
m3.metric("RISK TEMP", f"{risk_score:.1f}%")

st.divider()

g_col, i_col = st.columns([1, 1])
with g_col:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=risk_score,
        gauge={'bar':{'color':"#00E676"},'steps':[{'range':[0,40],'color':'#1565C0'},{'range':[40,75],'color':'#FF8F00'},{'range':[75,100],'color':'#C62828'}]}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=250)
    st.plotly_chart(fig, use_container_width=True)
with i_col:
    st.subheader("Concentration Status")
    if risk_score > 70: st.error("Critical Tech Coupling Detected.")
    else: st.success("Portfolio within optimal risk bands.")

st.subheader("Asset Ledger")
st.dataframe(df[['Pillar', 'Name', 'Curr', 'Risk']].sort_values(['Pillar', 'Curr'], ascending=False), use_container_width=True, hide_index=True)
