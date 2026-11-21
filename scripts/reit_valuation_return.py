# What should the base case expect from REITs, given where they're priced? Monthly since 1990:
# forward 12-month total return of FTSE Nareit All Equity REITs regressed on the starting gap between the index's
# dividend yield and the 10-year Treasury. Overlapping 12-month windows, so standard errors are Newey-West (12 lags).
from common import *
import numpy as np, warnings
import statsmodels.api as sm
warnings.filterwarnings("ignore")

s = snap()
v = pd.read_excel(os.path.join(DATA, "nareit", "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
assert str(v.iloc[5, 22]).strip() == "All Equity REITs" and str(v.iloc[6, 27]).strip() == "Dividend"
n = pd.DataFrame({"date": pd.to_datetime(v[0], errors="coerce"), "tri": pd.to_numeric(v[23], errors="coerce"),
                  "yld": pd.to_numeric(v[27], errors="coerce")}).dropna()
n["ym"] = n.date.dt.to_period("M")
t10 = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"])
t10["DGS10"] = pd.to_numeric(t10.DGS10, errors="coerce")
t10 = t10.dropna().groupby(t10.observation_date.dt.to_period("M")).DGS10.last()
n["t10"] = n.ym.map(t10)
n = n.dropna().reset_index(drop=True)
n["gap"] = n.yld - n.t10
n["fwd12"] = (n.tri.shift(-12) / n.tri - 1) * 100
gap_now = 3.77 - s["ust_10y"]   # Nareit All Equity dividend yield Oct 30, 2026 vs the 10-year on Nov 20
out = []
for start in ["1972-01", "1990-01", "2000-01"]:
    d = n[(n.ym >= pd.Period(start)) & n.fwd12.notna()]
    m = sm.OLS(d.fwd12, sm.add_constant(d.gap)).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    p = m.get_prediction(np.array([[1, gap_now]])).summary_frame(alpha=0.05)
    near = d[(d.gap - gap_now).abs() <= 1.0]
    out.append(dict(start=start, months=len(d), slope=m.params.gap, slope_t=m.tvalues.gap, r2=m.rsquared,
                    uncond_mean=d.fwd12.mean(), uncond_median=d.fwd12.median(), pred=p["mean"].iloc[0],
                    pred_lo=p["mean_ci_lower"].iloc[0], pred_hi=p["mean_ci_upper"].iloc[0],
                    near_n=len(near), near_median=near.fwd12.median(), gap_min=d.gap.min()))
O = pd.DataFrame(out)
O.round(3).to_csv(os.path.join(RESULTS, "reit_valuation_return.csv"), index=False)
n[["date", "yld", "t10", "gap", "fwd12"]].round(3).to_csv(os.path.join(RESULTS, "reit_yield_gap_monthly.csv"), index=False)
lines = [f"REIT dividend yield 3.77% (Oct 30, 2026) minus the 10-year {s['ust_10y']}% (Nov 20) = {gap_now:+.2f} pts"]
below = (n.gap <= gap_now).mean() * 100
lines.append(f"months since {n.date.iloc[0].date()} with a gap this low or lower: {below:.1f}%; lowest {n.gap.min():+.2f} ({n.loc[n.gap.idxmin(),'date'].date()})")
for r in out:
    lines.append(f"since {r['start']}: {r['months']} months, fwd 12m return = a + {r['slope']:.2f} x gap (t {r['slope_t']:.2f}, R2 {r['r2']:.2f}); unconditional mean {r['uncond_mean']:.2f}%, median {r['uncond_median']:.2f}%; "
                 f"at today's gap {r['pred']:.2f}% (95% {r['pred_lo']:.2f} to {r['pred_hi']:.2f}); months within 1 pt of today's gap: {r['near_n']}, median fwd {r['near_median']:.2f}%; lowest gap in sample {r['gap_min']:+.2f}")
save("reit_valuation_return.txt", "\n".join(lines) + "\n")
