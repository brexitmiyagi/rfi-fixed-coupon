# Price target, a bias-corrected range for the HOLD call, and the discount at which RFI only matches REITs.
# simulation_calibration.py found the simulation's optimism came from the REIT market assumption (REITs did
# worse than the valuation-aware estimate, by 5.9 points a year on average), while RFI's edge over REITs was
# forecast without bias. So the correction is to lower the REIT assumption by that average miss and rerun RFI's
# simulation exactly as joint_simulation.py does. The edge over REITs, and so the fair-value discount, is
# unaffected by that shift.
from common import *
import numpy as np, warnings
warnings.filterwarnings("ignore")
src = open(os.path.join(HERE, "joint_simulation.py")).read().split("vr = pd.read_csv")[0]
ns = {"__file__": os.path.join(HERE, "joint_simulation.py")}
exec(compile(src, "joint_head", "exec"), ns)
weekly_fund, B, PANEL, FUNDS, WELL_SD, WELL_INDEX = (ns[k] for k in ["weekly_fund", "B", "PANEL", "FUNDS", "WELL_SD", "WELL_INDEX"])
s = snap()
f = FUNDS["RFI"]
C = pd.read_csv(os.path.join(RESULTS, "simulation_calibration.csv"))
reit_miss = (C.bench_actual - C.v_E).mean()
base_E = 4.84   # post-1990 months within 1 pt of the Nov 20 yield gap (reit_valuation_return.txt); 5.68 on Nov 18

w = weekly_fund("RFI")
m = w.groupby(w.index.to_period("M")).last()
m["bench"] = B.reindex(m.index)
rows = []
for i in range(len(m) - 12):
    a, b = m.iloc[i], m.iloc[i + 12]
    if np.isnan(a.m3) or np.isnan(a.bench) or np.isnan(b.bench):
        continue
    pred = a.disc + PANEL[0] + PANEL[1] * a.disc + PANEL[2] * (a.disc - a.m3)
    rows.append(dict(nav_tr=(b.tri / a.tri - 1) * 100, bench=(b.bench / a.bench - 1) * 100, disc_miss=b.disc - pred))
H = pd.DataFrame(rows)
X = np.column_stack([np.ones(len(H)), H.bench])
coef = np.linalg.lstsq(X, H.nav_tr, rcond=None)[0]
H["nav_resid"] = H.nav_tr - X @ coef
d0 = (f["price"] / f["nav"] - 1) * 100
pred0 = d0 + PANEL[0] + PANEL[1] * d0 + PANEL[2] * (d0 - w.m3.iloc[-1])
over = f["well_pct"] - coef[1] * WELL_INDEX


def sim(E, seed=42, N=20000):
    rng = np.random.default_rng(seed)
    k = rng.integers(len(H), size=N)
    shock = rng.normal(0, WELL_SD, N) * over / 100
    bench = E + (H.bench.values[k] - H.bench.mean())
    nav1 = f["nav"] * (1 + (coef[0] + coef[1] * bench + H.nav_resid.values[k] + shock) / 100) - f["payout"]
    d1 = np.clip(pred0 + (H.disc_miss.values - H.disc_miss.mean())[k], -60, 40)
    p1 = nav1 * (1 + d1 / 100)
    return p1, nav1, bench


rows = []
lines = [f"mean miss of the REIT assumption in the real-time test: {reit_miss:+.2f} pts a year",
         f"RFI: NAV beta {coef[1]:.2f}; discount {d0:.2f}% -> model {pred0:.2f}%"]
for name, E in [("base, as published", base_E), ("bias-corrected", base_E + reit_miss)]:
    p1, nav1, bench = sim(E)
    tot = (p1 + f["payout"]) / f["price"] * 100 - 100
    q = np.percentile(tot, [5, 25, 50, 75, 95])
    lines.append(f"{name} (REITs {E:+.2f}%): expected NAV ${nav1.mean():.2f}, expected price ${p1.mean():.2f} (median ${np.median(p1):.2f}); "
                 f"total return mean {tot.mean():+.1f}%, 5/25/50/75/95th {'/'.join(f'{x:+.1f}' for x in q)}; loss {np.mean(tot<0)*100:.0f}%; "
                 f"vs the 10-year {s['ust_10y']:.2f}%: {tot.mean()-s['ust_10y']:+.1f} pts; edge over REITs {np.mean(tot-bench):+.1f} pts, beats REITs {np.mean(tot>bench)*100:.0f}%")
    rows.append(dict(case=name, reits=E, exp_price=p1.mean(), exp_total=tot.mean(), p5=q[0], p25=q[1], p50=q[2], p75=q[3], p90=np.percentile(tot, 90),
                     prob_loss=np.mean(tot < 0) * 100, prob_beat=np.mean(tot > bench) * 100, edge=np.mean(tot - bench)))
    fair_px = np.mean(p1 + f["payout"]) / (1 + np.mean(bench) / 100)
    lines.append(f"   price at which RFI's expected return equals REITs': ${fair_px:.2f}, a discount of {(fair_px/f['nav']-1)*100:.1f}% to today's NAV")
    px2 = np.mean(p1 + f["payout"]) / (1 + (np.mean(bench) + 2) / 100)
    lines.append(f"   price at which RFI's expected edge over REITs is +2 pts (OVERWEIGHT/NEUTRAL line): ${px2:.2f}, a discount of {(px2/f['nav']-1)*100:.1f}%")
    for target_disc in [-10.1, -13.1]:
        px = f["nav"] * (1 + target_disc / 100)
        tt = (p1 + f["payout"]) / px * 100 - 100
        lines.append(f"   bought at {target_disc}% (${px:.2f}): mean {tt.mean():+.1f}%, median {np.median(tt):+.1f}%, 5th {np.percentile(tt,5):+.1f}%, loss {np.mean(tt<0)*100:.0f}%, edge {np.mean(tt-bench):+.1f} pts, beats REITs {np.mean(tt>bench)*100:.0f}%")
pd.DataFrame(rows).round(3).to_csv(os.path.join(RESULTS, "price_target.csv"), index=False)
# How much rides on the size of the correction (bias_correction_check.py): the target and the two comparisons at
# no correction, the average, and the ends of its 95% interval, plus the correction at which RFI's expected return
# just equals the 10-year (the line between HOLD and BUY on my definitions).
bc = pd.read_csv(os.path.join(RESULTS, "bias_correction_check.csv")).iloc[0]
lines.append("sensitivity to the correction:")
for lab, c in [("none", 0.0), ("95% interval, small end", bc.ci_high), ("average (used)", bc.average_miss), ("95% interval, large end", bc.ci_low)]:
    p1, nav1, bench = sim(base_E + c)
    tot = (p1 + f["payout"]) / f["price"] * 100 - 100
    lines.append(f"   {lab} ({c:+.1f}): target ${p1.mean():.2f}, total return {tot.mean():+.1f}%, vs 10-year {tot.mean()-s['ust_10y']:+.1f} pts, vs REITs {np.mean(tot-bench):+.1f} pts, beats REITs {np.mean(tot>bench)*100:.0f}%")
lo_c, hi_c = -20.0, 5.0
for _ in range(40):
    mid = (lo_c + hi_c) / 2
    p1, nav1, bench = sim(base_E + mid)
    if ((p1 + f["payout"]) / f["price"] * 100 - 100).mean() > s["ust_10y"]:
        hi_c = mid
    else:
        lo_c = mid
lines.append(f"   correction at which RFI's expected return equals the 10-year: {mid:+.2f} pts (REITs {base_E+mid:+.2f}%)")
# Where the corrected case clears the 10-year. The expected price a year out depends on NAV and the discount
# forecast, not on what you pay, so the break-even entry price is (expected price + payout) / (1 + 10-year).
bc_row = pd.read_csv(os.path.join(RESULTS, "price_target.csv")).iloc[1]
be_px = (bc_row.exp_price + f["payout"]) / (1 + s["ust_10y"] / 100)
lines.append(f"corrected case clears the {s['ust_10y']}% 10-year below ${be_px:.2f}, a discount of {(be_px/f['nav']-1)*100:.1f}% to today's NAV (the 10.1% buy line sits below that)")
save("price_target.txt", "\n".join(lines) + "\n")

# Chart data: the spread of 12-month total returns in the corrected case, in 5-point buckets, plus the
# share of runs that beat REITs and the 10-year (the chart in the trade section).
p1, nav1, bench = sim(base_E + bc.average_miss)
tot = (p1 + f["payout"]) / f["price"] * 100 - 100
edges = np.arange(-60, 85, 5)
h, _ = np.histogram(np.clip(tot, edges[0], edges[-1] - 0.01), bins=edges)
pd.DataFrame({"bucket": [f"{a:+d} to {b:+d}%" for a, b in zip(edges[:-1], edges[1:])], "from": edges[:-1],
              "share_of_runs_pct": (h / h.sum() * 100).round(2)}).to_csv(os.path.join(RESULTS, "charts", "c22_corrected_distribution.csv"), index=False)
save("price_target_distribution.txt", f"corrected case: mean {tot.mean():+.1f}%, median {np.median(tot):+.1f}%, "
     f"5th {np.percentile(tot,5):+.1f}%, 95th {np.percentile(tot,95):+.1f}%, below zero {(tot<0).mean()*100:.0f}%, "
     f"above the {s['ust_10y']}% 10-year {(tot>s['ust_10y']).mean()*100:.0f}%, above REITs {(tot>bench).mean()*100:.0f}%\n")
