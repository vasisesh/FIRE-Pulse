import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse V3", layout="wide")

# --- OBSIDIAN & EMERALD UI ---
st.markdown("""
    <style>
    /* Global Background & Typography */
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    
    /* Precision Metrics */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stMetricLabel"] { 
        color: #B0B0B0 !important; 
        font-size: 0.85rem !important; 
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        color: #00E676 !important; /* Emerald */
        font-family: 'JetBrains Mono', 'Roboto Mono', monospace !important;
        font-weight: 800 !important;
    }
    
    /* Progress Bar Glow */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00C853 , #B2FF59);
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.3);
    }

    /* Table & Header Styling */
    thead tr th { background-color: #151921 !important; color: #00E676 !important; border-bottom: 2px solid #00E676 !important; }
    tbody tr:hover { background-color: rgba(255,255,255,0.05) !important; }
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
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    
    # 2. Automated Growth (401k & HSA)
    c_start = datetime(2026, 1, 1)
    biweekly_periods = max(0, (now - c_start).days // 14)
    total_401k = biweekly_periods * 1269.23
    hsa_p = (7750 + 8300 + 8300) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    
    return h_val, m_bal, total_401k, hsa_p

def load_all_pillars():
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
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
        {'Name': 'HSA (VTSAX)', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 118), 'Pillar': 'Non-US/India'},

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
        df['Curr'] = df.get('Base', 0); df['Prev'] = df['Curr']
    
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

# --- DASHBOARD UI ---
st.title("🛡️ FIRE PULSE V2")
st.caption("Strategic Wealth Control • Obsidian Edition")

m1, m2, m3 = st.columns(3)
m1.metric("NET WORTH", f"${nw_curr:,.0f}", delta=f"${nw_chg_dollar:,.2f} ({nw_chg_pct:.2f}%)")
m2.metric("LIQUID FIRE", f"${fire_cur:,.0f}")
m3.metric("GAP TO $2.5M", f"${max(0, NW_TARGET - nw_curr):,.0f}")

st.divider()

p_col1, p_col2 = st.columns(2)
with p_col1:
    st.subheader(f"FIRE TARGET ($1M) • {fire_pct:.1%}")
    st.progress(fire_pct)
with p_col2:
    st.subheader(f"NET WORTH TARGET ($2.5M) • {nw_goal_pct:.1%}")
    st.progress(nw_goal_pct)

st.divider()

# Charts & Summary
c_left, c_right = st.columns([1.5, 1])
with c_left:
    st.subheader("PILLAR ALLOCATION")
    fig_pie = px.pie(df[df['Curr'] > 0], values='Curr', names='Pillar', hole=0.6, 
                     color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#B0B0B0"), showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

with c_right:
    st.subheader("PILLAR SUMMARY")
    p_sum = df.groupby('Pillar')['Curr'].sum()
    for p in ['Robinhood', 'ETRADE', 'Retirement', 'College Fund', 'Non-US/India', 'Cash', 'Real Estate']:
        val = p_sum.get(p, 0)
        st.markdown(f"**{p}** <span style='float:right; color:#00E676;'>${val:,.0f}</span>", unsafe_allow_html=True)
        st.progress(min(val/1200000, 1.0))

st.divider()

# Top 10 RH Visuals
rh_df = df[df['Pillar'] == 'Robinhood'].copy()
rh_total = rh_df['Curr'].sum()
rh_df['Port_%'] = (rh_df['Curr'] / rh_total) * 100
top_10 = rh_df.sort_values('Curr', ascending=False).head(10)

st.subheader("ROBINHOOD CONCENTRATION (TOP 10)")
t10_col1, t10_col2 = st.columns([1.5, 1])
with t10_col1:
    fig_rh = px.bar(top_10, x='Name', y='Curr', text_auto='.2s', color='Curr', 
                    color_continuous_scale='tealgrn', hover_data={'Port_%': ':.2f%'})
    fig_rh.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#B0B0B0"), coloraxis_showscale=False)
    st.plotly_chart(fig_rh, use_container_width=True)
with t10_col2:
    st.dataframe(top_10[['Name', 'Curr', 'Port_%']].style.format({'Curr': '${:,.0f}', 'Port_%': '{:.2f}%'}), use_container_width=True, hide_index=True)

st.divider()

# Master Ledger
st.subheader("MASTER ASSET LEDGER")
def style_ledger(val):
    if isinstance(val, (int, float)):
        if val > 0: return 'color: #00E676'
        if val < 0: return 'color: #FF5252'
    return 'color: #E0E0E0'

st.dataframe(
    df[['Pillar', 'Name', 'Curr', 'Chg_$', 'Chg_%']]
    .sort_values(['Pillar', 'Curr'], ascending=False)
    .style.format({'Curr': '${:,.2f}', 'Chg_$': '${:,.2f}', 'Chg_%': '{:,.2f}%'})
    .map(style_ledger, subset=['Chg_$', 'Chg_%']),
    use_container_width=True, hide_index=True
)
