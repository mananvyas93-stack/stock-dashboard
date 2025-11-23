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
    """Fetch last few daily closes for all tickers, batched, and return simple columns=Ticker."""
    tickers = sorted({item["Ticker"] for item in portfolio_config})

    data = yf.download(
        tickers=tickers,
        period="5d",
        interval="1d",
        auto_adjust=True,_
