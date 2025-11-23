import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

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
        max-width: 900px;
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
        margin: 18px 0 6px 0;
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS ----------
USD_TO_AED = 3.6725  # this is essentially fixed (USD peg)

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

# ---------- FX HELPERS ----------

@st.cache_data(ttl=3600)
def get_aed_inr_rate_from_yahoo() -> float:
    """Fetch AED→INR from Yahoo FX ticker AEDINR=X, fallback to manual if needed."""
    try:
        tkr = yf.Ticker("AEDINR=X")
        hist = tkr.history(period="5d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return 22.50  # fallback manual rate
        return float(hist["Close"].iloc[-1])
    except Exception:
        return 22.50


def fmt_inr_lacs_from_aed(aed_value: float, aed_to_inr: float) -> str:
    inr = aed_value * aed_to_inr
    lacs = inr / 100000.0
    return f"₹ {lacs:,.2f} L"

# ---------- PRICE FETCHING ----------

@st.cache_data(ttl=300)
def load_prices() -> pd.DataFrame:
    """Fetch last few daily closes for all tickers, return DataFrame [date x ticker]."""
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

    # Multiple-ticker MultiIndex: (Ticker, Field)
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
        # Single-ticker case
        if "Adj Close" in data.columns:
            close = data[["Adj Close"]]
        elif "Close" in data.columns:
            close = data[["Close"]]
        else:
            return pd.DataFrame()
        close.columns = [tickers[0]]

    close = close.dropna(how="all")
    return close

# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Row per config line with P&L and weights.
    Missing / odd data ⇒ treat daily move as 0."""
    if prices is None or prices.empty or len(prices) < 1:
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

    use_day_change = len(prices) >= 2
    last = prices.iloc[-1]
    prev = prices.iloc[-2] if use_day_change else prices.iloc[-1]

    rows = []
    for item in portfolio_config:
        t = item["Ticker"]
        if t not in prices.columns:
            continue

        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        try:
            last_usd = float(last[t])
        except Exception:
            last_usd = 0.0

        try:
            prev_usd = float(prev[t])
        except Exception:
            prev_usd = last_usd

        if last_usd <= 0:
            value_aed = purchase
            day_pct = 0.0
            day_pl_aed = 0.0
            total_pl_aed = 0.0
            total_pct = 0.0
            price_usd = 0.0
        else:
            price_usd = last_usd
            price_aed = price_usd * USD_TO_AED
            value_aed = price_aed * units

            if use_day_change and prev_usd > 0:
                day_pct = (price_usd / prev_usd - 1.0) * 100.0
            else:
                day_pct = 0.0  # your rule: treat missing as 0 move
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
    """Merge all SV positions into one 'SV Portfolio' row."""
    if df.empty:
        return df

    mv = df[df["Owner"] == "MV"].copy()
    sv = df[df["Owner"] == "SV"].copy()

    if sv.empty:
        return df

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

    return pd.concat([mv, sv_row], ignore_index=True)

# ---------- UI / MAIN ----------

# Sidebar: FX settings
st.sidebar.markdown("### Settings")
base_fx = get_aed_inr_rate_from_yahoo()
AED_TO_INR = st.sidebar.number_input(
    "AED → INR (from Yahoo, editable)",
    value=float(round(base_fx, 2)),
    step=0.05,
    format="%.2f",
)

# Load prices & build portfolio
prices = load_prices()
positions = build_positions_from_prices(prices)
agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions

# Top metrics
total_val_aed = positions["ValueAED"].sum()
total_purchase_aed = positions["PurchaseAED"].sum()
total_pl_aed = positions["TotalPLAED"].sum()
day_pl_aed = positions["DayPLAED"].sum()

total_pl_pct = (total_pl_aed / total_purchase_aed * 100.0) if total_purchase_aed > 0 else 0.0

total_val_inr_lacs = fmt_inr_lacs_from_aed(total_val_aed, AED_TO_INR)
total_pl_inr_lacs = fmt_inr_lacs_from_aed(total_pl_aed, AED_TO_INR)
day_pl_inr_lacs = fmt_inr_lacs_from_aed(day_pl_aed, AED_TO_INR)

# Last data timestamp
if prices is not None and not prices.empty:
    last_ts = prices.index[-1]
    last_str = last_ts.strftime("%d %b %Y")
else:
    last_str = "N/A"

# ---------- HERO CARD ----------
st.markdown(
    f"""
<div class="card">
  <div class="page-title">Family Wealth Cockpit</div>
  <div class="page-subtitle">Clean mobile-first view of capital, momentum, and daily moves.</div>
  <div class="status-pill">
    <span>Last price: {last_str}</span>
  </div>

  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">Total Profit (INR)</div>
      <div class="kpi-value-main">{total_pl_inr_lacs}</div>
      <div class="kpi-sub">{total_pl_pct:+.2f}% overall</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-label">Today's P&L (INR)</div>
      <div class="kpi-value-main">{day_pl_inr_lacs}</div>
      <div class="kpi-sub">vs. previous close (0% if data missing)</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-label">Portfolio Size (INR)</div>
      <div class="kpi-value-main">{total_val_inr_lacs}</div>
      <div class="kpi-sub">Live mark-to-market</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-label">Holdings</div>
      <div class="kpi-value-main">{positions['Ticker'].nunique()}</div>
      <div class="kpi-sub">MV + SV (SV aggregated in heatmap)</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- HEATMAP ----------
st.markdown('<div class="section-title">Heat Map – Today</div>', unsafe_allow_html=True)

if agg_for_heatmap is None or agg_for_heatmap.empty:
    st.info("No live price data. Showing static valuation only; heat map disabled.")
else:
    fig = px.treemap(
        agg_for_heatmap,
        path=["Owner", "Name"],
        values="ValueAED",
        color="DayPct",
        color_continuous_scale=[COLOR_DANGER, "#16233a", COLOR_SUCCESS],
        color_continuous_midpoint=0,
        hover_data={
            "Ticker": True,
            "DayPct": ":.2f",
            "TotalPct": ":.2f",
            "ValueAED": ":.0f",
        },
    )
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor=COLOR_BG,
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- POSITIONS TABLE (compact) ----------
st.markdown('<div class="section-title">Positions (detail)</div>', unsafe_allow_html=True)

show_cols = [
    "Name",
    "Ticker",
    "Owner",
    "Sector",
    "Units",
    "PriceUSD",
    "ValueAED",
    "DayPct",
    "TotalPct",
]

if positions.empty:
    st.info("No positions to show.")
else:
    table = positions[show_cols].copy()
    table["ValueAED"] = table["ValueAED"].round(0)
    table["PriceUSD"] = table["PriceUSD"].round(2)
    table["DayPct"] = table["DayPct"].round(2)
    table["TotalPct"] = table["TotalPct"].round(2)

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
    )
