# What a move in the 10-year does to RFI. Monthly NAV total return and monthly change in the discount regressed on
# the monthly change in the 10-year (FRED DGS10), Newey-West errors. Then the 10-year to 6% (+93 bp) and to 4% (-107 bp)
# as one-off shocks. Two samples: since 1997 and since RFI went back to monthly payouts (October 2016).
from common import *
import numpy as np, warnings
import statsmodels.api as sm
warnings.filterwarnings("ignore")

s = snap()
w = weekly()
w["tri"] = nav_total_return_index(w)
w["disc"] = (w.price / w.nav - 1) * 100
m = w.groupby(w.index.to_period("M")).last()
t10 = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"])
t10["DGS10"] = pd.to_numeric(t10.DGS10, errors="coerce")
m["t10"] = t10.dropna().groupby(t10.observation_date.dt.to_period("M")).DGS10.last()
m["nav_r"] = m.tri.pct_change() * 100
m["d_disc"] = m.disc.diff()
m["d_t10"] = m.t10.diff()
m = m.dropna()
shocks = {"10-year to 6.00%": 6.00 - s["ust_10y"], "10-year to 4.00%": 4.00 - s["ust_10y"]}
out, lines = [], []
for start in ["1997-01", "2016-10"]:
    d = m[m.index >= pd.Period(start)]
    for y, lab in [("nav_r", "NAV total return, %"), ("d_disc", "discount change, pts")]:
        f = sm.OLS(d[y], sm.add_constant(d.d_t10)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
        b, t, lo, hi = f.params.d_t10, f.tvalues.d_t10, *f.conf_int().loc["d_t10"]
        out.append(dict(sample=start, y=lab, per_100bp=b, t=t, lo=lo, hi=hi, r2=f.rsquared, months=len(d)))
        lines.append(f"since {start} ({len(d)} months): {lab} per 1 pt rise in the 10-year {b:+.2f} (t {t:.2f}, 95% {lo:+.2f} to {hi:+.2f}, R2 {f.rsquared:.2f})")
O = pd.DataFrame(out)
O.round(3).to_csv(os.path.join(RESULTS, "rate_sensitivity.csv"), index=False)
for name, dy in shocks.items():
    for start in ["1997-01", "2016-10"]:
        bn = O[(O["sample"] == start) & (O.y.str.startswith("NAV"))].per_100bp.iloc[0]
        bd = O[(O["sample"] == start) & (O.y.str.startswith("disc"))].per_100bp.iloc[0]
        nav1 = s["rfi_nav"] * (1 + bn * dy / 100)
        disc1 = (s["rfi_close"] / s["rfi_nav"] - 1) * 100 + bd * dy
        lines.append(f"{name} ({dy:+.2f} pts), betas since {start}: NAV ${nav1:.2f} ({bn*dy:+.1f}%), discount {disc1:.2f}%, price ${nav1*(1+disc1/100):.2f}")
save("rate_sensitivity.txt", "\n".join(lines) + "\n")
