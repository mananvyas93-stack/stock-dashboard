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

# ---------- THEME / CSS (New Hierarchy) ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,400,1,0&display=swap');

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

    /* --- NEW ENHANCED KPI CARD CSS --- */
    .mf-card {
        background: #f4f6f8 !important;
        border: 1px solid #e0e4ea !important;
        border-radius: 8px;
        padding: 12px 14px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 90px;
        margin-bottom: 8px;
    }

    /* Top Row: Left Label + Right Label */
    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }

    .kpi-sub-left {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.75rem; /* 12px */
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b; /* Slate-500 */
        letter-spacing: 0.05em;
    }

    .kpi-sub-right {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.75rem; /* 12px */
        font-weight: 500;
        color: #94a3b8; /* Slate-400 */
        text-align: right;
    }

    /* Main Row: Big Value + Pct */
    .kpi-main-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    .kpi-value-big {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem; /* 24px */
        font-weight: 700;
        color: #0f172a; /* Slate-900 */
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .kpi-value-secondary {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 2px;
    }

    /* Bottom Row: Main Category Label */
    .kpi-bottom-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155; /* Slate-700 */
        margin-top: 6px;
    }

    /* Color Utilities */
    .text-green { color: #16a34a !important; }
    .text-red { color: #dc2626 !important; }
    .text-blue { color: #0f172a !important; }

    /* --- TAB STYLING --- */
    .stTabs { margin-top: 0.75rem; }
    .stTabs [data-baseweb="tab-list"] {
        display: flex; align-items: flex-end; gap: 0rem; width: 100%;
        border-bottom: 1px solid var(--border); background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 25% !important; display: flex; align-items: center; justify-content: center;
        font-family: 'Space Grotesk', sans-serif !important; font-size: 0.7rem !important;
        padding: 4px 0 3px 0 !important; color: #16233a !important; background: transparent !important;
        border: none !important; cursor: pointer;
    }
    .stTabs [aria-selected="true"] { color: #0f172a !important; font-weight: 500 !important; }
    .stTabs [data-baseweb="tab"]::after {
        content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px;
        border-radius: 999px; background: transparent; transition: background-color 140ms ease-out;
    }
    .stTabs [aria-selected="true"]::after { background: #0b1530; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; }

    /* Heatmap Container */
    .stPlotlyChart { background: transparent !important; }
    
    /* Header Card */
    .header-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 8px;
    }
    .page-title { color: #e6eaf0; font-size: 1.0rem; font-weight: 600; margin: 0; }
    .page-subtitle { color: #9ba7b8; font-size: 0.7rem; margin: 0; }

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
    if inr_value is None or inr_value != inr_value: return "₹0.0 L"
    lacs = inr_value / 100000.0
    return f"₹{lacs:,.1f} L"

@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    navs: dict[str, float] = {}
    for entry in MF_CONFIG:
        ticker = entry.get("Ticker") or ""
        scheme = entry["Scheme"]
        if not ticker: continue
        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period="5d", interval="1d")
            if hist is None or hist.empty: continue
            nav = float(hist["Close"].iloc[-1])
            if nav > 0: navs[scheme] = nav
        except Exception: continue
    return navs

def compute_india_mf_aggregate() -> dict:
    """
    Computes aggregate Indian MF metrics with 1-Day Change Logic.
    Also returns the 'latest_date_str' formatted as '7 December'.
    """
    total_value_inr = 0.0
    total_daily_pl_inr = 0.0
    latest_dt_obj = None

    for mf_entry in MF_CONFIG:
        ticker = mf_entry.get("Ticker") or ""
        units = float(mf_entry["Units"] or 0.0)
        file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

        if not ticker or units <= 0:
            total_value_inr += file_value_inr
            continue

        try:
            tkr = yf.Ticker(ticker)
            # Fetch 5 days to find at least 2 valid points and the date
            hist = tkr.history(period="5d")
            
            # --- 1. CAPTURE DATE ---
            if not hist.empty:
                last_idx = hist.index[-1]
                current_dt_obj = last_idx.date()
                if latest_dt_obj is None or current_dt_obj > latest_dt_obj:
                    latest_dt_obj = current_dt_obj

            # --- 2. CALCULATE VALUE (With Safety Check) ---
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

            # --- 3. CALCULATE 1-DAY CHANGE (P&L) ---
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

    # Format the date string (e.g., "7 December")
    if latest_dt_obj:
        date_str = latest_dt_obj.strftime("%d %B")
        if date_str.startswith("0"):
            date_str = date_str[1:]
    else:
        date_str = "N/A"

    return {
        "total_value_inr": total_value_inr, 
        "daily_pl_inr": total_daily_pl_inr,
        "latest_date_str": date_str
    }

# ---------- FX HELPERS ----------
@st.cache_data(ttl=3600)
def get_aed_inr_rate_from_yahoo() -> float:
    try:
        tkr = yf.Ticker("AEDINR=X")
        hist = tkr.history(period="5d")
        if hist is None or hist.empty: return 22.50
        return float(hist["Close"].iloc[-1])
    except: return 22.50

def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹{lacs:,.2f} L"

# ---------- PRICE FETCHING ----------
@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    data = yf.download(tickers=tickers, period="5d", interval="1d", auto_adjust=True, group_by="ticker", progress=False, threads=False)
    if data is None or data.empty: return pd.DataFrame()
    
    # Handle MultiIndex column flattening
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
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="5d", interval="1m", prepost=True)
            if hist is None or hist.empty: continue
            last_prices[t] = float(hist["Close"].iloc[-1])
        except: continue
    return pd.Series(last_prices) if last_prices else pd.Series(dtype=float)

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    # NEW DYNAMIC LABELS
    if weekday >= 5:
        phase_str = "Post Market" 
    else:
        if time(4,0) <= t < time(9,30): phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0): phase_str = "Live Market"
        else: phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()
    return phase_str, (intraday if (intraday is not None and not intraday.empty) else base_close)

# ---------- POSITION BUILDER ----------
def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None) -> pd.DataFrame:
    rows = []
    
    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        live_price = 0.0
        if prices_intraday is not None: live_price = float(prices_intraday.get(t, 0.0))
        if live_price == 0 and not prices_close.empty:
             live_price = float(prices_close.iloc[-1].get(t, 0.0))

        prev_close_price = 0.0
        if not prices_close.empty and t in prices_close.columns:
            col_data = prices_close[t].dropna()
            us_tz = ZoneInfo("America/New_York")
            today_date = datetime.now(us_tz).date()
            if len(col_data) >= 2:
                last_dt = col_data.index[-1].date()
                if last_dt == today_date: prev_close_price = float(col_data.iloc[-2])
                else: prev_close_price = float(col_data.iloc[-1])
            elif len(col_data) == 1:
                prev_close_price = float(col_data.iloc[-1])

        if live_price <= 0:
            value_aed = purchase; day_pct = 0.0; day_pl_aed = 0.0
            total_pl_aed = 0.0; total_pct = 0.0; price_usd = 0.0
        else:
            price_usd = live_price
            price_aed = price_usd * USD_TO_AED
            value_aed = price_aed * units
            
            # Simple P&L vs Prev Close
            if prev_close_price > 0:
                day_pct = (price_usd / prev_close_price - 1.0) * 100.0
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

    sv_vals = {k: sv[k].sum() for k in ["ValueAED", "PurchaseAED", "DayPLAED", "TotalPLAED", "Units"]}
    sv_row = pd.DataFrame([{
        "Name": "SV Portfolio", "Ticker": "SVPF", "Owner": "SV", "Sector": "Mixed",
        "Units": sv_vals["Units"], "PriceUSD": 0.0, "ValueAED": sv_vals["ValueAED"], "PurchaseAED": sv_vals["PurchaseAED"],
        "DayPct": (sv_vals["DayPLAED"] / sv_vals["ValueAED"] * 100.0) if sv_vals["ValueAED"] > 0 else 0.0,
        "DayPLAED": sv_vals["DayPLAED"],
        "TotalPct": (sv_vals["TotalPLAED"] / sv_vals["PurchaseAED"] * 100.0) if sv_vals["PurchaseAED"] > 0 else 0.0,
        "TotalPLAED": sv_vals["TotalPLAED"],
        "WeightPct": 0.0
    }])
    
    combined = pd.concat([mv, sv_row], ignore_index=True)
    total_all = combined["ValueAED"].sum()
    combined["WeightPct"] = combined["ValueAED"] / total_all * 100.0 if total_all > 0 else 0.0
    return combined
    # ---------- UI & EXECUTION ----------

market_status_str, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()

if isinstance(price_source, pd.DataFrame): positions = build_positions_from_prices(price_source, None)
else: positions = build_positions_from_prices(prices_close, price_source)

agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions
AED_TO_INR = get_aed_inr_rate_from_yahoo()

# Global Totals
total_val_aed = positions["ValueAED"].sum()
total_purchase_aed = positions["PurchaseAED"].sum()
total_pl_aed = positions["TotalPLAED"].sum()
day_pl_aed = positions["DayPLAED"].sum()
total_pl_pct = (total_pl_aed / total_purchase_aed * 100.0) if total_purchase_aed > 0 else 0.0

total_val_inr_lacs = fmt_inr_lacs_from_aed(total_val_aed, AED_TO_INR)

# Header
st.markdown(f"""
<div class="header-card">
  <div class="page-title">Stocks Dashboard</div>
  <div class="page-subtitle">{market_status_str} Data</div>
</div>
""", unsafe_allow_html=True)

overview_tab, sv_tab, us_tab, mf_tab = st.tabs(["🪙 Overview", "💷 SV Stocks", "💵 US Stocks", "💴 India MF"])

# --- OVERVIEW ---
with overview_tab:
    # 1. Calc Data
    us_day_pl_inr = day_pl_aed * AED_TO_INR
    us_prev_val_aed = total_val_aed - day_pl_aed
    us_day_pct = (day_pl_aed / us_prev_val_aed * 100.0) if us_prev_val_aed > 0 else 0.0

    mf_data = compute_india_mf_aggregate()
    mf_val_inr = float(mf_data.get("total_value_inr", 0.0))
    mf_day_pl_inr = float(mf_data.get("daily_pl_inr", 0.0))
    mf_date_str = mf_data.get("latest_date_str", "N/A")
    
    mf_prev_val = mf_val_inr - mf_day_pl_inr
    mf_day_pct = (mf_day_pl_inr / mf_prev_val * 100.0) if mf_prev_val > 0 else 0.0
    
    mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
    mf_abs_return_pct = ((mf_val_inr - mf_total_cost)/mf_total_cost*100.0) if mf_total_cost > 0 else 0.0

    # 2. Render Cards
    c1, c2, c3, c4 = st.columns(4)

    def render_enhanced_card(col, top_left, top_right, main_val, sec_val, bottom_label):
        sec_color = "text-green" if "+" in sec_val else ("text-red" if "-" in sec_val else "text-blue")
        with col:
            st.markdown(f"""
            <div class="mf-card">
                <div class="kpi-top-row">
                    <span class="kpi-sub-left">{top_left}</span>
                    <span class="kpi-sub-right">{top_right}</span>
                </div>
                <div class="kpi-main-row">
                    <span class="kpi-value-big">{main_val}</span>
                    <span class="kpi-value-secondary {sec_color}">{sec_val}</span>
                </div>
                <div class="kpi-bottom-label">{bottom_label}</div>
            </div>
            """, unsafe_allow_html=True)

    # Card 1: Dynamic US
    render_enhanced_card(c1, market_status_str, "Today's Profit", f"₹{us_day_pl_inr:,.0f}", f"{us_day_pct:+.2f}%", "US Stocks")

    # Card 2: India MF with Date
    render_enhanced_card(c2, "Latest Profit", mf_date_str, f"₹{mf_day_pl_inr:,.0f}", f"{mf_day_pct:+.2f}%", "India MF")

    # Card 3: US Holding
    render_enhanced_card(c3, "Total Holding", "Total Return", total_val_inr_lacs, f"{total_pl_pct:+.2f}%", "US Stocks")

    # Card 4: MF Holding
    render_enhanced_card(c4, "Total Holding", "Total Return", fmt_inr_lacs(mf_val_inr), f"{mf_abs_return_pct:.2f}%", "India MF")

    # 3. Heatmap
    st.markdown('''<div style="font-family: 'Space Grotesk'; color:#16233a; font-size:0.75rem; margin:10px 0 4px 0;">Today's Gains</div>''', unsafe_allow_html=True)
    
    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data.")
    else:
        hm = agg_for_heatmap.copy()
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR
        # Add MF Block
        if mf_val_inr > 0:
            hm = pd.concat([hm, pd.DataFrame([{
                "Name": "Indian MF", "Ticker": "INDMF", "Owner": "MF", "Sector": "India MF",
                "Units": 0, "PriceUSD": 0, "ValueAED": mf_val_inr / AED_TO_INR, "PurchaseAED": 0,
                "DayPct": 0, "DayPLAED": mf_day_pl_inr / AED_TO_INR, "DayPLINR": mf_day_pl_inr,
                "TotalPct": 0, "TotalPLAED": 0, "WeightPct": 0
            }])], ignore_index=True)
        
        hm["SizeForHeatmap"] = hm["DayPLINR"].abs() + 1e-6
        hm["DayPLK"] = hm["DayPLINR"] / 1000.0
        hm["DayPLKLabel"] = hm["DayPLK"].apply(lambda v: f"₹{abs(v):,.0f}k" if v>=0 else f"[₹{abs(v):,.0f}k]")

        fig = px.treemap(
            hm, path=["Name"], values="SizeForHeatmap", color="DayPLINR",
            color_continuous_scale=[COLOR_DANGER, "#16233a", COLOR_SUCCESS],
            color_continuous_midpoint=0, custom_data=["DayPLINR", "Ticker", "DayPLKLabel"]
        )
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>%{customdata[2]}<extra></extra>",
            texttemplate="%{label}<br>%{customdata[2]}",
            textfont=dict(family="Space Grotesk", color="#e6eaf0", size=11),
            marker=dict(line=dict(width=0)), root_color=COLOR_BG
        )
        fig.update_layout(margin=dict(t=0,l=0,r=0,b=0), paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# --- OTHER TABS (Restored Full Logic) ---
with sv_tab:
    if sv_positions.empty: st.info("No SV positions.")
    else:
        # Full SV Cards
        sv_total_val_aed = sv_positions["ValueAED"].sum()
        sv_total_pl_aed = sv_positions["TotalPLAED"].sum()
        sv_day_pl_aed = sv_positions["DayPLAED"].sum()
        sv_total_pl_pct = (sv_total_pl_aed / sv_positions["PurchaseAED"].sum() * 100.0) if sv_positions["PurchaseAED"].sum() > 0 else 0.0
        sv_day_pl_pct = (sv_day_pl_aed / (sv_total_val_aed - sv_day_pl_aed) * 100.0) if (sv_total_val_aed - sv_day_pl_aed) > 0 else 0.0

        c1, c2, c3 = st.columns(3)
        render_enhanced_card(c1, "SV Portfolio", "Today's Profit", f"AED {sv_day_pl_aed:,.0f}", f"{sv_day_pl_pct:+.2f}%", "Realized + Unrealized")
        render_enhanced_card(c2, "SV Portfolio", "Total Profit", f"AED {sv_total_pl_aed:,.0f}", f"{sv_total_pl_pct:+.2f}%", "Since Inception")
        render_enhanced_card(c3, "SV Portfolio", "Total Holding", f"AED {sv_total_val_aed:,.0f}", "", fmt_inr_lacs_from_aed(sv_total_val_aed, AED_TO_INR))

        hm_sv = sv_positions.copy()
        hm_sv["Name"] = hm_sv["Name"].str.replace(r"\s*\[SV\]", "", regex=True)
        hm_sv["SizeForHeatmap"] = hm_sv["DayPLAED"].abs() + 1e-6
        hm_sv["DayPLLabel"] = hm_sv["DayPLAED"].apply(lambda v: f"AED {v:,.0f}" if v>=0 else f"[AED {abs(v):,.0f}]")

        fig_sv = px.treemap(
            hm_sv, path=["Name"], values="SizeForHeatmap", color="DayPLAED",
            color_continuous_scale=[COLOR_DANGER, "#16233a", COLOR_SUCCESS],
            color_continuous_midpoint=0, custom_data=["DayPLAED", "Ticker", "DayPLLabel"]
        )
        fig_sv.update_traces(
            hovertemplate="<b>%{label}</b><br>%{customdata[2]}<extra></extra>",
            texttemplate="%{label}<br>%{customdata[2]}",
            textfont=dict(family="Space Grotesk", color="#e6eaf0", size=11),
            marker=dict(line=dict(width=0)), root_color=COLOR_BG
        )
        fig_sv.update_layout(margin=dict(t=0,l=0,r=0,b=0), paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG, coloraxis_showscale=False)
        st.plotly_chart(fig_sv, use_container_width=True)

with us_tab:
    st.info("US Stocks Details")

with mf_tab:
    if not MF_CONFIG: st.info("No MF Config")
    else:
        mf_rows = []
        mf_navs_list = load_mf_navs_from_yahoo()
        for item in MF_CONFIG:
            sch = item["Scheme"]; units = item["Units"]; cost = item["CostINR"]; file_val = item.get("InitialValueINR", 0.0)
            ln = mf_navs_list.get(sch)
            val = file_val
            # Safety Check
            if ln and ln > 0:
                cand = ln * units
                if file_val > 0 and 0.9 <= (cand/file_val) <= 1.1: val = cand
                elif file_val == 0: val = cand
            
            # Abs Return
            ret = ((val - cost)/cost * 100.0) if cost > 0 else 0.0
            mf_rows.append({"n": sch, "v": val, "r": ret})
        
        mf_rows.sort(key=lambda x: x["v"], reverse=True)
        
        # Header Card
        tot_v = sum(r["v"] for r in mf_rows); tot_c = sum(i["CostINR"] for i in MF_CONFIG)
        tot_r = ((tot_v - tot_c)/tot_c * 100.0) if tot_c > 0 else 0.0
        
        render_enhanced_card(st, "Mutual Fund Portfolio", "Total Value", fmt_inr_lacs(tot_v), f"{tot_r:.2f}%", "Weighted Return")

        for r in mf_rows:
            disp_name = r["n"].replace(" Fund Growth", "").split("\n")[0]
            st.markdown(f"""
            <div class="card mf-card" style="padding:8px 10px; margin-bottom:6px; min-height:auto;">
                <div class="page-title" style="margin-bottom:2px; font-size:0.9rem;">{disp_name}</div>
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span class="kpi-value-main" style="font-size:1.0rem;">{fmt_inr_lacs(r["v"])}</span>
                    <span class="kpi-sub-right" style="color:#0f172a; font-weight:600;">{r["r"]:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
