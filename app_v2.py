import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. APP CONFIG & OBSIDIAN UI ---
st.set_page_config(page_title="FIRE Pulse V2.4", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
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
RET_AGE = 50
CUR_AGE = 43
YEARS_TO_GO = RET_AGE - CUR_AGE
GROWTH_RATE = 0.07  # 7% Nominal
SWR = 0.035         # 3.5% Safe Withdrawal Rate

# --- 3. DYNAMIC VALUE ENGINES ---
def calculate_dynamic_values():
    now = datetime.now()
    # Home Equity
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    # Contributions
    biweekly_periods = max(0, (now - datetime(2026, 1, 1)).days // 14)
    total_401k = biweekly_periods * 1269.23
    hsa_p = (7750 + 8300 + 8300) + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, total_401k, hsa_p

def load_all_data():
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
    data = [
        # PILLAR 1: Robinhood (High Risk)
        {'Name': 'AAPL', 'Tkr': 'AAPL', 'Qty': 32.875, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'NVDA', 'Tkr': 'NVDA', 'Qty': 41.067, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'VGT', 'Tkr': 'VGT', 'Qty': 88.524, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'Bitcoin', 'Tkr': 'BTC-USD', 'Qty': 0.0675, 'Pillar': 'Robinhood', 'Risk': 'High'},
        {'Name': 'AMD', 'Tkr': 'AMD', 'Qty': 17.228, 'Pillar': 'Robinhood', 'Risk': 'High'},
        # PILLAR 2: ETRADE (Mid Risk)
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        # PILLAR 3: Retirement
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'Auto 401k', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Retirement', 'Base': auto_401k, 'Risk': 'Mid'},
        # PILLAR 5: Non-US/India & HSA (Low Risk)
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
        {'Name': 'HSA (VTSAX)', 'Tkr': 'VTSAX', 'Qty': (hsa_p / 120), 'Pillar': 'Non-US/India', 'Risk': 'Mid'},
        # PILLAR 6: Cash
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
        # SYSTEM
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val, 'Risk': 'Low'},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base': -m_bal, 'Risk': 'Low'}
    ]
    df = pd.DataFrame(data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    try:
        p_df = yf.download(tkrs, period="7d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base'], r['Base']
            valid = p_df[r['Tkr']].dropna()
            return valid.iloc[-1] * r['Qty'], valid.iloc[-2] * r['Qty']
        df[['Curr', 'Prev']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr'] = df.get('Base', 0); df['Prev'] = df['Curr']
    df['Chg_$'] = (df['Curr'] - df['Prev']).fillna(0)
    return df

df = load_all_data()

# --- 4. CALCULATIONS & FORECASTS ---
nw_curr = df['Curr'].sum()
liquid_total = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()

# Risk Concentration Score
high_risk_val = df[df['Risk'] == 'High']['Curr'].sum()
risk_score = (high_risk_val / liquid_total) * 100

# Future Projection
def project_wealth(base, rate):
    months = YEARS_TO_GO * 12
    m_rate = (1 + rate)**(1/12) - 1
    b = [base]
    for _ in range(months): b.append((b[-1] * (1 + m_rate)) + 3600)
    return b

projection = project_wealth(liquid_total, GROWTH_RATE)
final_val = projection[-1]
monthly_runway = (final_val * SWR) / 12

# --- 5. UI DASHBOARD ---
st.title("🛡️ THE VASIREDDY FORTRESS")
st.caption(f"Status: Age {CUR_AGE} • Vision: Retire at {RET_AGE} (2035) • Obsidian v2.4")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL NET WORTH", f"${nw_curr:,.0f}", delta=f"${df['Chg_$'].sum():,.2f}")
m2.metric("LIQUID ASSETS", f"${liquid_total:,.0f}")
m3.metric("TECH CONCENTRATION", f"{risk_score:.1f}%")

st.divider()

# --- RISK GAUGE SECTION ---
st.subheader("PORTFOLIO RISK CLIMATE")
g_col, t_col = st.columns([1, 1])

with g_col:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = risk_score,
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#00E676"},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 40], 'color': '#1565C0'}, 
                {'range': [40, 75], 'color': '#FF8F00'}, 
                {'range': [75, 100], 'color': '#C62828'}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'value': risk_score}
        }
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "JetBrains Mono"}, height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

with t_col:
    st.write("### Strategy Insight")
    if risk_score > 75:
        st.error("**Heat Level: Critical.** Your liquid wealth is highly coupled to Tech/AI volatility. High reward, but vulnerable to sector corrections.")
    elif risk_score > 40:
        st.warning("**Heat Level: Optimal.** Balanced growth with a solid safety net in India Assets and Cash.")
    else:
        st.success("**Heat Level: Defensive.** High stability, well-protected against market swings.")
    
    st.info(f"**Safe Monthly Runway (2035):** Based on your {GROWTH_RATE*100:.0f}% projection, you're on track for **${monthly_runway:,.0f}/month**.")

st.divider()

# --- GROWTH PATH & PILLAR BREAKDOWN ---
c1, c2 = st.columns([1.5, 1])

with c1:
    st.subheader(f"Projected Growth Path to 2035")
    fig_path = go.Figure()
    fig_path.add_trace(go.Scatter(y=projection, fill='tozeroy', line=dict(color='#00E676', width=4)))
    fig_path.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=350)
    st.plotly_chart(fig_path, use_container_width=True)

with c2:
    st.subheader("Pillar Distribution")
    fig_pie = px.pie(df[df['Curr']>0], values='Curr', names='Pillar', hole=0.6, color_discrete_sequence=px.colors.sequential.Tealgrn)
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# --- MASTER LEDGER ---
st.subheader("MASTER ASSET LEDGER")
def style_ledger(val):
    if isinstance(val, (int, float)):
        if val > 0: return 'color: #00E676'
        if val < 0: return 'color: #FF5252'
    return 'color: #E0E0E0'

st.dataframe(
    df[['Pillar', 'Name', 'Curr', 'Risk']]
    .sort_values(['Pillar', 'Curr'], ascending=False)
    .style.format({'Curr': '${:,.2f}'})
    .map(style_ledger, subset=['Curr']),
    use_container_width=True, hide_index=True
)
