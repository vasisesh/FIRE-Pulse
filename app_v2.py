import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- APP CONFIG & THEME ---
st.set_page_config(page_title="FIRE Pulse V2.3", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetric"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; }
    [data-testid="stMetricValue"] { color: #00E676 !important; font-family: 'JetBrains Mono', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🕹️ Simulation Controls")
adjust_inflation = st.sidebar.toggle("Adjust for Inflation (Real Dollars)", value=False)
nominal_growth = st.sidebar.slider("Nominal Market Growth (%)", 4.0, 12.0, 7.0) / 100
inflation_rate = 0.03 # 2026-2035 Estimated Anchor

# Logic for "Real" vs "Nominal"
display_rate = nominal_growth - inflation_rate if adjust_inflation else nominal_growth
mode_label = "Real (Purchasing Power)" if adjust_inflation else "Nominal (Face Value)"

# --- CONFIGURATION ---
RET_AGE = 50
CUR_AGE = 43
YEARS_TO_GO = RET_AGE - CUR_AGE
SWR = 0.035

# --- ENGINE ---
def project_wealth(base, rate, monthly_contrib):
    months = YEARS_TO_GO * 12
    m_rate = (1 + rate)**(1/12) - 1
    balances = [base]
    for _ in range(months):
        balances.append((balances[-1] * (1 + m_rate)) + monthly_contrib)
    return balances

# Current Liquid Total (RH + ET + India + Cash + HSA)
# Based on your ledger, we'll anchor at ~$1,065,000
current_liquid = 1065000 
monthly_contrib = 3600 # 401k + HSA + Match

projection = project_wealth(current_liquid, display_rate, monthly_contrib)
final_val = projection[-1]
monthly_income = (final_val * SWR) / 12

# --- UI ---
st.title("🛡️ THE VASIREDDY FORTRESS: 2035 PREDICTOR")
st.caption(f"Currently Viewing: {mode_label} | Target Age: {RET_AGE}")

m1, m2, m3 = st.columns(3)
m1.metric(f"PROJECTED ASSETS ({2035})", f"${final_val:,.0f}")
m2.metric("MONTHLY RETIREMENT SALARY", f"${monthly_income:,.0f}")
m3.metric("SAFE WITHDRAWAL RATE", f"{SWR*100:.1%}")

st.divider()

# CHART
st.subheader(f"Growth Curve to Age 50 ({mode_label})")
fig = go.Figure()
fig.add_trace(go.Scatter(y=projection, mode='lines', fill='tozeroy', 
                         line=dict(color='#00E676', width=4), name="Wealth Path"))
fig.add_hline(y=2500000, line_dash="dot", line_color="orange", annotation_text="Net Worth Goal")
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
                  xaxis_title="Months from May 2026", yaxis_title="Liquid Assets ($)")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ANALYTICS SECTION
st.subheader("Strategy Insights")
c1, c2 = st.columns(2)

with c1:
    st.info("**What this means:**")
    if adjust_inflation:
        st.write(f"In 2035, your portfolio will have the buying power of **${final_val:,.0f}** in today's money. This is the 'true' weight of your wealth.")
    else:
        st.write(f"Your bank account will show **${final_val:,.0f}**. This is the number you will actually see on your screen in 2035.")

with c2:
    st.write("**Fortress Stability Check**")
    # Simple check: Does monthly income cover a projected $6k/mo lifestyle?
    if monthly_income > 6000:
        st.success("✅ Your 2035 Runway exceeds the $6k/mo lifestyle benchmark.")
    else:
        st.warning("⚠️ Runway is tight against the $6k/mo benchmark. Consider increasing savings or yield.")
