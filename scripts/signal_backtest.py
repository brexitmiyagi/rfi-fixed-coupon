# Does the discount signal make money as a strategy? Each month-end from 2016, rank the funds by the pre-2016
# model's expected discount change, go long the top five and short the bottom five, and measure the change in
# log(1 + discount) of each side. Versions: hold one month with no gap (this picks up last week's noise reversing),
# skip one month then hold one, and skip one month then hold twelve, rebalanced once a year (four start months).
# This measures the discount leg only. Distributions and NAV moves aren't in it; a real trade would hedge the NAV side.
from common import *
import numpy as np
import discount_panel as dp

O = dp.build(dp.U.ticker)
O["ym"] = O.date.dt.to_period("M")
W = O.dropna(subset=["fwd"])
tr = W[W.date + pd.Timedelta(days=366) < pd.Timestamp("2016-01-01")]
b = dp.fit(tr)
me = O.groupby(["ticker", "ym"]).last().reset_index()
me["s"] = b[0] + b[1] * me.d + b[2] * me.dev
disc = me.pivot(index="ym", columns="ticker", values="d")
sig = me.pivot(index="ym", columns="ticker", values="s")
months = list(disc.index)


def leg(i, skip, hold, k=5):
    if i + skip + hold >= len(months):
        return None
    s = sig.iloc[i].dropna()
    a, z = disc.iloc[i + skip], disc.iloc[i + skip + hold]
    ok = s.index[a[s.index].notna() & z[s.index].notna()]
    if len(ok) < 12:
        return None
    s = s[ok].sort_values(ascending=False)
    r = np.log(1 + z[ok] / 100) - np.log(1 + a[ok] / 100)
    return (r[s.index[:k]].mean() - r[s.index[-k:]].mean()) * 100


start = months.index(pd.Period("2016-01"))
lines = []
for name, skip, hold in [("no gap, hold 1 month", 0, 1), ("skip 1, hold 1 month", 1, 1)]:
    v = np.array([x for x in (leg(i, skip, hold) for i in range(start, len(months))) if x is not None])
    lines.append(f"{name}: {len(v)} months, {v.mean()*12:+.2f} pts a year, t {v.mean()/(v.std(ddof=1)/len(v)**0.5):.2f}, positive {np.mean(v>0)*100:.0f}%")
for off in (0, 3, 6, 9):
    v = np.array([x for x in (leg(i, 1, 12) for i in range(start + off, len(months), 12)) if x is not None])
    lines.append(f"skip 1, hold 12, start month +{off}: {len(v)} years, mean {v.mean():+.2f} pts, t {v.mean()/(v.std(ddof=1)/len(v)**0.5):.2f}, positive {np.sum(v>0)} of {len(v)}")
save("signal_backtest.txt", "\n".join(lines) + "\n")
