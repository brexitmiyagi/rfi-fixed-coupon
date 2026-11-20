# What buying at a discount is worth when the payout is a fixed dollar amount.
# If the discount stays where it is, price return = NAV total return + D/P - D/N.
from common import *

s = snap()
P, N = s["rfi_close"], s["rfi_nav"]
f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
fee = f["expense_ratio_2025_pct"]
yop, yon = PAYOUT / P * 100, PAYOUT / N * 100
carry = yop - yon
fee_neutral_pn = 1 / (1 + fee / yon)
lines = [
    f"yield on price {yop:.2f}%, payout on NAV {yon:.2f}%, carry {carry:.2f} pts a year vs expense ratio {fee}%",
    f"discount where carry equals the fee: {(fee_neutral_pn-1)*100:.2f}% (price ${N*fee_neutral_pn:.2f} on today's NAV)",
]
# buyback: the board authorised 10% for 2026 and bought none in H1
sh = f["shares_outstanding_2026_06_30"]
bought = 0.10 * sh
gain = bought * (N - P)
lines.append(f"10% buyback at today's price: {bought/1e6:.3f}m shares, NAV gain ${gain/1e6:.2f}m = ${gain/(sh-bought):.3f} a remaining share")
# yield-buyer lens
spread = yop - s["ust_10y"]
w = weekly()
y = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
w["y10"] = pd.to_numeric(y, errors="coerce").ffill().reindex(w.index, method="ffill")
hist = (PAYOUT / w.price * 100 - w.y10)["2016-10":]
lines.append(f"yield on price minus 10-year: {spread:.2f} pts; weekly since Oct 2016 median {hist.median():.2f}, share of weeks below today {(hist<spread).mean()*100:.0f}%")
lines.append(f"price at the median spread with the 10-year at {s['ust_10y']}%: ${PAYOUT/((hist.median()+s['ust_10y'])/100):.2f}")
# The 12-month target is in scenarios.py now. An earlier draft used RFI's own 8 episodes (median -1.37% a year later);
# the 36-fund panel in discount_panel.py says that was too generous, so it's kept here only for comparison.
own = N * (1 - 1.0 / 100) * (1 - 1.37 / 100)
lines.append(f"for comparison only, RFI's own-episode median (-1.37%) on a 1% lower NAV would give ${own:.2f}")
lines.append(f"carry-only buy level (fee fully covered): {(fee_neutral_pn-1)*100:.2f}% discount = ${N*fee_neutral_pn:.2f} on today's NAV")
rows = []
for nav_chg in [-10, -5, 0, 5]:
    for d in [-10.63, -8.65, -7.22, -3.48]:
        n1 = N * (1 + nav_chg / 100); p1 = n1 * (1 + d / 100)
        rows.append((nav_chg, d, round(p1, 2), round(((p1 + PAYOUT) / P - 1) * 100, 1)))
sc = pd.DataFrame(rows, columns=["nav_change_pct", "discount_pct", "price", "total_return_pct"])
sc.to_csv(os.path.join(RESULTS, "scenarios.csv"), index=False)
lines.append(sc.pivot(index="nav_change_pct", columns="discount_pct", values="total_return_pct").to_string())
save("carry_and_target.txt", "\n".join(lines) + "\n")
