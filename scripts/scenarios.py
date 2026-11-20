# Bear, base and bull for the next 12 months, each built from a measured distribution rather than a single guess.
#   REIT market: the 25th, 50th and 75th percentile year of RFI's own blended benchmark, 2005-2025 (annual reports).
#   Manager: bear = no skill (lose the 0.94% fee) and Welltower falls 20% more than the index, which costs the
#            overweight; base = the 2005-2025 average net excess; bull = the 2017-2025 average net excess.
#   Discount a year out: 25th, 50th and 75th percentile of the 1,028 comparable fund-weeks (results/discount_panel.txt).
# Probabilities 25/50/25. NAV in a year = NAV x (1 + total return) - $0.96 paid out.
from common import *
import numpy as np
import warnings
warnings.filterwarnings("ignore")

s = snap()
P0, N0 = s["rfi_close"], s["rfi_nav"]
r = pd.read_csv(os.path.join(DATA, "annual_report_returns_vs_benchmark.csv"), dtype={"period": str})
full = r[r.period != "2026H1"].copy()
full["excess"] = full.nav_total_return - full.blended_benchmark
bench = np.percentile(full.blended_benchmark, [25, 50, 75])
exc_all = full.excess.mean()
exc_late = full[full.period.astype(int) >= 2017].excess.mean()
caps = pd.read_csv(os.path.join(DATA, "nareit", "nareit_constituent_caps.csv"))
well_idx = caps.welltower_musd.iloc[-1] / caps.equity_reits_total_musd.iloc[-1] * 100   # Oct 30, 2026
well_rfi = (13.8 + 14.8) / 2        # today's range, results/house_bet.txt
overweight = well_rfi - 0.8 * well_idx  # the benchmark is 80% equity REITs
wh = -overweight * 0.20
disc = [-10.63, -7.22, -3.48]       # results/discount_panel.txt
FEE = 0.94
cases = {
    "bear": dict(p=0.25, bench=bench[0], excess=-FEE + wh, disc=disc[0]),
    "base": dict(p=0.50, bench=bench[1], excess=exc_all, disc=disc[1]),
    "bull": dict(p=0.25, bench=bench[2], excess=exc_late, disc=disc[2]),
}
rows = []
for k, c in cases.items():
    tr = c["bench"] + c["excess"]
    nav1 = N0 * (1 + tr / 100) - PAYOUT
    p1 = nav1 * (1 + c["disc"] / 100)
    tot = (p1 + PAYOUT) / P0 - 1
    rows.append(dict(case=k, prob=c["p"], reit_market=round(c["bench"], 2), manager_vs_benchmark=round(c["excess"], 2),
                     nav_total_return=round(tr, 2), nav_in_12m=round(nav1, 2), discount=c["disc"], price_in_12m=round(p1, 2),
                     total_return=round(tot * 100, 1), vs_benchmark=round(tot * 100 - c["bench"], 1)))
S = pd.DataFrame(rows)
S.to_csv(os.path.join(RESULTS, "scenarios_weighted.csv"), index=False)
ev_p = (S.prob * S.price_in_12m).sum()
ev_t = (S.prob * ((S.price_in_12m + PAYOUT) / P0 - 1)).sum() * 100
ev_b = (S.prob * S.reit_market).sum()
ev_at = lambda px: (S.prob * ((S.price_in_12m + PAYOUT) / px - 1)).sum() * 100
from_lo, from_hi = 9.0, 13.0
for _ in range(60):
    mid = (from_lo + from_hi) / 2
    from_lo, from_hi = (mid, from_hi) if ev_at(mid) > ev_b else (from_lo, mid)
breakeven = mid
entry = [(px, ev_at(px), ev_at(px) - ev_b) for px in (9.94, 10.29, 10.45, 10.82)]
# a stress case outside the weights: the 10th percentile benchmark year (2008-type years sit below it),
# bear-case manager, and the 10th percentile discount
b10 = np.percentile(full.blended_benchmark, 10)
nav_s = N0 * (1 + (b10 - FEE + wh) / 100) - PAYOUT
p_s = nav_s * (1 - 13.01 / 100)
lines = [
    f"benchmark years 2005-2025, 25th/50th/75th percentile: {bench[0]:.2f}% / {bench[1]:.2f}% / {bench[2]:.2f}%",
    f"manager net excess: 2005-2025 average {exc_all:+.2f} pts, 2017-2025 average {exc_late:+.2f} pts",
    f"Welltower: RFI ~{well_rfi:.1f}% of NAV vs {0.8*well_idx:.2f}% in the benchmark (80% x {well_idx:.2f}% of All Equity REITs on Oct 30, 2026); 20% relative fall costs {wh:.2f} pts",
    S.to_string(index=False),
    f"probability-weighted price in 12 months: ${ev_p:.2f}; total return {ev_t:.1f}% vs {ev_b:.1f}% for the benchmark in the same cases; edge {ev_t-ev_b:+.1f} pts",
    "entry price -> weighted 12-month total return, and edge over the benchmark: " + "; ".join(f"${px:.2f}: {e:.1f}% ({x:+.1f} pts)" for px, e, x in entry),
    f"entry price where the weighted return equals the benchmark's: ${breakeven:.2f}",
    f"stress (not weighted): benchmark {b10:.2f}% (10th percentile year), manager {(-FEE+wh):.2f}, discount -13.01% -> NAV ${nav_s:.2f}, price ${p_s:.2f}, total {((p_s+PAYOUT)/P0-1)*100:.1f}%",
]
save("scenarios_weighted.txt", "\n".join(lines) + "\n")
