import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="FIRE Pulse", layout="wide", page_icon="🔥")

def fmt(v): return f"${int(round(v)):,}"

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #00d4ff; font-weight: 800; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINES ---
def get_mortgage_balance():
    orig_bal, rate, term_months, start_dt = 480000, 0.0299, 15 * 12, date(2022, 4, 1)
    months_passed = (date.today().year - start_dt.year) * 12 + (date.today().month - start_dt.month)
    if months_passed >= term_months: return 0
    m_rate = rate / 12
    return max(0, orig_bal * ((1 + m_rate)**term_months - (1 + m_rate)**months_passed) / ((1 + m_rate)**term_months - 1))

def get_home_value():
    orig_price, start_dt = 600000, date(2022, 4, 1)
    yrs = (date.today() - start_dt).days / 365.25
    return orig_price * (1.02 ** yrs)

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv("portfolio.csv", on_bad_lines='skip')
    df.columns = [c.strip() for c in df.columns]
    
    # Fill empty categories and force numeric
    df['Category'] = df['Category'].fillna('Uncategorized').astype(str)
    for col in ['Quantity', 'Purchase Price', 'Annual_Contribution']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    tickers = [t for t in df['Ticker'].unique() if str(t).upper() not in ['CASH', 'INDIA_ASSETS', 'NAN']]
    live_prices = {}
    if tickers:
        try:
            sync = yf.download(tickers, period="1d", interval="1m", progress=False)
            if not sync.empty: live_prices = sync['Close'].iloc[-1].to_dict()
        except: pass

    def calc_row(row):
        t = str(row['Ticker']).strip().upper()
        p = live_prices.get(t, row.get('Purchase Price', 0))
        q = row.get('Quantity', 0)
        if t in ['CASH', 'INDIA_ASSETS']: return row.get('Purchase Price', 0)
        
        # Bi-weekly DCA
        if row.get('Annual_Contribution', 0) > 0:
            try:
                dt = datetime.strptime(str(row.get('Start_Date', '')).strip(), '%m/%d/%y').date()
                pay_periods = (date.today() - dt).days // 14
                if pay_periods > 0 and p > 0:
                    q += (row['Annual_Contribution'] / 26 * pay_periods) / p
            except: pass
        return q * p

    df['Current Value'] = df.apply(calc_row, axis=1)
    return df

# --- 3. UI ---
try:
    df = load_data()
    invested_total = df['Current Value'].sum()
    equity = get_home_value() - get_mortgage_balance()
    
    st.title("🔥 FIRE Pulse")
    
    # TOP METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("🌐 NET WORTH", fmt(invested_total + equity))
    c2.metric("📈 INVESTMENTS", fmt(invested_total))
    c3.metric("🏠 HOME EQUITY", fmt(equity))
    
    st.divider()

    # PILLAR METRICS (BROADER SEARCH)
    m = st.columns(5)
    pillars = [('Robinhood', 'Robin'), ('ETRADE', 'ETRADE'), ('Retirement', 'Retir'), ('College', 'Coll'), ('India Assets', 'India')]
    for i, (label, search) in enumerate(pillars):
        val = df[df['Category'].str.contains(search, case=False)]['Current Value'].sum()
        m[i].metric(label, fmt(val))

    st.divider()
    st.write("### 🏗️ Complete Asset Ledger")
    st.dataframe(df[df['Current Value'] > 0][['Ticker', 'Category', 'Current Value']].sort_values('Current Value', ascending=False).style.format({'Current Value': fmt}), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
