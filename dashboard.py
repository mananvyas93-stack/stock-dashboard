hm_sv = sv_positions.copy()
hm_sv["Name"] = hm_sv["Name"].str.replace(r"\s*\[SV\]", "", regex=True)

# Tile size is absolute day P&L in AED
hm_sv["SizeForHeatmap"] = hm_sv["DayPLAED"].abs() + 1e-6

def label_for_sv(v: float) -> str:
    if v >= 0:
        return f"AED {v:,.0f}"
    else:
        return f"[AED {abs(v):,.0f}]"

# This is what gets printed on the tile
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
    ...
)
