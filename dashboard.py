import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Family Wealth Cockpit",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- THEME / CSS ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

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
        font-family: 'Inter', sans-serif;
        background: var(--bg);
        color: var(--text);
    }

    header {visibility: hidden;}

    .block-container {
        padding: 1.2rem 1.0rem 2rem;
        max-width: 900px;   /* tighter, more mobile-like */
    }

    .card, .kpi-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: none;
    }

    .page-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0 0 2px 0;
        color: var(--text);
    }

    .page-subtitle {
        margin: 0 0 8px 0;
        color: var(--muted);
        font-size: 0.9rem;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: #111b2c;
        font-size: 0.78rem;
        color: var(--muted);
    }

    .kpi-row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 10px;
    }

    @media (min-width: 900px) {
        .kpi-row {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }
    }

    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        margin-bottom: 4px;
    }

    .kpi-value-main {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text);
    }

    .kpi-sub {
        font-size: 0.8rem;
        color: var(--muted);
        margin-top: 2px;
    }

    .section-title {
        margin: 14px 0 6px 0;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text);
    }

    .dataframe tbody tr:nth-child(odd) {
        background: rgba(255,255,255,0.02) !important;
    }
    .dataframe tbody tr:hover {
        background: rgba(74,163,255,0.10) !important;
    }
    .dataframe th {
        color: var(--text) !important;
        background: var(--card) !important;
    }
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS ----------
USD_TO_AED = 3.6725
AED_TO_INR = 23.0

COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f"
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# ---------- PORTFOLIO CONFIG ----------
portfolio_config = [
    {"Name": "Alphabet",          "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34128, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Apple",             "Ticker": "AAPL",  "Units": 50, "PurchaseValAED": 37183, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla",             "Ticker": "TSLA",  "Units": 30, "PurchaseValAED": 33116, "Owner": "MV", "Sector": "Auto"},
    {"Name": "Nasdaq 100",        "Ticker": "QQQM",  "Units": 180,"PurchaseValAED": 150894,"Owner": "MV", "Sector": "ETF"},
    {"Name": "AMD",               "Ticker": "AMD",   "Units": 27, "PurchaseValAED": 16075, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom",          "Ticker": "AVGO",  "Units": 13, "PurchaseValAED": 13578, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Nvidia",            "Ticker": "NVDA",  "Units": 78, "PurchaseValAED": 49707, "Owner": "MV", "Sector": "Semi"},
    {"Name": "Amazon",            "Ticker": "AMZN",  "Units": 59, "PurchaseValAED": 47720, "Owner": "MV", "Sector": "Retail"},
    {"Name": "MSFT",              "Ticker": "MSFT",  "Units": 26, "PurchaseValAED": 49949, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Meta",              "Ticker": "META",  "Units": 18, "PurchaseValAED": 48744, "Owner": "MV", "Sector": "Tech"},
    {"Name": "Broadcom [SV]",     "Ticker": "AVGO",  "Units": 2,  "PurchaseValAED": 2122,  "Owner": "SV", "Sector": "Semi"},
    {"Name": "Apple [SV]",        "Ticker": "AAPL",  "Units": 2,  "PurchaseValAED": 1486,  "Owner": "SV", "Sector": "Tech"},
    {"Name": "Nasdaq [SV]",       "Ticker": "QQQ",   "Units": 1,  "PurchaseValAED": 2095,  "Owner": "SV", "Sector": "ETF"},
    {"Name": "Nvidia [SV]",       "Ticker": "NVDA",  "Units": 2,  "PurchaseValAED": 1286,  "Owner": "SV", "Sector": "Semi"},
    {"Name": "Amazon [SV]",       "Ticker": "AMZN",  "Units": 4,  "PurchaseValAED": 3179,  "Owner": "SV", "Sector": "Retail"},
    {"Name": "Novo [SV]",         "Ticker": "NVO",   "Units": 4,  "PurchaseValAED": 714,   "Owner": "SV", "Sector": "Health"},
    {"Name": "Nasdaq 100 [SV]",   "Ticker": "QQQM",  "Units": 10, "PurchaseValAED": 8989,  "Owner": "SV", "Sector": "ETF"},
    {"Name": "MSFT [SV]",         "Ticker": "MSFT",  "Units": 4,  "PurchaseValAED": 7476,  "Owner": "SV", "Sector": "Tech"},
]

# ---------- HELPERS ----------
def fmt_inr_lacs_from_aed(aed_value: float) -> str:
    inr = aed_value * AED_TO_INR
    lacs = inr / 100000.0
    return f"₹ {lacs:,.2f} L"

@st.cache_data(ttl=300)
def load_prices() -> pd.DataFrame:
    """Fetch last few daily closes for all tickers, batched."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    # 5 days of daily closes is enough for yesterday vs today
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
        if "Adj Close" in data.columns.levels[0]:
            close = data["Adj Close"].copy()
        else:
            # fallback to first level
            close = data.xs("Close", axis=1, level=1, drop_level=False)
    else:
        close = data.copy()

    close = close.dropna(how="all")
    return close

def build_positions_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Return a row per portfolio_config line with P&L and weights."""
    if prices is None or prices.empty or len(prices) < 2:
        # no reliable history; fallback to static valuation
        rows = []
        for item in portfolio_config:
            purchase = float(item["PurchaseValAED"])
            rows.append(
                {
                    "Name": item["Name"],
                    "Ticker": item["Ticker"],
                    "Owner": item["Owner"],
                    "Sector": item["Sector"],
                    "Units": float(item["Units"]),
                    "PriceUSD": 0.0,
                    "ValueAED": purchase,
                    "PurchaseAED": purchase,
                    "DayPct": 0.0,
                    "DayPLAED": 0.0,
                    "TotalPct": 0.0,
                    "TotalPLAED": 0.0,
                }
            )
        df = pd.DataFrame(rows)
        total_val = df["ValueAED"].sum()
        df["WeightPct"] = df["ValueAED"] / total_val * 100 if total_val > 0 else 0
        return df

    last = prices.iloc[-1]
    prev = prices.iloc[-2]

    rows = []
    for item in portfolio_config:
        t = item["Ticker"]
        if t not in prices.columns:
            continue

        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])
        last_usd = float(last[t])
        prev_usd = float(prev[t]) if prev[t] > 0 else last_usd

        price_aed = last_usd * USD_TO_AED
        value_aed = price_aed * units

        day_pct = (last_usd / prev_usd - 1.0) * 100.0 if prev_usd != 0 else 0.0
        day_pl_aed = value_aed * (day_pct / 100.0)

        total_pl_aed = value_aed - purchase
        total_pct = (total_pl_aed / purchase) * 100.0 if purchase != 0 else 0.0

        rows.append(
            {
                "Name": item["Name"],
                "Ticker": t,
                "Owner": item["Owner"],
                "Sector": item["Sector"],
                "Units": units,
                "PriceUSD": last_usd,
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
    """Merge all SV positions into one 'SV Portfolio' tile."""
    if df.empty:
        return df

    mv = df[df["Owner"] == "MV"].copy()

    # Aggregate SV as one bucket
    sv = df[df["Owner"] == "SV"].copy()
    if not sv.empty:
        sv_row = {
            "Name": "SV Portfolio",
            "Ticker": "SVPF",
            "Owner": "SV",
            "Sector": "Mixed",
            "Units": sv["Units"].sum(),
            "PriceUSD": 0.0,  # not meaningful as a basket
            "ValueAED": sv["ValueAED"].sum(),
            "PurchaseAED": sv["PurchaseAED"].sum(),
            "DayPct": (
                sv["DayPLAED"].sum() / sv["ValueAED"].sum() * 100.0
                if sv["ValueAED"].sum() > 0 else 0.0
            ),
            "DayPLAED": sv["DayPLAED"].sum(),
            "TotalPct": (
                sv["TotalPLAED"].sum() / sv["PurchaseAED"].sum() * 100.0
                if sv["PurchaseAED"].sum() > 0 else 0.0
            ),
            "TotalPLAED": sv["TotalPLAED"].sum(),
        }
        mv = pd.concat([mv, pd.DataFrame([sv_row])], ignore_index=True)

    total_val = mv["ValueAED"].sum()
    mv["WeightPct"] = mv["ValueAED"] / total_val * 100.0 if total_val > 0 else 0.0
    return mv

def detect_mode_label() -> str:
    """Very simple time-based label for now."""
    # US Eastern trading hours approx vs UTC
    # Pre-market: 09:00–13:30 UTC, Regular: 13:30–20:00, Post: 20:00–01:00
    now_utc = datetime.utcnow()
    hour = now_utc.hour + now_utc.minute / 60

    if 9 <= hour < 13.5:
        return "Pre-Market Snapshot"
    elif 13.5 <= hour < 20:
        return "Live Market Snapshot"
    else:
        return "After-Hours Snapshot"

# ---------- LOAD DATA ----------
prices = load_prices()
positions = build_positions_from_prices(prices)
heatmap_df = aggregate_for_heatmap(positions)

if positions.empty:
    st.error("Unable to build portfolio view from configuration.")
    st.stop()

# ---------- METRICS ----------
total_value_aed = positions["ValueAED"].sum()
total_purchase_aed = positions["PurchaseAED"].sum()
total_pl_aed = positions["TotalPLAED"].sum()
day_pl_aed = positions["DayPLAED"].sum()

total_pl_pct = (total_pl_aed / total_purchase_aed * 100.0) if total_purchase_aed > 0 else 0.0
day_pl_inr = day_pl_aed * AED_TO_INR
total_pl_inr = total_pl_aed * AED_TO_INR
total_value_inr = total_value_aed * AED_TO_INR

# ---------- LAYOUT: SINGLE MOBILE-FIRST SCREEN ----------
mode_label = detect_mode_label()

with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='page-title'>Family Wealth Cockpit</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='page-subtitle'>Personal market view across MV + SV holdings.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span class='status-pill'>{mode_label}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# KPI grid (Level 1 + Level 2)
st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)

# 1. Total profit in INR lacs
st.markdown(
    f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Total Profit</div>
        <div class='kpi-value-main'>{fmt_inr_lacs_from_aed(total_pl_aed)}</div>
        <div class='kpi-sub'>Across entire portfolio</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 2. Total profit %
st.markdown(
    f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Total Profit %</div>
        <div class='kpi-value-main'>{total_pl_pct:+.2f}%</div>
        <div class='kpi-sub'>Vs total invested</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 3. Today's P&L in INR lacs
st.markdown(
    f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Today P&L</div>
        <div class='kpi-value-main'>{fmt_inr_lacs_from_aed(day_pl_aed)}</div>
        <div class='kpi-sub'>Vs previous close</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4. Total portfolio value in INR lacs
st.markdown(
    f"""
    <div class='kpi-card'>
        <div class='kpi-label'>Portfolio Value</div>
        <div class='kpi-value-main'>{fmt_inr_lacs_from_aed(total_value_aed)}</div>
        <div class='kpi-sub'>Current snapshot</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)  # end kpi-row

# ---------- HEAT MAP SECTION ----------
st.markdown("<div class='section-title'>Today’s Heat Map</div>", unsafe_allow_html=True)

if heatmap_df.empty:
    st.info("No positions available for heat map.")
else:
    # For mobile, keep text minimal but clear
    fig = px.treemap(
        heatmap_df,
        path=["Owner", "Name"],    # MV tickers + SV Portfolio under their owners
        values="ValueAED",
        color="DayPct",
        color_continuous_scale=["#f27d72", "#16233a", "#6bcf8f"],  # red -> neutral -> green
        color_continuous_midpoint=0,
        hover_data={
            "DayPct": ":.2f",
            "TotalPct": ":.2f",
            "ValueAED": ":.0f",
        },
    )
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        height=420,
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        font=dict(family="Inter", size=11, color="#e6eaf0"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- OPTIONAL: SIMPLE MOVERS LIST ----------
st.markdown("<div class='section-title'>Top Movers Today</div>", unsafe_allow_html=True)

# Use aggregated view for clarity (MV tickers + SV Portfolio)
movers = heatmap_df.sort_values("DayPct", ascending=False)
top_gainers = movers.head(3)
top_losers = movers.tail(3).sort_values("DayPct")

col_g, col_l = st.columns(2)

with col_g:
    st.caption("Gainers")
    for _, row in top_gainers.iterrows():
        if row["DayPct"] > 0:
            st.markdown(
                f"**{row['Name']}**  \n"
                f"<span style='color:{COLOR_SUCCESS}; font-size:0.85rem;'>+{row['DayPct']:.2f}% today</span>",
                unsafe_allow_html=True,
            )

with col_l:
    st.caption("Losers")
    for _, row in top_losers.iterrows():
        if row["DayPct"] < 0:
            st.markdown(
                f"**{row['Name']}**  \n"
                f"<span style='color:{COLOR_DANGER}; font-size:0.85rem;'>{row['DayPct']:.2f}% today</span>",
                unsafe_allow_html=True,
            )
