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
    
    # Comprehensive Ticker List from provided screenshot
    data = [
        # PILLAR 1: Robinhood (Taxable Brokerage)
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875151, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.228305, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMZN', 'Tkr': 'AMZN', 'Qty': 6.139473, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'ANET', 'Tkr': 'ANET', 'Qty': 5.85366 + 1.116857, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AVGO', 'Tkr': 'AVGO', 'Qty': 16.015482 + 1.677061, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'CRWD', 'Tkr': 'CRWD', 'Qty': 6.730194, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'DELL', 'Tkr': 'DELL', 'Qty': 7.15184, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'DIS', 'Tkr': 'DIS', 'Qty': 14.709586, 'Pillar': 'Robinhood', 'Risk': 'Mid'},
        {'Name': 'ENPH', 'Tkr': 'ENPH', 'Qty': 10.65757, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'GEV', 'Tkr': 'GEV', 'Qty': 0.985332 + 0.222237, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'GLD', 'Tkr': 'GLD', 'Qty': 3.048105, 'Pillar': 'Robinhood', 'Risk': 'Low'},
        {'Name': 'GOOGL', 'Tkr': 'GOOGL', 'Qty': 42.149825, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'JPM', 'Tkr': 'JPM', 'Qty': 2.753308, 'Pillar': 'Robinhood', 'Risk': 'Mid'},
        {'Name': 'META', 'Tkr': 'META', 'Qty': 8.317115, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MRVL', 'Tkr': 'MRVL', 'Qty': 2.385513 + 1.823521, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MSFT', 'Tkr': 'MSFT', 'Qty': 19.746979, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NFLX', 'Tkr': 'NFLX', 'Qty': 77.97709, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067308, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'PANW', 'Tkr': 'PANW', 'Qty': 2.468968, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'PLTR', 'Tkr': 'PLTR', 'Qty': 12.746453 + 5.438288, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'SHOP', 'Tkr': 'SHOP', 'Qty': 42.621966, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TSLA', 'Tkr': 'TSLA', 'Qty': 16.669082, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TSM', 'Tkr': 'TSM', 'Qty': 4.457336, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'TTWO', 'Tkr': 'TTWO', 'Qty': 2.719393, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'UBER', 'Tkr': 'UBER', 'Qty': 42.189843, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524888, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VRT', 'Tkr': 'VRT', 'Qty': 7.719113 + 0.840221, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.06752957, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'CRDO', 'Tkr': 'CRDO', 'Qty': 8.3776, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'CRWV', 'Tkr': 'CRWV', 'Qty': 9, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'FLEX', 'Tkr': 'FLEX', 'Qty': 10, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'HOOD', 'Tkr': 'HOOD', 'Qty': 8, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'INOD', 'Tkr': 'INOD', 'Qty': 17.750223, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'LRCX', 'Tkr': 'LRCX', 'Qty': 9.22168, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'MU', 'Tkr': 'MU', 'Qty': 6.94118, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NBIS', 'Tkr': 'NBIS', 'Qty': 1, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'OKLO', 'Tkr': 'OKLO', 'Qty': 1.184033, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'PSI', 'Tkr': 'PSI', 'Qty': 2.491277, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'RDDT', 'Tkr': 'RDDT', 'Qty': 4.992676, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'SNDK', 'Tkr': 'SNDK', 'Qty': 4.347362, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'STX', 'Tkr': 'STX', 'Qty': 4.744995, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'WDC', 'Tkr': 'WDC', 'Qty': 8.910648, 'Pillar': 'Robinhood', 'Risk': 'High'},
        
        # PILLAR 2: ETRADE
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE', 'Risk': 'High'},
        {'Name': 'VFIAX (ET)', 'Tkr': 'VFIAX', 'Qty': 15.115, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VTIAX (ET)', 'Tkr': 'VTIAX', 'Qty': 225.887, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        
        # PILLAR 3: Retirement
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'FELG (Roth IRA)', 'Tkr': 'FELG', 'Qty': 386, 'Pillar': 'Retirement', 'Risk': 'High'},
        {'Name': 'WFSPX (Roth 401k)', 'Tkr': 'WFSPX', 'Qty': 157.092, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'JLGMX (Roth 401k)', 'Tkr': 'JLGMX', 'Qty': 641.562, 'Pillar': 'Retirement', 'Risk': 'High'},
        {'Name': 'Auto 401k Growth', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k, 'Risk': 'Mid'},
        
        # PILLAR 4: College Fund
        {'Name': 'VTSAX (College)', 'Tkr': 'VTSAX', 'Qty': 209.296, 'Pillar': 'College Fund', 'Risk': 'Mid'},
        {'Name': 'VTI (College)', 'Tkr': 'VTI', 'Qty': 222.203, 'Pillar': 'College Fund', 'Risk': 'Mid'},
        
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
        p_df = yf.download(tkrs, period="5d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base'], r['Base']
            ticker_data = p_df[r['Tkr']].dropna()
            curr_p = ticker_data.iloc[-1]
            prev_p = ticker_data.iloc[-2] if len(ticker_data) > 1 else curr_p
            return curr_p * r['Qty'], prev_p * r['Qty']
        df[['Curr', 'Prev']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr'] = df.apply(lambda r: r.get('Base', 0), axis=1)
        df['Prev'] = df['Curr']
    
    df['Chg_$'] = (df['Curr'] - df['Prev']).fillna(0)
    df['Chg_%'] = ((df['Curr'] / df['Prev'] - 1) * 100).fillna(0)
    return df

df = load_all_data()

# --- 4. CALCULATIONS ---
nw_curr = df['Curr'].sum()
liquid_total = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()
high_risk_val = df[df['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk_val / liquid_total) * 100
fire_progress = min(liquid_total / FIRE_TARGET, 1.0)
nw_progress = min(nw_curr / NW_TARGET, 1.0)

# --- 5. UI DASHBOARD ---
st.title("🛡️ THE VASIREDDY FORTRESS V3")
st.caption("Full Asset Inventory • Precision Risk Sync • Obsidian Edition")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL NET WORTH", f"${nw_curr:,.0f}", delta=f"${df['Chg_$'].sum():,.2f}")
m2.metric("LIQUID ASSETS", f"${liquid_total:,.0f}")
m3.metric("TECH CONCENTRATION", f"{risk_score:.1f}%")

st.divider()

# --- GAUGE & MISSION ---
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
    st.info(f"Robinhood Total: **${df[df['Pillar']=='Robinhood']['Curr'].sum():,.0f}**")

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
def style_ledger(v):
    if isinstance(v, (int, float)):
        if v > 0: return 'color: #00E676'
        elif v < 0: return 'color: #FF5252'
    return 'color: #E0E0E0'

st.dataframe(
    df[['Pillar', 'Name', 'Curr', 'Chg_$', 'Chg_%']]
    .sort_values(['Pillar', 'Curr'], ascending=False)
    .style.format({'Curr': '${:,.2f}', 'Chg_$': '${:,.2f}', 'Chg_%': '{:,.2f}%'})
    .map(style_ledger, subset=['Chg_$', 'Chg_%']),
    use_container_width=True, hide_index=True
)
