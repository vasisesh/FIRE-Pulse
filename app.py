import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #d1d5db; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    [data-testid="stMetricLabel"] { color: #4b5563 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800 !important; }
    .main { background-color: #0e1117; }
    /* FIRE Progress Bar Color */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #008080 , #00ffcc); }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
FIRE_TARGET = 1000000
COLLEGE_TARGET = 125000
COLLEGE_TARGET_YEAR = 2030

# --- ENGINES ---
def calculate_real_estate():
    start_date = datetime(2022, 4, 1)
    purchase_price = 600000
    mortgage_start = 480000
    now = datetime.now()
    delta = relativedelta(now, start_date)
    months_passed = delta.years * 12 + delta.months
    
    # Mortgage Balance (2.99%, 15yr)
    r, n = 0.0299 / 12, 15 * 12
    m_pay = mortgage_start * (r * (1 + r)**n) / ((1 + r)**n - 1)
    balance = mortgage_start * (1 + r)**months_passed - (m_pay / r) * ((1 + r)**months_passed - 1)
    
    # Appreciation (2.5% Annual)
    growth_rate = (1 + 0.025)**(1/12) - 1
    current_house_val = purchase_price * (1 + growth_rate)**months_passed
    
    return current_house_val, balance

def load_all_pillars():
    h_val, m_bal = calculate_real_estate()
    data = [
        # PILLAR 1: Robinhood
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875151, 'Pillar': 'Robinhood'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.228305, 'Pillar': 'Robinhood'},
        {'Name': 'AMZN', 'Tkr': 'AMZN', 'Qty': 6.139473, 'Pillar': 'Robinhood'},
        {'Name': 'ANET', 'Tkr': 'ANET', 'Qty': 6.970517, 'Pillar': 'Robinhood'},
        {'Name': 'AVGO', 'Tkr': 'AVGO', 'Qty': 17.692543, 'Pillar': 'Robinhood'},
        {'Name': 'CRWD', 'Tkr': 'CRWD', 'Qty': 6.730194, 'Pillar': 'Robinhood'},
        {'Name': 'DELL', 'Tkr': 'DELL', 'Qty': 7.15184, 'Pillar': 'Robinhood'},
        {'Name': 'DIS', 'Tkr': 'DIS', 'Qty': 14.709586, 'Pillar': 'Robinhood'},
        {'Name': 'ENPH', 'Tkr': 'ENPH', 'Qty': 10.65757, 'Pillar': 'Robinhood'},
        {'Name': 'GEV', 'Tkr': 'GEV', 'Qty': 1.207569, 'Pillar': 'Robinhood'},
        {'Name': 'GLD', 'Tkr': 'GLD', 'Qty': 3.048105, 'Pillar': 'Robinhood'},
        {'Name': 'GOOGL', 'Tkr': 'GOOGL', 'Qty': 42.149825, 'Pillar': 'Robinhood'},
        {'Name': 'JPM', 'Tkr': 'JPM', 'Qty': 2.753308, 'Pillar': 'Robinhood'},
        {'Name': 'META', 'Tkr': 'META', 'Qty': 8.317115, 'Pillar': 'Robinhood'},
        {'Name': 'MRVL', 'Tkr': 'MRVL', 'Qty': 4.209034, 'Pillar': 'Robinhood'},
        {'Name': 'MSFT', 'Tkr': 'MSFT', 'Qty': 19.746979, 'Pillar': 'Robinhood'},
        {'Name': 'NFLX', 'Tkr': 'NFLX', 'Qty': 77.97709, 'Pillar': 'Robinhood'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067308, 'Pillar': 'Robinhood'},
        {'Name': 'PANW', 'Tkr': 'PANW', 'Qty': 2.468968, 'Pillar': 'Robinhood'},
        {'Name': 'PLTR', 'Tkr': 'PLTR', 'Qty': 18.184741, 'Pillar': 'Robinhood'},
        {'Name': 'SHOP', 'Tkr': 'SHOP', 'Qty': 42.621966, 'Pillar': 'Robinhood'},
        {'Name': 'TSLA', 'Tkr': 'TSLA', 'Qty': 16.669082, 'Pillar': 'Robinhood'},
        {'Name': 'TSM', 'Tkr': 'TSM', 'Qty': 4.457336, 'Pillar': 'Robinhood'},
        {'Name': 'TTWO', 'Tkr': 'TTWO', 'Qty': 2.719393, 'Pillar': 'Robinhood'},
        {'Name': 'UBER', 'Tkr': 'UBER', 'Qty': 42.189843, 'Pillar': 'Robinhood'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524888, 'Pillar': 'Robinhood'},
        {'Name': 'VRT', 'Tkr': 'VRT', 'Qty': 8.559334, 'Pillar': 'Robinhood'},
        {'Name': 'CRDO', 'Tkr': 'CRDO', 'Qty': 8.3776, 'Pillar': 'Robinhood'},
        {'Name': 'CRWV', 'Tkr': 'CRWV', 'Qty': 9.0, 'Pillar': 'Robinhood'},
        {'Name': 'FLEX', 'Tkr': 'FLEX', 'Qty': 10.0, 'Pillar': 'Robinhood'},
        {'Name': 'HOOD', 'Tkr': 'HOOD', 'Qty': 8.0, 'Pillar': 'Robinhood'},
        {'Name': 'INOD', 'Tkr': 'INOD', 'Qty': 17.750223, 'Pillar': 'Robinhood'},
        {'Name': 'LRCX', 'Tkr': 'LRCX', 'Qty': 9.22168, 'Pillar': 'Robinhood'},
        {'Name': 'MU', 'Tkr': 'MU', 'Qty': 6.94118, 'Pillar': 'Robinhood'},
        {'Name': 'NBIS', 'Tkr': 'NBIS', 'Qty': 1.0, 'Pillar': 'Robinhood'},
        {'Name': 'OKLO', 'Tkr': 'OKLO', 'Qty': 1.184033, 'Pillar': 'Robinhood'},
        {'Name': 'PSI', 'Tkr': 'PSI', 'Qty': 2.491277, 'Pillar': 'Robinhood'},
        {'Name': 'RDDT', 'Tkr': 'RDDT', 'Qty': 4.992676, 'Pillar': 'Robinhood'},
        {'Name': 'SNDK', 'Tkr': 'SNDK', 'Qty': 4.347362, 'Pillar': 'Robinhood'},
        {'Name': 'STX', 'Tkr': 'STX', 'Qty': 4.744995, 'Pillar': 'Robinhood'},
        {'Name': 'WDC', 'Tkr': 'WDC', 'Qty': 8.910648, 'Pillar': 'Robinhood'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.06752957, 'Pillar': 'Robinhood'},
        
        # PILLAR 2: ETRADE
        {'Name': 'Total Stock Market', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE'},
        {'Name': 'US Growth Fund', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE'},
        {'Name': 'S&P 500 Index', 'Tkr': 'VFIAX', 'Qty': 15.115, 'Pillar': 'ETRADE'},
        {'Name': 'International Stock', 'Tkr': 'VTIAX', 'Qty': 225.887, 'Pillar': 'ETRADE'},
        
        # PILLAR 3: Retirement (Placeholder)
        {'Name': 'Retirement Balances', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base_Val': 0},
        
        # PILLAR 4: College Fund (Live Holdings)
        {'Name': 'VTSAX (College)', 'Tkr': 'VTSAX', 'Qty': 209.296, 'Pillar': 'College Fund'},
        {'Name': 'VTI (College)', 'Tkr': 'VTI', 'Qty': 222.203, 'Pillar': 'College Fund'},
        
        # PILLAR 5: Non-US/India
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base_Val': 300000},
        
        # SYSTEM
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base_Val': h_val},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base_Val': -m_bal}
    ]
    df = pd.DataFrame(data)
    tkrs = df[df['Tkr'] != 'FIXED']['Tkr'].unique().tolist()
    try:
        p_df = yf.download(tkrs, period="7d", group_by='ticker', progress=False)
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base_Val'], r['Base_Val']
            valid = p_df[r['Tkr']]['Close'].dropna()
            return valid.iloc[-1] * r['Qty'], valid.iloc[-2] * r['Qty']
        df[['Curr_Val', 'Prev_Val']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr_Val'] = df.get('Base_Val', 0)
        df['Prev_Val'] = df['Curr_Val']
    df['Day_Chg'] = (df['Curr_Val'] - df['Prev_Val']).fillna(0)
    return df

df = load_all_pillars()

# --- CALCULATIONS ---
nw = df['Curr_Val'].sum()
day_p = df['Day_Chg'].sum()

fire_current = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India'])]['Curr_Val'].sum()
fire_pct = min(fire_current / FIRE_TARGET, 1.0)

college_current = df[df['Pillar'] == 'College Fund']['Curr_Val'].sum()
college_pct = min(college_current / COLLEGE_TARGET, 1.0)

# --- DASHBOARD ---
st.title("🔥 FIRE Pulse: Roadmap to Milestones")

col1, col2, col3 = st.columns(3)
col1.metric("Total Net Worth", f"${nw:,.0f}", delta=f"${day_p:,.2f} Today")
col2.metric("FIRE Asset Value", f"${fire_current:,.0f}")
col3.metric("College Asset Value", f"${college_current:,.0f}")

st.divider()

# PROGRESS TRACKERS
left_prog, right_prog = st.columns(2)
with left_prog:
    st.subheader(f"FIRE Goal Progress ($1M): {fire_pct:.1%}")
    st.progress(fire_pct)
with right_prog:
    st.subheader(f"College Goal Progress ($125k): {college_pct:.1%}")
    st.progress(college_pct)

st.divider()

c_left, c_right = st.columns([1.5, 1])
with c_left:
    st.subheader("Pillar Distribution")
    pie_df = df[df['Curr_Val'] > 0].groupby('Pillar')['Curr_Val'].sum().reset_index()
    fig = px.pie(pie_df, values='Curr_Val', names='Pillar', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

with c_right:
    st.subheader("Component Summary")
    for p in ['Robinhood', 'ETRADE', 'College Fund', 'Non-US/India']:
        val = df[df['Pillar'] == p]['Curr_Val'].sum()
        st.write(f"**{p}**: ${val:,.0f}")

st.divider()
st.subheader("Master Asset Ledger")
st.dataframe(df[['Pillar', 'Name', 'Curr_Val', 'Day_Chg']].sort_values(['Pillar', 'Curr_Val'], ascending=False).style.format({
    'Curr_Val': '${:,.2f}', 'Day_Chg': '${:,.2f}'
}), use_container_width=True, hide_index=True)
