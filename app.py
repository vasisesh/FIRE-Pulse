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
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION & GOALS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030
CURRENT_DATE = datetime.now()
YEARS_REMAINING = max(0, TARGET_YEAR - CURRENT_DATE.year)

# --- DATA LOADING ---
def load_base_data():
    # Initializing your specific holdings
    data = {
        'Category': ['Equity', 'Equity', 'International', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'INTL_FLAT', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'International Holdings', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 1, 1, 1],
        'Base_Value': [400, 210, 300000, 600000, 50000] # Fallback values
    }
    return pd.DataFrame(data)

def update_with_live_prices(df):
    tickers = ['NVDA', 'VTI']
    try:
        # Fetching data with a more robust method to avoid MultiIndex errors
        stock_info = yf.download(tickers, period="1d", group_by='ticker', progress=False)
        
        # Create a dictionary to hold the latest prices
        prices = {}
        for ticker in tickers:
            # Get the last valid 'Close' price
            prices[ticker] = stock_info[ticker]['Close'].iloc[-1]
        
        # Calculate values: (Quantity * Price) if it's a stock, else use Base_Value
        df['Current_Value'] = df.apply(
            lambda x: (prices[x['Ticker']] * x['Quantity']) if x['Ticker'] in prices 
            else x['Base_Value'], axis=1
        )
    except Exception as e:
        # If the internet/API fails, use the base values so the app still loads
        st.sidebar.warning("Note: Using cached prices (Live data unavailable)")
        df['Current_Value'] = df['Base_Value']
    
    return df

# Initialize Data
raw_df = load_base_data()
df = update_with_live_prices(raw_df)

# Calculations
total_net_worth = df['Current_Value'].sum()
# FIRE Fund = Total Net Worth minus the Home Value
fire_fund_current = df[df['Ticker'] != 'HOME']['Current_Value'].sum()
fire_fund_progress = (fire_fund_current / TARGET_FIRE_FUND) * 100

# --- DASHBOARD UI ---
st.title("🔥 FIRE Pulse")
st.subheader(f"Roadmap to {TARGET_YEAR}")

# Top Row Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Net Worth", f"${total_net_worth:,.0f}")
m2.metric("FIRE Fund Status", f"${fire_fund_current:,.0f}")
m3.metric("Goal Progress", f"{fire_fund_progress:.1f}%")
m4.metric("Years to {TARGET_YEAR}", f"{YEARS_REMAINING}")

st.divider()

# Progress Section
col_prog, col_gap = st.columns([3, 1])
with col_prog:
    st.write(f"**Progress toward ${TARGET_FIRE_FUND:,.0f} FIRE Fund**")
    st.progress(min(fire_fund_progress / 100, 1.0))
with col_gap:
    gap = max(0, TARGET_FIRE_FUND - fire_fund_current)
    st.metric("Gap to Goal", f"${gap:,.0f}")

st.write("##") # Spacer

# Charts Row
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Asset Allocation")
    fig = px.pie(df, values='Current_Value', names='Category', 
                 hole=0.6, color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Current Holdings")
    # Cleaned up table view
    display_df = df[['Name', 'Category', 'Current_Value']].sort_values('Current_Value', ascending=False)
    st.dataframe(display_df.style.format({'Current_Value': '${:,.0f}'}), 
                 use_container_width=True, hide_index=True)

# Milestone Insights
st.success(f"💡 At your current pace, you have secured ${fire_fund_current:,.0f} of your ${TARGET_FIRE_FUND:,.0f} target.")
