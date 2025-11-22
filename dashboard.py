import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Wealth Command Center")

# --- CSS: REMOVE THE WEBSITE FEEL ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h1, h2, h3 { font-family: 'Roboto', sans-serif; font-weight: 300; }
    [data-testid="stMetricValue"] { font-family: 'Roboto Mono', monospace; font-size: 1.6rem; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem; color: #888; }
</style>
""", unsafe_allow_html=True)

# --- 1. DATA ENGINE ---
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

portfolio_data = [
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34128, "Owner": "MV"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37183, "Owner": "MV"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33116, "Owner": "MV"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150894, "Owner": "MV"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16075, "Owner": "MV"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13578, "Owner": "MV"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 78, "PurchaseValAED": 49707, "Owner": "MV"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47720, "Owner": "MV"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 26, "PurchaseValAED": 49949, "Owner": "MV"},
    {"Name": "Meta", "Ticker": "META", "Units": 18, "PurchaseValAED": 48744, "Owner": "MV"},
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2122, "Owner": "SV"},
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1486, "Owner": "SV"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2095, "Owner": "SV"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 2, "PurchaseValAED": 1286, "Owner": "SV"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3179, "Owner": "SV"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 10, "PurchaseValAED": 8989, "Owner": "SV"},
    {"Name": "MSFT [SV]", "Ticker": "MSFT", "Units": 4, "PurchaseValAED": 7476, "Owner": "SV"},
]

with st.spinner('Syncing Market Data...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    try:
        data = yf.download(tickers, period="5d")['Close']
        latest = data.iloc[-1]
        prev = data.iloc[-2]
    except:
        st.stop()

rows = []
for item in portfolio_data:
    t = item["Ticker"]
    try: live = latest[t]; close = prev[t]
    except: live = 0; close = 0
    
    val_aed = live * item["Units"] * USD_TO_AED
    profit = val_aed - item["PurchaseValAED"]
    day_change = (live - close) * item["Units"] * USD_TO_AED
    day_pct = ((live - close) / close) * 100 if close > 0 else 0

    rows.append({
        "Ticker": t, "Name": item["Name"], "Owner": item["Owner"],
        "Value": val_aed, "Profit": profit, "Day": day_change, "Day %": day_pct
    })
df = pd.DataFrame(rows)

# --- 2. LAYOUT: THE "HEADS UP" DISPLAY ---

# Global Stats
total_val = df["Value"].sum()
day_pl = df["Day"].sum()
inr_lac = (total_val * AED_TO_INR) / 100000

# Metric Row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Liquidation", f"Dh {total_val:,.0f}")
c2.metric("Today's P&L", f"{day_pl:+,.0f}", delta=f"{(day_pl/total_val):.2%}")
c3.metric("INR Wealth", f"₹ {inr_lac:,.2f} L")
# Allocation Bar
mv_pct = (df[df["Owner"]=="MV"]["Value"].sum() / total_val) * 100
c4.caption(f"**Allocation:** MV {mv_pct:.0f}% | SV {100-mv_pct:.0f}%")
c4.progress(int(mv_pct))

st.divider()

# --- 3. THE VISUAL CORE (TREEMAP + MOVERS) ---
# This is where we separate "Dashboard" from "Table"

col_map, col_movers = st.columns([2, 1])

with col_map:
    st.subheader("Market Map (Size = Value)")
    # TREEMAP: The institutional way to see risk
    fig = px.treemap(
        df, 
        path=[px.Constant("Portfolio"), 'Owner', 'Ticker'], 
        values='Value',
        color='Day %',
        color_continuous_scale=['#d73027', '#fee08b', '#1a9850'], # Red to Green
        color_continuous_midpoint=0,
        custom_data=['Day %', 'Value']
    )
    fig.update_traces(
        textposition="middle center",
        textinfo="label+text+value",
        hovertemplate='<b>%{label}</b><br>Value: Dh %{value:,.0f}<br>Change: %{customdata[0]:.2f}%'
    )
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=400)
    st.plotly_chart(fig, use_container_width=True)

with col_movers:
    st.subheader("Today's Movers")
    
    # Sort for bar chart
    movers = df.sort_values("Day %", ascending=False)
    top_3 = movers.head(3)
    bot_3 = movers.tail(3).sort_values("Day %", ascending=True) # Sort for visual bar logic
    
    # Combined Bar Chart
    fig_movers = go.Figure()
    
    # Winners
    fig_movers.add_trace(go.Bar(
        y=top_3["Ticker"], x=top_3["Day %"], orientation='h',
        name="Winners", marker_color='#1a9850', texttemplate="%{x:.1f}%", textposition="inside"
    ))
    
    # Losers
    fig_movers.add_trace(go.Bar(
        y=bot_3["Ticker"], x=bot_3["Day %"], orientation='h',
        name="Losers", marker_color='#d73027', texttemplate="%{x:.1f}%", textposition="inside"
    ))
    
    fig_movers.update_layout(
        barmode='relative', 
        height=400,
        margin=dict(t=0, b=0),
        xaxis_title="Daily Change %",
        yaxis=dict(autorange="reversed"), # Top movers at top
        showlegend=False
    )
    st.plotly_chart(fig_movers, use_container_width=True)

# --- 4. THE DATA GRID (RELEGATED TO BOTTOM) ---
with st.expander("View Detailed Ledger", expanded=False):
    st.dataframe(
        df.style.format({
            "Value": "{:,.0f}", "Profit": "{:+,.0f}", "Day": "{:+,.0f}", "Day %": "{:+.2f}%"
        }).background_gradient(subset=["Day %"], cmap="RdYlGn", vmin=-3, vmax=3),
        use_container_width=True, hide_index=True
    )
