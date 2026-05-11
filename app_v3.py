import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- 1. APP CONFIG & OBSIDIAN UI ---
st.set_page_config(page_title="FIRE Pulse V3.1: Tax Alpha", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 0.85rem !important; letter-spacing: 1px; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 800 !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00C853 , #B2FF59); }
    thead tr th { background-color: #151921 !important; color: #00E676 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TAX ALPHA ENGINE (CSV PARSER) ---
@st.cache_data
def load_tax_lots(file_path):
    try:
        # Load and handle multi-line descriptions
        df = pd.read_csv(file_path, on_bad_lines='skip')
        
        # Filter for Purchases
        df = df[df['Trans Code'] == 'Buy'].copy()
        
        # Clean numeric columns
        def clean_num(x):
            if isinstance(x, str):
                return float(x.replace('$', '').replace('(', '').replace(')', '').replace(',', ''))
            return x

        df['Quantity'] = df['Quantity'].apply(clean_num)
        df['Price_Paid'] = df['Price'].apply(clean_num)
        df['Cost_Basis'] = df['Amount'].apply(clean_num)
        
        # Convert Dates
        df['Activity Date'] = pd.to_datetime(df['Activity Date'])
        now = datetime.now()
        
        # Calculate Holding Periods
        df['Days_Held'] = (now - df['Activity Date']).dt.days
        df['Status'] = np.where(df['Days_Held'] > 365, 'Long-Term', 'Short-Term')
        
        # Identify Crossover Lots (Within 30 days of 1 year)
        df['Days_To_LT'] = 365 - df['Days_Held']
        df['Alert'] = (df['Days_To_LT'] > 0) & (df['Days_To_LT'] <= 30)
        
        return df
    except Exception as e:
        st.error(f"Tax Engine Error: {e}")
        return pd.DataFrame()

# --- 3. DYNAMIC ENGINES ---
def calculate_dynamic_values():
    now = datetime.now()
    h_start = datetime(2022, 4, 1)
    h_months = (relativedelta(now, h_start).years * 12) + relativedelta(now, h_start).months
    r_h, n_h = 0.0299 / 12, 15 * 12
    m_pay = 480000 * (r_h * (1 + r_h)**n_h) / ((1 + r_h)**n_h - 1)
    m_bal = 480000 * (r_h + 1)**h_months - (m_pay / r_h) * ((r_h + 1)**h_months - 1)
    h_val = 600000 * (1 + (1.025**(1/12)-1))**h_months
    biweekly_periods = max(0, (now - datetime(2026, 1, 1)).days // 14)
    total_401k = biweekly_periods * 1269.23
    hsa_p = 24350 + max(0, ((now.year - 2026) * 12 + now.month) * 712.50)
    return h_val, m_bal, total_401k, hsa_p

# --- 4. DATA MERGE & SYNC ---
def load_full_portfolio(tax_df):
    h_val, m_bal, auto_401k, hsa_p = calculate_dynamic_values()
    
    # 1. Start with high-precision manual baseline for ETRADE/Retirement
    manual_data = [
        {'Name': 'VTSAX (ET)', 'Tkr': 'VTSAX', 'Qty': 1080, 'Pillar': 'ETRADE', 'Risk': 'Mid'},
        {'Name': 'VWUSX (ET)', 'Tkr': 'VWUSX', 'Qty': 82.772, 'Pillar': 'ETRADE', 'Risk': 'High'},
        {'Name': 'VTSAX (Roth IRA)', 'Tkr': 'VTSAX', 'Qty': 3318.528, 'Pillar': 'Retirement', 'Risk': 'Mid'},
        {'Name': 'India Assets', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Non-US/India', 'Base': 300000, 'Risk': 'Low'},
        {'Name': 'HYSA Savings', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Cash', 'Base': 40000, 'Risk': 'Low'},
        {'Name': 'Roswell Home', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Real Estate', 'Base': h_val, 'Risk': 'Low'},
        {'Name': 'Mortgage Debt', 'Tkr': 'FIXED', 'Qty': 1, 'Pillar': 'Liability', 'Base': -m_bal, 'Risk': 'Low'}
    ]
    
    # 2. Aggregating Robinhood Data from CSV
    if not tax_df.empty:
        rh_agg = tax_df.groupby('Instrument').agg({'Quantity': 'sum', 'Cost_Basis': 'sum'}).reset_index()
        for _, row in rh_agg.iterrows():
            manual_data.append({
                'Name': row['Instrument'], 
                'Tkr': 'BTC-USD' if row['Instrument'] == 'BTC' else row['Instrument'], 
                'Qty': row['Quantity'], 
                'Pillar': 'Robinhood', 
                'Risk': 'High'
            })
    
    df = pd.DataFrame(manual_data)
    tkrs = [t for t in df['Tkr'].unique() if t != 'FIXED']
    
    try:
        p_df = yf.download(tkrs, period="5d", progress=False)['Close']
        def get_v(r):
            if r['Tkr'] == 'FIXED': return r['Base'], r['Base']
            ticker_data = p_df[r['Tkr']].dropna()
            curr_p = ticker_data.iloc[-1]
            prev_p = ticker_data.iloc[-2] if len(ticker_data) > 1 else curr_p
            return curr_p * r['Qty'], prev_p * r['Qty']
        df[['Curr', 'Prev']] = df.apply(lambda x: pd.Series(get_v(x)), axis=1)
    except:
        df['Curr'] = df.apply(lambda r: r.get('Base', 0), axis=1)
        df['Prev'] = df['Curr']
    
    df['Chg_$'] = (df['Curr'] - df['Prev']).fillna(0)
    return df

# Initialize Data
tax_df = load_tax_lots('cad10a93-0560-50ad-b5f5-9e36ffd4bc9c (1).csv')
df = load_full_portfolio(tax_df)

# Logic for UI
liquid_total = df[df['Pillar'].isin(['Robinhood', 'ETRADE', 'Non-US/India', 'Cash'])]['Curr'].sum()
st_val = tax_df[tax_df['Status'] == 'Short-Term']['Cost_Basis'].sum()
lt_val = tax_df[tax_df['Status'] == 'Long-Term']['Cost_Basis'].sum()
tax_eff_score = (lt_val / (st_val + lt_val)) * 100 if (st_val+lt_val) > 0 else 0

# --- 5. UI DASHBOARD ---
st.title("🛡️ FORTRESS V3.1: TAX ALPHA")
st.caption("Active Tax-Lot Accounting • Roswell, GA Baseline")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL LIQUID", f"${liquid_total:,.0f}")
m2.metric("TAX EFFICIENCY", f"{tax_eff_score:.1f}%", help="Percentage of your portfolio held > 1 year.")
m3.metric("LT CAP GAINS TARGET", "$0.00", delta="Ready to Harvest", delta_color="normal")

st.divider()

# --- TAX EFFICIENCY GAUGE ---
c_gauge, c_alert = st.columns([1, 1.5])
with c_gauge:
    st.subheader("TAX CLIMATE")
    fig_tax = go.Figure(go.Indicator(
        mode = "gauge+number", value = tax_eff_score,
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': "#00E676"},
            'steps': [{'range': [0, 50], 'color': 'rgba(255, 82, 82, 0.2)'}, 
                      {'range': [50, 100], 'color': 'rgba(0, 230, 118, 0.2)'}]
        }
    ))
    fig_tax.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=280)
    st.plotly_chart(fig_tax, use_container_width=True)

with c_alert:
    st.subheader("⚠️ CROSSOVER BRIDGE")
    crossover = tax_df[tax_df['Alert']].copy()
    if not crossover.empty:
        st.warning(f"Detection: {len(crossover)} lots are nearing Long-Term status. Do not sell these yet!")
        st.dataframe(crossover[['Instrument', 'Activity Date', 'Days_To_LT', 'Cost_Basis']].sort_values('Days_To_LT'), use_container_width=True, hide_index=True)
    else:
        st.success("No immediate tax crossovers detected. All Short-Term lots have > 30 days remaining.")

st.divider()

# --- ASSET LEDGER & PILLARS ---
st.subheader("MASTER ASSET LEDGER")
st.dataframe(
    df[['Pillar', 'Name', 'Qty', 'Curr', 'Chg_$']]
    .sort_values(['Pillar', 'Curr'], ascending=False)
    .style.format({'Curr': '${:,.2f}', 'Chg_$': '${:,.2f}', 'Qty': '{:,.4f}'}),
    use_container_width=True, hide_index=True
)
