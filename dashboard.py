# ---------- MARKET STATUS & DATA SOURCE ----------

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    # Define Strings based on Time - NO SQUARE BRACKETS
    if weekday >= 5:
        # Weekend -> "Post Market" (Last State)
        phase_str = "Post Market"
    else:
        # Weekday Logic
        if time(4,0) <= t < time(9,30):
            phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0):
            phase_str = "Live Market"
        else:
            # Evenings/Nights -> "Post Market"
            phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()

    # Always prefer intraday if available as it has pre/post info
    if intraday is None or intraday.empty:
        return phase_str, base_close

    return phase_str, intraday

@st.cache_data(ttl=60)
def get_market_indices_change(phase_str: str) -> str:
    """
    Fetches Nifty 50 and Nasdaq 100 changes.
    FIXED: Uses ^NDX (Index) as primary, QQQ as fallback. 
    Improved logic to prevent '0.0%' errors during pre/post market.
    """
    
    # --- 1. NIFTY 50 ---
    nifty_str = "Nifty 0.0%"
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 2:
            close_now = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            pct = (close_now / prev_close - 1) * 100
            nifty_str = f"Nifty {pct:+.1f}%"
        elif len(hist) == 1:
            # If only 1 day data (e.g. holiday glitch), try 5d
            hist_5d = nifty.history(period="5d")
            if len(hist_5d) >= 2:
                close_now = hist_5d["Close"].iloc[-1]
                prev_close = hist_5d["Close"].iloc[-2]
                pct = (close_now / prev_close - 1) * 100
                nifty_str = f"Nifty {pct:+.1f}%"
    except:
        pass

    # --- 2. NASDAQ 100 (Robust Fix) ---
    nasdaq_str = "Nasdaq 0.0%"
    
    def calculate_change(ticker_symbol):
        """Helper to try getting change from a specific ticker"""
        tkr = yf.Ticker(ticker_symbol)
        # Get intraday data to capture Pre/Post market moves
        hist_1m = tkr.history(period="1d", interval="1m", prepost=True)
        # Get daily data for baseline
        daily = tkr.history(period="5d")
        
        if daily.empty:
            return None

        # Determine 'Current' Price
        if not hist_1m.empty:
            current_price = hist_1m["Close"].iloc[-1]
        else:
            current_price = daily["Close"].iloc[-1]

        # Determine 'Previous' Close (Baseline)
        # If we are in Live/Pre market, baseline is Yesterday's Close
        # If we are in Post market, baseline is Today's Close (usually)
        # To be safe, we always compare against the most recent COMPLETED trading day.
        
        if len(daily) >= 2:
            # Check if the last row is 'today' (incomplete) or 'yesterday'
            last_date = daily.index[-1].date()
            now_date = datetime.now(ZoneInfo("America/New_York")).date()
            
            if last_date == now_date:
                # Last row is today. Prev close is row -2.
                prev_close = daily["Close"].iloc[-2]
            else:
                # Last row is yesterday (or Friday). That is the current close? No, that's the baseline.
                # If we have live data (hist_1m), we compare against last_date close.
                prev_close = daily["Close"].iloc[-1]
        else:
            return None

        if prev_close == 0:
            return None
            
        return (current_price / prev_close - 1) * 100

    # Try Primary: ^NDX (Official Index)
    pct_change = calculate_change("^NDX")
    
    # Try Secondary: QQQ (ETF) if Primary failed or returned flat 0.0 (suspicious)
    if pct_change is None or (abs(pct_change) < 0.001):
        pct_change_qqq = calculate_change("QQQ")
        if pct_change_qqq is not None:
            pct_change = pct_change_qqq

    if pct_change is not None:
        nasdaq_str = f"Nasdaq {pct_change:+.1f}%"

    return f"{nifty_str} <span style='opacity:0.4; margin:0 6px;'>|</span> {nasdaq_str}"


# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None, usd_to_aed_rate: float) -> pd.DataFrame:
    rows = []
    
    # We need a robust "Previous Close" to calculate change against.
    
    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        # 1. Get Live Price
        live_price = 0.0
        if prices_intraday is not None:
            live_price = float(prices_intraday.get(t, 0.0))
        
        # Fallback to close if no intraday
        if live_price == 0 and not prices_close.empty:
             live_price = float(prices_close.iloc[-1].get(t, 0.0))

        # 2. Get Previous Close (Reference for P&L)
        prev_close_price = 0.0
        if not prices_close.empty:
            last_date = prices_close.index[-1].date()
            us_tz = ZoneInfo("America/New_York")
            today_date = datetime.now(us_tz).date()
            
            col_data = prices_close[t]
            if len(col_data) >= 2:
                if last_date == today_date:
                    prev_close_price = float(col_data.iloc[-2])
                else:
                    prev_close_price = float(col_data.iloc[-1])
            elif len(col_data) == 1:
                prev_close_price = float(col_data.iloc[-1])

        if live_price <= 0:
            value_aed = purchase
            day_pct = 0.0
            day_pl_aed = 0.0
            total_pl_aed = 0.0
            total_pct = 0.0
            price_usd = 0.0
        else:
            price_usd = live_price
            price_aed = price_usd * usd_to_aed_rate
            value_aed = price_aed * units

            # Day P&L vs Previous Close
            if prev_close_price > 0:
                day_pct = (price_usd / prev_close_price - 1.0) * 100.0
            else:
                day_pct = 0.0
                
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
    # ---------- DATA PIPELINE ----------

market_status_str, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()
header_metrics_str = get_market_indices_change(market_status_str)

# FETCH API FX RATES
fx_rates = get_fx_rates()
USD_TO_AED = fx_rates["USD_AED"]
AED_TO_INR = fx_rates["AED_INR"]

if isinstance(price_source, pd.DataFrame):
    positions = build_positions_from_prices(price_source, None, USD_TO_AED)
else:
    positions = build_positions_from_prices(prices_close, price_source, USD_TO_AED)

agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions

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
  <div class="page-subtitle">{header_metrics_str}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- TABS ----------

overview_tab, sv_tab, us_tab, mf_tab = st.tabs([
    "🪙 Overview",
    "💷 SV Stocks",
    "💵 US Stocks",
    "💴 India MF",
])

# ---------- HOME TAB ----------

with overview_tab:
    # --- 1. PREPARE DATA FOR CARDS ---

    # A. US Stocks
    us_day_pl_inr = day_pl_aed * AED_TO_INR
    us_prev_val_aed = total_val_aed - day_pl_aed
    us_day_pct = (day_pl_aed / us_prev_val_aed * 100.0) if us_prev_val_aed > 0 else 0.0

    # B. India Mutual Funds
    mf_agg = compute_india_mf_aggregate()
    mf_val_inr = float(mf_agg.get("total_value_inr", 0.0) or 0.0)
    mf_day_pl_inr = float(mf_agg.get("daily_pl_inr", 0.0) or 0.0)
    
    # MF Change %
    mf_prev_val = mf_val_inr - mf_day_pl_inr
    mf_day_pct = (mf_day_pl_inr / mf_prev_val * 100.0) if mf_prev_val > 0 else 0.0

    # MF ABSOLUTE RETURN %
    mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
    mf_total_profit = mf_val_inr - mf_total_cost
    mf_abs_return_pct = (mf_total_profit / mf_total_cost * 100.0) if mf_total_cost > 0 else 0.0

    # --- 2. RENDER CARDS (FIXED: NO INDENTATION, UNIFIED FONTS) ---
    
    c1, c2, c3, c4 = st.columns(4)

    def render_new_kpi_card(col, top_label, main_value, right_value, bottom_label):
        with col:
            # HTML content must be flush left to avoid code block rendering
            html_content = f"""
<div class="card mf-card">
<div class="kpi-label">{top_label}</div>
<div class="kpi-mid-row">
<div class="kpi-number">{main_value}</div>
<div class="kpi-number">{right_value}</div>
</div>
<div class="kpi-label">{bottom_label}</div>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

    # Card 1: Today's Profit | Market Status -> US Stocks
    status_display = f"TODAY'S PROFIT <span style='opacity:0.5; margin:0 4px;'>|</span> {market_status_str.upper()}"
    
    render_new_kpi_card(
        c1, 
        status_display, 
        f"₹{us_day_pl_inr:,.0f}", 
        f"{us_day_pct:+.2f}%",
        "US STOCKS"
    )

    # Card 2: Today's Profit -> India MF
    render_new_kpi_card(
        c2, 
        "TODAY'S PROFIT", 
        f"₹{mf_day_pl_inr:,.0f}", 
        f"{mf_day_pct:+.2f}%",
        "INDIA MF"
    )

    # Card 3: Total Holding -> US Stocks
    render_new_kpi_card(
        c3, 
        "TOTAL HOLDING", 
        total_val_inr_lacs,
        f"{total_pl_pct:+.2f}%",  # Added + sign
        "US STOCKS"
    )

    # Card 4: Total Holding -> India MF
    render_new_kpi_card(
        c4, 
        "TOTAL HOLDING", 
        fmt_inr_lacs(mf_val_inr), 
        f"{mf_abs_return_pct:+.2f}%", # Added + sign
        "INDIA MF"
    )

    # --- 3. RENDER HEATMAP ---

    st.markdown(
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:10px 0 4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data. Showing static valuation only; heat map disabled.")
    else:
        hm = agg_for_heatmap.copy()
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR

        if mf_val_inr > 0 or mf_day_pl_inr != 0.0:
            ind_mf_row = {
                "Name": "Indian MF",
                "Ticker": "INDMF",
                "Owner": "MF",
                "Sector": "India MF",
                "Units": 0.0,
                "PriceUSD": 0.0,
                "ValueAED": mf_val_inr / AED_TO_INR if mf_val_inr > 0 else 0.0,
                "PurchaseAED": 0.0,
                "DayPct": 0.0,
                "DayPLAED": mf_day_pl_inr / AED_TO_INR,
                "DayPLINR": mf_day_pl_inr, 
                "TotalPct": 0.0,
                "TotalPLAED": 0.0,
                "WeightPct": 0.0,
            }
            hm = pd.concat([hm, pd.DataFrame([ind_mf_row])], ignore_index=True)

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

    sv_positions = positions[positions["Owner"] == "SV"].copy()

    if sv_positions.empty:
        st.info("No SV positions found.")
    else:
        sv_total_val_aed = sv_positions["ValueAED"].sum()
        sv_total_purchase_aed = sv_positions["PurchaseAED"].sum()
        sv_total_pl_aed = sv_positions["TotalPLAED"].sum()
        sv_day_pl_aed = sv_positions["DayPLAED"].sum()

        sv_total_pl_pct = (sv_total_pl_aed / sv_total_purchase_aed * 100.0) if sv_total_purchase_aed > 0 else 0.0
        prev_total_val = sv_total_val_aed - sv_day_pl_aed
        sv_day_pl_pct = (sv_day_pl_aed / prev_total_val * 100.0) if prev_total_val > 0 else 0.0

        sv_day_pl_aed_str = f"AED {sv_day_pl_aed:,.0f}"
        sv_day_pl_pct_str = f"{sv_day_pl_pct:+.2f}%"
        sv_total_pl_aed_str = f"AED {sv_total_pl_aed:,.0f}"
        sv_total_pl_pct_str = f"{sv_total_pl_pct:+.2f}%"
        sv_total_val_aed_str = f"AED {sv_total_val_aed:,.0f}"
        sv_total_val_inr_lacs_str = fmt_inr_lacs_from_aed(sv_total_val_aed, AED_TO_INR)

        # Layout: 3 columns for 3 cards (RESTORED)
        c1, c2, c3 = st.columns(3)

        # Card 1: Today's Profit
        with c1:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TODAY'S PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_day_pl_aed_str}</div>
                    <div class="kpi-number">{sv_day_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 2: Total Profit
        with c2:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_pl_aed_str}</div>
                    <div class="kpi-number">{sv_total_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 3: Total Holding Value
        with c3:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL HOLDING</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_val_aed_str}</div>
                    <div class="kpi-number">{sv_total_val_inr_lacs_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            """<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;">Today's Gains – SV</div>""",
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
        
        # --- NEW SECTION: SV HOLDINGS CARDS (FIXED LOOP) ---
        st.markdown(
            """<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:14px 0 4px 0;">SV Holdings</div>""",
            unsafe_allow_html=True,
        )
        
        # Sort by Total Profit High to Low
        sorted_sv = sv_positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base Label Style
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_sv:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            
            # Explicit SV Label
            units_str = f"{units:,.0f} UNITS • SV"
            
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # Determine Color Class
            color_class = "kpi-green" if pl_aed >= 0 else "kpi-red"
            
            # Clean Name
            display_name = name.upper().replace(" [SV]", "")

            # Render HTML Card with Explicit Class Logic
            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_pct_str}</div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

# ---------- US STOCKS TAB (NEW) ----------

with us_tab:
    if positions.empty:
        st.info("No US positions found.")
    else:
        # 3. INDIVIDUAL STOCK CARDS (REDESIGNED)
        # Sorted by Total Profit AED Descending
        sorted_pos = positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base Label Style to allow color override (avoids the class .kpi-label color conflict)
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_pos:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            owner = row["Owner"]
            
            # Label Update for SV
            suffix = " • SV" if owner == "SV" else ""
            units_str = f"{units:,.0f} UNITS{suffix}"
            
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # Determine Color Class
            color_class = "kpi-green" if pl_aed >= 0 else "kpi-red"
            
            # Clean Name
            display_name = name.upper().replace(" [SV]", "")

            # NEW CARD LAYOUT with Explicit Class Logic
            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_pct_str}</div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

# ---------- INDIA MF TAB ----------


with mf_tab:
    if not MF_CONFIG:
        st.info("No mutual fund data configured.")
    else:
        # Load NAVs from AMFI (Official API)
        mf_navs = load_mf_navs_from_amfi()
        mf_rows = []
        for mf_entry in MF_CONFIG:
            scheme = mf_entry["Scheme"]
            units = float(mf_entry["Units"] or 0.0)
            cost_inr = float(mf_entry["CostINR"] or 0.0)
            file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

            live_nav = mf_navs.get(scheme)

            # Safety check logic REMOVED - Trust Live Data if available
            value_inr = file_value_inr
            if live_nav is not None and live_nav > 0 and units > 0:
                candidate_value = live_nav * units
                value_inr = candidate_value
            
            # Absolute return
            if cost_inr > 0:
                abs_return = (value_inr - cost_inr) / cost_inr * 100.0
            else:
                abs_return = 0.0

            mf_rows.append(
                {
                    "scheme": scheme,
                    "value_inr": value_inr,
                    "return_pct": abs_return,
                }
            )

        mf_rows.sort(key=lambda r: r["value_inr"], reverse=True)
        total_value_inr = sum(r["value_inr"] for r in mf_rows)
        mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
        
        if mf_total_cost > 0:
            total_abs_return_pct = (total_value_inr - mf_total_cost) / mf_total_cost * 100.0
        else:
            total_abs_return_pct = 0.0

        total_value_str = fmt_inr_lacs(total_value_inr)
        total_return_str = f"{total_abs_return_pct:.2f}%"

        st.markdown(
            f"""
            <div class="card mf-card">
                <div class="kpi-top-row">
                    <div class="kpi-label">VALUE</div>
                    <div class="kpi-label">RETURN</div>
                </div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{total_value_str}</div>
                    <div class="kpi-number">{total_return_str}</div>
                </div>
                <div class="kpi-label">PORTFOLIO AGGREGATE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for row in mf_rows:
            scheme = row["scheme"]
            value_inr = row["value_inr"]
            ret_pct = row["return_pct"]

            display_name = scheme
            parts = display_name.split()
            if parts and all(ch.isdigit() or ch in "/-" for ch in parts[-1]):
                display_name = " ".join(parts[:-1])
            if "Fund Growth" in display_name:
                display_name = display_name.replace(" Fund Growth", "")

            value_str = fmt_inr_lacs(value_inr)
            ret_str = f"{ret_pct:.1f}%"

            st.markdown(
                f"""
                <div class="card mf-card">
                    <div class="kpi-top-row">
                        <div class="kpi-label">VALUE</div>
                        <div class="kpi-label">RETURN</div>
                    </div>
                    <div class="kpi-mid-row">
                        <div class="kpi-number">{value_str}</div>
                        <div class="kpi-number">{ret_str}</div>
                    </div>
                    <div class="kpi-label">{display_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # ---------- MARKET STATUS & DATA SOURCE ----------

def get_market_phase_and_prices():
    us_tz = ZoneInfo("America/New_York")
    now_us = datetime.now(us_tz)
    weekday = now_us.weekday()
    t = now_us.time()
    
    # Define Strings based on Time - NO SQUARE BRACKETS
    if weekday >= 5:
        # Weekend -> "Post Market" (Last State)
        phase_str = "Post Market"
    else:
        # Weekday Logic
        if time(4,0) <= t < time(9,30):
            phase_str = "Pre-Market"
        elif time(9,30) <= t < time(16,0):
            phase_str = "Live Market"
        else:
            # Evenings/Nights -> "Post Market"
            phase_str = "Post Market"

    base_close = load_prices_close()
    intraday = load_prices_intraday()

    # Always prefer intraday if available as it has pre/post info
    if intraday is None or intraday.empty:
        return phase_str, base_close

    return phase_str, intraday

@st.cache_data(ttl=60)
def get_market_indices_change(phase_str: str) -> str:
    """
    Fetches Nifty 50 and Nasdaq 100 changes.
    FIXED: Uses ^NDX (Index) as primary, QQQ as fallback. 
    Improved logic to prevent '0.0%' errors during pre/post market.
    """
    
    # --- 1. NIFTY 50 ---
    nifty_str = "Nifty 0.0%"
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 2:
            close_now = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            pct = (close_now / prev_close - 1) * 100
            nifty_str = f"Nifty {pct:+.1f}%"
        elif len(hist) == 1:
            # If only 1 day data (e.g. holiday glitch), try 5d
            hist_5d = nifty.history(period="5d")
            if len(hist_5d) >= 2:
                close_now = hist_5d["Close"].iloc[-1]
                prev_close = hist_5d["Close"].iloc[-2]
                pct = (close_now / prev_close - 1) * 100
                nifty_str = f"Nifty {pct:+.1f}%"
    except:
        pass

    # --- 2. NASDAQ 100 (Robust Fix) ---
    nasdaq_str = "Nasdaq 0.0%"
    
    def calculate_change(ticker_symbol):
        """Helper to try getting change from a specific ticker"""
        tkr = yf.Ticker(ticker_symbol)
        # Get intraday data to capture Pre/Post market moves
        hist_1m = tkr.history(period="1d", interval="1m", prepost=True)
        # Get daily data for baseline
        daily = tkr.history(period="5d")
        
        if daily.empty:
            return None

        # Determine 'Current' Price
        if not hist_1m.empty:
            current_price = hist_1m["Close"].iloc[-1]
        else:
            current_price = daily["Close"].iloc[-1]

        # Determine 'Previous' Close (Baseline)
        # If we are in Live/Pre market, baseline is Yesterday's Close
        # If we are in Post market, baseline is Today's Close (usually)
        # To be safe, we always compare against the most recent COMPLETED trading day.
        
        if len(daily) >= 2:
            # Check if the last row is 'today' (incomplete) or 'yesterday'
            last_date = daily.index[-1].date()
            now_date = datetime.now(ZoneInfo("America/New_York")).date()
            
            if last_date == now_date:
                # Last row is today. Prev close is row -2.
                prev_close = daily["Close"].iloc[-2]
            else:
                # Last row is yesterday (or Friday). That is the current close? No, that's the baseline.
                # If we have live data (hist_1m), we compare against last_date close.
                prev_close = daily["Close"].iloc[-1]
        else:
            return None

        if prev_close == 0:
            return None
            
        return (current_price / prev_close - 1) * 100

    # Try Primary: ^NDX (Official Index)
    pct_change = calculate_change("^NDX")
    
    # Try Secondary: QQQ (ETF) if Primary failed or returned flat 0.0 (suspicious)
    if pct_change is None or (abs(pct_change) < 0.001):
        pct_change_qqq = calculate_change("QQQ")
        if pct_change_qqq is not None:
            pct_change = pct_change_qqq

    if pct_change is not None:
        nasdaq_str = f"Nasdaq {pct_change:+.1f}%"

    return f"{nifty_str} <span style='opacity:0.4; margin:0 6px;'>|</span> {nasdaq_str}"


# ---------- PORTFOLIO BUILDERS ----------

def build_positions_from_prices(prices_close: pd.DataFrame, prices_intraday: pd.Series | None, usd_to_aed_rate: float) -> pd.DataFrame:
    rows = []
    
    # We need a robust "Previous Close" to calculate change against.
    
    for item in portfolio_config:
        t = item["Ticker"]
        units = float(item["Units"])
        purchase = float(item["PurchaseValAED"])

        # 1. Get Live Price
        live_price = 0.0
        if prices_intraday is not None:
            live_price = float(prices_intraday.get(t, 0.0))
        
        # Fallback to close if no intraday
        if live_price == 0 and not prices_close.empty:
             live_price = float(prices_close.iloc[-1].get(t, 0.0))

        # 2. Get Previous Close (Reference for P&L)
        prev_close_price = 0.0
        if not prices_close.empty:
            last_date = prices_close.index[-1].date()
            us_tz = ZoneInfo("America/New_York")
            today_date = datetime.now(us_tz).date()
            
            col_data = prices_close[t]
            if len(col_data) >= 2:
                if last_date == today_date:
                    prev_close_price = float(col_data.iloc[-2])
                else:
                    prev_close_price = float(col_data.iloc[-1])
            elif len(col_data) == 1:
                prev_close_price = float(col_data.iloc[-1])

        if live_price <= 0:
            value_aed = purchase
            day_pct = 0.0
            day_pl_aed = 0.0
            total_pl_aed = 0.0
            total_pct = 0.0
            price_usd = 0.0
        else:
            price_usd = live_price
            price_aed = price_usd * usd_to_aed_rate
            value_aed = price_aed * units

            # Day P&L vs Previous Close
            if prev_close_price > 0:
                day_pct = (price_usd / prev_close_price - 1.0) * 100.0
            else:
                day_pct = 0.0
                
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
    # ---------- DATA PIPELINE ----------

market_status_str, price_source = get_market_phase_and_prices()
prices_close = load_prices_close()
header_metrics_str = get_market_indices_change(market_status_str)

# FETCH API FX RATES
fx_rates = get_fx_rates()
USD_TO_AED = fx_rates["USD_AED"]
AED_TO_INR = fx_rates["AED_INR"]

if isinstance(price_source, pd.DataFrame):
    positions = build_positions_from_prices(price_source, None, USD_TO_AED)
else:
    positions = build_positions_from_prices(prices_close, price_source, USD_TO_AED)

agg_for_heatmap = aggregate_for_heatmap(positions) if not positions.empty else positions

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
  <div class="page-subtitle">{header_metrics_str}</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- TABS ----------

overview_tab, sv_tab, us_tab, mf_tab = st.tabs([
    "🪙 Overview",
    "💷 SV Stocks",
    "💵 US Stocks",
    "💴 India MF",
])

# ---------- HOME TAB ----------

with overview_tab:
    # --- 1. PREPARE DATA FOR CARDS ---

    # A. US Stocks
    us_day_pl_inr = day_pl_aed * AED_TO_INR
    us_prev_val_aed = total_val_aed - day_pl_aed
    us_day_pct = (day_pl_aed / us_prev_val_aed * 100.0) if us_prev_val_aed > 0 else 0.0

    # B. India Mutual Funds
    mf_agg = compute_india_mf_aggregate()
    mf_val_inr = float(mf_agg.get("total_value_inr", 0.0) or 0.0)
    mf_day_pl_inr = float(mf_agg.get("daily_pl_inr", 0.0) or 0.0)
    
    # MF Change %
    mf_prev_val = mf_val_inr - mf_day_pl_inr
    mf_day_pct = (mf_day_pl_inr / mf_prev_val * 100.0) if mf_prev_val > 0 else 0.0

    # MF ABSOLUTE RETURN %
    mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
    mf_total_profit = mf_val_inr - mf_total_cost
    mf_abs_return_pct = (mf_total_profit / mf_total_cost * 100.0) if mf_total_cost > 0 else 0.0

    # --- 2. RENDER CARDS (FIXED: NO INDENTATION, UNIFIED FONTS) ---
    
    c1, c2, c3, c4 = st.columns(4)

    def render_new_kpi_card(col, top_label, main_value, right_value, bottom_label):
        with col:
            # HTML content must be flush left to avoid code block rendering
            html_content = f"""
<div class="card mf-card">
<div class="kpi-label">{top_label}</div>
<div class="kpi-mid-row">
<div class="kpi-number">{main_value}</div>
<div class="kpi-number">{right_value}</div>
</div>
<div class="kpi-label">{bottom_label}</div>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

    # Card 1: Today's Profit | Market Status -> US Stocks
    status_display = f"TODAY'S PROFIT <span style='opacity:0.5; margin:0 4px;'>|</span> {market_status_str.upper()}"
    
    render_new_kpi_card(
        c1, 
        status_display, 
        f"₹{us_day_pl_inr:,.0f}", 
        f"{us_day_pct:+.2f}%",
        "US STOCKS"
    )

    # Card 2: Today's Profit -> India MF
    render_new_kpi_card(
        c2, 
        "TODAY'S PROFIT", 
        f"₹{mf_day_pl_inr:,.0f}", 
        f"{mf_day_pct:+.2f}%",
        "INDIA MF"
    )

    # Card 3: Total Holding -> US Stocks
    render_new_kpi_card(
        c3, 
        "TOTAL HOLDING", 
        total_val_inr_lacs,
        f"{total_pl_pct:+.2f}%",  # Added + sign
        "US STOCKS"
    )

    # Card 4: Total Holding -> India MF
    render_new_kpi_card(
        c4, 
        "TOTAL HOLDING", 
        fmt_inr_lacs(mf_val_inr), 
        f"{mf_abs_return_pct:+.2f}%", # Added + sign
        "INDIA MF"
    )

    # --- 3. RENDER HEATMAP ---

    st.markdown(
        '''<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:10px 0 4px 0;">Today's Gains</div>''',
        unsafe_allow_html=True,
    )

    if agg_for_heatmap is None or agg_for_heatmap.empty:
        st.info("No live price data. Showing static valuation only; heat map disabled.")
    else:
        hm = agg_for_heatmap.copy()
        hm["DayPLINR"] = hm["DayPLAED"] * AED_TO_INR

        if mf_val_inr > 0 or mf_day_pl_inr != 0.0:
            ind_mf_row = {
                "Name": "Indian MF",
                "Ticker": "INDMF",
                "Owner": "MF",
                "Sector": "India MF",
                "Units": 0.0,
                "PriceUSD": 0.0,
                "ValueAED": mf_val_inr / AED_TO_INR if mf_val_inr > 0 else 0.0,
                "PurchaseAED": 0.0,
                "DayPct": 0.0,
                "DayPLAED": mf_day_pl_inr / AED_TO_INR,
                "DayPLINR": mf_day_pl_inr, 
                "TotalPct": 0.0,
                "TotalPLAED": 0.0,
                "WeightPct": 0.0,
            }
            hm = pd.concat([hm, pd.DataFrame([ind_mf_row])], ignore_index=True)

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

    sv_positions = positions[positions["Owner"] == "SV"].copy()

    if sv_positions.empty:
        st.info("No SV positions found.")
    else:
        sv_total_val_aed = sv_positions["ValueAED"].sum()
        sv_total_purchase_aed = sv_positions["PurchaseAED"].sum()
        sv_total_pl_aed = sv_positions["TotalPLAED"].sum()
        sv_day_pl_aed = sv_positions["DayPLAED"].sum()

        sv_total_pl_pct = (sv_total_pl_aed / sv_total_purchase_aed * 100.0) if sv_total_purchase_aed > 0 else 0.0
        prev_total_val = sv_total_val_aed - sv_day_pl_aed
        sv_day_pl_pct = (sv_day_pl_aed / prev_total_val * 100.0) if prev_total_val > 0 else 0.0

        sv_day_pl_aed_str = f"AED {sv_day_pl_aed:,.0f}"
        sv_day_pl_pct_str = f"{sv_day_pl_pct:+.2f}%"
        sv_total_pl_aed_str = f"AED {sv_total_pl_aed:,.0f}"
        sv_total_pl_pct_str = f"{sv_total_pl_pct:+.2f}%"
        sv_total_val_aed_str = f"AED {sv_total_val_aed:,.0f}"
        sv_total_val_inr_lacs_str = fmt_inr_lacs_from_aed(sv_total_val_aed, AED_TO_INR)

        # Layout: 3 columns for 3 cards (RESTORED)
        c1, c2, c3 = st.columns(3)

        # Card 1: Today's Profit
        with c1:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TODAY'S PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_day_pl_aed_str}</div>
                    <div class="kpi-number">{sv_day_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 2: Total Profit
        with c2:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL PROFIT</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_pl_aed_str}</div>
                    <div class="kpi-number">{sv_total_pl_pct_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        # Card 3: Total Holding Value
        with c3:
            st.markdown(f"""
            <div class="card mf-card">
                <div class="kpi-label">TOTAL HOLDING</div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{sv_total_val_aed_str}</div>
                    <div class="kpi-number">{sv_total_val_inr_lacs_str}</div>
                </div>
                <div class="kpi-label">US STOCKS</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            """<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:4px 0;">Today's Gains – SV</div>""",
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
        
        # --- NEW SECTION: SV HOLDINGS CARDS (FIXED LOOP) ---
        st.markdown(
            """<div style="font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#16233a; font-size:0.75rem; margin:14px 0 4px 0;">SV Holdings</div>""",
            unsafe_allow_html=True,
        )
        
        # Sort by Total Profit High to Low
        sorted_sv = sv_positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base Label Style
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_sv:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            
            # Explicit SV Label
            units_str = f"{units:,.0f} UNITS • SV"
            
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # Determine Color Class
            color_class = "kpi-green" if pl_aed >= 0 else "kpi-red"
            
            # Clean Name
            display_name = name.upper().replace(" [SV]", "")

            # Render HTML Card with Explicit Class Logic
            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_pct_str}</div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

# ---------- US STOCKS TAB (NEW) ----------

with us_tab:
    if positions.empty:
        st.info("No US positions found.")
    else:
        # 3. INDIVIDUAL STOCK CARDS (REDESIGNED)
        # Sorted by Total Profit AED Descending
        sorted_pos = positions.sort_values(by="TotalPLAED", ascending=False).to_dict('records')
        
        # Base Label Style to allow color override (avoids the class .kpi-label color conflict)
        base_label_style = "font-family:'Space Grotesk',sans-serif; font-size:0.6rem; font-weight:400; text-transform:uppercase; margin:0;"
        
        for row in sorted_pos:
            name = row["Name"]
            ticker = row["Ticker"]
            units = row["Units"]
            val_aed = row["ValueAED"]
            pl_aed = row["TotalPLAED"]
            pl_pct = row["TotalPct"]
            owner = row["Owner"]
            
            # Label Update for SV
            suffix = " • SV" if owner == "SV" else ""
            units_str = f"{units:,.0f} UNITS{suffix}"
            
            val_aed_str = f"AED {val_aed:,.0f}"
            pl_aed_str = f"{'+ ' if pl_aed >= 0 else ''}AED {pl_aed:,.0f}"
            pl_pct_str = f"{pl_pct:+.2f}%"
            
            # Determine Color Class
            color_class = "kpi-green" if pl_aed >= 0 else "kpi-red"
            
            # Clean Name
            display_name = name.upper().replace(" [SV]", "")

            # NEW CARD LAYOUT with Explicit Class Logic
            html_card = f"""
<div class="card mf-card">
<div class="kpi-top-row">
<div class="kpi-label">{units_str}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_aed_str}</div>
</div>
<div class="kpi-mid-row">
<div class="kpi-number">{display_name}</div>
<div class="kpi-number">{val_aed_str}</div>
</div>
<div class="kpi-top-row">
<div class="kpi-label" style="color:#9ba7b8 !important;">{ticker}</div>
<div class="{color_class}" style="{base_label_style} font-weight:600;">{pl_pct_str}</div>
</div>
</div>
"""
            st.markdown(html_card, unsafe_allow_html=True)

# ---------- INDIA MF TAB ----------


with mf_tab:
    if not MF_CONFIG:
        st.info("No mutual fund data configured.")
    else:
        # Load NAVs from AMFI (Official API)
        mf_navs = load_mf_navs_from_amfi()
        mf_rows = []
        for mf_entry in MF_CONFIG:
            scheme = mf_entry["Scheme"]
            units = float(mf_entry["Units"] or 0.0)
            cost_inr = float(mf_entry["CostINR"] or 0.0)
            file_value_inr = float(mf_entry.get("InitialValueINR", 0.0))

            live_nav = mf_navs.get(scheme)

            # Safety check logic REMOVED - Trust Live Data if available
            value_inr = file_value_inr
            if live_nav is not None and live_nav > 0 and units > 0:
                candidate_value = live_nav * units
                value_inr = candidate_value
            
            # Absolute return
            if cost_inr > 0:
                abs_return = (value_inr - cost_inr) / cost_inr * 100.0
            else:
                abs_return = 0.0

            mf_rows.append(
                {
                    "scheme": scheme,
                    "value_inr": value_inr,
                    "return_pct": abs_return,
                }
            )

        mf_rows.sort(key=lambda r: r["value_inr"], reverse=True)
        total_value_inr = sum(r["value_inr"] for r in mf_rows)
        mf_total_cost = sum(item["CostINR"] for item in MF_CONFIG)
        
        if mf_total_cost > 0:
            total_abs_return_pct = (total_value_inr - mf_total_cost) / mf_total_cost * 100.0
        else:
            total_abs_return_pct = 0.0

        total_value_str = fmt_inr_lacs(total_value_inr)
        total_return_str = f"{total_abs_return_pct:.2f}%"

        st.markdown(
            f"""
            <div class="card mf-card">
                <div class="kpi-top-row">
                    <div class="kpi-label">VALUE</div>
                    <div class="kpi-label">RETURN</div>
                </div>
                <div class="kpi-mid-row">
                    <div class="kpi-number">{total_value_str}</div>
                    <div class="kpi-number">{total_return_str}</div>
                </div>
                <div class="kpi-label">PORTFOLIO AGGREGATE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for row in mf_rows:
            scheme = row["scheme"]
            value_inr = row["value_inr"]
            ret_pct = row["return_pct"]

            display_name = scheme
            parts = display_name.split()
            if parts and all(ch.isdigit() or ch in "/-" for ch in parts[-1]):
                display_name = " ".join(parts[:-1])
            if "Fund Growth" in display_name:
                display_name = display_name.replace(" Fund Growth", "")

            value_str = fmt_inr_lacs(value_inr)
            ret_str = f"{ret_pct:.1f}%"

            st.markdown(
                f"""
                <div class="card mf-card">
                    <div class="kpi-top-row">
                        <div class="kpi-label">VALUE</div>
                        <div class="kpi-label">RETURN</div>
                    </div>
                    <div class="kpi-mid-row">
                        <div class="kpi-number">{value_str}</div>
                        <div class="kpi-number">{ret_str}</div>
                    </div>
                    <div class="kpi-label">{display_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
