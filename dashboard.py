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
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');

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
    .stTabs {
        margin-top: 0.75rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        align-items: flex-end;
        gap: 0.25rem;
        width: 100%;
        border-bottom: 1px solid var(--border);
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        position: relative;
        flex: 1 1 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.8rem !important;
        padding: 6px 10px 4px 10px !important;
        color: #16233a !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer;
    }

    .stTabs [data-baseweb="tab"]::before {
        content: "";
        position: absolute;
        inset: -4px 4px 0 4px;
        border-radius: 8px 8px 0 0;
        background: #f4f5f8;
        border: 1px solid #d1d5e0;
        border-bottom: none;
        opacity: 0;
        transform: translateY(4px);
        transition: opacity 140ms ease-out, transform 140ms ease-out;
        z-index: -1;
    }

    .stTabs [aria-selected="true"] {
        color: #0f172a !important;
        font-weight: 500 !important;
    }

    .stTabs [aria-selected="true"]::before {
        opacity: 1;
        transform: translateY(0);
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
    """Get last intraday price per ticker using 1m/5m data."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    last_prices = {}
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="1d", interval="1m")
            if hist is None or hist.empty:
                hist = tkr.history(period="1d", interval="5m")
            if hist is None or hist.empty or "Close" not in hist.columns:
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
    intraday = load_prices_intraday()

    # Weekend: always treated as closed
    if weekday >= 5:
        return "Market Closed", base_close

    # Weekday phase label
    if t < open_time:
        phase = "Pre-Market Data"
    elif t >= close_time:
        phase = "Post-Market Data"
    else:
        phase = "Live Market Data"

    # Prefer intraday when available, otherwise fall back to last close
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

home_tab, sv_tab, portfolio_tab, news_tab = st.tabs([
    "⌂ Overview",
    "✦ SV Portfolio",
    "▤ Holdings",
    "✉ News",
])

# ---------- HOME TAB (existing KPI + heatmap) ----------

with home_tab:
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
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#e6eaf0; font-size:0.75rem; margin:4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data. Showing static valuation only; heat map disabled.")
    else:
        hm = agg_for_heatmap.copy()
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR
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
    st.markdown("<div class='kpi-label'>SV Portfolio – detailed view</div>", unsafe_allow_html=True)

    sv_positions = positions[positions["Owner"] == "SV"].copy()

    if sv_positions.empty:
        st.info("No SV positions found.")
    else:
        sv_positions["ValueINR"] = sv_positions["ValueAED"] * AED_TO_INR
        sv_positions["DayPLINR"] = sv_positions["DayPLAED"] * AED_TO_INR
        sv_positions["TotalPLINR"] = sv_positions["TotalPLAED"] * AED_TO_INR

        display_cols = [
            "Name",
            "Ticker",
            "Units",
            "ValueAED",
            "ValueINR",
            "DayPLAED",
            "DayPLINR",
            "TotalPLAED",
            "TotalPLINR",
            "TotalPct",
        ]

        st.dataframe(
            sv_positions[display_cols].round(2),
            use_container_width=True,
        )

# ---------- PLACEHOLDER TABS ----------

with portfolio_tab:
    st.info("Portfolio tab coming next.")

with news_tab:
    st.info("News tab coming next.")
