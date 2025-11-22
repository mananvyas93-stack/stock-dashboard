import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Wealth Dashboard")

# --- CONFIGURATION ---
# We still need this to convert the LIVE price to AED.
# But we will NOT use it for your purchase history anymore.
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

# --- CUSTOM CSS ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #4CAF50; 
    }
</style>
""", unsafe_allow_html=True)

st.title("Family Wealth Dashboard 🇦🇪")

# --- 1. PORTFOLIO DATA (EXACTLY FROM YOUR XLS) ---
# I have updated 'PurchaseValAED' and 'AvgCost' to match your sheet exactly.
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
with st.spinner('Refreshing Portfolio...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    data = yf.download(tickers, period="5d")['Close']

    if not data.empty:
        latest_prices = data.iloc[-1]
        prev_prices = data.iloc[-2]
    else:
        st.error("Data Error.")
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
    # WE USE YOUR HARDCODED VALUES NOW
    invested_val_aed = item["PurchaseValAED"] 
    cost_price_usd = item["AvgCost"]
    
    # Live Calculations
    current_val_aed = live_price * units * USD_TO_AED
    
    # Profit is now: (Live Value) - (YOUR HARDCODED COST)
    profit_aed = current_val_aed - invested_val_aed
    
    # Profit % based on your Avg Cost
    profit_pct = ((live_price - cost_price_usd) / cost_price_usd) if cost_price_usd > 0 else 0
    
    # Day's Gain
    day_gain_usd = live_price - prev_price
    day_gain_aed = day_gain_usd * units * USD_TO_AED
    day_gain_pct = (day_gain_usd / prev_price) if prev_price > 0 else 0

    processed_rows.append({
        "Stock": item["Name"],
        "Owner": item["Owner"],
        "Units": units,
        "Price ($)": live_price,
        "Value (AED)": current_val_aed,
        "Profit (AED)": profit_aed,
        "Profit %": profit_pct,
        "Day Gain (AED)": day_gain_aed,
        "Day Gain %": day_gain_pct
    })

df = pd.DataFrame(processed_rows)

# --- 4. VISUALS ---

# Totals
total_val = df["Value (AED)"].sum()
total_profit = df["Profit (AED)"].sum()
total_day_gain = df["Day Gain (AED)"].sum()
total_inr = (total_val * AED_TO_INR) / 100000

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Value", f"Dh {total_val:,.0f}")
col2.metric("Total Profit", f"Dh {total_profit:,.0f}", delta=f"{(total_profit/total_val)*100:.1f}%")
col3.metric("Day's Gain", f"Dh {total_day_gain:,.0f}", delta=f"{(total_day_gain/(total_val-total_day_gain))*100:.1f}%")
col4.metric("INR Value", f"₹ {total_inr:,.2f} L")

st.divider()

# Layout: Chart left, Table right
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Allocation")
    fig = px.pie(df, values='Value (AED)', names='Stock', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Holdings")
    
    def color_profit(val):
        color = '#d4edda' if val > 0 else '#f8d7da'
        text_color = '#155724' if val > 0 else '#721c24'
        return f'background-color: {color}; color: {text_color}'

    styler = df.style.format({
        "Price ($)": "${:,.2f}",
        "Value (AED)": "Dh {:,.0f}",
        "Profit (AED)": "Dh {:,.0f}",
        "Profit %": "{:.1%}",
        "Day Gain (AED)": "Dh {:,.0f}",
        "Day Gain %": "{:.1%}"
    }).map(color_profit, subset=["Profit (AED)", "Profit %", "Day Gain (AED)", "Day Gain %"])

    st.dataframe(styler, use_container_width=True, height=700)
