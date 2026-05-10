import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Projection Settings")
    monthly_invest = st.slider("Monthly Contribution ($)", 0, 5000, 1000, step=100)
    expected_return = st.slider("Expected Annual Return (%)", 1, 12, 7)
    st.divider()
    st.caption("Adjust these to see if you hit the $500k goal by 2030.")

# --- CONSTANTS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030
CURRENT_YEAR = datetime.now().year
YEARS_TO_GO = max(0, TARGET_YEAR - CURRENT_YEAR)

# --- DATA PROCESSING ---
def load_and_update_data():
    data = {
        'Category': ['Equity', 'Equity', 'International', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'INTL_FLAT', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'International Holdings', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 1, 1, 1],
        'Base_Value': [400, 210, 300000, 600000, 50000]
    }
    df = pd.DataFrame(data)
    
    try:
        tickers = ['NVDA', 'VTI']
        stock_info = yf.download(tickers, period="1d", group_by='ticker', progress=False)
        prices = {t: stock_info[t]['Close'].iloc[-1] for t in tickers}
        df['Current_Value'] = df.apply(lambda x: (prices[x['Ticker']] * x['Quantity']) if x['Ticker'] in prices else x['Base_Value'], axis=1)
    except:
        df['Current_Value'] = df['Base_Value']
    return df

df = load_and_update_data()
fire_fund_current = df[df['Ticker'] != 'HOME']['Current_Value'].sum()
total_net_worth = df['Current_Value'].sum()

# --- PROJECTION LOGIC ---
months = np.arange(YEARS_TO_GO * 12 + 1)
monthly_rate = (1 + expected_return/100)**(1/12) - 1
forecast_values = []
current_val = fire_fund_current

for m in months:
    forecast_values.append(current_val)
    current_val = (current_val + monthly_invest) * (1 + monthly_rate)

projection_df = pd.DataFrame({'Month': months, 'Projected_Value': forecast_values})
final_value = forecast_values[-1]

# --- UI LAYOUT ---
st.title("🔥 FIRE Pulse Dashboard")
st.markdown(f"### Milestone: **${TARGET_FIRE_FUND:,.0f} by {TARGET_YEAR}**")

# Row 1: Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Net Worth", f"${total_net_worth:,.0f}")
m2.metric("FIRE Fund", f"${fire_fund_current:,.0f}")
m3.metric("2030 Forecast", f"${final_value:,.0f}", delta=f"${final_value - TARGET_FIRE_FUND:,.0f} vs Goal")
m4.metric("FIRE Progress", f"{(fire_fund_current/TARGET_FIRE_FUND)*100:.1f}%")

st.divider()

# Row 2: The Chart
st.subheader("Wealth Projection to 2030")
fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=projection_df['Month']/12 + CURRENT_YEAR, y=projection_df['Projected_Value'], 
                             mode='lines', name='Forecast', line=dict(color='#1f77b4', width=4)))
fig_line.add_hline(y=TARGET_FIRE_FUND, line_dash="dash", line_color="green", annotation_text="FIRE Goal")
fig_line.update_layout(xaxis_title="Year", yaxis_title="Portfolio Value ($)", hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

# Row 3: Breakdown
c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("Asset Allocation")
    fig_pie = px.pie(df, values='Current_Value', names='Category', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
    st.plotly_chart(fig_pie, use_container_width=True)
with c2:
    st.subheader("Holdings")
    st.table(df[['Name', 'Current_Value']].sort_values('Current_Value', ascending=False).style.format({'Current_Value': '${:,.0f}'}))

# Final Status Message
if final_value >= TARGET_FIRE_FUND:
    st.success(f"✅ On Track! With ${monthly_invest}/mo and {expected_return}% return, you'll hit your goal in {TARGET_YEAR}.")
else:
    st.warning(f"⚠️ Gap Detected: You are projected to be ${TARGET_FIRE_FUND - final_value:,.0f} short. Increase contributions or target a higher return.")
