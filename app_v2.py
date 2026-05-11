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
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #008080 , #00ffcc); }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
FIRE_TARGET = 1000000
NW_TARGET = 2500000

# --- ENGINES ---
def calculate_dynamic_values():
    now = datetime.now()
    
    # 1. Home Equity (Roswell, GA)
    h_start = datetime(2022, 4, 1)
    h_delta = relativedelta(now, h_start)
    h_months = h_delta.years * 12 + h_delta.months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    
    # 2. 401k Contribution Engine ($33k/year total since Jan 2026)
    c_start = datetime(2026, 1, 1)
    days_passed = (now - c_start).days
    biweekly_periods = max(0, days_passed // 14)
    total_401k_contributions = biweekly_periods * 1269.23
    
    # 3. HSA Engine (Family Maxing since 2023)
    # 2023: $7,750 | 2024: $8,300 | 2025: $8,300
    hsa_past_principal = 7750 + 8300 + 8300
    # 2026: $8,550 max ($712.50 per month)
    hsa_2026_months = (now.year - 2026) * 12 + now.month
    hsa_2026_contrib = max(0, hsa_2026_months * 712.50)
    total_hsa_principal = hsa_past_principal + hsa_2026_contrib
    
    return h_val, m_bal, total_401k_contributions, total_hsa_principal

def load_all_pillars():
    h_val, m_bal, auto_401k, hsa_principal = calculate_dynamic_values()
    
    # Estimate HSA shares based on a proxy price if historical entry points aren't exact, 
    # but for this logic, we treat the total principal as a "Fixed" value that grows with the fund price.
    # We'll use VTSAX price to scale the HSA principal.
    
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
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE'},
        {'Name': 'VFIAX (ET)', 'Tkr': 'VFIAX', 'Qty': 15.115, 'Pillar': 'ETRADE'},
        {'Name': 'VTIAX (ET)', 'Tkr': 'VTIAX', 'Qty': 225.887, 'Pillar': 'ETRADE'},
        
        # PILLAR 3: Retirement
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement'},
        {'Name': 'FELG (Roth IRA)', 'Tkr': 'FELG', 'Qty': 386, 'Pillar': 'Retirement'},
        {'Name': 'WFSPX (Roth 401k)', 'Tkr': 'WFSPX', 'Qty': 157.092, 'Pillar': 'Retirement'},
        {'Name': 'JLGMX (Roth 401k)', 'Tkr': 'JLGMX', 'Qty': 641.5629, 'Pillar': 'Retirement'},
        {'Name': 'Auto 401k Principal', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k},
        
        # PILLAR 4: College Fund
        {'Name': 'VTSAX (College)', 'Tkr': 'VTSAX', 'Qty': 209.296, 'Pillar': 'College Fund'},
        {'Name': 'VTI (College)', 'Tkr': 'VTI', 'Qty': 222.203, 'Pillar': 'College Fund'},
        
        # PILLAR 5: Non-US/India & HSA
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000},
        # HSA is tracked here using VTSAX for growth on the calculated principal
        {'Name': 'HSA (VTSAX Invested)', 'Tkr': 'VTSAX', 'Qty': (hsa_principal / 115), 'Pillar': 'Non-US/India'},

        # PILLAR 6: Cash
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000},
        
        # SYSTEM
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base': -m_bal}
    ]
    df = pd.DataFrame(data)
    tkrs = df[df['Tkr'] != 'FIXED']['Tkr'].unique().tolist()
    try:
        p_df = yf.download(tkrs, period="7d", group_by='ticker', progress=False)
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base'], r['Base']
            valid = p_df[r['Tkr']]['Close'].dropna()
            return valid.iloc[-1] * r['Qty'], valid.iloc[-2] * r['Qty']
        df[['Curr', 'Prev']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr'] = df.get('Base', 0)
        df['Prev'] = df['Curr']
    
    df['Chg_$'] = (df['Curr'] - df['Prev']).fillna(0)
    df['Chg_%'] = ((df['Curr'] / df['Prev'] - 1) * 100).fillna(0)
    return df

df = load_all_pillars()

# --- CALCULATIONS ---
nw_curr = df['Curr'].sum()
nw_prev = df['Prev'].sum()
nw_chg_dollar = nw_curr - nw_prev
nw_chg_pct = (nw_chg_dollar / nw_prev) * 100

fire_cur = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()
fire_pct = min(fire_cur / FIRE_TARGET, 1.0)
nw_goal_pct = min(nw_curr / NW_TARGET, 1.0)

# --- DASHBOARD ---
st.title("🔥 FIRE Pulse")

col1, col2, col3 = st.columns(3)
col1.metric("Total Net Worth", f"${nw_curr:,.0f}", delta=f"${nw_chg_dollar:,.2f} ({nw_chg_pct:.2f}%)")
col2.metric("FIRE Asset Value", f"${fire_cur:,.0f}")
col3.metric("Gap to $2.5M", f"${max(0, NW_TARGET - nw_curr):,.0f}")

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.subheader(f"FIRE Goal ($1M): {fire_pct:.1%}")
    st.progress(fire_pct)
with c2:
    st.subheader(f"Net Worth Goal ($2.5M): {nw_goal_pct:.1%}")
    st.progress(nw_goal_pct)

st.divider()

# Allocation & Summary
l_col, r_col = st.columns([1.5, 1])
with l_col:
    st.subheader("Asset Allocation")
    fig_pie = px.pie(df[df['Curr'] > 0], values='Curr', names='Pillar', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    st.plotly_chart(fig_pie, use_container_width=True)
with r_col:
    st.subheader("Pillar Summary")
    p_sum = df.groupby('Pillar')['Curr'].sum()
    for p in ['Robinhood', 'ETRADE', 'Retirement', 'College Fund', 'Non-US/India', 'Cash', 'Real Estate']:
        st.write(f"**{p}**: ${p_sum.get(p, 0):,.0f}")

st.divider()
st.subheader("Full Ledger (Daily Movement)")
def color_change(val):
    if val > 0: return 'color: #28a745'
    elif val < 0: return 'color: #dc3545'
    return 'color: white'

st.dataframe(
    df[['Pillar', 'Name', 'Curr', 'Chg_$', 'Chg_%']]
    .sort_values(['Pillar', 'Curr'], ascending=False)
    .style.format({'Curr': '${:,.2f}', 'Chg_$': '${:,.2f}', 'Chg_%': '{:,.2f}%'})
    .map(color_change, subset=['Chg_$', 'Chg_%']), 
    use_container_width=True, hide_index=True
)
