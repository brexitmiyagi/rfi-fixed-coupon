# What the four stocks that paid for the check trade at, on each company's own 2026 guidance.
from common import *

v = pd.read_csv(os.path.join(DATA, "lookthrough_valuation_2026_11_20.csv"))
v["mid"] = (v.metric_2026_low + v.metric_2026_high) / 2
v["multiple"] = v.price_2026_11_20 / v["mid"]
v["earnings_yield_pct"] = v["mid"] / v.price_2026_11_20 * 100
v["div_yield_pct"] = v.annual_dividend / v.price_2026_11_20 * 100
h = pd.read_csv(os.path.join(RESULTS, "nport_holdings_panel.csv"))
cus = {"WELL": "95040Q104", "DLR": "253868103", "EQIX": "29444U700", "IRM": "46284V101"}
last = h.date.max()
v["weight_jun30_pct"] = v.ticker.map(lambda t: h[(h.date == last) & (h.cusip == cus[t])].pct.sum())
v.round(2).to_csv(os.path.join(RESULTS, "lookthrough_valuation.csv"), index=False)
s = snap()
wy = (v.weight_jun30_pct * v.earnings_yield_pct).sum() / v.weight_jun30_pct.sum()
# Welltower's weight today if the fund still holds the June 30 shares (the September N-PORT isn't out yet)
w = pd.read_csv(os.path.join(RESULTS, "welltower_position.csv")).iloc[-1]
well_px = v.set_index("ticker").loc["WELL", "price_2026_11_20"]
sh = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)["shares_outstanding_2026_06_30"]
w_now = w.units * well_px / (s["rfi_nav"] * sh) * 100
lines = [v[["ticker", "metric", "mid", "multiple", "earnings_yield_pct", "div_yield_pct", "weight_jun30_pct"]].round(2).to_string(index=False),
         f"combined June 30 weight {v.weight_jun30_pct.sum():.2f}%, weighted cash-earnings yield {wy:.2f}% vs 10-year {s['ust_10y']}%",
         f"Welltower now if unchanged since June 30: {w.units:,.0f} x ${well_px} = ${w.units*well_px/1e6:.2f}m, about {w_now:.1f}% of NAV (June 30 share count)",
         f"a 20% fall in Welltower takes about {w_now*0.2:.2f}% off NAV = ${s['rfi_nav']*w_now*0.002:.2f} a share",
         f"hedge: shorting Welltower worth {w_now:.1f}% of NAV is {w_now*s['rfi_nav']/s['rfi_close']:.1f}% of the money you put into RFI at ${s['rfi_close']}"]
save("lookthrough_valuation.txt", "\n".join(lines) + "\n")
