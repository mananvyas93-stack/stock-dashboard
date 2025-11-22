import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG (Browser Title & Layout) ---
st.set_page_config(layout="wide", page_title="Wealth Dashboard")

# --- CONFIGURATION ---
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

# --- CUSTOM CSS (To fix the boring look) ---
st.markdown("""
<style>
    /* Make metrics pop */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #4CAF50; 
    }
</style>
""", unsafe_allow_html=True)

st.title("Family Wealth Dashboard 🇦🇪")

# --- 1. PORTFOLIO DATA (ANONYMIZED) ---
portfolio_data = [
    # MV STOCKS
    {"Name": "Alphabet",      "Ticker": "GOOGL", "Units": 51,  "Cost": 182, "Owner": "MV"},
    {"Name": "Apple",         "Ticker": "AAPL",  "Units": 50,  "Cost": 203, "Owner": "MV"},
    {"Name": "Tesla",         "Ticker": "TSLA",  "Units": 30,  "Cost": 301, "Owner": "MV"},
    {"Name": "Nasdaq 100",    "Ticker": "QQQM",  "Units": 180, "Cost": 228, "Owner": "MV"},
    {"Name": "AMD",           "Ticker": "AMD",   "Units": 27,  "Cost": 162, "Owner": "MV"},
    {"Name": "Broadcom",      "Ticker": "AVGO",  "Units": 13,  "Cost": 285, "Owner": "MV"},
    {"Name": "Nvidia",        "Ticker": "NVDA",  "Units": 78,  "Cost": 174, "Owner": "MV"},
    {"Name": "Amazon",        "Ticker": "AMZN",  "Units": 59,  "Cost": 220, "Owner": "MV"},
    {"Name": "MSFT",          "Ticker": "MSFT",  "Units": 26,  "Cost": 523, "Owner": "MV"},
    {"Name": "Meta",          "Ticker": "META",  "Units": 18,  "Cost": 738, "Owner": "MV"},

    # SV STOCKS
    {"Name": "Broadcom [SV]", "Ticker": "AVGO",  "Units": 2,   "Cost": 289, "Owner": "SV"},
    {"Name": "Apple [SV]",    "Ticker": "AAPL",  "Units": 2,   "Cost": 202, "Owner": "SV"},
    {"Name": "Nasdaq [SV]",   "Ticker": "QQQ",   "Units": 1,   "Cost": 571, "Owner": "SV"},
    {"Name": "Nvidia [SV]",   "Ticker": "NVDA",  "Units": 2,   "Cost": 175, "Owner": "SV"},
    {"Name": "Amazon [SV]",   "Ticker": "AMZN",  "Units": 4,   "Cost": 217, "Owner": "SV"},
    {"Name": "Novo [SV]",     "Ticker": "NVO",   "Units": 4,   "Cost": 49,  "Owner": "SV"},
    {"Name": "MSFT [SV]",     "Ticker": "MSFT",  "Units": 4,   "Cost": 509, "Owner": "SV"},
]

# --- 2. FETCH DATA (LIVE) ---
with st.spinner('Fetching market data...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    # Get 5 days of data to ensure we find yesterday's close
    data = yf.download(tickers, period="5d")['Close']

    # Handle data availability
    if not data.empty:
        latest_prices = data.iloc[-1] # Today
        prev_prices = data.iloc[-2]   # Yesterday
    else:
        st.error("Failed to download data.")
        st.stop()

# --- 3. CALCULATE ALL METRICS ---
processed_rows = []

for item in portfolio_data:
    ticker = item["Ticker"]
    
    # Safe price fetch
    try:
        live_price = latest_prices[ticker] if ticker in latest_prices else 0
        yesterday_price = prev_prices[ticker] if ticker in prev_prices else 0
    except:
        live_price = 0
        yesterday_price = 0
        
    units = item["Units"]
    cost_price = item["Cost"]
    
    # Value Calcs
    current_val_aed = live_price * units * USD_TO_AED
    invested_val_aed = cost_price * units * USD_TO_AED
    
    # Profit Calcs
    profit_aed = current_val_aed - invested_val_aed
    profit_pct = ((live_price - cost_price) / cost_price) * 100 if cost_price > 0 else 0
    
    # Day Gain Calcs
    day_gain_per_share = live_price - yesterday_price
    day_gain_aed = day_gain_per_share * units * USD_TO_AED
    day_gain_pct = ((live_price - yesterday_price) / yesterday_price) * 100 if yesterday_price > 0 else 0

    processed_rows.append({
        "Stock": item["Name"],
        "Owner": item["Owner"],
        "Units": units,
        "Price ($)": live_price,
        "Value (AED)": current_val_aed,
        "Profit (AED)": profit_aed,
        "Profit %": profit_pct / 100, # Divide by 100 for formatting later
        "Day Gain (AED)": day_gain_aed,
        "Day Gain %": day_gain_pct / 100
    })

df = pd.DataFrame(processed_rows)

# --- 4. VISUALS & DASHBOARD ---

# Aggregates
total_val = df["Value (AED)"].sum()
total_profit = df["Profit (AED)"].sum()
total_day_gain = df["Day Gain (AED)"].sum()
total_inr = (total_val * AED_TO_INR) / 100000

# 4A. Top Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Value", f"Dh {total_val:,.0f}")
col2.metric("Total Profit", f"Dh {total_profit:,.0f}", delta=f"{(total_profit/total_val)*100:.1f}%")
col3.metric("Day's Gain", f"Dh {total_day_gain:,.0f}", delta=f"{(total_day_gain/(total_val-total_day_gain))*100:.1f}%")
col4.metric("INR Value", f"₹ {total_inr:,.2f} L")

st.divider()

# 4B. Allocation Chart (The "Fancy" Visual)
col_chart, col_data = st.columns([1, 2])

with col_chart:
    st.subheader("Allocation")
    # Simple Donut Chart
    fig = px.pie(df, values='Value (AED)', names='Stock', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("Detailed Holdings")
    
    # 4C. THE FANCY TABLE (Conditional Formatting)
    # We create a Styler object to color the cells
    def color_profit(val):
        color = '#d4edda' if val > 0 else '#f8d7da' # Green vs Red background
        text_color = '#155724' if val > 0 else '#721c24'
        return f'background-color: {color}; color: {text_color}'

    # Apply styling
    styler = df.style.format({
        "Price ($)": "${:,.2f}",
        "Value (AED)": "Dh {:,.0f}",
        "Profit (AED)": "Dh {:,.0f}",
        "Profit %": "{:.1%}",
        "Day Gain (AED)": "Dh {:,.0f}",
        "Day Gain %": "{:.1%}"
    }).map(color_profit, subset=["Profit (AED)", "Profit %", "Day Gain (AED)", "Day Gain %"])

    # Show the table
    st.dataframe(styler, use_container_width=True, height=600)
