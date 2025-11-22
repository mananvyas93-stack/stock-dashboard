import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Wealth Dashboard")

# --- CUSTOM CSS (INSTITUTIONAL THEME) ---
# This forces the UI to look cleaner and more compact
st.markdown("""
<style>
    /* Remove top padding */
    .block-container { padding-top: 2rem; }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.8rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Table font */
    .dataframe { font-family: 'Roboto Mono', monospace !important; font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

# --- 1. HARDCODED PORTFOLIO DATA (SOURCE OF TRUTH) ---
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

# --- 2. FETCH LIVE DATA ---
with st.spinner('Syncing market data...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    try:
        # Fetch 5 days to ensure we get a valid 'Yesterday Close' even on Mondays/Holidays
        data = yf.download(tickers, period="5d")['Close']
        
        if not data.empty:
            latest_prices = data.iloc[-1]
            prev_prices = data.iloc[-2]
        else:
            st.error("No data received from Yahoo Finance.")
            st.stop()
            
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        st.stop()

# --- 3. CALCULATE METRICS ---
processed_rows = []

for item in portfolio_data:
    ticker = item["Ticker"]
    try:
        live_price = latest_prices[ticker] if ticker in latest_prices else 0
        prev_price = prev_prices[ticker] if ticker in prev_prices else 0
    except:
        live_price = 0
        prev_price = 0
        
    units = item["Units"]
    invested_val_aed = item["PurchaseValAED"] 
    
    # Live Value in AED
    current_val_aed = live_price * units * USD_TO_AED
    
    # Profit = Live Value - Hardcoded Cost
    profit_aed = current_val_aed - invested_val_aed
    profit_pct = (profit_aed / invested_val_aed) if invested_val_aed > 0 else 0
    
    # Day's Gain = (Live - Prev) * Units * AED Rate
    day_gain_usd = live_price - prev_price
    day_gain_aed = day_gain_usd * units * USD_TO_AED
    day_gain_pct = (day_gain_usd / prev_price) if prev_price > 0 else 0

    processed_rows.append({
        "Symbol": item["Name"],
        "Owner": item["Owner"],
        "Units": units,
        "Price": live_price,
        "Value (AED)": current_val_aed,
        "Profit (AED)": profit_aed,
        "Profit %": profit_pct, 
        "Day (AED)": day_gain_aed,
        "Day %": day_gain_pct
    })

df = pd.DataFrame(processed_rows)

# --- 4. DASHBOARD LAYOUT ---

# A. HEADER METRICS (The "Bento Box")
total_val = df["Value (AED)"].sum()
total_profit = df["Profit (AED)"].sum()
total_day_gain = df["Day (AED)"].sum()
total_inr = (total_val * AED_TO_INR) / 100000

st.markdown("### Family Wealth Dashboard")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Net Liquidation (AED)", f"{total_val:,.0f}")
m2.metric("Daily P&L (AED)", f"{total_day_gain:,.0f}", delta=f"{(total_day_gain/(total_val-total_day_gain)):.2%}")
m3.metric("Total P&L (AED)", f"{total_profit:,.0f}", delta=f"{(total_profit/(total_val-total_profit)):.2%}")
m4.metric("Net Worth (INR Lacs)", f"₹ {total_inr:,.2f} L")

# B. ALLOCATION STRIP (The "Balance of Power")
mv_total = df[df["Owner"]=="MV"]["Value (AED)"].sum()
sv_total = df[df["Owner"]=="SV"]["Value (AED)"].sum()
mv_pct = (mv_total / total_val) * 100
sv_pct = (sv_total / total_val) * 100

# Create a slim horizontal bar chart using Plotly Graph Objects
fig = go.Figure()
fig.add_trace(go.Bar(
    y=[''], x=[mv_total], name=f'MV ({mv_pct:.0f}%)', orientation='h',
    marker=dict(color='#4b7bec', line=dict(width=0)) # Muted Blue
))
fig.add_trace(go.Bar(
    y=[''], x=[sv_total], name=f'SV ({sv_pct:.0f}%)', orientation='h',
    marker=dict(color='#a55eea', line=dict(width=0)) # Muted Purple
))
fig.update_layout(
    barmode='stack', 
    height=60, 
    margin=dict(l=0, r=0, t=0, b=0),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False,
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
st.caption(f"Allocation: **MV** {mv_pct:.1f}% (Blue) • **SV** {sv_pct:.1f}% (Purple)")

st.divider()

# C. THE TACTICAL GRID (Clean Design)

# Visual Formatting Function
def highlight_vals(val):
    if val > 0:
        return 'color: #0F9D58; font-weight: bold' # Google Green
    elif val < 0:
        return 'color: #D93025; font-weight: bold' # Google Red
    return 'color: #5f6368'

# Badge Logic
def color_owner(val):
    color = '#e8f0fe' if val == 'MV' else '#f3e8fd' # Very light blue vs purple background
    text = '#1967d2' if val == 'MV' else '#8430ce'
    return f'background-color: {color}; color: {text}; border-radius: 4px; padding: 2px 6px; font-weight: bold'

# Apply Styles
styler = df.style.format({
    "Price": "${:,.2f}",
    "Value (AED)": "{:,.0f}",
    "Profit (AED)": "{:+,.0f}", # + sign for positives
    "Profit %": "{:+.1%}",
    "Day (AED)": "{:+,.0f}",
    "Day %": "{:+.1%}"
})

# Apply conditional formatting to specific columns
styler = styler.map(highlight_vals, subset=["Profit (AED)", "Profit %", "Day (AED)", "Day %"])
styler = styler.map(color_owner, subset=["Owner"])

# Render
st.dataframe(
    styler,
    use_container_width=True,
    height=800,
    column_config={
        "Symbol": st.column_config.TextColumn("Ticker", width="medium"),
        "Value (AED)": st.column_config.NumberColumn("Value (AED)", help="Current Market Value"),
    }
)
