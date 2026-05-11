import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
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
    </style>
    """, unsafe_allow_html=True)

# --- CORRECTED MORTGAGE & REAL ESTATE CALCULATOR ---
def calculate_home_and_debt():
    # Constants
    START_DATE = datetime(2022, 4, 1)
    PURCHASE_PRICE = 600000       # Starting value for appreciation
    MORTGAGE_START = 480000       # Starting principal for debt
    ANNUAL_RATE = 0.0299
    TERM_YEARS = 15
    ANNUAL_APPRECIATION = 0.025
    
    # Time passed
    now = datetime.now()
    delta = relativedelta(now, START_DATE)
    months_passed = delta.years * 12 + delta.months
    
    # 1. Calculate Monthly Mortgage Payment (Principal + Interest)
    r = ANNUAL_RATE / 12
    n = TERM_YEARS * 12
    monthly_payment = MORTGAGE_START * (r * (1 + r)**n) / ((1 + r)**n - 1)
    
    # 2. Calculate Current Remaining Balance
    current_balance = MORTGAGE_START * (1 + r)**months_passed - (monthly_payment / r) * ((1 + r)**months_passed - 1)
    
    # 3. Calculate Current House Value (Compounded monthly based on Purchase Price)
    monthly_growth_rate = (1 + ANNUAL_APPRECIATION)**(1/12) - 1
    current_house_value = PURCHASE_PRICE * (1 + monthly_growth_rate)**months_passed
    
    return round(current_house_value, 2), round(current_balance, 2)

# --- DATA ENGINE ---
def load_and_pulse_data():
    stocks = {
        'AAPL': 32.875151, 'AMD': 17.228305, 'AMZN': 6.139473, 'ANET': 6.970517, 
        'AVGO': 17.692543, 'CRWD': 6.730194, 'DELL': 7.15184, 'DIS': 14.709586, 
        'ENPH': 10.65757, 'GEV': 1.207569, 'GLD': 3.048105, 'GOOGL': 42.149825, 
        'JPM': 2.753308, 'META': 8.317115, 'MRVL': 4.209034, 'MSFT': 19.746979, 
        'NFLX': 77.97709, 'NVDA': 41.067308, 'PANW': 2.468968, 'PLTR': 18.184741, 
        'SHOP': 42.621966, 'TSLA': 16.669082, 'TSM': 4.457336, 'TTWO': 2.719393, 
        'UBER': 42.189843, 'VGT': 88.524888, 'VRT': 8.559334, 'CRDO': 8.3776, 
        'CRWV': 9.0, 'FLEX': 10.0, 'HOOD': 8.0, 'INOD': 17.750223, 'LRCX': 9.22168, 
        'MU': 6.94118, 'NBIS': 1.0, 'OKLO': 1.184033, 'PSI': 2.491277, 'RDDT': 4.992676, 
        'SNDK': 4.347362, 'STX': 4.744995, 'WDC': 8.910648
    }
    
    current_house_value, current_mortgage_debt = calculate_home_and_debt()
    
    rows = []
    for ticker, qty in stocks.items():
        rows.append({'Name': ticker, 'Ticker': ticker, 'Quantity': qty, 'Category': 'Equity (RH)'})
    rows.append({'Name': 'Bitcoin', 'Ticker': 'BTC-USD', 'Quantity': 0.06752957, 'Category': 'Crypto'})
    rows.append({'Name': 'International Holdings', 'Ticker': 'INTL_FLAT', 'Quantity': 1, 'Category': 'International', 'Value': 300000})
    rows.append({'Name': 'Primary Residence', 'Ticker': 'HOME', 'Quantity': 1, 'Category': 'Real Estate', 'Value': current_house_value})
    rows.append({'Name': 'Mortgage Debt', 'Ticker': 'DEBT', 'Quantity': 1, 'Category': 'Liability', 'Value': -current_mortgage_debt})
    
    df = pd.DataFrame(rows)
    tickers_to_fetch = list(stocks.keys()) + ['BTC-USD']
    
    try:
        stock_data = yf.download(tickers_to_fetch, period="5d", group_by='ticker', progress=False)
        def get_p(t):
            if t in ['INTL_FLAT', 'HOME', 'DEBT']: return 0, 0
            v_data = stock_data[t]['Close'].dropna()
            return v_data.iloc[-1], v_data.iloc[-2]
        df[['Price', 'Prev']] = df.apply(lambda x: pd.Series(get_p(x['Ticker'])), axis=1)
    except:
        df['Price'], df['Prev'] = 0, 0
        
    df['Current_Value'] = df.apply(lambda x: x['Value'] if x['Ticker'] in ['INTL_FLAT', 'HOME', 'DEBT'] else x['Price'] * x['Quantity'], axis=1)
    df['Prev_Value'] = df.apply(lambda x: x['Value'] if x['Ticker'] in ['INTL_FLAT', 'HOME', 'DEBT'] else x['Prev'] * x['Quantity'], axis=1)
    df['Day_Change'] = (df['Current_Value'] - df['Prev_Value']).fillna(0)
    return df

df = load_and_pulse_data()

# --- CALCULATIONS ---
total_nw = df['Current_Value'].sum()
day_change = df['Day_Change'].sum()
fire_fund = df[~df['Category'].isin(['Real Estate', 'Liability'])]['Current_Value'].sum()
current_val = df[df['Ticker']=='HOME']['Current_Value'].values[0]
current_debt = abs(df[df['Ticker']=='DEBT']['Current_Value'].values[0])
home_equity = current_val - current_debt

# --- DASHBOARD ---
st.title("🔥 FIRE Pulse")
st.subheader("Roswell Real Estate & Portfolio Tracker")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Net Worth", f"${total_nw:,.0f}", delta=f"${day_change:,.2f} Today")
m2.metric("FIRE Fund Status", f"${fire_fund:,.0f}")
m3.metric("Home Equity", f"${home_equity:,.0f}")
m4.metric("Mortgage Balance", f"${current_debt:,.0f}")

st.divider()

c_left, c_right = st.columns([1.5, 1])
with c_left:
    st.subheader("Asset Allocation")
    pie_df = df[df['Category'] != 'Liability'].copy()
    fig = px.pie(pie_df, values='Current_Value', names='Category', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

with c_right:
    st.subheader("Home Equity Pulse")
    st.write(f"**Estimated Value:** ${current_val:,.0f}")
    st.write(f"**Mortgage Principal:** ${current_debt:,.0f}")
    st.progress(home_equity / current_val)
    st.caption(f"Equity: **{home_equity / current_val:.1%}** | Debt: **{current_debt / current_val:.1%}**")

st.divider()
st.subheader("Net Worth Breakdown")
st.dataframe(df[['Name', 'Category', 'Current_Value', 'Day_Change']].sort_values('Current_Value', ascending=False).style.format({
    'Current_Value': '${:,.2f}', 'Day_Change': '${:,.2f}'
}), use_container_width=True, hide_index=True)
