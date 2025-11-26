import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, time
from zoneinfo import ZoneInfo

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
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,400,1,0&display=swap');

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

    .kpi-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 12px;
        box-shadow: none;
        margin-top: 4px;
        margin-bottom: 4px;
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
        font-size: 0.7rem;
        color: var(--muted);
        margin: 0;
        letter-spacing: 0.03em;
    }

    .kpi-label {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        margin-bottom: 4px;
    }

    .kpi-value-main {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text);
    }

    .stPlotlyChart {
        background: transparent !important;
    }

    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 18px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        vertical-align: middle;
        /* Recommended settings from Google */
        font-variation-settings:
          'FILL' 0,
          'wght' 400,
          'GRAD' 0,
          'opsz' 24;
    }

    .tab-icon {
        margin-right: 0.35rem;
    }

    .tab-label {
        display: inline-block;
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
        flex: 1 1 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.2rem;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.7rem !important;
        padding: 4px 2px 3px 2px !important;
        color: #16233a !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
        white-space: nowrap;
    }

    .stTabs [role="tab"] {
        min-width: 0 !important;
    }

    /* disable raised card, keep tabs flat */
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

    /* navy underline equal to tab width */
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
        background: #0b1530; /* navy indicator */
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    /* MF card styling */
    .mf-card {
        background: #f4f6f8 !important;
        border-color: #e0e4ea !important;
        color: #0f1a2b !important;
    }
    .mf-card .page-title {
        color: #0f1a2b !important;
    }
    .mf-card .kpi-label {
        color: #4b5563 !important;
    }
    .mf-card .kpi-value-main {
        color: #0f1a2b !important;
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
MF_CONFIG = [
    {
        "Scheme": "Axis Large and Mid Cap Fund Growth",
        "Category": "Large & Mid Cap",
        "Units": 55026.38,
        "CostINR": 1754912.25,
        "CurrentValueINR": 1829626.97,
        "XIRR": 8.66,
        "Ticker": "0P0001EP9Q.BO",  # Axis Large & Midcap Reg Gr
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 19360019",
        "Category": "ELSS",
        "Units": 286.62,
        "CostINR": 160000.00,
        "CurrentValueINR": 430364.02,
        "XIRR": 15.96,
        "Ticker": "0P00005VDI.BO",  # Franklin India ELSS Tax Saver Reg Gr
    },
    {
        "Scheme": "Franklin India ELSS Tax Saver Fund Growth 30097040",
        "Category": "ELSS",
        "Units": 190.43,
        "CostINR": 95000.00,
        "CurrentValueINR": 285933.35,
        "XIRR": 13.79,
        "Ticker": "0P00005VDI.BO",  # Same scheme/plan as above
    },
    {
        "Scheme": "ICICI Prudential ELSS Tax Saver Fund Growth 7389918/81",
        "Category": "ELSS",
        "Units": 267.83,
        "CostINR": 98000.00,
        "CurrentValueINR": 257506.11,
        "XIRR": 15.27,
        "Ticker": "0P00005WD6.BO",  # ICICI Pru ELSS Tax Saver Reg Gr
    },
    {
        "Scheme": "ICICI Prudential NASDAQ 100 Index Fund Growth 35135108/17",
        "Category": "US Index",
        "Units": 43574.66,
        "CostINR": 654967.25,
        "CurrentValueINR": 825534.95,
        "XIRR": 32.66,
        "Ticker": "0P0001NCLS.BO",  # ICICI Pru NASDAQ 100 Index Reg Gr
    },
    {
        "Scheme": "Mirae Asset Large and Mid Cap Fund Growth 79975690352",
        "Category": "Large & Mid Cap",
        "Units": 9054.85,
        "CostINR": 1327433.63,
        "CurrentValueINR": 1412837.30,
        "XIRR": 15.38,
        "Ticker": "0P0000ON3O.BO",  # Mirae Asset Large & Midcap Reg Gr
    },
    {
        "Scheme": "Nippon India Multi Cap Fund Growth 499355757325",
        "Category": "Multi Cap",
        "Units": 4813.52,
        "CostINR": 1404929.75,
        "CurrentValueINR": 1447001.15,
        "XIRR": 5.58,
        "Ticker": "0P00005WDS.BO",  # Nippon India Multi Cap Reg Gr
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15530560",
        "Category": "Flexi Cap",
        "Units": 25345.69,
        "CostINR": 2082395.88,
        "CurrentValueINR": 2191061.05,
        "XIRR": 9.66,
        "Ticker": "0P0000YWL0.BO",  # PPFAS Flexi Cap Reg Gr (old LT Equity Reg Gr)
    },
    {
        "Scheme": "Parag Parikh Flexi Cap Fund Growth 15722429",
        "Category": "Flexi Cap",
        "Units": 6095.12,
        "CostINR": 499975.00,
        "CurrentValueINR": 526905.71,
        "XIRR": 4.60,
        "Ticker": "0P0000YWL0.BO",  # Same scheme/plan as above
    },
    {
        "Scheme": "SBI Multicap Fund Growth 40501504",
        "Category": "Multi Cap",
        "Units": 83983.45,
        "CostINR": 1404929.75,
        "CurrentValueINR": 1434941.30,
        "XIRR": 3.97,
        "Ticker": "0P0001OF6C.BO",  # SBI Multicap Reg Gr
    },
]

# Helper: format INR values as "₹10.1 L"

def fmt_inr_lacs(inr_value: float) -> str:
    if inr_value is None or inr_value != inr_value:  # NaN check
        return "₹0.0 L"
    lacs = inr_value / 100000.0
    return f"₹{lacs:,.1f} L"


@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    """Fetch latest NAV for each MF that has a Yahoo ticker.

    Returns a mapping {SchemeName: nav_in_inr}. If a ticker is missing or
    data is unavailable, that scheme is simply omitted from the result.
    """
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
            # Use the last available close as NAV
            nav = float(hist["Close"].iloc[-1])
            if nav > 0:
                navs[scheme] = nav
        except Exception:
            continue
    return navs

@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    """Fetch latest NAV for each MF that has a Yahoo ticker.

    Returns a mapping {SchemeName: nav_in_inr}. If a ticker is missing or
    data is unavailable, that scheme is simply omitted from the result.
    """
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
            # Use the last available close as NAV
            nav = float(hist["Close"].iloc[-1])
            if nav > 0:
                navs[scheme] = nav
        except Exception:
            continue
    return navs


@st.cache_data(ttl=3600)
def compute_india_mf_aggregate() -> dict:
    """Compute aggregate Indian MF metrics including daily P&L.

    Uses Yahoo history(period="7d") to obtain the two latest valid NAVs
    for each mutual fund. Aggregates both total value and daily P&L.
    """
    mf_navs_full = {}

    # Fetch last 7 days for each ticker
    for entry in MF_CONFIG:
        ticker = entry.get("Ticker") or ""
        scheme = entry["Scheme"]
        if not ticker:
            continue
        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period="7d", interval="1d")
            if hist is None or hist.empty or "Close" not in hist.columns:
                continue
            closes = hist["Close"].dropna().tolist()
            if len(closes) >= 2:
                today_nav = float(closes[-1])
                yesterday_nav = float(closes[-2])
                mf_navs_full[scheme] = {
                    "today": today_nav,
                    "yesterday": yesterday_nav,
                }
        except Exception:
            continue

    total_value_inr = 0.0
    total_daily_pl_inr = 0.0

    for mf_entry in MF_CONFIG:
        scheme = mf_entry["Scheme"]
        units = float(mf_entry["Units"] or 0.0)
        stored_value_inr = float(mf_entry["CurrentValueINR"] or 0.0)

        nav_info = mf_navs_full.get(scheme)

        if nav_info:
            today_nav = nav_info["today"]
            yesterday_nav = nav_info["yesterday"]
            candidate_value = today_nav * units
            # Consistency check with stored total
            if stored_value_inr > 0:
                ratio = candidate_value / stored_value_inr
                value_inr = candidate_value if 0.8 <= ratio <= 1.2 else stored_value_inr
            else:
                value_inr = candidate_value

            daily_pl = (today_nav - yesterday_nav) * units
        else:
            # fallback: no daily P&L
            value_inr = stored_value_inr
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
            return 22.50
        return float(hist["Close"].iloc[-1])
    except Exception:
        return 22.50


def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹{lacs:,.2f} L"

# ---------- PRICE FETCHING (REGULAR CLOSE) ----------

@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({item["Ticker"] for item in portfolio_config})
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
    """Get last intraday price per ticker using 1m/5m data, **only if** data is from today (US date).

    This ensures pre-market moves are captured, but we don't accidentally reuse
    yesterday's last tick before the first trade of the new session.
    """
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    last_prices: dict[str, float] = {}

    us_tz = ZoneInfo("America/New_York")
    today_us = datetime.now(us_tz).date()

    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="1d", interval="1m")
            if hist is None or hist.empty:
                hist = tkr.history(period="1d", interval="5m")
            if hist is None or hist.empty or "Close" not in hist.columns:
                continue

            last_idx = hist.index[-1]
            # yfinance usually returns a tz-aware index in US/Eastern
            try:
                last_dt = last_idx.tz_convert(us_tz)
            except Exception:
                # Fallback: assume US timezone if tz info is missing
                last_dt = last_idx.replace(tzinfo=us_tz)

            # Skip if the latest bar is not from "today" in US time
            if last_dt.date() != today_us:
                continue

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
    open_time = time(9, 30)
    close_time = time(16, 0)

    base_close = load_prices_close()

    # Weekend: always treated as closed, use last available close
    if weekday >= 5:
        return "Market Closed", base_close

    # Try to get intraday prices **only for today's US date**
    intraday = load_prices_intraday()

    # Decide phase label based on clock + whether we have any intraday ticks
    if t < open_time:
        phase = "Pre-Market Data" if intraday is not None and not intraday.empty else "Market Closed"
    elif t >= close_time:
        phase = "Post-Market Data"
    else:
        phase = "Live Market Data"

    # Prefer intraday when we have it; otherwise fall back to last close
    if intraday is None or intraday.empty:
        return phase, base_close

    return phase, intraday

# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None) -> pd.DataFrame:
    """Row per config line with P&L and weights."""
    rows = []
    has_close = prices_close is not None and not prices_close.empty

    if has_close and len(prices_close) >= 1:
        last_close = prices_close.iloc[-1]
        prev_close = prices_close.iloc[-2] if len(prices_close) >= 2 else prices_close.iloc[-1]
    else:
        last_close = pd.Series(dtype=float)
        prev_close = pd.Series(dtype=float)

    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        base_price = float(last_close.get(t, 0.0)) if has_close else 0.0
        live_price = float(prices_intraday.get(t, base_price)) if prices_intraday is not None else base_price

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

            prev_usd = float(prev_close.get(t, price_usd)) if has_close else price_usd
            day_pct = (price_usd / prev_usd - 1.0) * 100.0 if prev_usd > 0 else 0.0
            # Artificial reset pre-market
            from __main__ import market_status
            if market_status == "Pre-Market Data":
                day_pct = 0.0
            day_pl_aed = value_aed * (day_pct / 100.0)
            # Artificial reset pre-market
            if market_status == "Pre-Market Data":
                day_pl_aed = 0.0

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

# ---------- UI HELPERS ----------

def render_kpi(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value-main">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- DATA PIPELINE ----------

market_status, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()

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
  <div class="page-subtitle">{market_status}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- TABS ----------

overview_tab, sv_tab, us_tab, mf_tab = st.tabs([
    "🪙 Overview",
    "💷 SV Stocks",
    "🏦 US Stocks",
    "📜 India MF",
])

# ---------- HOME TAB (existing KPI + heatmap) ----------

with overview_tab:
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_kpi("Total Profit (INR)", total_pl_inr_lacs)

    with c2:
        render_kpi("Today's P&L (INR)", day_pl_inr_lacs)

    with c3:
        render_kpi("Portfolio Size (INR)", total_val_inr_lacs)

    with c4:
        render_kpi("Overall Return (%)", overall_pct_str)

    st.markdown(
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data. Showing static valuation only; heat map disabled.")
    else:
        hm = agg_for_heatmap.copy()
        # Convert AED values to INR for sizing
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR
        hm["ValueINR"] = hm["ValueAED"] * AED_TO_INR

        # Add aggregate Indian MF block as a single tile
        mf_agg = compute_india_mf_aggregate()
        ind_mf_val_inr = float(mf_agg.get("total_value_inr", 0.0) or 0.0)

        if ind_mf_val_inr > 0:
            ind_mf_row = {
                "Name": "Indian MF",
                "Ticker": "INDMF",
                "Owner": "MF",
                "Sector": "India MF",
                "Units": 0.0,
                "PriceUSD": 0.0,
                "ValueAED": ind_mf_val_inr / AED_TO_INR,
                "PurchaseAED": 0.0,
                "DayPct": 0.0,
                "DayPLAED": 0.0,
                "TotalPct": 0.0,
                "TotalPLAED": 0.0,
                "WeightPct": 0.0,
                "DayPLINR": 0.0,
                "ValueINR": ind_mf_val_inr,
            }

            hm = pd.concat([hm, pd.DataFrame([ind_mf_row])], ignore_index=True)

        # Size tiles by total INR value, color by daily P&L where available
        hm["SizeForHeatmap"] = hm["ValueINR"].abs() + 1e-6
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
        # Recompute SV-only aggregates in AED
        sv_total_val_aed = sv_positions["ValueAED"].sum()
        sv_total_purchase_aed = sv_positions["PurchaseAED"].sum()
        sv_total_pl_aed = sv_positions["TotalPLAED"].sum()
        sv_day_pl_aed = sv_positions["DayPLAED"].sum()

        sv_total_pl_pct = (sv_total_pl_aed / sv_total_purchase_aed * 100.0) if sv_total_purchase_aed > 0 else 0.0

        sv_total_val_str = f"AED {sv_total_val_aed:,.0f}"
        sv_total_pl_str = f"AED {sv_total_pl_aed:,.0f}"
        sv_day_pl_str = f"AED {sv_day_pl_aed:,.0f}"

        sv_overall_pct_str = f"{sv_total_pl_pct:+.2f}%"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi("SV Total Profit (AED)", sv_total_pl_str)
        with c2:
            render_kpi("SV Today's P&L (AED)", sv_day_pl_str)
        with c3:
            render_kpi("SV Portfolio Size (AED)", sv_total_val_str)
        with c4:
            render_kpi("SV Overall Return (%)", sv_overall_pct_str)

        st.markdown(
            """<div style=\"font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;\">Today's Gains – SV</div>""",
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
        # Fetch latest NAVs from Yahoo for all mapped schemes
        mf_navs = load_mf_navs_from_yahoo()

        mf_rows = []
        for mf_entry in MF_CONFIG:
            scheme = mf_entry["Scheme"]
            units = float(mf_entry["Units"] or 0.0)
            stored_value_inr = float(mf_entry["CurrentValueINR"] or 0.0)
            xirr = mf_entry["XIRR"]

            live_nav = mf_navs.get(scheme)

            # Prefer Yahoo NAV * units, but only if it is consistent with
            # the portfolio file (within ~20% of stored total). Otherwise,
            # fall back to the XLS total to avoid bad ticker mappings.
            if live_nav is not None and live_nav > 0 and units > 0:
                candidate_value = live_nav * units
                if stored_value_inr > 0:
                    ratio = candidate_value / stored_value_inr
                    if 0.8 <= ratio <= 1.2:
                        value_inr = candidate_value
                    else:
                        value_inr = stored_value_inr
                else:
                    value_inr = candidate_value
            else:
                value_inr = stored_value_inr

            mf_rows.append(
                {
                    "scheme": scheme,
                    "value_inr": value_inr,
                    "xirr": xirr,
                }
            )

        # Sort by total value (descending)
        mf_rows.sort(key=lambda r: r["value_inr"], reverse=True)

        for row in mf_rows:
            scheme = row["scheme"]
            value_inr = row["value_inr"]
            xirr = row["xirr"]

            # Shorten scheme name for display: drop trailing numeric codes
            # and the verbose "Fund Growth" suffix.
            display_name = scheme
            parts = display_name.split()
            if parts and all(ch.isdigit() or ch in "/-" for ch in parts[-1]):
                display_name = " ".join(parts[:-1])
            if "Fund Growth" in display_name:
                display_name = display_name.replace(" Fund Growth", "")

            value_str = fmt_inr_lacs(value_inr)
            xirr_str = f"{xirr:.1f}%" if xirr is not None else "N/A"

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
                            <div class="kpi-label" style="margin-bottom:1px;">XIRR</div>
                            <div class="kpi-value-main">{xirr_str}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
