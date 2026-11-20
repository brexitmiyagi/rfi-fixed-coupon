# Would the simulation have told the truth in the past? Standing at each month-end from January 2005 to
# October 2025, rebuild RFI's simulation using only what was known then: 12-month windows that had already
# finished, the REIT return those windows averaged, a NAV-on-REITs fit and an RFI-only discount model fitted on
# the same past windows (no Welltower shock). Then check where the actual next-12-month total return from the
# price landed in the predicted distribution. A well-calibrated model puts 5% of outcomes below its 5th
# percentile, 50% inside its 25th-75th range, and so on.
from common import *
import numpy as np, warnings
warnings.filterwarnings("ignore")
import importlib.util
src = open(os.path.join(HERE, "joint_simulation.py")).read().split("vr = pd.read_csv")[0]
ns = {"__file__": os.path.join(HERE, "joint_simulation.py")}
exec(compile(src, "joint_head", "exec"), ns)
weekly_fund, B = ns["weekly_fund"], ns["B"]

w = weekly_fund("RFI")
dv = dists().set_index("ex_date").amount
m = w.groupby(w.index.to_period("M")).last()
m["bench"] = B.reindex(m.index)
idx = list(m.index)
rows = []
for i in range(len(m) - 12):
    a, b = m.iloc[i], m.iloc[i + 12]
    if np.isnan(a.m3) or np.isnan(a.bench) or np.isnan(b.bench):
        continue
    paid = dv[(dv.index > w.index[w.index.to_period("M") == idx[i]][-1]) & (dv.index <= w.index[w.index.to_period("M") == idx[i + 12]][-1])].sum()
    rows.append(dict(start=idx[i], end=idx[i + 12], nav_tr=(b.tri / a.tri - 1) * 100, bench=(b.bench / a.bench - 1) * 100,
                     d0=a.disc, dev0=a.disc - a.m3, d1=b.disc, nav0=a.nav, price0=a.price, price1=b.price, paid=paid,
                     price_tr=((b.price + paid) / a.price - 1) * 100))
H = pd.DataFrame(rows)
G = pd.read_csv(os.path.join(RESULTS, "reit_yield_gap_monthly.csv"), parse_dates=["date"])
G["ym"] = G.date.dt.to_period("M")
G = G.set_index("ym")


def valuation_E(now_ym):
    # what a valuation-aware analyst could have assumed then: the median forward REIT return of months since
    # 1990 whose yield gap was within 1 pt of that month's gap and whose 12-month outcome was already known
    if now_ym not in G.index:
        return None
    g = G.loc[now_ym, "gap"]
    known = G[(G.index >= pd.Period("1990-01")) & (G.index <= now_ym - 12)].dropna(subset=["fwd12"])
    near = known[(known.gap - g).abs() <= 1]
    return near.fwd12.median() if len(near) >= 12 else None


rng = np.random.default_rng(7)
out = []
for _, now in H[(H.start >= pd.Period("2005-01")) & (H.start <= pd.Period("2025-10"))].iterrows():
    past = H[H.end <= now.start]
    if len(past) < 60:
        continue
    X = np.column_stack([np.ones(len(past)), past.bench])
    cn = np.linalg.lstsq(X, past.nav_tr, rcond=None)[0]
    rn = past.nav_tr - X @ cn
    Xd = np.column_stack([np.ones(len(past)), past.d0, past.dev0])
    cd = np.linalg.lstsq(Xd, past.d1 - past.d0, rcond=None)[0]
    rd = (past.d1 - past.d0) - Xd @ cd
    k = rng.integers(len(past), size=4000)
    d1 = now.d0 + cd[0] + cd[1] * now.d0 + cd[2] * now.dev0 + rd.values[k]
    pay = now.paid   # the payout actually declared over the year (known in advance for a level-paying fund)
    rec = dict(start=str(now.start), actual=now.price_tr)
    for tag, E in [("", past.bench.mean()), ("v_", valuation_E(now.start))]:
        if E is None:
            E = past.bench.mean()
        nav_tr = cn[0] + cn[1] * (E + past.bench.values[k] - past.bench.mean()) + rn.values[k]
        p1 = (now.nav0 * (1 + nav_tr / 100) - pay) * (1 + d1 / 100)
        tot = ((p1 + pay) / now.price0 - 1) * 100
        pct = np.percentile(tot, [5, 25, 50, 75, 95])
        rec.update({tag + "E": E, tag + "p5": pct[0], tag + "p25": pct[1], tag + "p50": pct[2], tag + "p75": pct[3], tag + "p95": pct[4],
                    tag + "edge_mean": np.mean(tot - (E + past.bench.values[k] - past.bench.mean()))})
    rec["bench_actual"] = now.bench
    out.append(rec)
C = pd.DataFrame(out)
C.round(2).to_csv(os.path.join(RESULTS, "simulation_calibration.csv"), index=False)
jan = C[C.start.str.endswith("-01")]


def cover(c, tag=""):
    p = lambda k: c[tag + k]
    return (f"{len(c)} forecasts: below 5th pct {np.mean(c.actual < p('p5'))*100:.0f}% (should be 5), below 25th {np.mean(c.actual < p('p25'))*100:.0f}% (25), "
            f"inside 25th-75th {np.mean((c.actual >= p('p25')) & (c.actual <= p('p75')))*100:.0f}% (50), above 75th {np.mean(c.actual > p('p75'))*100:.0f}% (25), above 95th {np.mean(c.actual > p('p95'))*100:.0f}% (5); "
            f"median forecast {p('p50').median():.1f}% vs median outcome {c.actual.median():.1f}%; mean absolute miss of the median {np.mean(np.abs(c.actual - p('p50'))):.1f} pts")
lines = ["REITs assumed to repeat their past average:",
         "  every month-end, January 2005 to October 2025 (overlapping years): " + cover(C), "  January starts only (separate years): " + cover(jan),
         "REIT return set the valuation-aware way (post-1990 median at a similar yield gap, using only outcomes known at the time):",
         "  every month-end: " + cover(C, "v_"), "  January starts only: " + cover(jan, "v_")]
# How far off, and on which part? Split each miss of the valuation-aware median into the REIT market's miss
# (actual REIT return minus the assumed one) and everything else. Then the miss on the edge over REITs alone.
C["miss"] = C.actual - C.v_p50
C["reit_miss"] = C.bench_actual - C.v_E
C["edge_actual"] = C.actual - C.bench_actual
C["edge_miss"] = C.edge_actual - C.v_edge_mean
q = lambda x: "/".join(f"{v:+.1f}" for v in np.percentile(x, [10, 25, 50, 75, 90]))
lines += ["Misses of the valuation-aware forecast (actual minus forecast; 10/25/50/75/90th percentiles, all 250 month-ends):",
          f"  total return vs forecast median: {q(C.miss)}; mean {C.miss.mean():+.1f}",
          f"  REIT market vs the assumed REIT return: {q(C.reit_miss)}; mean {C.reit_miss.mean():+.1f}",
          f"  RFI's edge over REITs vs the forecast edge: {q(C.edge_miss)}; mean {C.edge_miss.mean():+.1f}; forecast edge mean {C.v_edge_mean.mean():+.1f}, actual edge mean {C.edge_actual.mean():+.1f}, median {C.edge_actual.median():+.1f}",
          f"  same, January starts only: total {q(jan.actual - jan.v_p50)}; edge miss median {(jan.actual - jan.bench_actual - jan.v_edge_mean).median():+.1f}"]
C.round(2).to_csv(os.path.join(RESULTS, "simulation_calibration.csv"), index=False)
save("simulation_calibration.txt", "\n".join(lines) + "\n")
