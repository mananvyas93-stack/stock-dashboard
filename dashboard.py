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

# ---------- THEME / CSS (Strict Hierarchy) ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-dark: #0f1a2b;
        --card-bg: #f8fafc;
        --text-dark: #0f172a;
        --text-muted: #64748b;
        --success: #16a34a;
        --danger: #dc2626;
        --accent: #2563eb;
    }

    /* Global Reset */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        background-color: var(--bg-dark);
        color: #e2e8f0;
    }

    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 3rem; max-width: 1200px; }

    /* --- ENHANCED KPI CARD --- */
    .kpi-container {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Top Row: Label + Status Tag */
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b; /* Slate-500 */
    }

    .kpi-tag {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 99px;
        background: #e2e8f0;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Middle: Value */
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a; /* Slate-900 */
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    /* Bottom: Pct + Sub-label */
    .kpi-footer {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-top: 4px;
    }

    .kpi-pct {
        font-size: 0.95rem;
        font-weight: 600;
    }

    .kpi-sub {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
    }

    /* Colors */
    .txt-green { color: var(--success); }
    .txt-red { color: var(--danger); }
    .txt-blue { color: var(--accent); }

    /* --- TABS --- */
    .stTabs { margin-top: 1.5rem; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #1e293b; gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #94a3b8;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.9rem;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #f8fafc;
        background-color: #1e293b;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* Header Title */
    .dashboard-header {
        margin-bottom: 10px;
    }
    .main-title { font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin: 0; }
    .sub-title { font-size: 0.85rem; color: #94a3b8; margin: 0; }

</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONFIGURATION ----------
USD_TO_AED = 3.6725
PORTFOLIO_INITIAL_XIRR = 13.78
PORTFOLIO_INITIAL_PROFIT = 1269608.61

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

MF_CONFIG = [
    {"Scheme": "Axis Large and Mid Cap", "Units": 55026.38, "CostINR": 1754912.25, "InitialValueINR": 1853288.31, "Ticker": "0P0001EP9Q.BO"},
    {"Scheme": "Franklin India ELSS Tax Saver", "Units": 286.62, "CostINR": 160000.0, "InitialValueINR": 433606.67, "Ticker": "0P00005VDI.BO"},
    {"Scheme": "Franklin India ELSS Tax Saver", "Units": 190.43, "CostINR": 95000.0, "InitialValueINR": 288087.76, "Ticker": "0P00005VDI.BO"},
    {"Scheme": "ICICI Prudential ELSS Tax Saver", "Units": 267.83, "CostINR": 98000.0, "InitialValueINR": 260058.54, "Ticker": "0P00005WD7.BO"},
    {"Scheme": "ICICI Prudential NASDAQ 100", "Units": 43574.66, "CostINR": 654967.25, "InitialValueINR": 846603.3, "Ticker": "0P0001NCLS.BO"},
    {"Scheme": "Mirae Asset Large and Mid Cap", "Units": 9054.85, "CostINR": 1327433.63, "InitialValueINR": 1429353.35, "Ticker": "0P0000ON3O.BO"},
    {"Scheme": "Nippon India Multi Cap", "Units": 4813.52, "CostINR": 1404929.75, "InitialValueINR": 1460345.18, "Ticker": "0P00005WDS.BO"},
    {"Scheme": "Parag Parikh Flexi Cap", "Units": 25345.69, "CostINR": 2082395.88, "InitialValueINR": 2204332.05, "Ticker": "0P0000YWL0.BO"},
    {"Scheme": "Parag Parikh Flexi Cap", "Units": 6095.12, "CostINR": 499975.0, "InitialValueINR": 530097.11, "Ticker": "0P0000YWL0.BO"},
    {"Scheme": "SBI Multicap Fund", "Units": 83983.45, "CostINR": 1404929.75, "InitialValueINR": 1446379.84, "Ticker": "0P0001OF6C.BO"}
]
# ---------- GLOBAL HELPERS ----------
def render_card(col, label, tag, value, pct_str, sub_label):
    color_cls = "txt-green" if "+" in pct_str else ("txt-red" if "-" in pct_str else "txt-blue")
    with col:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-header">
                <span class="kpi-label">{label}</span>
                <span class="kpi-tag">{tag}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-footer">
                <span class="kpi-pct {color_cls}">{pct_str}</span>
                <span class="kpi-sub">{sub_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def fmt_inr_lacs(val):
    if val is None or val != val: return "₹0.0 L"
    return f"₹{val/100000:.1f} L"

def fmt_inr_lacs_from_aed(val, rate):
    return fmt_inr_lacs(val * rate)

# ---------- DATA LOGIC ----------
@st.cache_data(ttl=3600)
def load_mf_navs_from_yahoo() -> dict:
    navs = {}
    for entry in MF_CONFIG:
        t = entry["Ticker"]
        if not t: continue
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="5d", interval="1d")
            if not hist.empty:
                navs[entry["Scheme"]] = float(hist["Close"].iloc[-1])
        except: continue
    return navs

def compute_india_mf_aggregate() -> dict:
    total_val = 0.0; total_pl = 0.0; latest_dt = None
    
    for entry in MF_CONFIG:
        t = entry["Ticker"]; u = entry["Units"]; file_v = entry["InitialValueINR"]
        if not t or u <= 0:
            total_val += file_v
            continue
            
        try:
            tkr = yf.Ticker(t)
            hist = tkr.history(period="5d")
            
            # Date
            if not hist.empty:
                dt = hist.index[-1].date()
                if latest_dt is None or dt > latest_dt: latest_dt = dt
            
            # Value with Safety Check
            val = file_v
            if not hist.empty:
                nav = float(hist["Close"].iloc[-1])
                cand = nav * u
                # If within 10%, trust Yahoo. Else trust File.
                if file_v > 0 and 0.9 <= (cand/file_v) <= 1.1: val = cand
                elif file_v == 0: val = cand
            
            # 1-Day Change
            pl = 0.0
            if len(hist) >= 2:
                pl = (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[-2])) * u
            
        except:
            val = file_v; pl = 0.0
            
        total_val += val
        total_pl += pl
        
    date_str = latest_dt.strftime("%d %B") if latest_dt else "N/A"
    if date_str.startswith("0"): date_str = date_str[1:]
    
    return {"val": total_val, "pl": total_pl, "date": date_str}

@st.cache_data(ttl=300)
def load_prices_close() -> pd.DataFrame:
    tickers = sorted({i["Ticker"] for i in portfolio_config})
    d = yf.download(tickers, period="5d", interval="1d", auto_adjust=True, group_by="ticker", progress=False, threads=False)
    if d is None or d.empty: return pd.DataFrame()
    
    if isinstance(d.columns, pd.MultiIndex):
        lvl1 = d.columns.get_level_values(1)
        if "Adj Close" in lvl1: c = d.xs("Adj Close", level=1, axis=1)
        elif "Close" in lvl1: c = d.xs("Close", level=1, axis=1)
        else: c = d.xs(lvl1[0], level=1, axis=1)
        c.columns = c.columns.get_level_values(0)
    else:
        c = d["Adj Close"] if "Adj Close" in d.columns else d["Close"]
        if isinstance(c, pd.Series): c = c.to_frame(name=tickers[0])
    return c.dropna(how="all")

@st.cache_data(ttl=60)
def load_prices_intraday() -> pd.Series:
    tickers = sorted({i["Ticker"] for i in portfolio_config})
    last_p = {}
    for t in tickers:
        try:
            tkr = yf.Ticker(t)
            h = tkr.history(period="5d", interval="1m", prepost=True)
            if not h.empty: last_p[t] = float(h["Close"].iloc[-1])
        except: continue
    return pd.Series(last_p) if last_p else pd.Series(dtype=float)

def get_market_status():
    us_tz = ZoneInfo("America/New_York")
    now = datetime.now(us_tz)
    t = now.time()
    if now.weekday() >= 5: return "Post Market"
    if time(4,0) <= t < time(9,30): return "Pre-Market"
    if time(9,30) <= t < time(16,0): return "Live Market"
    return "Post Market"

def get_aed_inr_rate_from_yahoo() -> float:
    try:
        tkr = yf.Ticker("AEDINR=X")
        hist = tkr.history(period="5d")
        if hist is None or hist.empty: return 22.50
        return float(hist["Close"].iloc[-1])
    except: return 22.50

def build_us_positions(close_df, live_s):
    rows = []
    us_tz = ZoneInfo("America/New_York")
    today = datetime.now(us_tz).date()
    
    for i in portfolio_config:
        t = i["Ticker"]; u = i["Units"]; purch = i["PurchaseValAED"]
        
        lp = 0.0
        if live_s is not None: lp = float(live_s.get(t, 0.0))
        if lp == 0 and not close_df.empty: lp = float(close_df.iloc[-1].get(t, 0.0))
        
        # Prev Close
        prev = 0.0
        if not close_df.empty and t in close_df.columns:
            s = close_df[t].dropna()
            if len(s) >= 2:
                prev = float(s.iloc[-2]) if s.index[-1].date() == today else float(s.iloc[-1])
            elif len(s) == 1: prev = float(s.iloc[-1])
            
        if lp <= 0:
            val_aed = purch; dpct = 0.0; dpl = 0.0
        else:
            p_usd = lp
            val_aed = p_usd * 3.6725 * u
            dpct = ((p_usd/prev)-1)*100 if prev > 0 else 0.0
            dpl = val_aed * (dpct/100.0)
            
        rows.append({
            "Name": i["Name"], "Ticker": t, "Owner": i["Owner"], "ValueAED": val_aed,
            "DayPLAED": dpl, "PurchaseAED": purch, "DayPct": dpct
        })
    return pd.DataFrame(rows)

def aggregate_for_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    mv = df[df["Owner"] == "MV"].copy()
    sv = df[df["Owner"] == "SV"].copy()
    if sv.empty: return mv.reset_index(drop=True)

    # Summarize SV
    sv_vals = {k: sv[k].sum() for k in ["ValueAED", "PurchaseAED", "DayPLAED", "Units"]}
    sv_row = pd.DataFrame([{
        "Name": "SV Portfolio", "Ticker": "SVPF", "Owner": "SV", "Sector": "Mixed",
        "Units": sv_vals["Units"], "PriceUSD": 0.0, "ValueAED": sv_vals["ValueAED"], "PurchaseAED": sv_vals["PurchaseAED"],
        "DayPct": (sv_vals["DayPLAED"] / sv_vals["ValueAED"] * 100.0) if sv_vals["ValueAED"] > 0 else 0.0,
        "DayPLAED": sv_vals["DayPLAED"],
        "WeightPct": 0.0
    }])
    
    combined = pd.concat([mv, sv_row], ignore_index=True)
    total_all = combined["ValueAED"].sum()
    combined["WeightPct"] = combined["ValueAED"] / total_all * 100.0 if total_all > 0 else 0.0
    return combined
    # ---------- EXECUTION & UI ----------

# 1. Fetch Data
m_status = get_market_status()
p_close = load_prices_close()
p_live = load_prices_intraday()
us_df = build_us_positions(p_close, p_live)
mf_data = compute_india_mf_aggregate()
aed_rate = get_aed_inr_rate_from_yahoo()

# 2. Header
st.markdown(f"""
<div class="dashboard-header">
  <div class="main-title">Stocks Dashboard</div>
  <div class="sub-title">{m_status} • Currency: 1 AED = ₹{aed_rate:.2f}</div>
</div>
""", unsafe_allow_html=True)

# 3. Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "SV Stocks", "US Stocks", "India MF"])

with tab1:
    # Aggregates
    us_val_inr = us_df["ValueAED"].sum() * aed_rate
    us_pl_inr = us_df["DayPLAED"].sum() * aed_rate
    us_pct = (us_df["DayPLAED"].sum() / (us_df["ValueAED"].sum() - us_df["DayPLAED"].sum()) * 100) if us_df["ValueAED"].sum() > 0 else 0
    
    mf_val = mf_data["val"]
    mf_pl = mf_data["pl"]
    mf_pct = (mf_pl / (mf_val - mf_pl) * 100) if (mf_val - mf_pl) > 0 else 0.0
    
    # Calculate Total Portfolio Cost for Absolute Return (using config)
    mf_tot_cost = sum(i["CostINR"] for i in MF_CONFIG)
    mf_abs_ret = ((mf_val - mf_tot_cost)/mf_tot_cost*100) if mf_tot_cost > 0 else 0.0
    
    # Render 4 Cards
    c1, c2, c3, c4 = st.columns(4)
    
    # Card 1: US Profit (Dynamic Header)
    render_card(c1, m_status, "TODAY", f"₹{us_pl_inr:,.0f}", f"{us_pct:+.2f}%", "US Stocks")
    
    # Card 2: MF Profit (Dynamic Date)
    render_card(c2, mf_data["date"], "CHANGE", f"₹{mf_pl:,.0f}", f"{mf_pct:+.2f}%", "India MF")
    
    # Card 3 & 4: Holdings
    us_tot_pct = (us_df["ValueAED"].sum() - us_df["PurchaseAED"].sum()) / us_df["PurchaseAED"].sum() * 100
    
    render_card(c3, "TOTAL HOLDING", "VALUE", fmt_inr_lacs(us_val_inr), f"{us_tot_pct:+.2f}%", "US Stocks")
    render_card(c4, "TOTAL HOLDING", "VALUE", fmt_inr_lacs(mf_val), f"{mf_abs_ret:+.2f}%", "India MF")

    # Heatmap
    st.subheader("Asset Performance")
    agg_df = aggregate_for_heatmap(us_df)
    
    if not agg_df.empty:
        # Prep Heatmap Data
        hm = agg_df.copy()
        hm["ValueINR"] = hm["ValueAED"] * aed_rate
        hm["PL_INR"] = hm["DayPLAED"] * aed_rate
        
        # Add MF Block
        hm = pd.concat([hm, pd.DataFrame([{
            "Name": "India MF", "Ticker": "IND", "ValueINR": mf_val, "PL_INR": mf_pl
        }])], ignore_index=True)
        
        hm["ColorVal"] = hm["PL_INR"]
        hm["Label"] = hm.apply(lambda x: f"{x['Name']}<br>₹{x['PL_INR']/1000:.0f}k", axis=1)
        
        fig = px.treemap(hm, path=["Name"], values="ValueINR", color="ColorVal",
                         color_continuous_scale=[COLOR_DANGER, "#1e293b", COLOR_SUCCESS],
                         color_continuous_midpoint=0)
        fig.update_traces(textinfo="label", texttemplate="%{label}", textfont_size=14)
        fig.update_layout(margin=dict(t=0,l=0,r=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Re-calculate SV specific aggregates
    sv_only = us_df[us_df["Owner"] == "SV"]
    if sv_only.empty: st.info("No SV positions.")
    else:
        sv_val_aed = sv_only["ValueAED"].sum()
        sv_pl_aed = sv_only["DayPLAED"].sum()
        sv_cost_aed = sv_only["PurchaseAED"].sum()
        
        sv_day_pct = (sv_pl_aed / (sv_val_aed - sv_pl_aed) * 100) if (sv_val_aed - sv_pl_aed) > 0 else 0
        sv_tot_pct = ((sv_val_aed - sv_cost_aed)/sv_cost_aed * 100) if sv_cost_aed > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        render_card(c1, "TODAY'S PROFIT", "AED", f"{sv_pl_aed:,.0f}", f"{sv_day_pct:+.2f}%", "SV Portfolio")
        render_card(c2, "TOTAL PROFIT", "AED", f"{(sv_val_aed - sv_cost_aed):,.0f}", f"{sv_tot_pct:+.2f}%", "SV Portfolio")
        render_card(c3, "TOTAL HOLDING", "AED", f"{sv_val_aed:,.0f}", "", fmt_inr_lacs_from_aed(sv_val_aed, aed_rate))

        # SV Heatmap
        fig_sv = px.treemap(sv_only, path=["Name"], values="ValueAED", color="DayPLAED",
                            color_continuous_scale=[COLOR_DANGER, "#1e293b", COLOR_SUCCESS],
                            color_continuous_midpoint=0)
        fig_sv.update_layout(margin=dict(t=0,l=0,r=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sv, use_container_width=True)

with tab3:
    # Detailed US List
    for _, row in us_df.iterrows():
        nm = row['Name']; tk = row['Ticker']
        val_inr = row['ValueAED'] * aed_rate
        pct = row['DayPct']
        
        st.markdown(f"""
        <div class="kpi-container" style="min-height: auto; padding: 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #0f172a;">{nm}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">{tk}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 700; font-size: 1.1rem; color: #0f172a;">{fmt_inr_lacs(val_inr)}</div>
                    <div style="font-weight: 600; color: {'#16a34a' if pct>=0 else '#dc2626'};">{pct:+.2f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    # Mutual Fund Detailed List
    if not MF_CONFIG: st.info("No MF Config")
    else:
        mf_rows = []
        mf_navs_list = load_mf_navs_from_yahoo()
        for item in MF_CONFIG:
            sch = item["Scheme"]; units = item["Units"]; cost = item["CostINR"]; file_val = item.get("InitialValueINR", 0.0)
            ln = mf_navs_list.get(item["Ticker"])
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
        
        # Total MF Header
        tot_v = sum(r["v"] for r in mf_rows)
        tot_r = ((tot_v - mf_tot_cost)/mf_tot_cost * 100.0) if mf_tot_cost > 0 else 0.0
        
        st.markdown(f"""
        <div class="kpi-container" style="background: #e2e8f0; border: none;">
            <div class="kpi-header"><span class="kpi-label">MF PORTFOLIO</span></div>
            <div class="kpi-main-row">
                <span class="kpi-value-big">{fmt_inr_lacs(tot_v)}</span>
                <span class="kpi-value-secondary txt-blue">{tot_r:.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for r in mf_rows:
            disp_name = r["n"].replace(" Fund Growth", "").split("\n")[0]
            st.markdown(f"""
            <div class="kpi-container" style="min-height: auto; padding: 12px; margin-bottom: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div style="font-weight: 600; font-size: 0.95rem; color: #334155;">{disp_name}</div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
                    <div style="font-weight: 700; font-size: 1.1rem; color: #0f172a;">{fmt_inr_lacs(r["v"])}</div>
                    <div style="font-weight: 600; font-size: 0.95rem; color: #0f172a;">{r["r"]:.1f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
