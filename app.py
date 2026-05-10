import streamlit as st
import pandas as pd
import yfinance as yf

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
    df = pd.read_csv("portfolio.csv", on_bad_lines='skip')
    # Clean all column names and string values of hidden spaces
    df.columns = [c.strip() for c in df.columns]
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Strict Robinhood Filter (now space-proof)
    df = df[df['Category'].fillna('').str.contains('Robinhood', case=False)].copy()
    
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
    df['Purchase Price'] = pd.to_numeric(df['Purchase Price'], errors='coerce').fillna(0)

    # Price Sync
    tickers = [t for t in df['Ticker'].unique() if str(t).upper() not in ['CASH', 'NAN']]
    live_prices = {}
    if tickers:
        try:
            sync = yf.download(tickers, period="1d", interval="1m", progress=False)
            if not sync.empty:
                live_prices = sync['Close'].iloc[-1].to_dict()
        except: pass

    df['Current Value'] = df.apply(lambda r: r['Quantity'] * live_prices.get(str(r['Ticker']).upper(), r['Purchase Price']), axis=1)
    return df

# --- 3. UI ---
try:
    df = load_robinhood_data()
    
    st.title("🔥 FIRE Pulse: Robinhood Core")
    # This total is the sum of every row that passed the 'Robinhood' filter
    st.metric("📦 TOTAL ROBINHOOD ASSETS", fmt(df['Current Value'].sum()))
    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.write(f"### 🏗️ All Robinhood Holdings ({len(df)} positions)")
        disp = df[df['Current Value'] > 0][['Ticker', 'Account Type', 'Current Value']]
        
        # FIX: Added 'height=None' to force the table to show all rows without a scrollbar
        st.dataframe(
            disp.sort_values('Current Value', ascending=False).style.format({'Current Value': fmt}),
            use_container_width=True, 
            hide_index=True,
            height=None 
        )

    with right:
        st.write("### 🏆 Top 10 Positions")
        top_10 = df.groupby('Ticker')['Current Value'].sum().nlargest(10).reset_index()
        st.dataframe(
            top_10.style.format({'Current Value': fmt}),
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Syncing Error: {e}")
