import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION & GOALS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030
CURRENT_DATE = datetime.now()
YEARS_REMAINING = TARGET_YEAR - CURRENT_DATE.year

# --- DATA LOADING ---
def load_data():
    # Adding your International Holdings at a flat $300,000
    data = {
        'Category': ['Equity', 'Equity', 'International', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'INTL_FLAT', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'International Holdings', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 1, 1, 1],
        'Value': [0, 0, 300000, 600000, 50000] # Equities updated live below
    }
    return pd.DataFrame(data)

def get_live_prices(df):
    # Only fetch for actual stock tickers
    tickers = ['NVDA', 'VTI']
    stock_data = yf.download(tickers, period="1d")['Close'].iloc[-1]
    
    # Update equity values, keep flat values for others
    df.loc[df['Ticker'] == 'NVDA', 'Value'] = stock_data['NVDA'] * 10
    df.loc[df['Ticker'] == 'VTI', 'Value'] = stock_data['VTI'] * 100
    return df

df = get_live_prices(load_data())
total_net_worth = df['Value'].sum()

# Assuming "FIRE Fund" consists of Equities + International + Cash (excluding Home Equity)
fire_fund_current = df[df['Ticker'] != 'HOME']['Value'].sum()
fire_fund_progress = (fire_fund_current / TARGET_FIRE_FUND) * 100

# --- DASHBOARD UI ---
st.title("🔥 FIRE Pulse: Roadmap to 2030")

# Top Row: The Big Picture
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Net Worth", f"${total_net_worth:,.0f}")
m2.metric("FIRE Fund Status", f"${fire_fund_current:,.0f}")
m3.metric("Goal Progress", f"{fire_fund_progress:.1f}%")
m4.metric("Years to 2030", f"{YEARS_REMAINING}")

st.divider()

# Progress Bar toward the $500k Goal
st.subheader(f"Progress toward ${TARGET_FIRE_FUND:,.0f} FIRE Fund")
st.progress(min(fire_fund_progress / 100, 1.0))
st.caption(f"Remaining to reach goal: ${max(0, TARGET_FIRE_FUND - fire_fund_current):,.0f}")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Asset Distribution")
    # Sunburst chart looks very premium for diverse holdings
    fig = px.sunburst(df, path=['Category', 'Name'], values='Value',
                  color='Value', color_continuous_scale='RdBu')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Holdings Detail")
    # Clean table for quick review
    st.dataframe(df[['Name', 'Category', 'Value']].sort_values('Value', ascending=False), 
                 use_container_width=True, hide_index=True)

# Milestone Note
st.info(f"💡 To hit your 2030 goal, you are currently tracking at {fire_fund_progress:.1f}% of your target fund.")
