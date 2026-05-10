import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

# --- APP CONFIG ---
st.set_page_config(page_title="FIRE Pulse", layout="wide", initial_sidebar_state="expanded")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR / SETTINGS ---
with st.sidebar:
    st.title("🔥 FIRE Pulse")
    st.subheader("Configuration")
    annual_expenses = st.number_input("Annual Target Expenses ($)", value=80000, step=5000)
    fire_multiplier = st.slider("FIRE Multiplier (e.g. 25x)", 20, 33, 25)
    fire_number = annual_expenses * fire_multiplier
    st.divider()
    st.info(f"Target FIRE Number: ${fire_number:,.0f}")

# --- DATA LOADING (Mock Data for initial setup) ---
@st.cache_data
def load_data():
    # Replace this with pd.read_csv('holdings.csv') later
    data = {
        'Category': ['Equity', 'Equity', 'Equity', 'Real Estate', 'Cash'],
        'Ticker': ['NVDA', 'VTI', 'AVGO', 'HOME', 'CASH'],
        'Name': ['NVIDIA', 'Vanguard Total Stock', 'Broadcom', 'Primary Residence', 'HYSA'],
        'Quantity': [10, 100, 5, 1, 1],
        'Cost_Basis': [400, 210, 800, 600000, 50000]
    }
    return pd.DataFrame(data)

df = load_data()

# --- LIVE PRICE UPDATES ---
def get_live_prices(df):
    tickers = [t for t in df['Ticker'].tolist() if t not in ['HOME', 'CASH']]
    if tickers:
        stock_data = yf.download(tickers, period="1d")['Close'].iloc[-1]
        df['Current_Price'] = df.apply(lambda x: stock_data[x['Ticker']] if x['Ticker'] in stock_data else x['Cost_Basis'], axis=1)
    else:
        df['Current_Price'] = df['Cost_Basis']
    
    df['Current_Value'] = df['Quantity'] * df['Current_Price']
    return df

df = get_live_prices(df)
total_net_worth = df['Current_Value'].sum()
fire_progress = (total_net_worth / fire_number) * 100

# --- DASHBOARD LAYOUT ---
st.title("Investment Dashboard")

# Top Row: KPI Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Net Worth", f"${total_net_worth:,.2f}", delta=f"{((total_net_worth/df['Cost_Basis'].sum())-1)*100:.1f}%")
col2.metric("FIRE Progress", f"{fire_progress:.1f}%")
col3.metric("Gap to Goal", f"${max(0, fire_number - total_net_worth):,.0f}")

st.divider()

# Middle Row: Visuals
left_chart, right_chart = st.columns([1, 1])

with left_chart:
    st.subheader("Asset Allocation")
    fig_pie = px.pie(df, values='Current_Value', names='Category', hole=0.5,
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with right_chart:
    st.subheader("Holdings Value")
    fig_bar = px.bar(df.sort_values('Current_Value'), x='Current_Value', y='Name', 
                     orientation='h', color='Category',
                     color_discrete_sequence=px.colors.qualitative.Prism)
    st.plotly_chart(fig_bar, use_container_width=True)

# Bottom: Data Table
st.subheader("Detailed Portfolio Breakdown")
st.dataframe(df.style.format({
    'Cost_Basis': '${:,.2f}',
    'Current_Price': '${:,.2f}',
    'Current_Value': '${:,.2f}'
}), use_container_width=True)
