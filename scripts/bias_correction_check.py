# Does the -5.9 pt correction punish the same thing twice? The real-time REIT assumption was usually high in
# 2005-2025 (REITs looked cheap against bonds), and today's is already low (4.8%). If the miss was mostly a
# high-assumption problem, today's correction should be smaller. Three checks on the 250 month-ends in
# simulation_calibration.csv (overlapping 12-month windows, so Newey-West errors with 12 lags):
#   1. regress the miss (actual REIT return minus the assumed one) on the assumption itself
#   2. regress it on the starting yield gap (REIT dividend yield minus the 10-year)
#   3. the average miss in months that started like today, with REITs yielding less than the 10-year
# Each also run without June 2006 to December 2008, so one crash can't carry it.
from common import *
import numpy as np, statsmodels.api as sm

C = pd.read_csv(os.path.join(RESULTS, "simulation_calibration.csv"))
G = pd.read_csv(os.path.join(RESULTS, "reit_yield_gap_monthly.csv"), parse_dates=["date"])
G["start"] = G.date.dt.to_period("M").astype(str)
C = C.merge(G[["start", "gap"]], on="start", how="left")
C["miss"] = C.bench_actual - C.v_E
E_NOW, GAP_NOW = 4.84, -1.15   # Nov 20: reit_valuation_return.txt
hac = dict(cov_type="HAC", cov_kwds={"maxlags": 12})
lines = [f"{len(C)} month-ends, {C.start.min()} to {C.start.max()}; assumption ranged {C.v_E.min():.1f}% to {C.v_E.max():.1f}%, gap {C.gap.min():+.2f} to {C.gap.max():+.2f}"]
m0 = sm.OLS(C.miss, np.ones(len(C))).fit(**hac)
lo, hi = m0.conf_int().iloc[0]
lines.append(f"average miss {m0.params.iloc[0]:+.2f} pts (95% interval {lo:+.1f} to {hi:+.1f}, Newey-West)")
for label, D in [("all months", C), ("without Jun 2006-Dec 2008", C[~C.start.between("2006-06", "2008-12")])]:
    for x, now in [("v_E", E_NOW), ("gap", GAP_NOW)]:
        m = sm.OLS(D.miss, sm.add_constant(D[x])).fit(**hac)
        p = m.get_prediction(np.array([[1, now]])).summary_frame(alpha=0.05)
        lines.append(f"{label}: miss on {'the assumption' if x == 'v_E' else 'the yield gap'}: slope {m.params[x]:+.2f} (t {m.tvalues[x]:+.2f}), "
                     f"R2 {m.rsquared:.3f}; at today's {now:+.2f} the fitted miss is {p['mean'].iloc[0]:+.1f} (95% {p['mean_ci_lower'].iloc[0]:+.1f} to {p['mean_ci_upper'].iloc[0]:+.1f})"
                     + (" [outside the sample range]" if (x == "v_E" and now < D.v_E.min()) else ""))
q = C.groupby(pd.qcut(C.v_E, 4)).miss.agg(["mean", "median", "size"])
lines.append("miss by quarter of the assumption (lowest first): " + "; ".join(f"{i.left:.1f}-{i.right:.1f}%: mean {r['mean']:+.1f}, median {r['median']:+.1f}" for i, r in q.iterrows()))
neg = C[C.gap < 0]
mn = sm.OLS(neg.miss, np.ones(len(neg))).fit(**hac)
lines.append(f"months starting with REITs yielding less than the 10-year: {len(neg)}, average miss {neg.miss.mean():+.2f} "
             f"(95% {mn.conf_int().iloc[0,0]:+.1f} to {mn.conf_int().iloc[0,1]:+.1f}); without 2006-08: {neg[~neg.start.between('2006-06','2008-12')].miss.mean():+.2f}")
pd.DataFrame({"average_miss": [m0.params.iloc[0]], "ci_low": [lo], "ci_high": [hi], "negative_gap_miss": [neg.miss.mean()]}).round(3).to_csv(
    os.path.join(RESULTS, "bias_correction_check.csv"), index=False)
save("bias_correction_check.txt", "\n".join(lines) + "\n")
