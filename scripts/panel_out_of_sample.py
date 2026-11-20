# Out-of-sample test of the discount model. Fit on fund-weeks whose one-year-forward date falls before 2016,
# test on fund-weeks starting in 2016 or later. Reports out-of-sample R2 against a no-change forecast, the
# calibration of actual on predicted changes, quintiles, direction hits, and what the model would say for RFI
# under the pre-2016 fit, the calibrated pre-2016 fit and a post-2016 fit.
from common import *
import numpy as np
import discount_panel as dp

s = snap()
O = dp.build(dp.U.ticker).merge(dp.U, on="ticker")
W = O.dropna(subset=["fwd"]).copy()
W["fdate"] = W.date + pd.Timedelta(days=366)
cut = pd.Timestamp("2016-01-01")
tr, te = W[W.fdate < cut], W[W.date >= cut]
b_tr, b_te = dp.fit(tr), dp.fit(te)
pred = lambda b, d: b[0] + b[1] * d.d + b[2] * d.dev
p, y = pred(b_tr, te), te.fwd - te.d
r2 = 1 - ((y - p) ** 2).sum() / (y ** 2).sum()
cal = np.polyfit(p, y, 1)
q = pd.qcut(p, 5, labels=False)
big = p.abs() > 1
rfi = O[O.ticker == "RFI"].iloc[-1]
d0 = (s["rfi_close"] / s["rfi_nav"] - 1) * 100
dev0 = d0 - rfi.m
C = te[(te.d >= d0 - 2) & (te.d <= d0 + 2) & (te.dev <= -6)]
lines = [
    f"train {len(tr):,} fund-weeks (forward date before 2016), test {len(te):,} (start 2016 or later)",
    f"pre-2016 fit: {b_tr[0]:.4f} {b_tr[1]:+.4f} d {b_tr[2]:+.4f} dev; post-2016 fit: {b_te[0]:.4f} {b_te[1]:+.4f} d {b_te[2]:+.4f} dev",
    f"out-of-sample R2 vs no change: {r2:.3f}; correlation {np.corrcoef(p, y)[0,1]:.3f}; actual = {cal[1]:.2f} + {cal[0]:.2f} x predicted",
    f"direction right when |predicted| > 1 pt: {(np.sign(p[big]) == np.sign(y[big])).mean()*100:.1f}% of {big.sum():,}",
    "quintiles (predicted mean, actual mean): " + "; ".join(f"{p[q==k].mean():+.2f}/{y[q==k].mean():+.2f}" for k in range(5)),
    f"RFI-like test cases: {len(C)}; model said {(C.d + pred(b_tr, C)).mean():.2f}% a year on, actual mean {C.fwd.mean():.2f}%, median {C.fwd.median():.2f}%",
    f"RFI now ({d0:.2f}%, {dev0:.2f} below its average): full-sample model {d0 + pred(np.array([0.2822,-0.0923,-0.32]), pd.Series(dict(d=d0, dev=dev0))):.2f}%, "
    f"post-2016 fit {d0 + pred(b_te, pd.Series(dict(d=d0, dev=dev0))):.2f}%, calibrated pre-2016 {d0 + cal[1] + cal[0]*pred(b_tr, pd.Series(dict(d=d0, dev=dev0))):.2f}%",
]
save("panel_out_of_sample.txt", "\n".join(lines) + "\n")
