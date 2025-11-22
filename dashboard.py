import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Wealth Dashboard")

# --- CUSTOM CSS (INSTITUTIONAL THEME) ---
st.markdown("""
<style>
    /* 1. TIGHTEN VERTICAL RHYTHM */
    .block-container { 
        padding-top: 2rem; 
        padding-bottom: 2rem;
    }
    
    /* 2. INSTITUTIONAL METRICS */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
    }
    
    /* 3. TABLE TYPOGRAPHY */
    .dataframe { 
        font-family: 'Roboto Mono', monospace !important; 
        font-size: 0.85rem !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

# --- 1. HARDCODED DATA (Source of Truth) ---
portfolio_data = [
    # MV STOCKS
    {"Name": "Alphabet",      "Ticker": "GOOGL", "Units": 51,  "AvgCost": 182.34, "PurchaseValAED": 34128,  "Owner": "MV"},
    {"Name": "Apple",         "Ticker": "AAPL",  "Units": 50,  "AvgCost": 202.63, "PurchaseValAED": 37183,  "Owner": "MV"},
    {"Name": "Tesla",         "Ticker": "TSLA",  "Units": 30,  "AvgCost": 300.78, "PurchaseValAED": 33116,  "Owner": "MV"},
    {"Name": "Nasdaq 100",    "Ticker": "QQQM",  "Units": 180, "AvgCost": 228.42, "PurchaseValAED": 150894, "Owner": "MV"},
    {"Name": "AMD",           "Ticker": "AMD",   "Units": 27,  "AvgCost": 162.23, "PurchaseValAED": 16075,  "Owner": "MV"},
    {"Name": "Broadcom",      "Ticker": "AVGO",  "Units": 13,  "AvgCost": 284.59, "PurchaseValAED": 13578,  "Owner": "MV"},
    {"Name": "Nvidia",        "Ticker": "NVDA",  "Units": 78,  "AvgCost": 173.64, "PurchaseValAED": 49707,  "Owner": "MV"},
    {"Name": "Amazon",        "Ticker": "AMZN",  "Units": 59,  "AvgCost": 220.38, "PurchaseValAED": 47720,  "Owner": "MV"},
    {"Name": "MSFT",          "Ticker": "MSFT",  "Units": 26,  "AvgCost": 523.46, "PurchaseValAED": 49949,  "Owner": "MV"},
    {"Name": "Meta",          "Ticker": "META",  "Units": 18,  "AvgCost": 737.87, "PurchaseValAED": 48744,  "Owner": "MV"},

    # SV STOCKS
    {"Name": "Broadcom [SV]", "Ticker": "AVGO",  "Units": 2,   "AvgCost": 289.06, "PurchaseValAED": 2122,   "Owner": "SV"},
    {"Name": "Apple [SV]",    "Ticker": "AAPL",  "Units": 2,   "AvgCost": 202.41, "PurchaseValAED": 1486,   "Owner": "SV"},
    {"Name": "Nasdaq [SV]",   "Ticker": "QQQ",   "Units": 1,   "AvgCost": 570.80, "PurchaseValAED": 2095,   "Owner": "SV"},
    {"Name": "Nvidia [SV]",   "Ticker": "NVDA",  "Units": 2,   "AvgCost": 175.27, "PurchaseValAED": 1286,   "Owner": "SV"},
    {"Name": "Amazon [SV]",   "Ticker": "AMZN",  "Units": 4,   "AvgCost": 216.54, "PurchaseValAED": 3179,   "Owner": "SV"},
    {"Name": "Novo [SV]",     "Ticker": "NVO",   "Units": 4,   "AvgCost": 48.61,  "PurchaseValAED": 714,    "Owner": "SV"},
    {"Name": "Nasdaq 100 [SV]","Ticker": "QQQM", "Units": 10,  "AvgCost": 244.94, "PurchaseValAED": 8989,   "Owner": "SV"},
    {"Name": "MSFT [SV]",     "Ticker": "MSFT",  "Units": 4,   "AvgCost": 509.25, "PurchaseValAED": 7476,   "Owner": "SV"},
]

# --- 2. DATA ENGINE ---
with st.spinner('Syncing...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    try:
        data = yf.download(tickers, period="5d")['Close']
        if not data.empty:
            latest = data.iloc[-1]
            prev = data.iloc[-2]
        else:
            st.stop()
    except:
        st.stop()

processed_rows = []
for item in portfolio_data:
    t = item["Ticker"]
    try:
        # Safe Get
        live = latest[t] if t in latest else 0
        close = prev[t] if t in prev else 0
    except:
        live = 0; close = 0
        
    # CALCS
    val_aed = live * item["Units"] * USD_TO_AED
    profit_aed = val_aed - item["PurchaseValAED"]
    profit_pct = (profit_aed / item["PurchaseValAED"]) if item["PurchaseValAED"] > 0 else 0
    day_aed = (live - close) * item["Units"] * USD_TO_AED
    day_pct = (live - close) / close if close > 0 else 0

    processed_rows.append({
        "Ticker": item["Name"],
        "Owner": item["Owner"],
        "Units": item["Units"],
        "Price": live,
        "Value": val_aed,
        "Total P&L": profit_aed,
        "Total %": profit_pct,
        "1D P&L": day_aed,
        "1D %": day_pct
    })

df = pd.DataFrame(processed_rows)

# --- 3. LAYOUT & VISUALS ---

# METRICS DECK
total_val = df["Value"].sum()
total_pl = df["Total P&L"].sum()
day_pl = df["1D P&L"].sum()
inr_val = (total_val * AED_TO_INR) / 100000

m1, m2, m3, m4 = st.columns(4)
m1.metric("Net Liquidation (AED)", f"{total_val:,.0f}")
m2.metric("Daily P&L (AED)", f"{day_pl:+,.0f}", delta=f"{(day_pl/(total_val-day_pl)):.2%}")
m3.metric("Total P&L (AED)", f"{total_pl:+,.0f}", delta=f"{(total_pl/(total_val-total_pl)):.2%}")
m4.metric("Net Worth (INR Lacs)", f"₹ {inr_val:,.2f} L")

# ALLOCATION STRIP (Slim Version)
mv_total = df[df["Owner"]=="MV"]["Value"].sum()
sv_total = df[df["Owner"]=="SV"]["Value"].sum()
mv_pct = (mv_total / total_val) * 100
sv_pct = (sv_total / total_val) * 100

fig = go.Figure()
fig.add_trace(go.Bar(
    y=[''], x=[mv_total], name='MV', orientation='h',
    marker=dict(color='#3b82f6', line=dict(width=0)), # Muted Blue
    hoverinfo='text', hovertext=f'MV: {mv_pct:.1f}%'
))
fig.add_trace(go.Bar(
    y=[''], x=[sv_total], name='SV', orientation='h',
    marker=dict(color='#8b5cf6', line=dict(width=0)), # Muted Purple
    hoverinfo='text', hovertext=f'SV: {sv_pct:.1f}%'
))
fig.update_layout(
    barmode='stack', height=20, margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(visible=False), yaxis=dict(visible=False),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# TACTICAL GRID
def color_numbers(val):
    if val > 0: return 'color: #16a34a; font-weight: 500' # Emerald 600
    if val < 0: return 'color: #dc2626; font-weight: 500' # Red 600
    return 'color: #6b7280'

def badge_owner(val):
    bg = '#eff6ff' if val == 'MV' else '#f3e8fd'
    txt = '#1d4ed8' if val == 'MV' else '#7e22ce'
    return f'background-color: {bg}; color: {txt}; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8em'

styler = df.style.format({
    "Price": "${:,.2f}",
    "Value": "{:,.0f}",
    "Total P&L": "{:+,.0f}",
    "Total %": "{:+.1%}",
    "1D P&L": "{:+,.0f}",
    "1D %": "{:+.1%}"
})
styler = styler.map(color_numbers, subset=["Total P&L", "Total %", "1D P&L", "1D %"])
styler = styler.map(badge_owner, subset=["Owner"])

st.dataframe(
    styler,
    use_container_width=True,
    height=800,
    hide_index=True, # THIS REMOVES THE 0,1,2...
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
        "Units": st.column_config.NumberColumn("Units", format="%.0f"),
        "Value": st.column_config.NumberColumn("Value (AED)"),
    }
)
