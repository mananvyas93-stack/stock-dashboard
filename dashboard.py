import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 0. PAGE SETUP ---
st.set_page_config(layout="wide", page_title="Wealth Cockpit v2.1")

# --- 1. STYLES ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    [data-testid="stMetricValue"] { font-family: 'Roboto Mono', monospace; font-size: 1.6rem; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 1rem;
    }
    .modebar { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
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

with st.spinner('Fetching Data...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    try:
        data = yf.download(tickers, period="5d")['Close']
        latest = data.iloc[-1]; prev = data.iloc[-2]
    except:
        st.stop()

rows = []
for item in portfolio_data:
    t = item["Ticker"]
    try: live = latest[t]; close = prev[t]
    except: live = 0; close = 0
    
    val = live * item["Units"] * USD_TO_AED
    prof = val - item["PurchaseValAED"]
    day = (live - close) * item["Units"] * USD_TO_AED
    pct = ((live - close) / close) * 100 if close > 0 else 0
    
    # PRE-FORMAT STRINGS FOR CHARTS (The "Bulletproof" Fix)
    # We create a string column that combines Ticker + Value + %
    # e.g. "GOOGL<br>+1.2%<br>Dh 50k"
    val_str = f"Dh {val/1000:.1f}k"
    pct_str = f"{pct:+.1f}%"
    label_html = f"<span style='font-weight:bold; font-size:14px'>{t}</span><br><span style='color:#ccc'>{pct_str}</span><br>{val_str}"

    rows.append({
        "Ticker": t, "Owner": item["Owner"], "Value": val, 
        "Profit": prof, "Day": day, "Day %": pct,
        "Label": label_html # New Column
    })
df = pd.DataFrame(rows)

# --- 3. DASHBOARD LAYOUT ---

# Title with Version Badge
st.caption("FAMILY WEALTH COCKPIT • v2.1")

# METRICS
total_val = df["Value"].sum()
day_pl = df["Day"].sum()
total_pl = df["Profit"].sum()
inr_lac = (total_val * AED_TO_INR) / 100000

k1, k2, k3, k4 = st.columns(4)
k1.metric("Net Liquidation", f"{total_val:,.0f}", delta=None)
k2.metric("Daily P&L", f"{day_pl:+,.0f}", delta=f"{(day_pl/total_val):.2%}")
k3.metric("Total P&L", f"{total_pl:+,.0f}", delta=f"{(total_pl/(total_val-total_pl)):.2%}")
k4.metric("INR Wealth", f"₹ {inr_lac:,.2f} L")

st.markdown("---")

# MAIN CHARTS
c_map, c_rail = st.columns([2, 1])

with c_map:
    st.subheader("Risk Map")
    fig_map = px.treemap(
        df, path=[px.Constant("Portfolio"), 'Owner', 'Ticker'], values='Value',
        color='Day %', color_continuous_scale=['#da3633', '#21262d', '#238636'],
        color_continuous_midpoint=0, range_color=[-3, 3]
    )
    # USE THE PRE-FORMATTED LABEL COLUMN
    fig_map.update_traces(text=df['Label'], textinfo='text') 
    fig_map.update_layout(margin=dict(t=0,l=0,r=0,b=0), height=500, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_map, use_container_width=True)

with c_rail:
    st.subheader("Top Movers")
    movers = df.sort_values("Day %", ascending=False)
    top = movers.head(3); bot = movers.tail(3).sort_values("Day %", ascending=True)
    
    fig_mov = go.Figure()
    fig_mov.add_trace(go.Bar(
        y=top["Ticker"], x=top["Day %"], orientation='h',
        marker_color='#238636', texttemplate="%{x:+.1f}%", textposition="inside"
    ))
    fig_mov.add_trace(go.Bar(
        y=bot["Ticker"], x=bot["Day %"], orientation='h',
        marker_color='#da3633', texttemplate="%{x:+.1f}%", textposition="inside"
    ))
    fig_mov.update_layout(
        barmode='relative', height=250, margin=dict(t=0,b=0,l=0,r=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(color='#999')),
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_mov, use_container_width=True)

    st.subheader("Allocation")
    mv = df[df["Owner"]=="MV"]["Value"].sum()
    fig_don = go.Figure(go.Pie(
        labels=['MV', 'SV'], values=[mv, total_val-mv], hole=.7,
        marker=dict(colors=['#1f6feb', '#8957e5']), textinfo='none'
    ))
    fig_don.update_layout(
        height=180, margin=dict(t=0,b=0,l=0,r=0), showlegend=False,
        annotations=[dict(text=f"MV<br>{mv/total_val:.0%}", showarrow=False, font_size=20, font_color="#fff")]
    )
    st.plotly_chart(fig_don, use_container_width=True)

st.markdown("---")
with st.expander("Ledger Details"):
    st.dataframe(df, hide_index=True, use_container_width=True)
