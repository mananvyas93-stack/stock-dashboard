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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&display=swap');

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
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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
    }

    .page-subtitle {
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.7rem;
        color: var(--muted);
        margin: 0;
    }

    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
        margin-bottom: 4px;
    }

    .kpi-value-main {
        font-family: 'Space Grotesk', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- CONSTANTS ----------
USD_TO_AED = 3.6725  # USD–AED peg

COLOR_PRIMARY = "#4aa3ff"
COLOR_SUCCESS = "#6bcf8f"
COLOR_DANGER = "#f27d72"
COLOR_BG = "#0f1a2b"

# ---------- PORTFOLIO CONFIG ----------
portfolio_config = [
    {"Name": "Alphabet",          "Ticker": "GOOGL", "Units": 51, "PurchaseValAED": 34128,  "Owner": "MV", "Sector": "Tech"},
    {"Name": "Apple",             "Ticker": "AAPL",  "Units": 50, "PurchaseValAED": 37183,  "Owner": "MV", "Sector": "Tech"},
    {"Name": "Tesla",             "Ticker": "TSLA",  "Units": 30, "PurchaseValAED": 33116,  "Owner": "MV", "Sector": "Auto"},
    {"Name": "Nasdaq 100",        "Ticker": "QQQM",  "Units": 180,"PurchaseValAED": 150894, "Owner": "MV", "Sector": "ETF"},
    {"Name": "AMD",               "Ticker": "AMD",   "Units": 27, "PurchaseValAED": 16075,  "Owner": "MV", "Sector": "Semi"},
    {"Name": "Broadcom",          "Ticker": "AVGO",  "Units": 13, "PurchaseValAED": 13578,  "Owner": "MV", "Sector"
