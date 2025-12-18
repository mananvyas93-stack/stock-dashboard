import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
from pathlib import Path

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Stocks Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- THEME / CSS ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,400,1,0&display=swap');

    :root {
        --bg: #0f1a2b;
        --card: #16233a;
        --border: #1f2d44;
        --text: #e6eaf0;
        --muted: #9ba7b8;
        --accent: #4aa3ff;
        --accent-soft: #7fc3ff;
        --danger: #f27d72;
        --success: #6bcf8f; /* Vibrant Green for Heatmap */
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: var(--bg);
        color: var(--text);
    }

    header {visibility: hidden;}

    .block-container {
        padding: 0.8rem 0.9rem 2rem;
        max-width: 900px;
    }

    .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 6px 10px;
        box-shadow: none;
        margin-bottom: 8px;
    }

    /* --- KPI CARD STYLING --- */
    .mf-card {
        background: #f4f6f8 !important;
        border-color: #e0e4ea !important;
        color: #0f1a2b !important; /* Default Text Color */
        display: flex;
        flex-direction: column;
        justify-content: space-between; 
        height: 96px; 
        padding: 12px 16px !important; 
        box-sizing: border-box;
    }

    /* --- COLOR CLASSES FOR PROFIT/LOSS (Must override parent !important) --- */
    .kpi-green {
        color: #15803d !important; /* Dark Green for readability on light bg */
    }
    
    .kpi-red {
        color: #b91c1c !important; /* Dark Red */
    }

    /* --- COLOR CORRECTION FOR MUTUAL FUND TAB & WHITE CARDS --- */
    .mf-card .page-title {
        color: #020617 !important; 
        font-weight: 600;
    }

    .mf-card .kpi-label {
        color: #475569; 
        font-weight: 500;
    }

    .mf-card .kpi-value-main {
        color: #0f1a2b; 
        font-weight: 700;
    }
    
    .mf-card .kpi-number {
         color: #0f1a2b; 
    }

    /* --------------------------------------------------------- */

    /* UNIFIED LABEL STYLE: Top/Bottom Labels */
    .kpi-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.6rem; 
        font-weight: 400; /* Normal weight */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.0;
        white-space: nowrap;
        margin: 0;
    }

    /* UNIFIED NUMBER STYLE: Value & Percentage */
    .kpi-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem; 
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.0;
    }
    
    .kpi-value-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.0rem;
        font-weight: 700;
        line-height: 1.1;
    }

    /* Container for the middle row of numbers */
    .kpi-mid-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 0; 
    }

    /* Helper for Top Row Split (Value Left, Return Right) */
    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        width: 100%;
        align-items: flex-end; /* Align bottom so text sits nicely */
    }

    .page-title {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 1.0rem;
        font-weight: 600;
        margin: 0 0 2px 0;
        color: var(--text);
        letter-spacing: 0.01em;
    }

    .page-subtitle {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.75rem;
        color: var(--muted);
        margin: 0;
        letter-spacing: 0.03em;
    }

    .stPlotlyChart {
        background: transparent !important;
    }

    .stTabs {
        margin-top: 0.75rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        align-items: flex-end;
        gap: 0rem;
        width: 100%;
        border-bottom: 1px solid var(--border);
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        position: relative;
        flex: 1 1 25% !important;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.15rem;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.7rem !important;
        padding: 4px 0 3px 0 !important;
        color: #16233a !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
        white-space: nowrap;
        box-sizing: border-box;
    }

    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.6rem !important;
            padding: 4px 0 3px 0 !important;
        }
    }

    .stTabs [role="tab"] {
        min-width: 0 !important;
    }

    .stTabs [data-baseweb="tab"]::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 0;
        background: transparent;
        border: none;
        opacity: 0;
    }

    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        font-weight: 500 !important;
    }

    .stTabs [data-baseweb="tab"]::after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        bottom: -1px;
        height: 2px;
        border-radius: 999px;
        background: transparent;
        transition: background-color 140ms ease-out;
    }

    .stTabs [aria-selected="true"]::after {
        background: #0b1530; 
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS & FALLBACKS ----------
DEFAULT_USD_AED = 3.6725
DEFAULT_AED_INR = 24.50

COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f" # Vibrant Green for Heatmap
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# ---------- PORTFOLIO CONFIG (UPDATED) ----------
# Values calculated at 3.6725 USD/AED based on provided purchase prices
portfolio_config = [
    # --- MV PORTFOLIO ---
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34152, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33138, "Owner": "MV", "Sector": "Auto"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37208, "Owner": "MV", "Sector": "Tech"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16086, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13587, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150997, "Owner": "MV", "Sector": "ETF"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47751, "Owner": "MV", "Sector": "Retail"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 80, "PurchaseValAED": 51051, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Meta", "Ticker": "META", "Units": 24, "PurchaseValAED": 60991, "Owner": "MV", "Sector": "Tech"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 29, "PurchaseValAED": 55272, "Owner": "MV", "Sector": "Tech"},

    # --- SV PORTFOLIO ---
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1487, "Owner": "SV", "Sector": "Tech"},
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2123, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2096, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3181, "Owner": "SV", "Sector": "Retail"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 14, "PurchaseValAED": 12728, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV", "Sector": "Health"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 6, "PurchaseValAED": 3832, "Owner": "SV", "Sector": "Semi"},
    {"Name": "MSFT [SV]", "Ticker": "MSFT", "Units": 6, "PurchaseValAED": 11128, "Owner": "SV", "Sector": "Tech"},
]

# ---------- INDIA MF CONFIG ----------

MF_CONFIG = [
    {
        "Scheme": "Axis Large and Mid Cap Fund Growth",
        "Category": "Equity",
        "Units": 55026.38,
        "CostINR": 1754912.25,
        "InitialValueINR": 1853288.31,
        "Ticker": "0P0001EP9Q.BO"
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 19360019",
        "Category": "Equity",
        "Units": 286.62,
        "CostINR": 160000.0,
        "InitialValueINR": 433606.67,
        "Ticker": "0P00005VDI.BO"
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 30097040",
        "Category": "Equity",
        "Units": 190.43,
        "CostINR": 95000.0,
        "InitialValueINR": 288087.76,
        "Ticker": "0P00005VDI.BO"
    },
    {
        "Scheme": "ICICI Prudential ELSS Tax Saver Fund Growth",
        "Category": "Equity",
        "Units": 267.83,
        "CostINR": 98000.0,
        "InitialValueINR": 260058.54,
        "Ticker": "0P00005WD7.BO"
    },
    {
        "Scheme": "ICICI Prudential NASDAQ 100 Index Fund Growth",
        "Category": "Equity",
        "Units": 43574.66,
        "CostINR": 654967.25,
        "InitialValueINR": 846603.3,
        "Ticker": "0P0001NCLS.BO"
    },
    {
        "Scheme": "Mirae Asset Large and Mid Cap Fund Growth",
        "Category": "Equity",
        "Units": 9054.85,
        "CostINR": 1327433.63,
        "InitialValueINR": 1429353.35,
        "Ticker": "0P0000ON3O.BO"
    },
    {
        "Scheme": "Nippon India Multi Cap Fund Growth",
        "Category": "Equity",
        "Units": 4813.52,
        "CostINR": 1404929.75,
        "InitialValueINR": 1460345.18,
        "Ticker": "0P00005WDS.BO"
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15530560",
        "Category": "Equity",
        "Units": 25345.69,
        "CostINR": 2082395.88,
        "InitialValueINR": 2204332.05,
        "Ticker": "0P0000YWL0.BO"
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15722429",
        "Category": "Equity",
        "Units": 6095.12,
        "CostINR": 499975.0,
        "InitialValueINR": 530097.11,
        "Ticker": "0P0000YWL0.BO"
    },
    {
        "Scheme": "SBI Multicap Fund Growth",
        "Category": "Equity",
        "Units": 83983.45,
        "CostINR": 1404929.75,
        "InitialValueINR": 1446379.84,
        "Ticker": "0P0001OF6C.BO"
    }
]
# Helper: format INR values as "₹10.1 L"

def fmt_inr_lacs(inr_value: float) -> str:
    if inr_value is None or inr_value != inr_value:  # NaN check
        return "₹0.0 L"
    lacs = inr_value / 100000.0
    return f"₹{lacs:,.1f} L"


@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    """Fetch latest NAV for each MF that has a Yahoo ticker."""
    navs: dict[str, float] = {}
    for entry in MF_CONFIG:
        ticker = entry.get("Ticker") or ""
        scheme = entry["Scheme"]
        if not ticker:
            continue
        try:
            tkr = yf.Ticker(ticker)
            # Fetch 5 days to handle weekends/holidays better
            hist = tkr.history(period="5d", interval="1d")
            if hist is None or hist.empty:
                continue
            nav = float(hist["Close"].iloc[-1])
            if nav > 0:
                navs[scheme] = nav
        except Exception:
            continue
    return navs


def compute_india_mf_aggregate() -> dict:
    """Computes aggregate Indian MF metrics with 1-Day Change Logic."""
    total_value_inr = 0.0
    total_daily_pl_inr = 0.0

    for mf_entry in MF_CONFIG:
        scheme = mf_entry["Scheme"]
        ticker = mf_entry.get("Ticker") or ""
        units = float(mf_entry["Units"] or 0.0)
        file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

        if not ticker or units <= 0:
            total_value_inr += file_value_inr
            continue

        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period="5d")
            
            # --- 1. CALCULATE VALUE (Safety Check Removed) ---
            if not hist.empty:
                latest_nav = float(hist["Close"].iloc[-1])
                candidate_value = latest_nav * units
                
                # We simply trust the live value now, no safety restriction
                if candidate_value > 0:
                    value_inr = candidate_value
                else:
                    value_inr = file_value_inr
            else:
                value_inr = file_value_inr

            # --- 2. CALCULATE 1-DAY CHANGE (P&L) ---
            daily_pl = 0.0
            if len(hist) >= 2:
                latest_nav = float(hist["Close"].iloc[-1])
                prev_nav = float(hist["Close"].iloc[-2])
                daily_pl = (latest_nav - prev_nav) * units
            
        except Exception:
            value_inr = file_value_inr
            daily_pl = 0.0

        total_value_inr += value_inr
        total_daily_pl_inr += daily_pl

    return {"total_value_inr": total_value_inr, "daily_pl_inr": total_daily_pl_inr}

# ---------- FX HELPERS (API DRIVEN) ----------

@st.cache_data(ttl=3600)
def get_fx_rates() -> dict:
    """
    Fetches live FX rates for USD->AED and AED->INR.
    Includes fallbacks if API fails.
    """
    rates = {
        "USD_AED": DEFAULT_USD_AED,
        "AED_INR": DEFAULT_AED_INR
    }
    
    # 1. USD -> AED
    try:
        # USDAED=X is the standard ticker for USD to AED
        hist = yf.Ticker("USDAED=X").history(period="5d")
        if not hist.empty:
            rates["USD_AED"] = float(hist["Close"].iloc[-1])
    except Exception:
        pass
        
    # 2. AED -> INR
    try:
        # AEDINR=X is the standard ticker for AED to INR
        hist = yf.Ticker("AEDINR=X").history(period="5d")
        if not hist.empty:
            rates["AED_INR"] = float(hist["Close"].iloc[-1])
    except Exception:
        pass
        
    return rates


def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹{lacs:,.2f} L"

# ---------- PRICE FETCHING (REGULAR CLOSE) ----------

@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    # Fetch 5 days to ensure we have previous close data even on weekends
    data = yf.download(
        tickers=tickers,
        period="5d",
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=False,
    )
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        lvl1 = data.columns.get_level_values(1)
        if "Adj Close" in lvl1:
            close = data.xs("Adj Close", level=1, axis=1)
        elif "Close" in lvl1:
            close = data.xs("Close", level=1, axis=1)
        else:
            close = data.xs(lvl1[0], level=1, axis=1)
        close.columns = close.columns.get_level_values(0)
    else:
        if "Adj Close" in data.columns:
            close = data[["Adj Close"]]
        elif "Close" in data.columns:
            close = data[["Close"]]
        else:
            return pd.DataFrame()
        close.columns = [tickers[0]]
    close = close.dropna(how="all")
    return close

# ---------- PRICE FETCHING (INTRADAY) ----------

@st.cache_data(ttl=60)
def load_prices_intraday() -> pd.Series:
    """Get last intraday price per ticker using 1m data with pre/post market enabled."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    last_prices: dict[str, float] = {}

    us_tz = ZoneInfo("America/New_York")
    
    # We don't filter by "Today" anymore, we just take the absolute latest tick available
    # This ensures we see Post-Market data even if it is technically "tomorrow" or weekend
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            # Fetch 5 days to be safe on weekends
            hist = tkr.history(period="5d", interval="1m", prepost=True)
            if hist is None or hist.empty:
                continue
            
            # The last row is the latest trade (Pre, Live, or Post)
            last_prices[t] = float(hist["Close"].iloc[-1])
        except Exception:
            continue

    if not last_prices:
        return pd.Series(dtype=float)
    return pd.Series(last_prices)
    # ---------- MARKET STATUS & DATA SOURCE ----------

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    # Define Strings based on Time - NO SQUARE BRACKETS
    if weekday >= 5:
        # Weekend -> "Post Market" (Last State)
        phase_str = "Post Market"
    else:
        # Weekday Logic
        if time(4,0) <= t < time(9,30):
            phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0):
            phase_str = "Live Market"
        else:
            # Evenings/Nights -> "Post Market"
            phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()

    # Always prefer intraday if available as it has pre/post info
    if intraday is None or intraday.empty:
        return phase_str, base_close

    return phase_str, intraday
    import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
from pathlib import Path

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Stocks Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- THEME / CSS ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,400,1,0&display=swap');

    :root {
        --bg: #0f1a2b;
        --card: #16233a;
        --border: #1f2d44;
        --text: #e6eaf0;
        --muted: #9ba7b8;
        --accent: #4aa3ff;
        --accent-soft: #7fc3ff;
        --danger: #f27d72;
        --success: #6bcf8f; /* Vibrant Green for Heatmap */
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: var(--bg);
        color: var(--text);
    }

    header {visibility: hidden;}

    .block-container {
        padding: 0.8rem 0.9rem 2rem;
        max-width: 900px;
    }

    .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 6px 10px;
        box-shadow: none;
        margin-bottom: 8px;
    }

    /* --- KPI CARD STYLING --- */
    .mf-card {
        background: #f4f6f8 !important;
        border-color: #e0e4ea !important;
        color: #0f1a2b !important; /* Default Text Color */
        display: flex;
        flex-direction: column;
        justify-content: space-between; 
        height: 96px; 
        padding: 12px 16px !important; 
        box-sizing: border-box;
    }

    /* --- COLOR CLASSES FOR PROFIT/LOSS (Must override parent !important) --- */
    .kpi-green {
        color: #15803d !important; /* Dark Green for readability on light bg */
    }
    
    .kpi-red {
        color: #b91c1c !important; /* Dark Red */
    }

    /* --- COLOR CORRECTION FOR MUTUAL FUND TAB & WHITE CARDS --- */
    .mf-card .page-title {
        color: #020617 !important; 
        font-weight: 600;
    }

    .mf-card .kpi-label {
        color: #475569; 
        font-weight: 500;
    }

    .mf-card .kpi-value-main {
        color: #0f1a2b; 
        font-weight: 700;
    }
    
    .mf-card .kpi-number {
         color: #0f1a2b; 
    }

    /* --------------------------------------------------------- */

    /* UNIFIED LABEL STYLE: Top/Bottom Labels */
    .kpi-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.6rem; 
        font-weight: 400; /* Normal weight */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.0;
        white-space: nowrap;
        margin: 0;
    }

    /* UNIFIED NUMBER STYLE: Value & Percentage */
    .kpi-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem; 
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.0;
    }
    
    .kpi-value-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.0rem;
        font-weight: 700;
        line-height: 1.1;
    }

    /* Container for the middle row of numbers */
    .kpi-mid-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 0; 
    }

    /* Helper for Top Row Split (Value Left, Return Right) */
    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        width: 100%;
        align-items: flex-end; /* Align bottom so text sits nicely */
    }

    .page-title {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 1.0rem;
        font-weight: 600;
        margin: 0 0 2px 0;
        color: var(--text);
        letter-spacing: 0.01em;
    }

    .page-subtitle {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.75rem;
        color: var(--muted);
        margin: 0;
        letter-spacing: 0.03em;
    }

    .stPlotlyChart {
        background: transparent !important;
    }

    .stTabs {
        margin-top: 0.75rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        align-items: flex-end;
        gap: 0rem;
        width: 100%;
        border-bottom: 1px solid var(--border);
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        position: relative;
        flex: 1 1 25% !important;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.15rem;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.7rem !important;
        padding: 4px 0 3px 0 !important;
        color: #16233a !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
        white-space: nowrap;
        box-sizing: border-box;
    }

    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.6rem !important;
            padding: 4px 0 3px 0 !important;
        }
    }

    .stTabs [role="tab"] {
        min-width: 0 !important;
    }

    .stTabs [data-baseweb="tab"]::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 0;
        background: transparent;
        border: none;
        opacity: 0;
    }

    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        font-weight: 500 !important;
    }

    .stTabs [data-baseweb="tab"]::after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        bottom: -1px;
        height: 2px;
        border-radius: 999px;
        background: transparent;
        transition: background-color 140ms ease-out;
    }

    .stTabs [aria-selected="true"]::after {
        background: #0b1530; 
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS & FALLBACKS ----------
DEFAULT_USD_AED = 3.6725
DEFAULT_AED_INR = 24.50

COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f" # Vibrant Green for Heatmap
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# ---------- PORTFOLIO CONFIG (UPDATED) ----------
# Values calculated at 3.6725 USD/AED based on provided purchase prices
portfolio_config = [
    # --- MV PORTFOLIO ---
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34152, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33138, "Owner": "MV", "Sector": "Auto"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37208, "Owner": "MV", "Sector": "Tech"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16086, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13587, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150997, "Owner": "MV", "Sector": "ETF"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47751, "Owner": "MV", "Sector": "Retail"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 80, "PurchaseValAED": 51051, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Meta", "Ticker": "META", "Units": 24, "PurchaseValAED": 60991, "Owner": "MV", "Sector": "Tech"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 29, "PurchaseValAED": 55272, "Owner": "MV", "Sector": "Tech"},

    # --- SV PORTFOLIO ---
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1487, "Owner": "SV", "Sector": "Tech"},
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2123, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2096, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3181, "Owner": "SV", "Sector": "Retail"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 14, "PurchaseValAED": 12728, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV", "Sector": "Health"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 6, "PurchaseValAED": 3832, "Owner": "SV", "Sector": "Semi"},
    {"Name": "MSFT [SV]", "Ticker": "MSFT", "Units": 6, "PurchaseValAED": 11128, "Owner": "SV", "Sector": "Tech"},
]

# ---------- INDIA MF CONFIG ----------

MF_CONFIG = [
    {
        "Scheme": "Axis Large and Mid Cap Fund Growth",
        "Category": "Equity",
        "Units": 55026.38,
        "CostINR": 1754912.25,
        "InitialValueINR": 1853288.31,
        "Ticker": "0P0001EP9Q.BO"
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 19360019",
        "Category": "Equity",
        "Units": 286.62,
        "CostINR": 160000.0,
        "InitialValueINR": 433606.67,
        "Ticker": "0P00005VDI.BO"
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 30097040",
        "Category": "Equity",
        "Units": 190.43,
        "CostINR": 95000.0,
        "InitialValueINR": 288087.76,
        "Ticker": "0P00005VDI.BO"
    },
    {
        "Scheme": "ICICI Prudential ELSS Tax Saver Fund Growth",
        "Category": "Equity",
        "Units": 267.83,
        "CostINR": 98000.0,
        "InitialValueINR": 260058.54,
        "Ticker": "0P00005WD7.BO"
    },
    {
        "Scheme": "ICICI Prudential NASDAQ 100 Index Fund Growth",
        "Category": "Equity",
        "Units": 43574.66,
        "CostINR": 654967.25,
        "InitialValueINR": 846603.3,
        "Ticker": "0P0001NCLS.BO"
    },
    {
        "Scheme": "Mirae Asset Large and Mid Cap Fund Growth",
        "Category": "Equity",
        "Units": 9054.85,
        "CostINR": 1327433.63,
        "InitialValueINR": 1429353.35,
        "Ticker": "0P0000ON3O.BO"
    },
    {
        "Scheme": "Nippon India Multi Cap Fund Growth",
        "Category": "Equity",
        "Units": 4813.52,
        "CostINR": 1404929.75,
        "InitialValueINR": 1460345.18,
        "Ticker": "0P00005WDS.BO"
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15530560",
        "Category": "Equity",
        "Units": 25345.69,
        "CostINR": 2082395.88,
        "InitialValueINR": 2204332.05,
        "Ticker": "0P0000YWL0.BO"
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15722429",
        "Category": "Equity",
        "Units": 6095.12,
        "CostINR": 499975.0,
        "InitialValueINR": 530097.11,
        "Ticker": "0P0000YWL0.BO"
    },
    {
        "Scheme": "SBI Multicap Fund Growth",
        "Category": "Equity",
        "Units": 83983.45,
        "CostINR": 1404929.75,
        "InitialValueINR": 1446379.84,
        "Ticker": "0P0001OF6C.BO"
    }
]
# Helper: format INR values as "₹10.1 L"

def fmt_inr_lacs(inr_value: float) -> str:
    if inr_value is None or inr_value != inr_value:  # NaN check
        return "₹0.0 L"
    lacs = inr_value / 100000.0
    return f"₹{lacs:,.1f} L"


@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    """Fetch latest NAV for each MF that has a Yahoo ticker."""
    navs: dict[str, float] = {}
    for entry in MF_CONFIG:
        ticker = entry.get("Ticker") or ""
        scheme = entry["Scheme"]
        if not ticker:
            continue
        try:
            tkr = yf.Ticker(ticker)
            # Fetch 5 days to handle weekends/holidays better
            hist = tkr.history(period="5d", interval="1d")
            if hist is None or hist.empty:
                continue
            nav = float(hist["Close"].iloc[-1])
            if nav > 0:
                navs[scheme] = nav
        except Exception:
            continue
    return navs


def compute_india_mf_aggregate() -> dict:
    """Computes aggregate Indian MF metrics with 1-Day Change Logic."""
    total_value_inr = 0.0
    total_daily_pl_inr = 0.0

    for mf_entry in MF_CONFIG:
        scheme = mf_entry["Scheme"]
        ticker = mf_entry.get("Ticker") or ""
        units = float(mf_entry["Units"] or 0.0)
        file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

        if not ticker or units <= 0:
            total_value_inr += file_value_inr
            continue

        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period="5d")
            
            # --- 1. CALCULATE VALUE (Safety Check Removed) ---
            if not hist.empty:
                latest_nav = float(hist["Close"].iloc[-1])
                candidate_value = latest_nav * units
                
                # We simply trust the live value now, no safety restriction
                if candidate_value > 0:
                    value_inr = candidate_value
                else:
                    value_inr = file_value_inr
            else:
                value_inr = file_value_inr

            # --- 2. CALCULATE 1-DAY CHANGE (P&L) ---
            daily_pl = 0.0
            if len(hist) >= 2:
                latest_nav = float(hist["Close"].iloc[-1])
                prev_nav = float(hist["Close"].iloc[-2])
                daily_pl = (latest_nav - prev_nav) * units
            
        except Exception:
            value_inr = file_value_inr
            daily_pl = 0.0

        total_value_inr += value_inr
        total_daily_pl_inr += daily_pl

    return {"total_value_inr": total_value_inr, "daily_pl_inr": total_daily_pl_inr}

# ---------- FX HELPERS (API DRIVEN) ----------

@st.cache_data(ttl=3600)
def get_fx_rates() -> dict:
    """
    Fetches live FX rates for USD->AED and AED->INR.
    Includes fallbacks if API fails.
    """
    rates = {
        "USD_AED": DEFAULT_USD_AED,
        "AED_INR": DEFAULT_AED_INR
    }
    
    # 1. USD -> AED
    try:
        # USDAED=X is the standard ticker for USD to AED
        hist = yf.Ticker("USDAED=X").history(period="5d")
        if not hist.empty:
            rates["USD_AED"] = float(hist["Close"].iloc[-1])
    except Exception:
        pass
        
    # 2. AED -> INR
    try:
        # AEDINR=X is the standard ticker for AED to INR
        hist = yf.Ticker("AEDINR=X").history(period="5d")
        if not hist.empty:
            rates["AED_INR"] = float(hist["Close"].iloc[-1])
    except Exception:
        pass
        
    return rates


def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹{lacs:,.2f} L"

# ---------- PRICE FETCHING (REGULAR CLOSE) ----------

@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    # Fetch 5 days to ensure we have previous close data even on weekends
    data = yf.download(
        tickers=tickers,
        period="5d",
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=False,
    )
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        lvl1 = data.columns.get_level_values(1)
        if "Adj Close" in lvl1:
            close = data.xs("Adj Close", level=1, axis=1)
        elif "Close" in lvl1:
            close = data.xs("Close", level=1, axis=1)
        else:
            close = data.xs(lvl1[0], level=1, axis=1)
        close.columns = close.columns.get_level_values(0)
    else:
        if "Adj Close" in data.columns:
            close = data[["Adj Close"]]
        elif "Close" in data.columns:
            close = data[["Close"]]
        else:
            return pd.DataFrame()
        close.columns = [tickers[0]]
    close = close.dropna(how="all")
    return close

# ---------- PRICE FETCHING (INTRADAY) ----------

@st.cache_data(ttl=60)
def load_prices_intraday() -> pd.Series:
    """Get last intraday price per ticker using 1m data with pre/post market enabled."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    last_prices: dict[str, float] = {}

    us_tz = ZoneInfo("America/New_York")
    
    # We don't filter by "Today" anymore, we just take the absolute latest tick available
    # This ensures we see Post-Market data even if it is technically "tomorrow" or weekend
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            # Fetch 5 days to be safe on weekends
            hist = tkr.history(period="5d", interval="1m", prepost=True)
            if hist is None or hist.empty:
                continue
            
            # The last row is the latest trade (Pre, Live, or Post)
            last_prices[t] = float(hist["Close"].iloc[-1])
        except Exception:
            continue

    if not last_prices:
        return pd.Series(dtype=float)
    return pd.Series(last_prices)
    # ---------- MARKET STATUS & DATA SOURCE ----------

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    # Define Strings based on Time - NO SQUARE BRACKETS
    if weekday >= 5:
        # Weekend -> "Post Market" (Last State)
        phase_str = "Post Market"
    else:
        # Weekday Logic
        if time(4,0) <= t < time(9,30):
            phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0):
            phase_str = "Live Market"
        else:
            # Evenings/Nights -> "Post Market"
            phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()

    # Always prefer intraday if available as it has pre/post info
    if intraday is None or intraday.empty:
        return phase_str, base_close

    return phase_str, intraday
