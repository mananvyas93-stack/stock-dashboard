import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide", page_title="Family Portfolio")

# --- CONFIGURATION ---
USD_TO_AED = 3.6725  # Fixed peg
# We estimate INR rate (or you could fetch this live too)
AED_TO_INR = 23.0    

st.title("Family Wealth Dashboard 🇦🇪")

# --- 1. YOUR PORTFOLIO DATA (EDIT THIS LIST TO UPDATE HOLDINGS) ---
# I transcribed this from your screenshot. Please check the "Ticker" column carefully!
portfolio_data = [
    # MANAN'S STOCKS
    {"Name": "Alphabet",      "Ticker": "GOOGL", "Units": 51,  "Cost": 182, "Owner": "Manan"},
    {"Name": "Apple",         "Ticker": "AAPL",  "Units": 50,  "Cost": 203, "Owner": "Manan"},
    {"Name": "Tesla",         "Ticker": "TSLA",  "Units": 30,  "Cost": 301, "Owner": "Manan"},
    {"Name": "Nasdaq 100",    "Ticker": "QQQM",  "Units": 180, "Cost": 228, "Owner": "Manan"}, # Guessed QQQM based on price
    {"Name": "AMD",           "Ticker": "AMD",   "Units": 27,  "Cost": 162, "Owner": "Manan"},
    {"Name": "Broadcom",      "Ticker": "AVGO",  "Units": 13,  "Cost": 285, "Owner": "Manan"},
    {"Name": "Nvidia",        "Ticker": "NVDA",  "Units": 78,  "Cost": 174, "Owner": "Manan"},
    {"Name": "Amazon",        "Ticker": "AMZN",  "Units": 59,  "Cost": 220, "Owner": "Manan"},
    {"Name": "MSFT",          "Ticker": "MSFT",  "Units": 26,  "Cost": 523, "Owner": "Manan"},
    {"Name": "Meta",          "Ticker": "META",  "Units": 18,  "Cost": 738, "Owner": "Manan"},

    # SAE'S STOCKS ([SV])
    {"Name": "Broadcom [SV]", "Ticker": "AVGO",  "Units": 2,   "Cost": 289, "Owner": "Sae"},
    {"Name": "Apple [SV]",    "Ticker": "AAPL",  "Units": 2,   "Cost": 202, "Owner": "Sae"},
    {"Name": "Nasdaq [SV]",   "Ticker": "QQQ",   "Units": 1,   "Cost": 571, "Owner": "Sae"}, # Guessed QQQ based on price
    {"Name": "Nvidia [SV]",   "Ticker": "NVDA",  "Units": 2,   "Cost": 175, "Owner": "Sae"},
    {"Name": "Amazon [SV]",   "Ticker": "AMZN",  "Units": 4,   "Cost": 217, "Owner": "Sae"},
    {"Name": "Novo [SV]",     "Ticker": "NVO",   "Units": 4,   "Cost": 49,  "Owner": "Sae"},
    {"Name": "MSFT [SV]",     "Ticker": "MSFT",  "Units": 4,   "Cost": 509, "Owner": "Sae"},
]

# --- 2. FETCH LIVE PRICES ---
with st.spinner('Fetching live market prices...'):
    tickers = [item["Ticker"] for item in portfolio_data]
    # Download all data at once for speed
    data = yf.download(tickers, period="1d")['Close']
    
    # Get the latest price for each stock
    # (Handle cases where only 1 row of data comes back)
    if len(data) > 0:
        latest_prices = data.iloc[-1]
    else:
        st.error("Could not fetch data.")
        st.stop()

# --- 3. CALCULATE VALUES ---
processed_rows = []

for item in portfolio_data:
    ticker = item["Ticker"]
    try:
        # Get live price (handle if ticker is missing)
        live_price = latest_prices[ticker] if ticker in latest_prices else 0
    except:
        live_price = 0
        
    units = item["Units"]
    cost_price = item["Cost"]
    
    # Calculations
    current_value_usd = live_price * units
    current_value_aed = current_value_usd * USD_TO_AED
    purchase_value_aed = cost_price * units * USD_TO_AED
    profit_aed = current_value_aed - purchase_value_aed
    profit_pct = ((live_price - cost_price) / cost_price) * 100 if cost_price > 0 else 0
    
    processed_rows.append({
        "Stock": item["Name"],
        "Owner": item["Owner"],
        "Units": units,
        "Live Price ($)": live_price,
        "Current Value (AED)": current_value_aed,
        "Profit (AED)": profit_aed,
        "Profit %": profit_pct
    })

df = pd.DataFrame(processed_rows)

# --- 4. DISPLAY DASHBOARD ---

# Calculate Totals
total_value_aed = df["Current Value (AED)"].sum()
total_profit_aed = df["Profit (AED)"].sum()
total_value_inr_lacs = (total_value_aed * AED_TO_INR) / 100000

# Top Metrics (Joint View)
st.header("Joint Portfolio Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Value (AED)", f"Dh {total_value_aed:,.0f}")
col2.metric("Total Profit (AED)", f"Dh {total_profit_aed:,.0f}", delta_color="normal")
col3.metric("Total Value (INR Lacs)", f"₹ {total_value_inr_lacs:,.2f} L")

st.divider()

# Tabs for Individual Views
tab1, tab2, tab3 = st.tabs(["👨🏻‍💻 Manan's View", "👩🏻‍💼 Sae's View", "📊 Joint Data"])

def show_portfolio_table(dataframe):
    # Format the columns for display
    display_df = dataframe.copy()
    display_df["Live Price ($)"] = display_df["Live Price ($)"].map("${:,.2f}".format)
    display_df["Current Value (AED)"] = display_df["Current Value (AED)"].map("Dh {:,.0f}".format)
    display_df["Profit (AED)"] = display_df["Profit (AED)"].map("Dh {:,.0f}".format)
    display_df["Profit %"] = display_df["Profit %"].map("{:,.1f}%".format)
    
    # Color the profit column logic? (Streamlit handles dataframe display nicely by default now)
    st.dataframe(
        display_df[["Stock", "Units", "Live Price ($)", "Current Value (AED)", "Profit (AED)", "Profit %"]],
        use_container_width=True,
        hide_index=True
    )

with tab1:
    st.subheader("Manan's Holdings")
    manan_df = df[df["Owner"] == "Manan"]
    
    # Mini metrics for Manan
    m_val = manan_df["Current Value (AED)"].sum()
    m_prof = manan_df["Profit (AED)"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Manan Value", f"Dh {m_val:,.0f}")
    c2.metric("Manan Profit", f"Dh {m_prof:,.0f}")
    
    show_portfolio_table(manan_df)

with tab2:
    st.subheader("Sae's Holdings")
    sae_df = df[df["Owner"] == "Sae"]
    
    # Mini metrics for Sae
    s_val = sae_df["Current Value (AED)"].sum()
    s_prof = sae_df["Profit (AED)"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Sae Value", f"Dh {s_val:,.0f}")
    c2.metric("Sae Profit", f"Dh {s_prof:,.0f}")
    
    show_portfolio_table(sae_df)

with tab3:
    st.subheader("All Holdings Combined")
    show_portfolio_table(df)
