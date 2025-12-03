import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
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
        --success: #6bcf8f;
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

    /* --- KPI CARD STYLING (UPDATED) --- */
    .mf-card {
        background: #f4f6f8 !important;
        border-color: #e0e4ea !important;
        color: #0f1a2b !important;
        display: flex;
        flex-direction: column;
        
        /* DISTRIBUTION LOGIC: space-between pushes content to edges. */
        justify-content: space-between; 
        
        /* HEIGHT: 86px for tight spacing */
        height: 86px; 
        
        padding: 10px 14px !important; 
        box-sizing: border-box;
    }

    /* --- COLOR CORRECTION FOR MUTUAL FUND TAB & WHITE CARDS --- */
    .mf-card .page-title {
        color: #020617 !important; /* Almost Black for Fund Names */
        font-weight: 600;
    }

    .mf-card .kpi-label {
        color: #475569 !important; /* Dark Slate Grey for Labels */
        font-weight: 500;
    }

    .mf-card .kpi-value-main {
        color: #0f1a2b !important; /* Dark Navy for Values in MF List */
        font-weight: 700;
    }
    
    .mf-card .kpi-number {
         color: #0f1a2b !important; /* Dark Navy for Values in KPI Cards */
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

# ---------- CONSTANTS ----------
USD_TO_AED = 3.6725
COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f"
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# ---------- PORTFOLIO CONFIG ----------
portfolio_config = [
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34128, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37183, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33116, "Owner": "MV", "Sector": "Auto"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150894, "Owner": "MV", "Sector": "ETF"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16075, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13578, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 78, "PurchaseValAED": 49707, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47720, "Owner": "MV", "Sector": "Retail"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 26, "PurchaseValAED": 49949, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Meta", "Ticker": "META", "Units": 18, "PurchaseValAED": 48744, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2122, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1486, "Owner": "SV", "Sector": "Tech"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2095, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 2, "PurchaseValAED": 1286, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3179, "Owner": "SV", "Sector": "Retail"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV", "Sector": "Health"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 10, "PurchaseValAED": 8989, "Owner": "SV", "Sector": "ETF"},
    {"Name": "MSFT [SV]", "Ticker": "MSFT", "Units": 4, "PurchaseValAED": 7476, "Owner": "SV", "Sector": "Tech"},
]

# ---------- INDIA MF CONFIG ----------
PORTFOLIO_INITIAL_XIRR = 13.78
PORTFOLIO_INITIAL_PROFIT = 1269608.61

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
            
            # --- 1. CALCULATE VALUE (With Safety Check) ---
            if not hist.empty:
                latest_nav = float(hist["Close"].iloc[-1])
                candidate_value = latest_nav * units
                
                # Trust Yahoo only if within 10% of File Value
                if file_value_inr > 0:
                    ratio = candidate_value / file_value_inr
                    if 0.9 <= ratio <= 1.1:
                        value_inr = candidate_value
                    else:
                        value_inr = file_value_inr
                else:
                    value_inr = candidate_value
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

# ---------- FX HELPERS ----------

@st.cache_data(ttl=3600)
def get_aed_inr_rate_from_yahoo() -> float:
    try:
        tkr = yf.Ticker("AEDINR=X")
        hist = tkr.history(period="5d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return 24.50
        return float(hist["Close"].iloc[-1])
    except Exception:
        return 24.50


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

@st.cache_data(ttl=60)
def get_market_indices_change(phase_str: str) -> str:
    """
    Fetches Nifty 50 and Nasdaq 100 changes.
    Uses 'QMI' (Pre) and 'QIV' (Post) if available, falling back to QQQ.
    """
    
    # 1. NIFTY 50
    nifty_str = "Nifty 0.0%"
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 1:
            # Nifty is mostly closed when US is active, so we just take last close diff
            close_now = hist["Close"].iloc[-1]
            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                pct = (close_now / prev_close - 1) * 100
                # STRICT FORMAT: +5% or -5% (using Python + specifier)
                nifty_str = f"Nifty {pct:+.1f}%"
    except:
        pass

    # 2. NASDAQ 100
    nasdaq_str = "Nasdaq 0.0%"
    
    # Determine which ticker to TRY first based on phase
    target_ticker = "QQQ" # Default
    status_label = ""
    
    if "Pre" in phase_str:
        target_ticker = "^QMI" # Try the specific indicator
        status_label = "Pre Market" # Removed brackets
    elif "Post" in phase_str:
        target_ticker = "^QIV" # Try the specific indicator
        status_label = "Post Market" # Removed brackets
    
    try:
        # Try fetching the target (QMI/QIV or QQQ)
        tkr = yf.Ticker(target_ticker)
        # We need prepost=True to see QMI/QIV data if it exists, or QQQ ext hours
        hist = tkr.history(period="1d", interval="1m", prepost=True)
        
        # If QMI/QIV fails (empty), FALLBACK to QQQ
        if hist.empty and target_ticker in ["^QMI", "^QIV"]:
             tkr = yf.Ticker("QQQ")
             hist = tkr.history(period="1d", interval="1m", prepost=True)
        
        if not hist.empty:
            curr = hist["Close"].iloc[-1]
            # We need a reference price. 
            # Ideally previous day close.
            prev_close = 0.0
            
            # Fetch daily history for close
            daily = tkr.history(period="5d")
            if len(daily) >= 1:
                # If we are in pre-market today, compare vs Yesterday Close
                # If we are in post-market today, compare vs Today Close (usually)
                # Simpler: Just compare vs the last available 'regular' close
                prev_close = daily["Close"].iloc[-1]
                # If the 1m data is 'newer' than the daily close, use daily close as ref
                # If 1m data timestamp is same day as daily close, we might need T-1 close
                
                # Robust fallback: use T-1 close if available
                if len(daily) >= 2:
                     # Check dates
                     last_day_date = daily.index[-1].date()
                     now_date = datetime.now(ZoneInfo("America/New_York")).date()
                     if last_day_date == now_date:
                         # Today's daily bar exists (maybe live or closed)
                         prev_close = daily["Close"].iloc[-2]
                     else:
                         prev_close = daily["Close"].iloc[-1]
            
            if prev_close > 0:
                pct = (curr / prev_close - 1) * 100
                # STRICT FORMAT: +5% or -5%
                nasdaq_str = f"Nasdaq {status_label} {pct:+.1f}%"

    except:
        pass

    return f"{nifty_str} <span style='opacity:0.4; margin:0 6px;'>|</span> {nasdaq_str}"


# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None) -> pd.DataFrame:
    rows = []
    
    # We need a robust "Previous Close" to calculate change against.
    # prices_close has daily candles. 
    # If today is trading, prices_close.iloc[-1] might be *today's* partial bar.
    # We need Yesterday's close.
    
    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        # 1. Get Live Price
        live_price = 0.0
        if prices_intraday is not None:
            live_price = float(prices_intraday.get(t, 0.0))
        
        # Fallback to close if no intraday
        if live_price == 0 and not prices_close.empty:
             live_price = float(prices_close.iloc[-1].get(t, 0.0))

        # 2. Get Previous Close (Reference for P&L)
        prev_close_price = 0.0
        if not prices_close.empty:
            # Logic: If the last date in prices_close is TODAY, take the row before it.
            # If the last date is YESTERDAY, take the last row.
            last_date = prices_close.index[-1].date()
            us_tz = ZoneInfo("America/New_York")
            today_date = datetime.now(us_tz).date()
            
            col_data = prices_close[t]
            if len(col_data) >= 2:
                if last_date == today_date:
                    prev_close_price = float(col_data.iloc[-2])
                else:
                    prev_close_price = float(col_data.iloc[-1])
            elif len(col_data) == 1:
                prev_close_price = float(col_data.iloc[-1]) # Best guess if no history

        if live_price <= 0:
            value_aed = purchase
            day_pct = 0.0
            day_pl_aed = 0.0
            total_pl_aed = 0.0
            total_pct = 0.0
            price_usd = 0.0
        else:
            price_usd = live_price
            price_aed = price_usd * USD_TO_AED
            value_aed = price_aed * units

            # Day P&L vs Previous Close
            if prev_close_price > 0:
                day_pct = (price_usd / prev_close_price - 1.0) * 100.0
            else:
                day_pct = 0.0
                
            day_pl_aed = value_aed * (day_pct / 100.0)

            total_pl_aed = value_aed - purchase
            total_pct = (total_pl_aed / purchase) * 100.0 if purchase > 0 else 0.0

        rows.append(
            {
                "Name": item["Name"],
                "Ticker": t,
                "Owner": item["Owner"],
                "Sector": item["Sector"],
                "Units": units,
                "PriceUSD": price_usd,
                "ValueAED": value_aed,
                "PurchaseAED": purchase,
                "DayPct": day_pct,
                "DayPLAED": day_pl_aed,
                "TotalPct": total_pct,
                "TotalPLAED": total_pl_aed,
            }
        )

    df = pd.DataFrame(rows)
    total_val = df["ValueAED"].sum()
    df["WeightPct"] = df["ValueAED"] / total_val * 100.0 if total_val > 0 else 0.0
    return df

def aggregate_for_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mv = df[df["Owner"] == "MV"].copy()
    sv = df[df["Owner"] == "SV"].copy()
    if sv.empty:
        return mv.reset_index(drop=True)

    total_val_all = df["ValueAED"].sum()
    sv_val = sv["ValueAED"].sum()
    sv_purchase = sv["PurchaseAED"].sum()
    sv_day_pl = sv["DayPLAED"].sum()
    sv_total_pl = sv["TotalPLAED"].sum()

    sv_row = pd.DataFrame(
        [
            {
                "Name": "SV Portfolio",
                "Ticker": "SVPF",
                "Owner": "SV",
                "Sector": "Mixed",
                "Units": sv["Units"].sum(),
                "PriceUSD": 0.0,
                "ValueAED": sv_val,
                "PurchaseAED": sv_purchase,
                "DayPct": (sv_day_pl / sv_val * 100.0) if sv_val > 0 else 0.0,
                "DayPLAED": sv_day_pl,
                "TotalPct": (sv_total_pl / sv_purchase * 100.0) if sv_purchase > 0 else 0.0,
                "TotalPLAED": sv_total_pl,
                "WeightPct": (sv_val / total_val_all * 100.0) if total_val_all > 0 else 0.0,
            }
        ]
    )

    mv = mv.copy()
    mv["WeightPct"] = mv["ValueAED"] / total_val_all * 100.0 if total_val_all > 0 else 0.0

    combined = pd.concat([mv, sv_row], ignore_index=True)
    return combined

# ---------- DATA PIPELINE ----------

market_status_str, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()
header_metrics_str = get_market_indices_change(market_status_str)

if isinstance(price_source, pd.DataFrame):
    positions = build_positions_from_prices(price_source, None)
else:
    positions = build_positions_from_prices(prices_close, price_source)

agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions

base_fx = get_aed_inr_rate_from_yahoo()
AED_TO_INR = base_fx

total_val_aed = positions["ValueAED"].sum()
total_purchase_aed = positions["PurchaseAED"].sum()
total_pl_aed = positions["TotalPLAED"].sum()
day_pl_aed = positions["DayPLAED"].sum()

total_pl_pct = (total_pl_aed / total_purchase_aed * 100.0) if total_purchase_aed > 0 else 0.0

total_val_inr_lacs = fmt_inr_lacs_from_aed(total_val_aed, AED_TO_INR)
total_pl_inr_lacs = fmt_inr_lacs_from_aed(total_pl_aed, AED_TO_INR)
day_pl_inr_lacs = fmt_inr_lacs_from_aed(day_pl_aed, AED_TO_INR)

overall_pct_str = f"{total_pl_pct:+.2f}%"

# ---------- HEADER ----------

st.markdown(
    f"""
<div class="card">
  <div class="page-title">Stocks Dashboard</div>
  <div class="page-subtitle">{header_metrics_str}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- TABS ----------

overview_tab, sv_tab, us_tab, mf_tab = st.tabs([
    "🪙 Overview",
    "💷 SV Stocks",
    "💵 US Stocks",
    "💴 India MF",
])

# ---------- HOME TAB ----------

with overview_tab:
    # --- 1. PREPARE DATA FOR CARDS ---

    # A. US Stocks
    us_day_pl_inr = day_pl_aed * AED_TO_INR
    us_prev_val_aed = total_val_aed - day_pl_aed
    us_day_pct = (day_pl_aed / us_prev_val_aed * 100.0) if us_prev_val_aed > 0 else 0.0

    # B. India Mutual Funds
    mf_agg = compute_india_mf_aggregate()
    mf_val_inr = float(mf_agg.get("total_value_inr", 0.0) or 0.0)
    mf_day_pl_inr = float(mf_agg.get("daily_pl_inr", 0.0) or 0.0)
    
    # MF Change %
    mf_prev_val = mf_val_inr - mf_day_pl_inr
    mf_day_pct = (mf_day_pl_inr / mf_prev_val * 100.0) if mf_prev_val > 0 else 0.0

    # MF ABSOLUTE RETURN %
    mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
    mf_total_profit = mf_val_inr - mf_total_cost
    mf_abs_return_pct = (mf_total_profit / mf_total_cost * 100.0) if mf_total_cost > 0 else 0.0

    # --- 2. RENDER CARDS (FIXED: NO INDENTATION, UNIFIED FONTS) ---
    
    c1, c2, c3, c4 = st.columns(4)

    def render_new_kpi_card(col, top_label, main_value, right_value, bottom_label):
        with col:
            # HTML content must be flush left to avoid code block rendering
            html_content = f"""
<div class="card mf-card">
<div class="kpi-label">{top_label}</div>
<div class="kpi-mid-row">
<div class="kpi-number">{main_value}</div>
<div class="kpi-number">{right_value}</div>
</div>
<div class="kpi-label">{bottom_label}</div>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

    # Card 1: Today's Profit | Market Status -> US Stocks
    status_display = f"TODAY'S PROFIT <span style='opacity:0.5; margin:0 4px;'>|</span> {market_status_str.upper()}"
    
    render_new_kpi_card(
        c1, 
        status_display, 
        f"₹{us_day_pl_inr:,.0f}", 
        f"{us_day_pct:+.2f}%",
        "US STOCKS"
    )

    # Card 2: Today's Profit -> India MF
    render_new_kpi_card(
        c2, 
        "TODAY'S PROFIT", 
        f"₹{mf_day_pl_inr:,.0f}", 
        f"{mf_day_pct:+.2f}%",
        "INDIA MF"
    )

    # Card 3: Total Holding -> US Stocks
    render_new_kpi_card(
        c3, 
        "TOTAL HOLDING", 
        total_val_inr_lacs,
        f"{total_pl_pct:+.2f}%",  # Added + sign
        "US STOCKS"
    )

    # Card 4: Total Holding -> India MF
    render_new_kpi_card(
        c4, 
        "TOTAL HOLDING", 
        fmt_inr_lacs(mf_val_inr), 
        f"{mf_abs_return_pct:+.2f}%", # Added + sign
        "INDIA MF"
    )

    # --- 3. RENDER HEATMAP ---

    st.markdown(
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:10px 0 4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data. Showing static valuation only; heat map disabled.")
    else:
        hm = agg_for_heatmap.copy()
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR

        if mf_val_inr > 0 or mf_day_pl_inr != 0.0:
            ind_mf_row = {
                "Name": "Indian MF",
                "Ticker": "INDMF",
                "Owner": "MF",
                "Sector": "India MF",
                "Units": 0.0,
                "PriceUSD": 0.0,
                "ValueAED": mf_val_inr / AED_TO_INR if mf_val_inr > 0 else 0.0,
                "PurchaseAED": 0.0,
                "DayPct": 0.0,
                "DayPLAED": mf_day_pl_inr / AED_TO_INR,
                "DayPLINR": mf_day_pl_inr, 
                "TotalPct": 0.0,
                "TotalPLAED": 0.0,
                "WeightPct": 0.0,
            }
            hm = pd.concat([hm, pd.DataFrame([ind_mf_row])], ignore_index=True)

        hm["SizeForHeatmap"] = hm["DayPLINR"].abs() + 1e-6
        hm["DayPLK"] = hm["DayPLINR"] / 1000.0

        def label_for_k(v: float) -> str:
            if v >= 0:
                return f"₹{abs(v):,.0f}k"
            else:
                return f"[₹{abs(v):,.0f}k]"

        hm["DayPLKLabel"] = hm["DayPLK"].apply(label_for_k)

        fig = px.treemap(
            hm,
            path=["Name"],
            values="SizeForHeatmap",
            color="DayPLINR",
            color_continuous_scale=[COLOR_DANGER, "#16233a", COLOR_SUCCESS],
            color_continuous_midpoint=0,
            custom_data=["DayPLINR", "Ticker", "DayPLKLabel"],
        )

        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Ticker: %{customdata[1]}<br>Day P&L: ₹%{customdata[0]:,.0f}<extra></extra>",
            texttemplate="%{label}<br>%{customdata[2]}",
            textfont=dict(family="Space Grotesk, sans-serif", color="#e6eaf0", size=11),
            marker=dict(line=dict(width=0)),
            root_color=COLOR_BG,
        )

        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            paper_bgcolor=COLOR_BG,
            plot_bgcolor=COLOR_BG,
            coloraxis_showscale=False,
            font=dict(family="Space Grotesk, sans-serif"),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------- SV TAB (Sae Vyas portfolio detail) ----------

with sv_tab:

    sv_positions = positions[positions["Owner"] == "SV"].copy()

    if sv_positions.empty:
        st.info("No SV positions found.")
    else:
        sv_total_val_aed = sv_positions["ValueAED"].sum()
        sv_total_purchase_aed = sv_positions["PurchaseAED"].sum()
        sv_total_pl_aed = sv_positions["TotalPLAED"].sum()
        sv_day_pl_aed = sv_positions["DayPLAED"].sum()

        sv_total_pl_pct = (sv_total_pl_aed / sv_total_purchase_aed * 100.0) if sv_total_purchase_aed > 0 else 0.0
        prev_total_val = sv_total_val_aed - sv_day_pl_aed
        sv_day_pl_pct = (sv_day_pl_aed / prev_total_val * 100.0) if prev_total_val > 0 else 0.0

        sv_day_pl_aed_str = f"AED {sv_day_pl_aed:,.0f}"
        sv_day_pl_pct_str = f"{sv_day_pl_pct:+.2f}%"
        sv_total_pl_aed_str = f"AED {sv_total_pl_aed:,.0f}"
        sv_total_pl_pct_str = f"{sv_total_pl_pct:+.2f}%"
        sv_total_val_aed_str = f"AED {sv_total_val_aed:,.0f}"
        sv_total_val_inr_lacs_str = fmt_inr_lacs_from_aed(sv_total_val_aed, AED_TO_INR)

        # ---- Card 1: Today's Profit ----
        st.markdown(
            f"""
            <div class="card mf-card" style="padding:12px 14px; margin-bottom:8px;">
                <div class="page-title" style="margin-bottom:4px;">Today's Profit</div>
                <div style="margin-top:2px; display:flex; justify-content:space-between; align-items:flex-end;">
                    <div>
                        <div class="kpi-value-main">{sv_day_pl_aed_str}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="kpi-value-main">{sv_day_pl_pct_str}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Card 2: Total Profit ----
        st.markdown(
            f"""
            <div class="card mf-card" style="padding:12px 14px; margin-bottom:8px;">
                <div class="page-title" style="margin-bottom:4px;">Total Profit</div>
                <div style="margin-top:2px; display:flex; justify-content:space-between; align-items:flex-end;">
                    <div>
                        <div class="kpi-value-main">{sv_total_pl_aed_str}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="kpi-value-main">{sv_total_pl_pct_str}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Card 3: Holding Value ----
        st.markdown(
            f"""
            <div class="card mf-card" style="padding:12px 14px; margin-bottom:8px;">
                <div class="page-title" style="margin-bottom:4px;">Total Holding Value</div>
                <div style="margin-top:2px; display:flex; justify-content:space-between; align-items:flex-end;">
                    <div>
                        <div class="kpi-value-main">{sv_total_val_aed_str}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="kpi-value-main">{sv_total_val_inr_lacs_str}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;">Today's Gains – SV</div>""",
            unsafe_allow_html=True,
        )

        hm_sv = sv_positions.copy()
        hm_sv["Name"] = hm_sv["Name"].str.replace(r"\s*\[SV\]", "", regex=True)
        hm_sv["SizeForHeatmap"] = hm_sv["DayPLAED"].abs() + 1e-6

        def label_for_sv(v: float) -> str:
            if v >= 0:
                return f"AED {v:,.0f}"
            else:
                return f"[AED {abs(v):,.0f}]"

        hm_sv["DayPLLabel"] = hm_sv["DayPLAED"].apply(label_for_sv)

        fig_sv = px.treemap(
            hm_sv,
            path=["Name"],
            values="SizeForHeatmap",
            color="DayPLAED",
            color_continuous_scale=[COLOR_DANGER, "#16233a", COLOR_SUCCESS],
            color_continuous_midpoint=0,
            custom_data=["DayPLAED", "Ticker", "DayPLLabel"],
        )

        fig_sv.update_traces(
            hovertemplate="<b>%{label}</b><br>Ticker: %{customdata[1]}<br>Day P&L: AED %{customdata[0]:,.0f}<extra></extra>",
            texttemplate="%{label}<br>%{customdata[2]}",
            textfont=dict(family="Space Grotesk, sans-serif", color="#e6eaf0", size=11),
            marker=dict(line=dict(width=0)),
            root_color=COLOR_BG,
        )

        fig_sv.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            paper_bgcolor=COLOR_BG,
            plot_bgcolor=COLOR_BG,
            coloraxis_showscale=False,
            font=dict(family="Space Grotesk, sans-serif"),
        )

        st.plotly_chart(fig_sv, use_container_width=True, config={"displayModeBar": False})

# ---------- US STOCKS TAB ----------

with us_tab:
    st.info("US Stocks tab coming next.")

# ---------- INDIA MF TAB ----------


with mf_tab:
    if not MF_CONFIG:
        st.info("No mutual fund data configured.")
    else:
        mf_navs = load_mf_navs_from_yahoo()
        mf_rows = []
        for mf_entry in MF_CONFIG:
            scheme = mf_entry["Scheme"]
            units = float(mf_entry["Units"] or 0.0)
            cost_inr = float(mf_entry["CostINR"] or 0.0)
            file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

            live_nav = mf_navs.get(scheme)

            # Safety check logic
            value_inr = file_value_inr
            if live_nav is not None and live_nav > 0 and units > 0:
                candidate_value = live_nav * units
                if file_value_inr > 0:
                    ratio = candidate_value / file_value_inr
                    if 0.9 <= ratio <= 1.1:
                        value_inr = candidate_value
                else:
                    value_inr = candidate_value
            
            # Absolute return
            if cost_inr > 0:
                abs_return = (value_inr - cost_inr) / cost_inr * 100.0
            else:
                abs_return = 0.0

            mf_rows.append(
                {
                    "scheme": scheme,
                    "value_inr": value_inr,
                    "return_pct": abs_return,
                }
            )

        mf_rows.sort(key=lambda r: r["value_inr"], reverse=True)
        total_value_inr = sum(r["value_inr"] for r in mf_rows)
        mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
        
        if mf_total_cost > 0:
            total_abs_return_pct = (total_value_inr - mf_total_cost) / mf_total_cost * 100.0
        else:
            total_abs_return_pct = 0.0

        total_value_str = fmt_inr_lacs(total_value_inr)
        total_return_str = f"{total_abs_return_pct:.2f}%"

        st.markdown(
            f"""
            <div class="card mf-card" style="padding:12px 14px; margin-bottom:8px;">
                <div class="page-title" style="margin-bottom:4px;">Mutual Fund Holding</div>
                <div style="margin-top:2px; display:flex; justify-content:space-between; align-items:flex-end;">
                    <div>
                        <div class="kpi-label" style="margin-bottom:1px;">Total Value</div>
                        <div class="kpi-value-main">{total_value_str}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="kpi-label" style="margin-bottom:1px;">Total Return</div>
                        <div class="kpi-value-main">{total_return_str}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for row in mf_rows:
            scheme = row["scheme"]
            value_inr = row["value_inr"]
            ret_pct = row["return_pct"]

            display_name = scheme
            parts = display_name.split()
            if parts and all(ch.isdigit() or ch in "/-" for ch in parts[-1]):
                display_name = " ".join(parts[:-1])
            if "Fund Growth" in display_name:
                display_name = display_name.replace(" Fund Growth", "")

            value_str = fmt_inr_lacs(value_inr)
            ret_str = f"{ret_pct:.1f}%"

            st.markdown(
                f"""
                <div class="card mf-card" style="padding:8px 10px; margin-bottom:6px;">
                    <div class="page-title" style="margin-bottom:4px;">{display_name}</div>
                    <div style="margin-top:2px; display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="kpi-label" style="margin-bottom:1px;">Total Value</div>
                            <div class="kpi-value-main">{value_str}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="kpi-label" style="margin-bottom:1px;">Total Return</div>
                            <div class="kpi-value-main">{ret_str}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
