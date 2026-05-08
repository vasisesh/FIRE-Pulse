import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="FIRE Pulse", layout="wide", page_icon="🔥")

def fmt(v): return f"${int(round(v)):,}"

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #00d4ff; font-weight: 800; font-size: 2.2rem !important; }
    .stDataFrame { border: 1px solid #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE FIRE ENGINES ---
def get_mortgage_balance():
    # Fixed parameters from your 15yr 2.99% loan
    orig_bal = 480000
    rate = 0.0299
    term_months = 15 * 12
    start_dt = date(2022, 4, 1)
    
    months_passed = (date.today().year - start_dt.year) * 12 + (date.today().month - start_dt.month)
    if months_passed >= term_months: return 0
    
    m_rate = rate / 12
    balance = orig_bal * ((1 + m_rate)**term_months - (1 + m_rate)**months_passed) / ((1 + m_rate)**term_months - 1)
    return max(0, balance)

def get_home_value():
    orig_price = 600000
    start_dt = date(2022, 4, 1)
    yrs = (date.today() - start_dt).days / 365.25
    return orig_price * (1.02 ** yrs) # 2% Appreciation

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv("portfolio.csv", on_bad_lines='skip')
    df.columns = [c.strip() for c in df.columns]
    
    # Force numerical types to prevent crashes
    for col in ['Quantity', 'Purchase Price', 'Annual_Contribution']:
        if col in df.columns:
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
        
        # DCA Logic
        if 'Annual_Contribution' in row and row['Annual_Contribution'] > 0:
            try:
                dt_str = str(row.get('Start_Date', '')).strip()
                for f in ('%m/%d/%y', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(dt_str, f).date()
                        periods = (date.today() - dt).days // 14
                        if periods > 0 and p > 0:
                            q += (row['Annual_Contribution'] / 26 * periods) / p
                        break
                    except: continue
            except: pass
        return q * p

    df['Current Value'] = df.apply(calc_row, axis=1)
    return df

# --- 3. DASHBOARD UI ---
try:
    df = load_data()
    invested_total = df['Current Value'].sum()
    home_val = get_home_value()
    debt_val = get_mortgage_balance()
    equity = home_val - debt_val
    net_worth = invested_total + equity

    st.title("🔥 FIRE Pulse")
    st.caption(f"Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Fixed 15Y Mortgage @ 2.99%")

    # HIGH LEVEL NET WORTH
    nw1, nw2, nw3 = st.columns(3)
    nw1.metric("🌐 TOTAL NET WORTH", fmt(net_worth))
    nw2.metric("📈 INVESTED ASSETS", fmt(invested_total))
    nw3.metric("🏠 HOME EQUITY", fmt(equity))
    
    st.divider()

    # PILLAR SUMMARY
    m = st.columns(5)
    pillars = ['Robinhood', 'ETRADE', 'Retirement', 'College Fund', 'Non-US Assets']
    for i, p_name in enumerate(pillars):
        val = df[df['Category'].fillna('').str.contains(p_name, case=False)]['Current Value'].sum()
        m[i].metric(p_name.replace(' Assets', ''), fmt(val))

    st.divider()
    
    st.write("### 🏗️ Live Asset Ledger")
    disp = df[df['Current Value'] > 0][['Ticker', 'Category', 'Current Value']]
    st.dataframe(disp.sort_values('Current Value', ascending=False).style.format({'Current Value': fmt}), use_container_width=True)

except Exception as e:
    st.error(f"Syncing Data... (System Note: {e})")
