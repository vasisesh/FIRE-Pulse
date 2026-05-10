import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide")

# --- STYLING (Fixed for Visibility) ---
st.markdown("""
    <style>
    /* Card Styling */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #d1d5db;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    /* Force Label Color (Small Text) */
    [data-testid="stMetricLabel"] {
        color: #4b5563 !important;
        font-weight: 600 !important;
    }
    /* Force Value Color (Big Numbers) */
    [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
    }
    /* Hide the default delta arrow for a cleaner look */
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    .main {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030
CURRENT_YEAR = datetime.now().year
YEARS_TO_GO = max(0, TARGET_YEAR - CURRENT_YEAR)

# --- DATA ENGINE ---
def load_and_pulse_data():
    data = {
        'Category': ['Equity', 'Equity', 'International', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'INTL_FLAT', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'International Holdings', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 1, 1, 1],
        'Base_Value': [400, 210, 300000, 600000, 50000]
    }
    df = pd.DataFrame(data)
    
    tickers = ['NVDA', 'VTI']
    try:
        stock_data = yf.download(tickers, period="2d", group_by='ticker', progress=False)
        current_prices = {t: stock_data[t]['Close'].iloc[-1] for t in tickers}
        prev_closes = {t: stock_data[t]['Close'].iloc[-2] for t in tickers}
            
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
st.subheader(f"Strategy Roadmap to {TARGET_YEAR}")

# Row 1: Metrics (Now with visible colors)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Net Worth", f"${total_nw:,.0f}", delta=f"${total_day_change:,.2f} Today")
m2.metric("Daily Change (%)", f"{day_change_pct:.2f}%")
m3.metric("FIRE Fund Status", f"${fire_fund_current:,.0f}")
m4.metric("Goal Progress", f"{fire_progress:.1f}%")

st.divider()

# Row 2: Charts
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Asset Allocation")
    fig_pie = px.pie(
        df, 
        values='Current_Value', 
        names='Category', 
        hole=0.5, 
        color_discrete_sequence=px.colors.sequential.Teal
    )
    fig_pie.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with right_col:
    st.subheader("Today's Pulse")
    pulse_df = df[df['Day_Change_Dollar'] != 0][['Name', 'Day_Change_Dollar']].sort_values('Day_Change_Dollar', ascending=False)
    
    if not pulse_df.empty:
        for _, row in pulse_df.iterrows():
            color = "#28a745" if row['Day_Change_Dollar'] > 0 else "#dc3545"
            st.markdown(f"**{row['Name']}**: <span style='color:{color}'>${row['Day_Change_Dollar']:,.2f}</span>", unsafe_allow_html=True)
    else:
        st.info("Markets are flat or closed.")

st.divider()

# Row 3: Table
st.subheader("Holdings Detail")
st.dataframe(df[['Name', 'Category', 'Quantity', 'Current_Value', 'Day_Change_Dollar']].sort_values('Current_Value', ascending=False).style.format({
    'Current_Value': '${:,.0f}',
    'Day_Change_Dollar': '${:,.2f}'
}), use_container_width=True, hide_index=True)
