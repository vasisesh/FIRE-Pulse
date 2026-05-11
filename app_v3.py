import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. APP CONFIG & OBSIDIAN UI ---
st.set_page_config(page_title="FIRE Pulse V3 Mastery", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 0.85rem !important; letter-spacing: 1px; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 800 !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00C853 , #B2FF59); }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINES ---
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
    hsa_p = (7750 + 8300 + 8300) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    
    return h_val, m_bal, total_401k, hsa_p

def load_data():
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
    data = [
        # PILLAR 1: Robinhood (Full Holdings)
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875151, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.228305, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMZN', 'Tkr': 'AMZN', 'Qty': 6.139473, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'ANET', 'Tkr': 'ANET', 'Qty': 6.970517, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AVGO', 'Tkr': 'AVGO', 'Qty': 17.692543, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'CRWD', 'Tkr': 'CRWD', 'Qty': 6.730194, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'DELL', 'Tkr': 'DELL', 'Qty': 7.15184, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'DIS', 'Tkr': 'DIS', 'Qty': 14.709586, 'Pillar': 'Robinhood', 'Risk': 'Mid'},
        {'Name': 'ENPH', 'Tkr': 'ENPH', 'Qty': 10.65757, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'GEV', 'Tkr': 'GEV', 'Qty': 1.207569, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'GLD', 'Tkr': 'GLD', 'Qty': 3.048105, 'Pillar': 'Robinhood', 'Risk': 'Low'},
        {'Name': 'GOOGL', 'Tkr': 'GOOGL', 'Qty': 42.149825, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'JPM', 'Tkr': 'JPM', 'Qty': 2.753308, 'Pillar': 'Robinhood', 'Risk': 'Mid'},
        {'Name': 'META', 'Tkr': 'META', 'Qty': 8.317115, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MRVL', 'Tkr': 'MRVL', 'Qty': 4.209034, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MSFT', 'Tkr': 'MSFT', 'Qty': 19.746979, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NFLX', 'Tkr': 'NFLX', 'Qty': 77.97709, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067308, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'PANW', 'Tkr': 'PANW', 'Qty': 2.468968, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'PLTR', 'Tkr': 'PLTR', 'Qty': 18.184741, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'SHOP', 'Tkr': 'SHOP', 'Qty': 42.621966, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TSLA', 'Tkr': 'TSLA', 'Qty': 16.669082, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TSM', 'Tkr': 'TSM', 'Qty': 4.457336, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TTWO', 'Tkr': 'TTWO', 'Qty': 2.719393, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'UBER', 'Tkr': 'UBER', 'Qty': 42.189843, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524888, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VRT', 'Tkr': 'VRT', 'Qty': 8.559334, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.06752957, 'Pillar': 'Robinhood', 'Risk': 'High'},
        
        # PILLAR 2: ETRADE
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE', 'Risk': 'High'},
        {'Name': 'VFIAX (ET)', 'Tkr': 'VFIAX', 'Qty': 15.115, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VTIAX (ET)', 'Tkr': 'VTIAX', 'Qty': 225.887, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        
        # PILLAR 3: Retirement
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'Auto 401k Growth', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k, 'Risk': 'Mid'},
        
        # PILLAR 5: Non-US/India & HSA
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
        {'Name': 'HSA (VTSAX)', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India', 'Risk': 'Mid'},
        
        # PILLAR 6: Cash
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
        
        # SYSTEM
        {'Name': 'Home Equity', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val - m_bal, 'Risk': 'Low'}
    ]
    df = pd.DataFrame(data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    try:
        p_df = yf.download(tkrs, period="1d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base']
            return p_df[r['Tkr']].dropna().iloc[-1] * r['Qty']
        df['Curr'] = df.apply(get_v, axis=1)
    except:
        df['Curr'] = df.get('Base', 0)
    return df

df = load_data()

# --- RISK CALCULATION ---
liquid_df = df[df['Pillar'] != 'Real Estate'] 
total_liquid = liquid_df['Curr'].sum()
high_risk_val = liquid_df[liquid_df['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk_val / total_liquid) * 100

# --- DASHBOARD UI ---
st.title("🛡️ FIRE PULSE V3: RISK MISSION CONTROL")
st.caption("Complete Asset Sync • Concentration Intelligence • Obsidian Edition")

m1, m2, m3 = st.columns(3)
m1.metric("LIQUID CAPITAL", f"${total_liquid:,.0f}")
m2.metric("TECH EXPOSURE", f"${high_risk_val:,.0f}")
m3.metric("RISK TEMPERATURE", f"{risk_score:.1f}%")

st.divider()

# --- GAUGE & INSIGHT ---
g_col, i_col = st.columns([1, 1])
with g_col:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = risk_score,
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#00E676"}, 'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 40], 'color': '#1565C0'}, 
                {'range': [40, 75], 'color': '#FF8F00'}, 
                {'range': [75, 100], 'color': '#C62828'}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'value': risk_score}
        }
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "JetBrains Mono"}, height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

with i_col:
    st.subheader("Concentration Strategy")
    if risk_score > 75:
        st.error("**Heat Level: Critical.** High tech/AI sector coupling.")
    elif risk_score > 40:
        st.warning("**Heat Level: Optimal.** Balanced growth with defensive layers.")
    else:
        st.success("**Heat Level: Defensive.** Low volatility posture.")
    
    st.info(f"Your **${total_liquid - high_risk_val:,.0f}** in 'Cooling Assets' (India, Cash, Bonds) acts as the primary firewall for your retirement roadmap.")

st.divider()

# --- PILLARS & LEDGER ---
c_left, c_right = st.columns([1, 1.5])
with c_left:
    st.subheader("Liquid Weights")
    fig_pie = px.pie(liquid_df[liquid_df['Curr']>0], values='Curr', names='Pillar', hole=0.6, color_discrete_sequence=px.colors.sequential.Tealgrn)
    st.plotly_chart(fig_pie, use_container_width=True)
with c_right:
    st.subheader("Sync Status: 100% Holdings")
    st.dataframe(df[['Pillar', 'Name', 'Curr', 'Risk']].sort_values(['Pillar', 'Curr'], ascending=False), use_container_width=True, hide_index=True)
