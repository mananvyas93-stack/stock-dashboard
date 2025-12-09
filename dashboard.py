import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
# FIXED: Added 'time' back to imports to prevent the crash
from datetime import datetime, time, timedelta, date
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
        color: #475569 !important; 
        font-weight: 500;
    }

    .mf-card .kpi-value-main {
        color: #0f1a2b !important; 
        font-weight: 700;
    }
    
    .mf-card .kpi-number {
         color: #0f1a2b !important; 
    }

    /* --------------------------------------------------------- */

    /* UNIFIED LABEL STYLE */
    .kpi-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.6rem; 
        font-weight: 400; 
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.0;
        white-space: nowrap;
        margin: 0;
    }

    /* UNIFIED NUMBER STYLE */
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

    /* Layout Helpers */
    .kpi-mid-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 0; 
    }

    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        width: 100%;
        align-items: flex-end; 
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
        flex: 1 1 20% !important;
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
</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS & FALLBACKS ----------
DEFAULT_USD_AED = 3.6725
DEFAULT_AED_INR = 24.50

COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f"
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# Card Text Colors (Darker for White Backgrounds)
TEXT_GREEN_DARK = "#15803d" 
TEXT_RED_DARK = "#b91c1c"

# ---------- PORTFOLIO CONFIG ----------
# UPDATED with latest MSFT data (29 units)
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
    navs: dict[str, float] = {}
    for entry in MF_CONFIG:
        ticker = entry.get("Ticker") or ""
        scheme = entry["Scheme"]
        if not ticker:
            continue
        try:
            tkr = yf.Ticker(ticker)
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
            
            if not hist.empty:
                latest_nav = float(hist["Close"].iloc[-1])
                candidate_value = latest_nav * units
                
                if candidate_value > 0:
                    value_inr = candidate_value
                else:
                    value_inr = file_value_inr
            else:
                value_inr = file_value_inr

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
def get_fx_rates() -> dict:
    rates = {
        "USD_AED": DEFAULT_USD_AED,
        "AED_INR": DEFAULT_AED_INR
    }
    try:
        hist = yf.Ticker("USDAED=X").history(period="5d")
        if not hist.empty:
            rates["USD_AED"] = float(hist["Close"].iloc[-1])
    except: pass
    try:
        hist = yf.Ticker("AEDINR=X").history(period="5d")
        if not hist.empty:
            rates["AED_INR"] = float(hist["Close"].iloc[-1])
    except: pass
    return rates


def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹{lacs:,.2f} L"

# ---------- PRICE FETCHING ----------

@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    data = yf.download(tickers, period="5d", interval="1d", auto_adjust=True, group_by="ticker", progress=False, threads=False)
    if data is None or data.empty: return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        lvl1 = data.columns.get_level_values(1)
        if "Adj Close" in lvl1: close = data.xs("Adj Close", level=1, axis=1)
        elif "Close" in lvl1: close = data.xs("Close", level=1, axis=1)
        else: close = data.xs(lvl1[0], level=1, axis=1)
        close.columns = close.columns.get_level_values(0)
    else:
        if "Adj Close" in data.columns: close = data[["Adj Close"]]
        elif "Close" in data.columns: close = data[["Close"]]
        else: return pd.DataFrame()
        close.columns = [tickers[0]]
    close = close.dropna(how="all")
    return close

@st.cache_data(ttl=60)
def load_prices_intraday() -> pd.Series:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    last_prices: dict[str, float] = {}
    us_tz = ZoneInfo("America/New_York")
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="5d", interval="1m", prepost=True)
            if hist is None or hist.empty: continue
            last_prices[t] = float(hist["Close"].iloc[-1])
        except: continue
    if not last_prices: return pd.Series(dtype=float)
    return pd.Series(last_prices)

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    if weekday >= 5: phase_str = "Post Market"
    else:
        if time(4,0) <= t < time(9,30): phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0): phase_str = "Live Market"
        else: phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()
    if intraday is None or intraday.empty: return phase_str, base_close
    return phase_str, intraday

@st.cache_data(ttl=60)
def get_market_indices_change(phase_str: str) -> str:
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
    except: pass

    nasdaq_str = "Nasdaq 0.0%"
    target_ticker = "QQQ"
    try:
        tkr = yf.Ticker(target_ticker)
        hist_1m = tkr.history(period="1d", interval="1m", prepost=True)
        daily = tkr.history(period="5d")
        if not hist_1m.empty and not daily.empty:
            curr = hist_1m["Close"].iloc[-1]
            prev_close = 0.0
            if "Post" in phase_str:
                prev_close = daily["Close"].iloc[-1]
                pct_post = (curr / prev_close - 1) * 100
                if abs(pct_post) < 0.01:
                    if len(daily) >= 2:
                        close_today = daily["Close"].iloc[-1]
                        close_prev = daily["Close"].iloc[-2]
                        pct = (close_today / close_prev - 1) * 100
                        nasdaq_str = f"Nasdaq {pct:+.1f}%"
                    else: nasdaq_str = f"Nasdaq {pct_post:+.1f}%"
                else: nasdaq_str = f"Nasdaq {phase_str} {pct_post:+.1f}%"
            else:
                last_daily_date = daily.index[-1].date()
                now_date = datetime.now(ZoneInfo("America/New_York")).date()
                if last_daily_date == now_date:
                    if len(daily) >= 2: prev_close = daily["Close"].iloc[-2]
                    else: prev_close = daily["Close"].iloc[-1] 
                else: prev_close = daily["Close"].iloc[-1]
                if prev_close > 0 and "Nasdaq" not in nasdaq_str: 
                    pct = (curr / prev_close - 1) * 100
                    nasdaq_str = f"Nasdaq {phase_str} {pct:+.1f}%"
    except: pass
    return f"{nifty_str} <span style='opacity:0.4; margin:0 6px;'>|</span> {nasdaq_str}"

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None, usd_to_aed_rate: float) -> pd.DataFrame:
    rows = []
    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])
        live_price = 0.0
        if prices_intraday is not None: live_price = float(prices_intraday.get(t, 0.0))
        if live_price == 0 and not prices_close.empty: live_price = float(prices_close.iloc[-1].get(t, 0.0))
        
        prev_close_price = 0.0
        if not prices_close.empty:
            last_date = prices_close.index[-1].date()
            us_tz = ZoneInfo("America/New_York")
            today_date = datetime.now(us_tz).date()
            col_data = prices_close[t]
            if len(col_data) >= 2:
                if last_date == today_date: prev_close_price = float(col_data.iloc[-2])
                else: prev_close_price = float(col_data.iloc[-1])
            elif len(col_data) == 1: prev_close_price = float(col_data.iloc[-1])

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
            if prev_close_price > 0: day_pct = (price_usd / prev_close_price - 1.0) * 100.0
            else: day_pct = 0.0
            day_pl_aed = value_aed * (day_pct / 100.0)
            total_pl_aed = value_aed - purchase
            total_pct = (total_pl_aed / purchase) * 100.0 if purchase > 0 else 0.0

        rows.append({
            "Name": item["Name"], "Ticker": t, "Owner": item["Owner"], "Sector": item["Sector"],
            "Units": units, "PriceUSD": price_usd, "ValueAED": value_aed, "PurchaseAED": purchase,
            "DayPct": day_pct, "DayPLAED": day_pl_aed, "TotalPct": total_pct, "TotalPLAED": total_pl_aed,
        })
    df = pd.DataFrame(rows)
    total_val = df["ValueAED"].sum()
    df["WeightPct"] = df["ValueAED"] / total_val * 100.0 if total_val > 0 else 0.0
    return df

def aggregate_for_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    mv = df[df["Owner"] == "MV"].copy()
    sv = df[df["Owner"] == "SV"].copy()
    if sv.empty: return mv.reset_index(drop=True)
    total_val_all = df["ValueAED"].sum()
    sv_val = sv["ValueAED"].sum()
    sv_purchase = sv["PurchaseAED"].sum()
    sv_day_pl = sv["DayPLAED"].sum()
    sv_total_pl = sv["TotalPLAED"].sum()
    sv_row = pd.DataFrame([{
        "Name": "SV Portfolio", "Ticker": "SVPF", "Owner": "SV", "Sector": "Mixed",
        "Units": sv["Units"].sum(), "PriceUSD": 0.0, "ValueAED": sv_val, "PurchaseAED": sv_purchase,
        "DayPct": (sv_day_pl / sv_val * 100.0) if sv_val > 0 else 0.0, "DayPLAED": sv_day_pl,
        "TotalPct": (sv_total_pl / sv_purchase * 100.0) if sv_purchase > 0 else 0.0,
        "TotalPLAED": sv_total_pl, "WeightPct": (sv_val / total_val_all * 100.0) if total_val_all > 0 else 0.0,
    }])
    mv = mv.copy()
    mv["WeightPct"] = mv["ValueAED"] / total_val_all * 100.0 if total_val_all > 0 else 0.0
    combined = pd.concat([mv, sv_row], ignore_index=True)
    return combined
    # ---------- DATA PIPELINE ----------

market_status_str, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()
header_metrics_str = get_market_indices_change(market_status_str)

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

overview_tab, sv_tab, us_tab, mf_tab, trend_tab = st.tabs([
    "🪙 Overview",
    "💷 SV Stocks",
    "💵 US Stocks",
    "💴 India MF",
    "💶 Trend"
])

# ---------- HOME TAB ----------

with overview_tab:
    us_day_pl_inr = day_pl_aed * AED_TO_INR
    us_prev_val_aed = total_val_aed - day_pl_aed
    us_day_pct = (day_pl_aed / us_prev_val_aed * 100.0) if us_prev_val_aed > 0 else 0.0

    mf_agg = compute_india_mf_aggregate()
    mf_val_inr = float(mf_agg.get("total_value_inr", 0.0) or 0.0)
    mf_day_pl_inr = float(mf_agg.get("daily_pl_inr", 0.0) or 0.0)
    
    mf_prev_val = mf_val_inr - mf_day_pl_inr
    mf_day_pct = (mf_day_pl_inr / mf_prev_val * 100.0) if mf_prev_val > 0 else 0.0

    mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
    mf_total_profit = mf_val_inr - mf_total_cost
    mf_abs_return_pct = (mf_total_profit / mf_total_cost * 100.0) if mf_total_cost > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)

    def render_new_kpi_card(col, top_label, main_value, right_value, bottom_label):
        with col:
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

    status_display = f"TODAY'S PROFIT <span style='opacity:0.5; margin:0 4px;'>|</span> {market_status_str.upper()}"
    render_new_kpi_card(c1, status_display, f"₹{us_day_pl_inr:,.0f}", f"{us_day_pct:+.2f}%", "US STOCKS")
    render_new_kpi_card(c2, "TODAY'S PROFIT", f"₹{mf_day_pl_inr:,.0f}", f"{mf_day_pct:+.2f}%", "INDIA MF")
    render_new_kpi_card(c3, "TOTAL HOLDING", total_val_inr_lacs, f"{total_pl_pct:+.2f}%", "US STOCKS")
    render_new_kpi_card(c4, "TOTAL HOLDING", fmt_inr_lacs(mf_val_inr), f"{mf_abs_return_pct:+.2f}%", "INDIA MF")

    st.markdown(
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:10px 0 4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data.")
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
            if v >= 0: return f"₹{abs(v):,.0f}k"
            else: return f"[₹{abs(v):,.0f}k]"

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

# ---------- SV TAB ----------

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

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="card mf-card"><div class="kpi-label">TODAY'S PROFIT</div><div class="kpi-mid-row"><div class="kpi-number">{sv_day_pl_aed_str}</div><div class="kpi-number">{sv_day_pl_pct_str}</div></div><div class="kpi-label">US STOCKS</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="card mf-card"><div class="kpi-label">TOTAL PROFIT</div><div class="kpi-mid-row"><div class="kpi-number">{sv_total_pl_aed_str}</div><div class="kpi-number">{sv_total_pl_pct_str}</div></div><div class="kpi-label">US STOCKS</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="card mf-card"><div class="kpi-label">TOTAL HOLDING</div><div class="kpi-mid-row"><div class="kpi-number">{sv_total_val_aed_str}</div><div class="kpi-number">{sv_total_val_inr_lacs_str}</div></div><div class="kpi-label">US STOCKS</div></div>""", unsafe_allow_html=True)

        st.markdown("""<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;">Today's Gains – SV</div>""", unsafe_allow_html=True)

        hm_sv = sv_positions.copy()
        hm_sv["Name"] = hm_sv["Name"].str.replace(r"\s*\[SV\]", "", regex=True)
        hm_sv["SizeForHeatmap"] = hm_sv["DayPLAED"].abs() + 1e-6
        def label_for_sv(v: float) -> str: return f"AED {v:,.0f}" if v >=0 else f"[AED {abs(v):,.0f}]"
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
        fig_sv.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG, coloraxis_showscale=False, font=dict(family="Space Grotesk, sans-serif"))
        st.plotly_chart(fig_sv, use_container_width=True, config={"displayModeBar": False})
        
        # --- FIXED SECTION: SV HOLDINGS CARDS ---
        st.markdown("""<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:14px 0 4px 0;">SV Holdings</div>""", unsafe_allow_html=True)
        
        sorted_sv = sv_positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base style WITHOUT color
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_sv:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            
            units_str = f"{units:,.0f} UNITS • SV"
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # INLINE COLOR LOGIC (Nuclear Option)
            color_pl = "#15803d" if pl_aed >= 0 else "#b91c1c"
            color_pct = "#15803d" if pl_pct >= 0 else "#b91c1c"
            display_name = name.upper().replace(" [SV]", "")

            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div style="{base_label_style} color:{color_pl} !important; font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div style="{base_label_style} color:{color_pct} !important; font-weight:600;">{pl_pct_str}</div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

# ---------- US STOCKS TAB ----------

with us_tab:
    if positions.empty:
        st.info("No US positions found.")
    else:
        sorted_pos = positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_pos:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            owner = row["Owner"]
            
            suffix = " • SV" if owner == "SV" else ""
            units_str = f"{units:,.0f} UNITS{suffix}"
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # INLINE COLOR LOGIC (Nuclear Option)
            color_pl = "#15803d" if pl_aed >= 0 else "#b91c1c"
            color_pct = "#15803d" if pl_pct >= 0 else "#b91c1c"
            display_name = name.upper().replace(" [SV]", "")

            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div style="{base_label_style} color:{color_pl} !important; font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div style="{base_label_style} color:{color_pct} !important; font-weight:600;">{pl_pct_str}</div>
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
            
            value_inr = file_value_inr
            if live_nav is not None and live_nav > 0 and units > 0:
                value_inr = live_nav * units
            
            abs_return = (value_inr - cost_inr) / cost_inr * 100.0 if cost_inr > 0 else 0.0
            mf_rows.append({"scheme": scheme, "value_inr": value_inr, "return_pct": abs_return})

        mf_rows.sort(key=lambda r: r["value_inr"], reverse=True)
        total_value_inr = sum(r["value_inr"] for r in mf_rows)
        mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
        total_abs_return_pct = (total_value_inr - mf_total_cost) / mf_total_cost * 100.0 if mf_total_cost > 0 else 0.0

        st.markdown(f"""<div class="card mf-card"><div class="kpi-top-row"><div class="kpi-label">VALUE</div><div class="kpi-label">RETURN</div></div><div class="kpi-mid-row"><div class="kpi-number">{fmt_inr_lacs(total_value_inr)}</div><div class="kpi-number">{total_abs_return_pct:.2f}%</div></div><div class="kpi-label">PORTFOLIO AGGREGATE</div></div>""", unsafe_allow_html=True)

        for row in mf_rows:
            scheme = row["scheme"]
            display_name = scheme.replace(" Fund Growth", "")
            parts = display_name.split()
            if parts and all(ch.isdigit() or ch in "/-" for ch in parts[-1]):
                display_name = " ".join(parts[:-1])
            
            st.markdown(f"""<div class="card mf-card"><div class="kpi-top-row"><div class="kpi-label">VALUE</div><div class="kpi-label">RETURN</div></div><div class="kpi-mid-row"><div class="kpi-number">{fmt_inr_lacs(row['value_inr'])}</div><div class="kpi-number">{row['return_pct']:.1f}%</div></div><div class="kpi-label">{display_name}</div></div>""", unsafe_allow_html=True)
            # ==========================================
# PART 3: TREND TAB
# ==========================================

with trend_tab:
    st.markdown("### Total Wealth Trend (₹)")
    
    # 1. PILLS SELECTOR (Modern)
    if hasattr(st, "pills"):
        range_selection = st.pills("Time Range", ["1W", "1M", "3M", "Max"], default="3M", selection_mode="single")
    else:
        range_selection = st.radio("Time Range", ["1W", "1M", "3M", "Max"], index=2, horizontal=True)

    # 2. FETCH HISTORY (Cached - Load MAX by default)
    @st.cache_data(ttl=3600) 
    def fetch_consolidated_history():
        us_tickers = sorted({item["Ticker"] for item in portfolio_config})
        # Start from Aug 1st, 2025 as requested
        us_data = yf.download(us_tickers, start="2025-08-01", progress=False, threads=True)
        
        if isinstance(us_data.columns, pd.MultiIndex):
            if "Close" in us_data.columns.get_level_values(0): us_close = us_data["Close"]
            else: us_close = us_data.xs("Close", level=1, axis=1) if "Close" in us_data.columns.get_level_values(1) else us_data
        else: us_close = us_data["Close"] if "Close" in us_data.columns else us_data

        mf_tickers = [item["Ticker"] for item in MF_CONFIG if item.get("Ticker")]
        mf_data = yf.download(mf_tickers, start="2025-08-01", progress=False, threads=True)
        
        if isinstance(mf_data.columns, pd.MultiIndex):
            if "Close" in mf_data.columns.get_level_values(0): mf_close = mf_data["Close"]
            else: mf_close = mf_data.xs("Close", level=1, axis=1) if "Close" in mf_data.columns.get_level_values(1) else mf_data
        else: mf_close = mf_data["Close"] if "Close" in mf_data.columns else mf_data

        all_dates = us_close.index.union(mf_close.index).sort_values()
        us_close = us_close.reindex(all_dates).ffill()
        mf_close = mf_close.reindex(all_dates).ffill()
        
        total_wealth = pd.Series(0.0, index=all_dates)
        rate_inr = AED_TO_INR if 'AED_TO_INR' in locals() else 24.5
        us_conversion_factor = 3.6725 * rate_inr 
        
        for item in portfolio_config:
            t = item["Ticker"]
            units = float(item["Units"])
            if t in us_close.columns:
                val = us_close[t] * units * us_conversion_factor
                total_wealth = total_wealth.add(val, fill_value=0)
        
        for item in MF_CONFIG:
            t = item.get("Ticker")
            units = float(item["Units"] or 0)
            if t and t in mf_close.columns:
                val = mf_close[t] * units
                total_wealth = total_wealth.add(val, fill_value=0)
                
        return total_wealth.dropna()

    try:
        full_trend = fetch_consolidated_history()
        
        if not full_trend.empty:
            end_date = full_trend.index.max()
            start_date = full_trend.index.min()
            
            if range_selection == "1W": cutoff = end_date - timedelta(days=7)
            elif range_selection == "1M": cutoff = end_date - timedelta(days=30)
            elif range_selection == "3M": cutoff = end_date - timedelta(days=90)
            else: cutoff = start_date
            
            filtered_trend = full_trend[full_trend.index >= cutoff]
            
            df_chart = pd.DataFrame({
                "Date": filtered_trend.index,
                "Total Wealth (₹)": filtered_trend.values
            })
            
            # FIXED CHART: Simplified arguments to prevent 'fill_color' error
            fig = px.area(
                df_chart, 
                x="Date", 
                y="Total Wealth (₹)",
                template="plotly_dark",
                height=350,
                color_discrete_sequence=["#2e7d32"] # Green line
            )
            
            fig.update_layout(
                paper_bgcolor="#0f1a2b",
                plot_bgcolor="#0f1a2b",
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(showgrid=False, title=None, tickfont=dict(family="Space Grotesk", color="#9ba7b8")),
                yaxis=dict(showgrid=True, gridcolor="#1f2d44", title=None, tickfont=dict(family="Space Grotesk", color="#9ba7b8")),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            
            curr_val = filtered_trend.iloc[-1]
            start_val_period = filtered_trend.iloc[0]
            abs_diff = curr_val - start_val_period
            pct_diff = (abs_diff / start_val_period) * 100 if start_val_period > 0 else 0
            
            st.metric(f"Change ({range_selection})", fmt_inr_lacs(abs_diff), f"{pct_diff:+.2f}%")
            
    except Exception as e:
        st.error(f"Error loading trends: {e}")
