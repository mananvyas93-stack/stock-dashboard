import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 0. PAGE SETUP (INSTITUTIONAL MODE) ---
st.set_page_config(layout="wide", page_title="Family Wealth Cockpit")

# --- 1. DESIGN SYSTEM INJECTION ---
st.markdown("""
<style>
    /* GLOBAL RESET */
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    
    /* TYPOGRAPHY */
    h1, h2, h3, p, div { font-family: 'Inter', sans-serif; }
    .metric-value, [data-testid="stMetricValue"] { 
        font-family: 'Roboto Mono', monospace !important; 
        font-weight: 600;
    }
    
    /* CARDS (CONTAINERS) */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #0d1117; /* Darker background for contrast */
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.2rem;
    }
    
    /* REMOVE CHART PADDING */
    .js-plotly-plot .plotly .modebar { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

# Hardcoded Source of Truth
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

# Fetch Data
with st.spinner('Syncing Market Data...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    try:
        # Fetch 5 days to handle weekends/holidays safely
        data = yf.download(tickers, period="5d")['Close']
        if not data.empty:
            latest = data.iloc[-1]
            prev = data.iloc[-2]
        else:
            st.error("Market Data Error")
            st.stop()
    except:
        st.stop()

# Process Data
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

# Aggregates
total_val = df["Value"].sum()
day_pl = df["Day"].sum()
total_pl = df["Profit"].sum()
inr_lac = (total_val * AED_TO_INR) / 100000

# --- 3. UI LAYER: COCKPIT ---

st.caption(f"FAMILY WEALTH COCKPIT • {pd.Timestamp.now().strftime('%d %b %Y')}")

# SECTION A: KPI STRIP
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Net Liquidation (AED)", f"{total_val:,.0f}", delta=None)
kpi2.metric("Daily P&L (AED)", f"{day_pl:+,.0f}", delta=f"{(day_pl/total_val):.2%}")
kpi3.metric("Total P&L (AED)", f"{total_pl:+,.0f}", delta=f"{(total_pl/(total_val-total_pl)):.2%}")
kpi4.metric("Net Worth (INR Lacs)", f"₹ {inr_lac:,.2f}", delta=None)

st.markdown("---") 

# SECTION B: THE MAIN GRID (2:1 Ratio)
col_main, col_rail = st.columns([2, 1])

with col_main:
    st.subheader("Risk Map")
    # TREEMAP
    fig_map = px.treemap(
        df, 
        path=[px.Constant("Portfolio"), 'Owner', 'Ticker'], 
        values='Value',
        color='Day %',
        color_continuous_scale=['#da3633', '#21262d', '#238636'], # Red -> Dark Grey -> Green
        color_continuous_midpoint=0,
        range_color=[-3, 3] 
    )
    # FIX: Format numbers to 2 decimals and use 'k' for thousands
    fig_map.update_traces(
        texttemplate="<span style='font-size:15px; font-weight:700'>%{label}</span><br>%{customdata[0]:+.2f}%<br>Dh %{value:.2s}", 
        textposition="middle center",
        customdata=df[['Day %']]
    )
    fig_map.update_layout(
        margin=dict(t=0, l=0, r=0, b=0), 
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_rail:
    st.subheader("Top Movers")
    
    # Sort Data
    movers = df.sort_values("Day %", ascending=False)
    top_3 = movers.head(3)
    bot_3 = movers.tail(3).sort_values("Day %", ascending=True)
    
    # BAR CHART
    fig_movers = go.Figure()
    
    # Winners (Green)
    fig_movers.add_trace(go.Bar(
        y=top_3["Ticker"], x=top_3["Day %"], orientation='h',
        name="Winners", marker_color='#238636', 
        # FIX: Explicitly format to 2 decimals
        texttemplate="%{x:+.2f}%", textposition="inside",
        hovertemplate="%{y}: %{x:.2f}%"
    ))
    
    # Losers (Red)
    fig_movers.add_trace(go.Bar(
        y=bot_3["Ticker"], x=bot_3["Day %"], orientation='h',
        name="Losers", marker_color='#da3633', 
        # FIX: Explicitly format to 2 decimals
        texttemplate="%{x:+.2f}%", textposition="inside",
        hovertemplate="%{y}: %{x:.2f}%"
    ))
    
    fig_movers.update_layout(
        barmode='relative', 
        height=250,
        margin=dict(t=0, b=0, l=0, r=0),
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='#30363d', showticklabels=False),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(color='#8b949e', size=12)),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_movers, use_container_width=True)
    
    # ALLOCATION MINI-CHART
    st.subheader("Allocation")
    mv_val = df[df["Owner"]=="MV"]["Value"].sum()
    sv_val = df[df["Owner"]=="SV"]["Value"].sum()
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=['MV', 'SV'], 
        values=[mv_val, sv_val], 
        hole=.7,
        marker=dict(colors=['#1f6feb', '#8957e5']),
        textinfo='none' # Clean look, no messy labels on the ring
    )])
    fig_donut.update_layout(
        height=180, 
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=False,
        # Center Text
        annotations=[dict(text=f"MV<br>{(mv_val/total_val):.0%}", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#f0f6fc")]
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# --- 4. NAVIGATION TO DETAILS ---
st.markdown("---")
col_btn1, col_btn2 = st.columns([6, 1])
with col_btn2:
    st.button("View Ledger →", type="primary")
