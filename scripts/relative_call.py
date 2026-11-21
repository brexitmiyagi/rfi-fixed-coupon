# The relative call (OVERWEIGHT vs REITs) taken apart, and the alternatives a REIT allocator actually has.
# 1. Where RFI's expected edge over REITs comes from, in the corrected case (price_target.py): rerun the same
#    simulation with the discount held where it is (no narrowing), then also with the manager's historical NAV
#    edge (the intercept of NAV on REITs) set to zero. What's left is the carry of buying the payout below NAV
#    plus RFI's beta below 1. Also the case where the discount ends at the post-2016 median for RFI-like funds.
# 2. Welltower scenarios: Welltower's 12-month total return fixed at -30%, 0% and +20%. The REIT index moves by
#    Welltower's 11.08% weight times the surprise, RFI's NAV moves with its beta to that index plus its extra
#    Welltower (14.3% of NAV minus beta x 11.08%) times Welltower's return over the index. Discount as in the model.
# 3. Alternatives over the same ten years (2016-2025), from each fund's own prospectus (data/alternatives_2025.csv)
#    and RFI's annual reports, and their expected edge over REITs going forward on the same footing.
import runpy, numpy as np
from common import *
ns = runpy.run_path(os.path.join(HERE, "price_target.py"))
sim, f, g = ns["sim"], ns["f"], ns["sim"].__globals__
E = ns["base_E"] + pd.read_csv(os.path.join(RESULTS, "bias_correction_check.csv")).average_miss.iloc[0]
d0, pred_model, coef0 = (f["price"] / f["nav"] - 1) * 100, g["pred0"], g["coef"].copy()


def run(pred=None, alpha=None):
    g["pred0"] = pred_model if pred is None else pred
    g["coef"] = coef0.copy()
    if alpha is not None:
        g["coef"][0] = alpha
    p1, nav1, bench = sim(E)
    tot = (p1 + f["payout"]) / f["price"] * 100 - 100
    g["pred0"], g["coef"] = pred_model, coef0.copy()
    return tot, bench, p1, nav1


lines = [f"corrected case, REITs {E:+.2f}%; discount today {d0:.2f}%, model a year out {pred_model:.2f}%; NAV intercept {coef0[0]:+.2f}, beta {coef0[1]:.2f}"]
t_full, b, p_full, _ = run()
t_nn, b2, p_nn, _ = run(pred=d0)
t_na, b3, _, _ = run(pred=d0, alpha=0.0)
e = lambda t, bb: np.mean(t - bb)
beta_part = (coef0[1] - 1) * np.mean(b3)
lines += [f"edge over REITs {e(t_full,b):+.2f} pts = discount narrowing {e(t_full,b)-e(t_nn,b2):+.2f} + manager's NAV edge {e(t_nn,b2)-e(t_na,b3):+.2f} "
          f"+ beta below 1 {beta_part:+.2f} + carry and the rest {e(t_na,b3)-beta_part:+.2f}"]
cases = [("model: discount narrows to %.1f%%" % pred_model, None), ("discount stays at today's %.2f%%" % d0, d0), ("post-2016 median for RFI-like cases, -8.88%", -8.88)]
rows = []
for lab, pr in cases:
    t, bb, p1, _ = run(pred=pr)
    rows.append(dict(case=lab, target=p1.mean(), total=t.mean(), edge=e(t, bb), beats=np.mean(t > bb) * 100))
    lines.append(f"{lab}: target ${p1.mean():.2f}, total return {t.mean():+.1f}%, edge {e(t,bb):+.1f} pts, beats REITs {np.mean(t>bb)*100:.0f}%")
pd.DataFrame(rows).round(2).to_csv(os.path.join(RESULTS, "relative_call_cases.csv"), index=False)

# Welltower scenarios
WI = g["WELL_INDEX"] / 100
over = g["over"] / 100
rng = np.random.default_rng(42)
H = g["H"]
k = rng.integers(len(H), size=20000)
bench0 = E + (H.bench.values[k] - H.bench.mean())
d1 = np.clip(pred_model + (H.disc_miss.values - H.disc_miss.mean())[k], -60, 40)
wrows = []
for X in (-30.0, 0.0, 20.0):
    bench = bench0 + WI * (X - E)
    nav_tr = coef0[0] + coef0[1] * bench + H.nav_resid.values[k] + over * (X - bench)
    nav1 = f["nav"] * (1 + nav_tr / 100) - f["payout"]
    p1 = nav1 * (1 + d1 / 100)
    t = (p1 + f["payout"]) / f["price"] * 100 - 100
    wrows.append(dict(welltower=X, reits=bench.mean(), nav=nav1.mean(), target=p1.mean(), total=t.mean(), edge=np.mean(t - bench), beats=np.mean(t > bench) * 100))
    lines.append(f"Welltower {X:+.0f}%: REITs {bench.mean():+.1f}%, RFI NAV ${nav1.mean():.2f}, price ${p1.mean():.2f}, total return {t.mean():+.1f}%, edge {np.mean(t-bench):+.1f} pts, beats REITs {np.mean(t>bench)*100:.0f}%")
pd.DataFrame(wrows).round(2).to_csv(os.path.join(RESULTS, "welltower_scenarios.csv"), index=False)

# Alternatives, 2016-2025
a = pd.read_csv(os.path.join(DATA, "annual_report_returns_vs_benchmark.csv"))
a = a[a.period.astype(str).isin([str(y) for y in range(2016, 2026)])]
geo = lambda c: (np.prod(1 + a[c].astype(float) / 100) ** 0.1 - 1) * 100
w = weekly()
dv = dists().set_index("ex_date").amount
ws = w[(w.index > "2015-12-15") & (w.index <= "2025-12-31")]
u = 1.0
for p, q in zip(ws.index[:-1], ws.index[1:]):
    u *= (ws.price[q] + dv[(dv.index > p) & (dv.index <= q)].sum()) / ws.price[p]
yrs = (ws.index[-1] - ws.index[0]).days / 365.25
alt = pd.read_csv(os.path.join(DATA, "alternatives_2025.csv"))
lines.append(f"2016-2025, a year: RFI share price {(u**(1/yrs)-1)*100:.2f}% ({ws.index[0].date()} to {ws.index[-1].date()}, discount {(ws.price.iloc[0]/ws.nav.iloc[0]-1)*100:.1f}% -> "
             f"{(ws.price.iloc[-1]/ws.nav.iloc[-1]-1)*100:.1f}%), RFI NAV {geo('nav_total_return'):.2f}% (fee 0.94%, about 20% preferreds), FTSE Nareit {geo('nareit_equity_index'):.2f}%")
for _, r in alt.iterrows():
    lines.append(f"  {r.ticker}: {r.ret_10y:.2f}% vs {r.benchmark} {r.bench_10y:.2f}% (after-fee edge {r.ret_10y-r.bench_10y:+.2f}); net fee {r.net_expense_ratio_pct:.2f}%")
csr = alt[alt.ticker == "CSRSX"].iloc[0]
vnq = alt[alt.ticker == "VNQ"].iloc[0]
lines.append(f"forward edge over REITs, a year: RFI {e(t_full,b):+.1f} (discount narrows) / {rows[2]['edge']:+.1f} (stays wide); "
             f"Cohen & Steers Realty Shares about {csr.ret_10y-csr.bench_10y:+.1f} if it repeats its ten-year record (5-year: {csr.ret_5y-csr.bench_5y:+.1f}); "
             f"VNQ plus Welltower to RFI's weight about {-vnq.net_expense_ratio_pct:+.1f} (the fee; the simulation gives Welltower no expected edge)")
save("relative_call.txt", "\n".join(lines) + "\n")
