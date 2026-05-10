import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide")

# --- STYLING (High Contrast) ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #d1d5db;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricLabel"] { color: #4b5563 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800 !important; }
    [data-testid="stMetricDelta"] svg { display: none; }
    .main { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
TARGET_FIRE_FUND = 500000
TARGET_YEAR = 2030

# --- DATA ENGINE ---
def load_and_pulse_data():
    # Robinhood Holdings
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
    
    rows = []
    # Add Stocks
    for ticker, qty in stocks.items():
        rows.append({'Name': ticker, 'Ticker': ticker, 'Quantity': qty, 'Category': 'Equity (RH)', 'Base_Value': 0})
    
    # Add Crypto
    rows.append({'Name': 'Bitcoin', 'Ticker': 'BTC-USD', 'Quantity': 0.06752957, 'Category': 'Crypto', 'Base_Value': 0})
    
    # Add Fixed Assets
    rows.append({'Name': 'International Holdings', 'Ticker': 'INTL_FLAT', 'Quantity': 1, 'Category': 'International', 'Base_Value': 300000})
    rows.append({'Name': 'Primary Residence', 'Ticker': 'HOME', 'Quantity': 1, 'Category': 'Real Estate', 'Base_Value': 600000})
    
    df = pd.DataFrame(rows)
    tickers_to_fetch = list(stocks.keys()) + ['BTC-USD']
    
    try:
        stock_data = yf.download(tickers_to_fetch, period="2d", group_by='ticker', progress=False)
        
        def get_prices(ticker):
            if ticker in ['INTL_FLAT', 'HOME']: 
                val = df.loc[df['Ticker']==ticker, 'Base_Value'].values[0]
                return val, val
            try:
                current = stock_data[ticker]['Close'].iloc[-1]
                prev = stock_data[ticker]['Close'].iloc[-2]
                return current, prev
            except:
                return 0, 0

        df[['
