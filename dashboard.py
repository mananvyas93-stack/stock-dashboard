import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 0. PAGE CONFIGURATION & THEME SETUP ---
st.set_page_config(
    layout="wide",
    page_title="Family Wealth Cockpit",
    initial_sidebar_state="collapsed",
)

# --- CUSTOM CSS SYSTEM ---
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
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: var(--bg);
        color: var(--text);
    }

    header {visibility: hidden;}

    .block-container {
        padding: 1.2rem 1.6rem 2rem;
        max-width: 1450px;
    }

    .panel, .card-container, .kpi-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 14px 16px;
        box-shadow: none;
    }

    .page-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 4px 0;
        color: var(--text);
    }

    .page-subtitle {
        margin: 0 0 10px 0;
        color: var(--muted);
        font-size: 0.95rem;
    }

    .meta-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        color: var(--muted);
        font-size: 0.85rem;
    }

    .meta-pill {
        padding: 6px 10px;
        border: 1px solid var(--border);
        border-radius: 4px;
        background: #111b2c;
    }

    .kpi-card {
        padding: 14px;
    }

    .kpi-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 6px;
    }

    .kpi-delta {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid var(--border);
        background: #13243c;
        font-size: 0.85rem;
    }

    .section-title {
        margin: 0 0 8px 0;
        font-weight: 700;
        color: var(--text);
    }

    .muted {
        color: var(--muted);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background: transparent;
        color: var(--muted);
        font-weight: 600;
        border-radius: 0;
        border: none;
        padding: 8px 6px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--text);
        box-shadow: inset 0 -2px 0 var(--accent);
    }

    .card-container {
        margin-bottom: 14px;
    }

    .dataframe tbody tr:nth-child(odd) {
        background: rgba(255,255,255,0.02) !important;
    }

    .dataframe tbody tr:hover {
        background: rgba(74,163,255,0.08) !important;
    }

    .dataframe th {
        color: var(--text) !important;
    }

    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""",
    unsafe_allow_html=True,
)

# --- 1. DATA ENGINE ---

USD_TO_AED = 3.6725
AED_TO_INR = 23.0

COLOR_PRIMARY = "#4aa3ff"
COLOR_ACCENT_SOFT = "#7fc3ff"
COLOR_PROFIT = "#6bcf8f"
COLOR_LOSS = "#f27d72"
COLOR_NEUTRAL = "#9ba7b8"
COLOR_BG = "#0f1a2b"


def fmt_aed(val: float) -> str:
    return f"Dh {val:,.0f}"


def fmt_delta(val: float) -> str:
    prefix = "+" if val >= 0 else ""
    return f"{prefix}{val:.2f}%"


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


@st.cache_data(ttl=300)
def load_history(days: int = 10) -> pd.DataFrame:
    """Lightweight loader: last ~10 days of prices, per ticker."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    data_dict = {}

    for t in tickers:
        try:
            d = yf.download(
                t,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if d is None or d.empty:
                continue

            if isinstance(d, pd.DataFrame):
                if "Adj Close" in d.columns:
                    s = d["Adj Close"]
                elif "Close" in d.columns:
                    s = d["Close"]
                else:
                    continue
            else:
                s = d

            data_dict[t] = s
        except Exception:
            continue

    if not data_dict:
        return pd.DataFrame()

    prices = pd.DataFrame(data_dict).dropna(how="all")
    return prices


def build_positions(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame()

    last = prices.iloc[-1]
    prev = prices.iloc[-2] if len(prices) > 1 else prices.iloc[-1]

    rows = []
    for item in portfolio_config:
        ticker = item["Ticker"]
        units = float(item["Units"])
        purchase_aed = float(item["PurchaseValAED"])

        if ticker not in prices.columns:
            continue

        last_usd = float(last[ticker])
        prev_usd = float(prev[ticker]) if prev[ticker] > 0 else last_usd

        price_aed = last_usd * USD_TO_AED
        value_aed = price_aed * units

        day_pct = (last_usd / prev_usd - 1.0) * 100.0 if prev_usd != 0 else 0.0
        day_pl_aed = value_aed * (day_pct / 100.0)

        total_pl_aed = value_aed - purchase_aed
        total_pct = (total_pl_aed / purchase_aed) * 100.0 if purchase_aed != 0 else 0.0

        rows.append(
            {
                "Name": item["Name"],
                "Ticker": ticker,
                "Owner": item["Owner"],
                "Sector": item["Sector"],
                "Units": units,
                "Price": last_usd,
                "Price (AED)": price_aed,
                "Value": value_aed,
                "PurchaseCost": purchase_aed,
                "Day %": day_pct,
                "Day P&L": day_pl_aed,
                "Total %": total_pct,
                "Total P&L": total_pl_aed,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    total_val = df["Value"].sum()
    df["Weight"] = df["Value"] / total_val * 100.0
    return df


def compute_portfolio_history(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame()

    hist_val = pd.DataFrame(index=prices.index)
    hist_val["Total"] = 0.0

    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        if t in prices.columns:
            hist_val["Total"] += prices[t] * units * USD_TO_AED

    return hist_val


def minimalist_chart(fig, height: int = 250):
    fig.update_layout(
        template=None,
        margin=dict(t=10, l=0, r=0, b=0),
        height=height,
        font=dict(family="Inter", size=11, color=COLOR_NEUTRAL),
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        xaxis=dict(
            showgrid=True,
            gridcolor="#1f2d44",
            zeroline=False,
            showline=True,
            linecolor="#1f2d44",
            tickfont=dict(color=COLOR_NEUTRAL),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1f2d44",
            zeroline=False,
            showline=True,
            linecolor="#1f2d44",
            tickfont=dict(color=COLOR_NEUTRAL),
        ),
        hovermode="x unified",
        legend=dict(font=dict(color=COLOR_NEUTRAL)),
    )
    return fig


# --- 2. LOAD DATA ---

try:
    hist_data = load_history()
except Exception:
    hist_data = pd.DataFrame()

if hist_data is None or hist_data.empty:
    st.error("Data service unavailable – could not load price history.")
    st.stop()

df = build_positions(hist_data)
if df is None or df.empty:
    st.error("No holdings could be built from portfolio_config.")
    st.stop()

total_val = df["Value"].sum()
hist_val = compute_portfolio_history(hist_data)

# KPIs
total_pl_val = df["Total P&L"].sum()
total_purchase = df["PurchaseCost"].sum()
total_pl_pct = (total_pl_val / total_purchase) * 100.0 if total_purchase != 0 else 0.0
day_pl_val = df["Day P&L"].sum()
day_pl_pct = (day_pl_val / (total_val - day_pl_val)) * 100.0 if (total_val - day_pl_val) != 0 else 0.0
inr_val = (total_val * AED_TO_INR) / 100000.0

last_updated_ts = hist_val.index[-1]
last_updated_str = last_updated_ts.strftime("%d %b %Y, %H:%M") if isinstance(
    last_updated_ts, pd.Timestamp
) else str(last_updated_ts)

top_sector = df.groupby("Sector")["Value"].sum().idxmax()

# --- 3. LAYOUT ---

tab_overview, tab_positions, tab_analytics = st.tabs(
    ["Overview", "Positions", "Analytics & Risk"]
)

# === TAB 1: OVERVIEW ===
with tab_overview:
    # HERO
    with st.container():
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        h1, h2 = st.columns([2.2, 1])
        with h1:
            st.markdown(
                "<div class='page-title'>Family Wealth Cockpit</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='page-subtitle'>Performance, allocation, and risk in a clean midnight palette.</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class='meta-row'>
                    <span class='meta-pill'>Last update: {last_updated_str}</span>
                    <span class='meta-pill'>Top sector: {top_sector}</span>
                    <span class='meta-pill'>Tickers tracked: {len({item["Ticker"] for item in portfolio_config})}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with h2:
            gauge_val = max(-50.0, min(50.0, total_pl_pct))
            st.markdown(
                f"""
                <div style='text-align:right'>
                    <div style='font-size:0.9rem; color:{COLOR_NEUTRAL}; text-transform:uppercase; letter-spacing:0.08em;'>Health</div>
                    <div style='font-size:1.6rem; font-weight:700; color:{COLOR_PRIMARY};'>{total_pl_pct:+.1f}%</div>
                    <div style='height:6px; border-radius:4px; background:#111b2c; overflow:hidden; border:1px solid #1f2d44;'>
                        <div style='width:{gauge_val + 50}%; height:100%; background:{COLOR_PRIMARY};'></div>
                    </div>
                    <div style='margin-top:6px; color:{COLOR_NEUTRAL}; font-size:0.9rem;'>Return since inception</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # KPI cards
    kpis = [
        {"label": "Net Liquidation", "value": fmt_aed(total_val), "delta": None, "accent": COLOR_PRIMARY},
        {
            "label": "Daily P&L",
            "value": fmt_aed(day_pl_val),
            "delta": fmt_delta(day_pl_pct),
            "accent": COLOR_PROFIT if day_pl_val >= 0 else COLOR_LOSS,
        },
        {
            "label": "Total P&L",
            "value": fmt_aed(total_pl_val),
            "delta": fmt_delta(total_pl_pct),
            "accent": COLOR_PROFIT if total_pl_val >= 0 else COLOR_LOSS,
        },
        {
            "label": "Net Worth (INR)",
            "value": f"₹ {inr_val:,.2f} L",
            "delta": None,
            "accent": COLOR_ACCENT_SOFT,
        },
    ]

    c1, c2, c3, c4 = st.columns(4)
    for col, card in zip([c1, c2, c3, c4], kpis):
        with col:
            st.markdown(
                f"""
                <div class='kpi-card' style='border-top: 3px solid {card['accent']};'>
                    <div class='kpi-label'>{card['label']}</div>
                    <div class='kpi-value'>{card['value']}</div>
                    {'' if not card['delta'] else f"<div class='kpi-delta' style='color:{card['accent']}; border-color:{card['accent']}; background:#0f1a2b;'>Δ {card['delta']}</div>"}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Daily brief
    top_gain = df.sort_values("Day %", ascending=False).head(1)
    top_loss = df.sort_values("Day %", ascending=True).head(1)
    gainer_name = top_gain.iloc[0]["Ticker"] if not top_gain.empty else "—"
    loser_name = top_loss.iloc[0]["Ticker"] if not top_loss.empty else "—"
    direction = "up" if day_pl_pct >= 0 else "down"

    st.markdown(
        f"""
        <div class='card-container' style='margin-top:6px;'>
            <div class='section-title' style='font-size:0.9rem; letter-spacing:0.08em; text-transform:uppercase;'>Daily Brief</div>
            <div class='muted'>Portfolio is {direction} <span style='color:{COLOR_PRIMARY}; font-weight:700'>{abs(day_pl_pct):.2f}%</span> today.</div>
            <div class='muted'>Top driver: <span style='color:{COLOR_PROFIT}; font-weight:700'>{gainer_name}</span> · Main detractor: <span style='color:{COLOR_LOSS}; font-weight:700'>{loser_name}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Trend & allocation
    c_trend, c_alloc = st.columns([2.5, 1.5])

    with c_trend:
        with st.container():
            st.markdown("<div class='card-container'>", unsafe_allow_html=True)
            st.markdown("#### Portfolio Value", unsafe_allow_html=True)

            t_range = st.radio("Range", ["3D", "1W", "2W"], horizontal=True, label_visibility="collapsed")
            hist_plot = hist_val.copy()
            if not hist_plot.empty:
                if t_range == "3D":
                    hist_plot = hist_plot.iloc[-3:]
                elif t_range == "1W":
                    hist_plot = hist_plot.iloc[-7:]
                elif t_range == "2W":
                    hist_plot = hist_plot.iloc[-14:]

            fig_trend = px.area(hist_plot, x=hist_plot.index, y="Total")
            fig_trend.update_traces(line_color=COLOR_PRIMARY, fillcolor="rgba(74, 163, 255, 0.18)")
            fig_trend = minimalist_chart(fig_trend, height=280)
            fig_trend.update_xaxes(title=None)
            fig_trend.update_yaxes(title=None, tickprefix="Dh ", showgrid=True)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with c_alloc:
        with st.container():
            st.markdown("<div class='card-container'>", unsafe_allow_html=True)
            st.markdown("#### Allocation", unsafe_allow_html=True)

            owner_agg = df.groupby("Owner")["Value"].sum().reset_index()
            fig_own = px.bar(owner_agg, x="Value", y="Owner", orientation="h", text_auto=".2s")
            fig_own.update_traces(
                marker_color=[COLOR_PRIMARY if x == "MV" else COLOR_ACCENT_SOFT for x in owner_agg["Owner"]]
            )
            fig_own = minimalist_chart(fig_own, height=100)
            fig_own.update_yaxes(title=None)
            fig_own.update_xaxes(showgrid=False, showticklabels=False, title=None)
            st.plotly_chart(fig_own, use_container_width=True, config={"displayModeBar": False})

            st.markdown("---")

            top_h = df.nlargest(5, "Value").sort_values("Value", ascending=True)
            fig_top = px.bar(top_h, x="Value", y="Ticker", orientation="h")
            fig_top.update_traces(marker_color=COLOR_ACCENT_SOFT)
            fig_top.data[0].marker.color = [
                COLOR_PRIMARY if i == len(top_h) - 1 else COLOR_ACCENT_SOFT for i in range(len(top_h))
            ]
            fig_top = minimalist_chart(fig_top, height=140)
            fig_top.update_yaxes(title=None)
            fig_top.update_xaxes(showgrid=False, showticklabels=False, title=None)
            st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

    # Movers & alerts
    c_movers, c_alerts = st.columns([1.5, 1.5])

    with c_movers:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Today's Movers", unsafe_allow_html=True)

        movers = df.sort_values("Day %", ascending=False)
        top_m = movers.head(5)
        bot_m = movers.tail(5).sort_values("Day %", ascending=True)

        col_w, col_l = st.columns(2)
        with col_w:
            st.caption("Gainers")
            for _, r in top_m.iterrows():
                if r["Day %"] > 0:
                    st.markdown(
                        f"**{r['Ticker']}** <span style='color:{COLOR_PROFIT}; float:right'>+{r['Day %']:.2f}%</span>",
                        unsafe_allow_html=True,
                    )
        with col_l:
            st.caption("Losers")
            for _, r in bot_m.iterrows():
                if r["Day %"] < 0:
                    st.markdown(
                        f"**{r['Ticker']}** <span style='color:{COLOR_LOSS}; float:right'>{r['Day %']:.2f}%</span>",
                        unsafe_allow_html=True,
                    )
        st.markdown("</div>", unsafe_allow_html=True)

    with c_alerts:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Risk & Alerts", unsafe_allow_html=True)

        alerts = []
        for _, r in df.iterrows():
            if r["Weight"] > 15:
                alerts.append(f"⚠️ **{r['Ticker']}** is overweight ({r['Weight']:.1f}%)")
            if r["Day %"] < -5:
                alerts.append(f"📉 **{r['Ticker']}** dropped > 5% today")
            if r["Total %"] < -20:
                alerts.append(f"❄️ **{r['Ticker']}** deep loss (>20%)")

        if not alerts:
            st.markdown(
                f"<div style='text-align:center; color:{COLOR_PROFIT}; padding:14px; border:1px solid #1f2d44; border-radius:4px; background:#111b2c;'>✅ All Clear. No risk triggers.</div>",
                unsafe_allow_html=True,
            )
        else:
            for a in alerts:
                st.markdown(
                    f"<div style='border:1px solid #1f2d44; color:{COLOR_NEUTRAL}; padding:8px; border-radius:4px; margin-bottom:8px; background:#111b2c; font-size:0.9rem'>{a}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Key Positions")
    key_pos = df.nlargest(8, "Weight")[["Ticker", "Owner", "Weight", "Total %", "Day %", "Value"]]

    st.dataframe(
        key_pos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Weight": st.column_config.NumberColumn(format="%.1f%%"),
            "Total %": st.column_config.NumberColumn(format="%.1f%%"),
            "Day %": st.column_config.NumberColumn(format="%.1f%%"),
            "Value": st.column_config.NumberColumn(format="Dh %.0f"),
        },
    )

# === TAB 2: POSITIONS ===
with tab_positions:
    with st.container():
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Filter positions", unsafe_allow_html=True)

        col_owner, col_sector, col_pl = st.columns(3)
        owners = ["All"] + sorted(df["Owner"].unique().tolist())
        sectors = ["All"] + sorted(df["Sector"].unique().tolist())

        owner_sel = col_owner.selectbox("Owner", owners, index=0)
        sector_sel = col_sector.selectbox("Sector", sectors, index=0)
        pl_filter = col_pl.radio(
            "P&L filter",
            ["All", "Profitable", "Losing"],
            horizontal=True,
        )

        filtered_df = df.copy()
        if owner_sel != "All":
            filtered_df = filtered_df[filtered_df["Owner"] == owner_sel]
        if sector_sel != "All":
            filtered_df = filtered_df[filtered_df["Sector"] == sector_sel]
        if pl_filter == "Profitable":
            filtered_df = filtered_df[filtered_df["Total P&L"] > 0]
        elif pl_filter == "Losing":
            filtered_df = filtered_df[filtered_df["Total P&L"] < 0]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Symbol"),
                "Value": st.column_config.NumberColumn(format="Dh %.0f"),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Total P&L": st.column_config.NumberColumn(format="Dh %.0f"),
                "Total %": st.column_config.NumberColumn(format="%.1f%%"),
                "Day P&L": st.column_config.NumberColumn(format="Dh %.0f"),
                "Day %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)

        inspect_ticker = st.selectbox("Inspect Position", options=filtered_df["Ticker"].unique())
        if inspect_ticker:
            row = df[df["Ticker"] == inspect_ticker].iloc[0]

            st.markdown(
                f"### {row['Ticker']} <span style='font-size:0.9rem; color:{COLOR_NEUTRAL}; font-weight:500'>({row['Owner']})</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<span class='muted'>{row['Sector']}</span>", unsafe_allow_html=True)

            st.divider()

            i1, i2 = st.columns(2)
            i1.metric("Units", f"{row['Units']:.0f}")
            i2.metric("Weight", f"{row['Weight']:.2f}%")

            i3, i4 = st.columns(2)
            i3.metric("Total Return", f"{row['Total %']:+.1f}%", delta_color="normal")
            i4.metric("Value", f"Dh {row['Value']/1000:.1f}k")

            st.divider()
            st.caption("Performance Trend (last few days)")

            if inspect_ticker in hist_data.columns:
                fig_mini = px.line(hist_data[inspect_ticker])
                fig_mini.update_traces(line_color=COLOR_PRIMARY, line_width=2)
                fig_mini = minimalist_chart(fig_mini, height=150)
                fig_mini.update_xaxes(visible=False)
                fig_mini.update_yaxes(visible=False)
                st.plotly_chart(fig_mini, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

# === TAB 3: ANALYTICS ===
with tab_analytics:
    with st.container():
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Portfolio vs Benchmark", unsafe_allow_html=True)

        fig_bench = go.Figure()
        fig_bench.add_trace(
            go.Scatter(
                x=hist_val.index,
                y=hist_val["Total"],
                name="Portfolio",
                line=dict(color=COLOR_PRIMARY, width=3),
            )
        )
        bench_sim = hist_val["Total"] * 0.95
        fig_bench.add_trace(
            go.Scatter(
                x=hist_val.index,
                y=bench_sim,
                name="Nasdaq 100 (Est)",
                line=dict(color=COLOR_ACCENT_SOFT, dash="dot"),
            )
        )

        fig_bench = minimalist_chart(fig_bench, height=350)
        fig_bench.update_layout(legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_bench, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c_cont, c_conc = st.columns(2)

    with c_cont:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Top Contributors (Total AED)", unsafe_allow_html=True)

        contrib = df.nlargest(8, "Total P&L")[["Ticker", "Total P&L"]]
        fig_ct = px.bar(contrib, x="Total P&L", y="Ticker", orientation="h")
        fig_ct.update_traces(marker_color=COLOR_PROFIT)
        fig_ct = minimalist_chart(fig_ct, height=300)
        st.plotly_chart(fig_ct, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_conc:
        st.markdown("<div class='card-container'>", unsafe_allow_html=True)
        st.markdown("#### Sector Concentration", unsafe_allow_html=True)

        sec_agg = df.groupby("Sector")["Value"].sum().reset_index()
        fig_sec = px.pie(
            sec_agg,
            values="Value",
            names="Sector",
            hole=0.6,
            color_discrete_sequence=[
                COLOR_PRIMARY,
                COLOR_ACCENT_SOFT,
                "#3d7fc4",
                "#2d5f92",
                "#234a74",
            ],
        )
        fig_sec.update_layout(
            height=300,
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True,
            paper_bgcolor=COLOR_BG,
            plot_bgcolor=COLOR_BG,
            font=dict(color=COLOR_NEUTRAL),
        )
        st.plotly_chart(fig_sec, use_container_width=True)

        top_1_w = df["Weight"].max()
        top_5_w = df.nlargest(5, "Weight")["Weight"].sum()

        st.markdown(f"**Top 5 Holdings:** {top_5_w:.1f}%", unsafe_allow_html=True)
        st.markdown(f"**Largest Single Position:** {top_1_w:.1f}%", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
