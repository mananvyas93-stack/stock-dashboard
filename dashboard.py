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
        --success: #6bcf8f; /* Vibrant green for Heatmap */
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
        color: #0f1a2b !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between; 
        height: 96px; 
        padding: 12px 16px !important; 
        box-sizing: border-box;
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

# Global colors (Heatmap uses COLOR_SUCCESS)
COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f" 
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# Specific Darker Colors for White Cards (Text visibility)
TEXT_GREEN_DARK = "#15803d" 
TEXT_RED_DARK = "#b91c1c"

# ---------- PORTFOLIO CONFIG ----------
portfolio_config = [
    # --- MV PORTFOLIO ---
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34152, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150997, "Owner": "MV", "Sector": "ETF"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37208, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33138, "Owner": "MV", "Sector": "Auto"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16086, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13587, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47751, "Owner": "MV", "Sector": "Retail"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 80, "PurchaseValAED": 51051, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Meta", "Ticker": "META", "Units": 24, "PurchaseValAED": 60991, "Owner": "MV", "Sector": "Tech"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 29, "PurchaseValAED": 55272, "Owner": "MV", "Sector": "Tech"},
    
    # --- SV PORTFOLIO ---
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1487, "Owner": "SV", "Sector": "Tech"},
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2123, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 14, "PurchaseValAED": 12728, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3181, "Owner": "SV", "Sector": "Retail"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2096, "Owner": "SV", "Sector": "ETF"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 3, "PurchaseValAED": 1971, "Owner": "SV", "Sector": "Semi"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV", "Sector": "Health"},
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

@st.cache_data(ttl=60)
def get_market_indices_change(phase_str: str) -> str:
    """
    Fetches Nifty 50 and Nasdaq 100 changes.
    Replaced unreliable ^QMI/^QIV with QQQ + Logic Fix.
    """
    
    # 1. NIFTY 50
    nifty_str = "Nifty 0.0%"
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 1:
            close_now = hist["Close"].iloc[-1]
            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                pct = (close_now / prev_close - 1) * 100
                nifty_str = f"Nifty {pct:+.1f}%"
    except:
        pass

    # 2. NASDAQ 100 (Using QQQ)
    nasdaq_str = "Nasdaq 0.0%"
    target_ticker = "QQQ"
    
    try:
        tkr = yf.Ticker(target_ticker)
        # 1m history for current status (Pre/Live/Post)
        hist_1m = tkr.history(period="1d", interval="1m", prepost=True)
        # Daily history for baseline (Yesterday Close vs Today Close)
        daily = tkr.history(period="5d")
        
        if not hist_1m.empty and not daily.empty:
            curr = hist_1m["Close"].iloc[-1]
            
            # --- LOGIC FIX: Determine Baseline based on Phase ---
            prev_close = 0.0
            
            if "Post" in phase_str:
                # Post Market: Compare Current Price vs TODAY'S Regular Close
                prev_close = daily["Close"].iloc[-1]
                
                # FALLBACK CHECK:
                # If calculations show exactly 0.0% change in Post Market (common on weekends/holidays),
                # Fall back to showing the regular daily change instead.
                pct_post = (curr / prev_close - 1) * 100
                
                if abs(pct_post) < 0.01:
                    # Switch to Daily View
                    if len(daily) >= 2:
                        close_today = daily["Close"].iloc[-1]
                        close_prev = daily["Close"].iloc[-2]
                        pct = (close_today / close_prev - 1) * 100
                        nasdaq_str = f"Nasdaq {pct:+.1f}%"
                    else:
                        nasdaq_str = f"Nasdaq {pct_post:+.1f}%"
                else:
                    nasdaq_str = f"Nasdaq {phase_str} {pct_post:+.1f}%"
                
            else:
                # Pre-Market OR Live Market: Compare vs YESTERDAY'S Close
                last_daily_date = daily.index[-1].date()
                now_date = datetime.now(ZoneInfo("America/New_York")).date()
                
                if last_daily_date == now_date:
                    if len(daily) >= 2:
                        prev_close = daily["Close"].iloc[-2]
                    else:
                        prev_close = daily["Close"].iloc[-1] 
                else:
                    prev_close = daily["Close"].iloc[-1]
            
                if prev_close > 0 and "Nasdaq" not in nasdaq_str: # Only if not already set by fallback
                    pct = (curr / prev_close - 1) * 100
                    nasdaq_str = f"Nasdaq {phase_str} {pct:+.1f}%"

    except:
        pass

    return f"{nifty_str} <span style='opacity:0.4; margin:0 6px;'>|</span> {nasdaq_str}"


# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None, usd_to_aed_rate: float) -> pd.DataFrame:
    rows = []
    
    # We need a robust "Previous Close" to calculate change against.
    
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
                prev_close_price = float(col_data.iloc[-1])

        if live_price <= 0:
            value_aed = purchase
            day_pct = 0.0
            day_pl_aed = 0.0
            total_pl_aed = 0.0
            total_pct = 0.0
            price_usd = 0.0
        else:
            price_usd = live_price
            price_aed = price_usd * usd_to_aed_rate
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

# FETCH API FX RATES
fx_rates = get_fx_rates()
USD_TO_AED = fx_rates["USD_AED"]
AED_TO_INR = fx_rates["AED_INR"]

if isinstance(price_source, pd.DataFrame):
    positions = build_positions_from_prices(price_source, None, USD_TO_AED)
else:
    positions = build_positions_from_prices(prices_close, price_source, USD_TO_AED)

agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions

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

        # Layout: 3 columns for 3 cards (RESTORED)
        c1, c2, c3 = st.columns(3)

        # Card 1: Today's Profit
        with c1:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TODAY'S PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_day_pl_aed_str}</div>
                    <div class="kpi-number">{sv_day_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 2: Total Profit
        with c2:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_pl_aed_str}</div>
                    <div class="kpi-number">{sv_total_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 3: Total Holding Value
        with c3:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL HOLDING</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_val_aed_str}</div>
                    <div class="kpi-number">{sv_total_val_inr_lacs_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

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

# ---------- US STOCKS TAB (NEW) ----------

with us_tab:
    if positions.empty:
        st.info("No US positions found.")
    else:
        # 3. INDIVIDUAL STOCK CARDS (REDESIGNED)
        # Sorted by Total Profit AED Descending
        sorted_pos = positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base Label Style to allow color override (avoids the class .kpi-label color conflict)
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_pos:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            owner = row["Owner"]
            
            # Label Update for SV
            suffix = " • SV" if owner == "SV" else ""
            units_str = f"{units:,.0f} UNITS{suffix}"
            
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # Colors - using new variables TEXT_GREEN_DARK / TEXT_RED_DARK
            # We are injecting hex codes directly to ensure !important works
            color_pl = TEXT_GREEN_DARK if pl_aed >= 0 else TEXT_RED_DARK
            color_pct = TEXT_GREEN_DARK if pl_pct >= 0 else TEXT_RED_DARK
            
            # Clean Name
            display_name = name.upper().replace(" [SV]", "")

            # NEW CARD LAYOUT (FLATTENED TO PREVENT MD ERROR)
            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div style="{base_label_style}"><span style="color:{color_pl} !important; font-weight:600;">{pl_aed_str}</span></div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div style="{base_label_style}"><span style="color:{color_pct} !important; font-weight:600;">{pl_pct_str}</span></div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

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

            # Safety check logic REMOVED - Trust Live Data
            value_inr = file_value_inr
            if live_nav is not None and live_nav > 0 and units > 0:
                candidate_value = live_nav * units
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
            <div class="card mf-card">
                <div class="kpi-top-row">
                    <div class="kpi-label">VALUE</div>
                    <div class="kpi-label">RETURN</div>
                </div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{total_value_str}</div>
                    <div class="kpi-number">{total_return_str}</div>
                </div>
                <div class="kpi-label">PORTFOLIO AGGREGATE</div>
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
                <div class="card mf-card">
                    <div class="kpi-top-row">
                        <div class="kpi-label">VALUE</div>
                        <div class="kpi-label">RETURN</div>
                    </div>
                    <div class="kpi-mid-row">
                        <div class="kpi-number">{value_str}</div>
                        <div class="kpi-number">{ret_str}</div>
                    </div>
                    <div class="kpi-label">{display_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
