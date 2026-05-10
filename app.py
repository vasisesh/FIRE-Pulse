import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="FIRE Pulse | Robinhood Core", layout="wide", page_icon="🔥")

def fmt(v): return f"${int(round(v)):,}"

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #00d4ff; font-weight: 800; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=300)
def load_robinhood_data():
    # Load and clean headers
    df = pd.read_csv("portfolio.csv", on_bad_lines='skip')
    df.columns = [c.strip() for c in df.columns]
    
    # STAGE 1: Strict Filtering for Robinhood only
    df = df[df['Category'].fillna('').str.contains('Robinhood', case=False)].copy()
    
    # STAGE 2: Force numeric types for calculations
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
    df['Purchase Price'] = pd.to_numeric(df['Purchase Price'], errors='coerce').fillna(0)

    # STAGE 3: Live Price Sync
    tickers = [t for t in df['Ticker'].unique() if str(t).upper() not in ['CASH', 'NAN']]
    live_prices = {}
    if tickers:
        try:
            sync = yf.download(tickers, period="1d", interval="1m", progress=False)
            if not sync.empty:
                live_prices = sync['Close'].iloc[-1].to_dict()
        except: pass

    # STAGE 4: Valuation
    def calc_val(row):
        t = str(row['Ticker']).strip().upper()
        p = live_prices.get(t, row['Purchase Price'])
        return row['Quantity'] * p

    df['Current Value'] = df.apply(calc_val, axis=1)
    return df

# --- 3. DASHBOARD UI ---
try:
    df = load_robinhood_data()
    total_val = df['Current Value'].sum()

    st.title("🔥 FIRE Pulse: Robinhood Core")
    
    # TOP SUMMARY
    st.metric("📦 TOTAL ROBINHOOD ASSETS", fmt(total_val))
    st.divider()

    # TWO-COLUMN DATA VIEW
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.write("### 🏗️ All Robinhood Holdings")
        disp_all = df[df['Current Value'] > 0][['Ticker', 'Account Type', 'Current Value']]
        st.dataframe(
            disp_all.sort_values('Current Value', ascending=False).style.format({'Current Value': fmt}),
            use_container_width=True,
            hide_index=True
        )

    with right_col:
        st.write("### 🏆 Top 10 Positions")
        top_10 = df.nlargest(10, 'Current Value')[['Ticker', 'Current Value']]
        st.dataframe(
            top_10.style.format({'Current Value': fmt}),
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Waiting for Data Connection... (System Note: {e})")
