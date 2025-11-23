import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(
    layout="wide",
    page_title="Stocks Dashboard",
    initial_sidebar_state="collapsed",
)

# ---------- GLOBAL STYLE (Space Grotesk everywhere) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #050b16;
        color: #e5ecff;
    }

    .block-container {
        padding: 1.0rem 1.4rem 2.0rem;
        max-width: 1200px;
    }

    .app-header {
        background: #111827;
        padding: 0.6rem 1.0rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
    }

    .app-header-title {
        font-size: 1.0rem;
        font-weight: 600;
        margin: 0;
    }

    .app-header-sub {
        margin: 2px 0 0 0;
        font-size: 0.78rem;
        color: #9ca3af;
    }

    .kpi-card {
        background: #111827;
        border-radius: 8px;
        padding: 0.7rem 0.9rem 0.85rem;
        border: 1px solid #1f2933;
    }

    .kpi-label {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.2rem;
        font-weight: 600;
    }

    .kpi-sub {
        font-size: 0.8rem;
        margin-top: 0.15rem;
        color: #9ca3af;
    }

    .heatmap-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9ca3af;
        margin: 0.6rem 0 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- CONFIG & STATIC DATA ----------
USD_TO_AED = 3.6725

portfolio_config = [
    {"Name": "Alphabet", "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34128, "Owner": "MV"},
    {"Name": "Apple", "Ticker": "AAPL", "Units": 50, "PurchaseValAED": 37183, "Owner": "MV"},
    {"Name": "Tesla", "Ticker": "TSLA", "Units": 30, "PurchaseValAED": 33116, "Owner": "MV"},
    {"Name": "Nasdaq 100", "Ticker": "QQQM", "Units": 180, "PurchaseValAED": 150894, "Owner": "MV"},
    {"Name": "AMD", "Ticker": "AMD", "Units": 27, "PurchaseValAED": 16075, "Owner": "MV"},
    {"Name": "Broadcom", "Ticker": "AVGO", "Units": 13, "PurchaseValAED": 13578, "Owner": "MV"},
    {"Name": "Nvidia", "Ticker": "NVDA", "Units": 78, "PurchaseValAED": 49707, "Owner": "MV"},
    {"Name": "Amazon", "Ticker": "AMZN", "Units": 59, "PurchaseValAED": 47720, "Owner": "MV"},
    {"Name": "MSFT", "Ticker": "MSFT", "Units": 26, "PurchaseValAED": 49949, "Owner": "MV"},
    {"Name": "Meta", "Ticker": "META", "Units": 18, "PurchaseValAED": 48744, "Owner": "MV"},
    # SV holdings (we aggregate them to one SV Portfolio tile)
    {"Name": "Broadcom [SV]", "Ticker": "AVGO", "Units": 2, "PurchaseValAED": 2122, "Owner": "SV"},
    {"Name": "Apple [SV]", "Ticker": "AAPL", "Units": 2, "PurchaseValAED": 1486, "Owner": "SV"},
    {"Name": "Nasdaq [SV]", "Ticker": "QQQ", "Units": 1, "PurchaseValAED": 2095, "Owner": "SV"},
    {"Name": "Nvidia [SV]", "Ticker": "NVDA", "Units": 2, "PurchaseValAED": 1286, "Owner": "SV"},
    {"Name": "Amazon [SV]", "Ticker": "AMZN", "Units": 4, "PurchaseValAED": 3179, "Owner": "SV"},
    {"Name": "Novo [SV]", "Ticker": "NVO", "Units": 4, "PurchaseValAED": 714, "Owner": "SV"},
    {"Name": "Nasdaq 100 [SV]", "Ticker": "QQQM", "Units": 10, "PurchaseValAED": 8989, "Owner": "SV"},
    {"Name": "MSFT [SV]", "Ticker": "MSFT", "Units": 4, "PurchaseValAED": 7476, "Owner": "SV"},
]


def infer_market_status(now_utc: datetime) -> str:
    # Rough NYSE timing in UTC; this is “good enough” for the label
    open_hour = 14  # ~9:30 ET
    close_hour = 21

    if now_utc.weekday() >= 5:
        return "US market closed (weekend) – showing last available close"
    if now_utc.hour < open_hour:
        return "US pre-market – using last close / pre-market quotes where available"
    if now_utc.hour >= close_hour:
        return "US post-market – using last close / post-market quotes where available"
    return "US market live – intraday prices"


@st.cache_data(ttl=300)
def fetch_fx_aed_inr() -> float:
    """AED → INR from Yahoo. Fallback to 22.5 if it fails."""
    try:
        pair = yf.Ticker("AEDINR=X")
        hist = pair.history(period="5d", interval="1d")
        if hist.empty:
            return 22.5
        return float(hist["Close"].iloc[-1])
    except Exception:
        return 22.5


@st.cache_data(ttl=300)
def fetch_prices(tickers):
    data = yf.download(
        tickers=" ".join(tickers),
        period="5d",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    return data


def build_positions_from_prices(prices_by_ticker, fx_aed_inr: float) -> pd.DataFrame:
    rows = []
    for pos in portfolio_config:
        t = pos["Ticker"]
        units = pos["Units"]
        purchase_aed = pos["PurchaseValAED"]

        hist = prices_by_ticker.get(t)
        if hist is None or hist.empty:
            last_usd = prev_usd = 0.0
        else:
            last_usd = float(hist["Close"].iloc[-1])
            prev_usd = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last_usd

        last_aed = last_usd * USD_TO_AED
        prev_aed = prev_usd * USD_TO_AED

        value_aed = last_aed * units
        prev_value_aed = prev_aed * units

        total_pl_aed = value_aed - purchase_aed
        total_pl_pct = (total_pl_aed / purchase_aed * 100) if purchase_aed > 0 else 0.0

        day_pl_aed = value_aed - prev_value_aed
        day_pl_pct = (day_pl_aed / prev_value_aed * 100) if prev_value_aed > 0 else 0.0

        rows.append(
            {
                "Display": "SV Portfolio" if pos["Owner"] == "SV" else pos["Name"],
                "Owner": pos["Owner"],
                "Ticker": t,
                "Units": units,
                "PurchaseAED": purchase_aed,
                "ValueAED": value_aed,
                "PrevValueAED": prev_value_aed,
                "TotalPLAED": total_pl_aed,
                "TotalPLPct": total_pl_pct,
                "DayPLAED": day_pl_aed,
                "DayPLPct": day_pl_pct,
            }
        )

    df = pd.DataFrame(rows)

    # Collapse all SV lines into a single SV Portfolio row
    sv_mask = df["Owner"] == "SV"
    if sv_mask.any():
        sv_purchase = df.loc[sv_mask, "PurchaseAED"].sum()
        sv_row = {
            "Display": "SV Portfolio",
            "Owner": "SV",
            "Ticker": "SV",
            "Units": df.loc[sv_mask, "Units"].sum(),
            "PurchaseAED": sv_purchase,
            "ValueAED": df.loc[sv_mask, "ValueAED"].sum(),
            "PrevValueAED": df.loc[sv_mask, "PrevValueAED"].sum(),
            "TotalPLAED": df.loc[sv_mask, "TotalPLAED"].sum(),
            "TotalPLPct": (df.loc[sv_mask, "TotalPLAED"].sum() / sv_purchase * 100) if sv_purchase > 0 else 0.0,
            "DayPLAED": df.loc[sv_mask, "DayPLAED"].sum(),
            "DayPLPct": 0.0,
        }
        df = pd.concat([df.loc[~sv_mask], pd.DataFrame([sv_row])], ignore_index=True)

    # Convert to INR
    df["ValueINR"] = df["ValueAED"] * fx_aed_inr
    df["TotalPLINR"] = df["TotalPLAED"] * fx_aed_inr
    df["DayPLINR"] = df["DayPLAED"] * fx_aed_inr

    return df


def fmt_inr_lacs(v: float) -> str:
    return f"₹{v/100000:.2f} L"


def fmt_k(v: float) -> str:
    """₹XXk with brackets for negatives."""
    v_k = abs(v) / 1000.0
    txt = f"₹{v_k:.0f}k"
    return f"[{txt}]" if v < 0 else txt


# ---------- DATA PIPELINE ----------
tickers = sorted({p["Ticker"] for p in portfolio_config})
now_utc = datetime.utcnow()
market_status = infer_market_status(now_utc)

fx_aed_inr = fetch_fx_aed_inr()
raw_prices = fetch_prices(tickers)

prices_by_ticker = {}
for t in tickers:
    try:
        df_t = raw_prices[t]
        if isinstance(df_t, pd.Series) or df_t.empty:
            continue
        prices_by_ticker[t] = df_t
    except Exception:
        continue

positions = build_positions_from_prices(prices_by_ticker, fx_aed_inr)

portfolio_value_inr = positions["ValueINR"].sum()
portfolio_purchase_inr = positions["PurchaseAED"].sum() * fx_aed_inr
total_profit_inr = positions["TotalPLINR"].sum()
overall_return_pct = (total_profit_inr / portfolio_purchase_inr * 100) if portfolio_purchase_inr > 0 else 0.0
day_pl_inr = positions["DayPLINR"].sum()

# ---------- HEADER ----------
st.markdown(
    f"""
    <div class="app-header">
        <div class="app-header-title">Stocks Dashboard</div>
        <div class="app-header-sub">{market_status}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- KPI ROW ----------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Profit (INR)</div>
            <div class="kpi-value">{fmt_inr_lacs(total_profit_inr)}</div>
            <div class="kpi-sub">Absolute profit / loss</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Today's P&amp;L (INR)</div>
            <div class="kpi-value">{fmt_inr_lacs(day_pl_inr)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Portfolio Size (INR)</div>
            <div class="kpi-value">{fmt_inr_lacs(portfolio_value_inr)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Overall Return (%)</div>
            <div class="kpi-value">{overall_return_pct:+.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- HEATMAP ----------
st.markdown('<div class="heatmap-title">Heat Map – Today</div>', unsafe_allow_html=True)

hm = positions[["Display", "DayPLINR"]].copy()
hm = hm.groupby("Display", as_index=False).sum()
hm["ValueLabel"] = hm["DayPLINR"].apply(fmt_k)

fig = px.treemap(
    hm,
    path=["Display"],
    values="DayPLINR",
    color="DayPLINR",
    color_continuous_scale=["#f97373", "#374151", "#4ade80"],
)

# Text = Name + ₹XXk / [₹XXk]
fig.update_traces(
    texttemplate="%{label}<br>%{customdata}",
    customdata=hm["ValueLabel"],
    marker=dict(line=dict(width=2, color="#111827")),
)

# Kill grey outer box + colour bar + modebar
fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    coloraxis_showscale=False,
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
