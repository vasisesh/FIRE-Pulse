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
    [data-testid="stMetricDelta"] svg { display: none; } /* Clean up the delta arrows */
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030
YEARS_TO_GO = max(0, TARGET_YEAR - datetime.now().year)

# --- DATA ENGINE ---
def load_and_pulse_data():
    # Base configuration
    data = {
        'Category': ['Equity', 'Equity', 'International', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'INTL_FLAT', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'International Holdings', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 1, 1, 1],
        'Base_Value': [400, 210, 300000, 600000, 50000]
    }
    df = pd.DataFrame(data)
    
    # Stock Pulser
    tickers = ['NVDA', 'VTI']
    try:
        # Get 2 days of data to compare today's close vs yesterday's close
        stock_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
        
        current_prices = {}
        prev_closes = {}
        
        for t in tickers:
            hist = stock_data[t]['Close']
            current_prices[t] = hist.iloc[-1]
            prev_closes[t] = hist.iloc[-2]
            
        df['Price'] = df.apply(lambda x: current_prices[x['Ticker']] if x['Ticker'] in current_prices else x['Base_Value'], axis=1)
        df['Prev_Price'] = df.apply(lambda x: prev_closes[x['Ticker']] if x['Ticker'] in prev_closes else x['Base_Value'], axis=1)
    except:
        df['Price'] = df['Base_Value']
        df['Prev_Price'] = df['Base_Value']
        
    df['Current_Value'] = df['Price'] * df['Quantity']
    df['Prev_Value'] = df['Prev_Price'] * df['Quantity']
    df['Day_Change_Dollar'] = df['Current_Value'] - df['Prev_Value']
    
    return df

df = load_and_pulse_data()

# --- CALCULATIONS ---
total_nw = df['Current_Value'].sum()
total_day_change = df['Day_Change_Dollar'].sum()
day_change_pct = (total_day_change / df['Prev_Value'].sum()) * 100 if df['Prev_Value'].sum() != 0 else 0

fire_fund_current = df[df['Ticker'] != 'HOME']['Current_Value'].sum()
fire_progress = (fire_fund_current / TARGET_FIRE_FUND) * 100

# --- DASHBOARD UI ---
st.title("🔥 FIRE Pulse")

# Daily Pulse Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Net Worth", f"${total_nw:,.0f}", delta=f"${total_day_change:,.2f} Today")
m2.metric("Daily Change (%)", f"{day_change_pct:.2f}%", delta=None)
m3.metric("FIRE Fund Status", f"${fire_fund_current:,.0f}")
m4.metric("FIRE Progress", f"{fire_progress:.1f}%")

st.divider()

# Left Column: Projection & Allocation | Right Column: Daily Pulse details
col_main, col_pulse = st.columns([2, 1])

with col_main:
    st.subheader("Asset Allocation")
    fig = px.pie(df, values='Current_Value',
