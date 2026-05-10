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
    # Load raw data
    df = pd.read_csv("portfolio.csv", on_bad_lines='skip')
    
    # Standardize column names by removing spaces and forcing lowercase for matching
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Filter for Robinhood rows before doing anything else
    # We use 'category' because we forced the header to lowercase
    df = df[df['category'].fillna('').str.contains('Robinhood', case=False)].copy()
    
    # Force the core columns to be clean and correctly typed
    df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
    df['purchase price'] = pd.to_numeric(df['purchase price'], errors='coerce').fillna(0)
    df['account type'] = df['account type'].fillna('Unknown').astype(str).str.strip()

    # Price Sync
    tickers = [t for t in df['ticker'].unique() if t not in ['CASH', 'NAN']]
    live_prices = {}
    if tickers:
        try:
            sync = yf.download(tickers, period="1d", interval="1m", progress=False)
            if not sync.empty:
                live_prices = sync['Close'].iloc[-1].to_dict()
        except: pass

    # Valuation Logic
    df['Current Value'] = df.apply(lambda r: r['quantity'] * live_prices.get(r['ticker'], r['purchase price']), axis=1)
    return df

# --- 3. UI ---
try:
    df = load_robinhood_data()
    
    st.title("🔥 FIRE Pulse: Robinhood Core")
    total_rh = df['Current Value'].sum()
    st.metric("📦 TOTAL ROBINHOOD ASSETS", fmt(total_rh))
    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.write(f"### 🏗️ All Robinhood Holdings ({len(df)} positions)")
        # We use the lowercase names to match our cleaned dataframe
        disp = df[df['Current Value'] > 0][['ticker', 'account type', 'Current Value']]
        # Rename columns back to 'Pretty' versions for the UI
        disp.columns = ['Ticker', 'Type', 'Current Value']
        
        st.dataframe(
            disp.sort_values('Current Value', ascending=False).style.format({'Current Value': fmt}),
            use_container_width=True, 
            hide_index=True,
            height=None 
        )

    with right:
        st.write("### 🏆 Top 10 Positions")
        top_10 = df.groupby('ticker')['Current Value'].sum().nlargest(10).reset_index()
        top_10.columns = ['Ticker', 'Current Value']
        st.dataframe(
            top_10.style.format({'Current Value': fmt}),
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Syncing Error: {e}. Please check your portfolio.csv headers.")
