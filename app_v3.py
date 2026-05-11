import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. APP CONFIG & OBSIDIAN UI ---
st.set_page_config(page_title="FIRE Pulse V3.1: Tax Alpha", layout="wide")

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
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: 'JetBrains Mono', monospace !important; }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE TICKER MAPPER (Crucial for CSV Sync) ---
# This maps the "Instrument" names in your CSV to live market Tickers
TICKER_MAP = {
    'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'DOGE': 'DOGE-USD',
    'META': 'META', 'NVDA': 'NVDA', 'TSLA': 'TSLA', 'AMZN': 'AMZN',
    'AAPL': 'AAPL', 'NFLX': 'NFLX', 'GOOGL': 'GOOGL', 'SHOP': 'SHOP',
    'AMD': 'AMD', 'AVGO': 'AVGO', 'VGT': 'VGT', 'PLTR': 'PLTR',
    'CRWD': 'CRWD', 'ANET': 'ANET', 'LRCX': 'LRCX', 'MU': 'MU',
    'WDC': 'WDC', 'VRT': 'VRT', 'PANW': 'PANW', 'ENPH': 'ENPH'
}

# --- 3. ENGINES ---
@st.cache_data
def process_tax_lots(file_path):
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
        df = df[df['Trans Code'].isin(['Buy', 'Sell', 'Reward'])].copy()
        
        def clean_val(x):
            if isinstance(x, str):
                return float(x.replace('$', '').replace('(', '-').replace(')', '').replace(',', ''))
            return x

        df['Quantity'] = df['Quantity'].apply(clean_val).fillna(0)
        df['Amount'] = df['Amount'].apply(clean_val).fillna(0)
        df['Activity Date'] = pd.to_datetime(df['Activity Date'])
        
        # Calculate current holdings per instrument
        # Note: Amount is negative for Buys in RH CSVs
        inventory = df.groupby('Instrument').agg({
            'Quantity': 'sum',
            'Amount': 'sum',
            'Activity Date': 'max'
        }).reset_index()
        
        inventory['Days_Held'] = (datetime.now() - inventory['Activity Date']).dt.days
        return inventory, df
    except Exception as e:
        st.error(f"CSV Parse Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_dynamics():
    now = datetime.now()
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    biweekly = max(0, (now - datetime(2026, 1, 1)).days // 14)
    total_401k = biweekly * 1269.23
    hsa_p = 24350 + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, total_401k, hsa_p

# --- 4. LOAD & MERGE ---
inventory, raw_tx = process_tax_lots('cad10a93-0560-50ad-b5f5-9e36ffd4bc9c (1).csv')
h_val, m_bal, ret_p, hsa_p = get_dynamics()

manual_assets = [
    {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
    {'Name': 'VTSAX (Roth)', 'Tkr': 'VTSAX', 'Qty': 3318.5, 'Pillar': 'Retirement', 'Risk': 'Mid'},
    {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
    {'Name': 'HSA', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India', 'Risk': 'Mid'},
    {'Name': 'HYSA', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
    {'Name': 'Home Equity', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val - m_bal, 'Risk': 'Low'}
]

# Convert CSV Inventory to app format
for _, row in inventory.iterrows():
    if row['Quantity'] > 0.001: # Filter out sold positions
        manual_assets.append({
            'Name': row['Instrument'],
            'Tkr': TICKER_MAP.get(row['Instrument'], row['Instrument']),
            'Qty': row['Quantity'],
            'Pillar': 'Robinhood',
            'Risk': 'High'
        })

df_final = pd.DataFrame(manual_assets)
tkrs = [t for t in df_final['Tkr'].unique() if t != 'FIXED']

try:
    p_df = yf.download(tkrs, period="5d", progress=False)['Close']
    df_final['Curr'] = df_final.apply(lambda r: p_df[r['Tkr']].iloc[-1] * r['Qty'] if r['Tkr'] != 'FIXED' else r['Base'], axis=1)
except:
    df_final['Curr'] = df_final.get('Base', 0)

# --- 5. UI ---
liquid_total = df_final[df_final['Pillar'] != 'Real Estate']['Curr'].sum()
high_risk = df_final[df_final['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk / liquid_total) * 100

st.title("🛡️ FORTRESS V3.1: TAX ALPHA SYNC")
st.caption(f"CSV Processed: {len(inventory)} Instruments Syncing...")

m1, m2, m3 = st.columns(3)
m1.metric("LIQUID CAPITAL", f"${liquid_total:,.0f}")
m2.metric("TECH CONCENTRATION", f"{risk_score:.1f}%")
m3.metric("CSV SYNC STATUS", "✅ ACTIVE")

st.divider()

col_g, col_l = st.columns([1, 1.5])
with col_g:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=risk_score,
        gauge={'bar':{'color':"#00E676"}, 'steps':[{'range':[0,40],'color':'#1565C0'},{'range':[75,100],'color':'#C62828'}]}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=250)
    st.plotly_chart(fig, use_container_width=True)

with col_l:
    st.subheader("Asset Ledger (CSV Data)")
    st.dataframe(df_final[['Pillar', 'Name', 'Qty', 'Curr']].sort_values('Curr', ascending=False), use_container_width=True, hide_index=True)
