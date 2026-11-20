# The buy rule tested on RFI's own history: every week since 1996 that RFI's discount was at or beyond a
# threshold, what did the next 12 months return (price plus distributions), and how did that compare with the
# FTSE Nareit All Equity REITs total return over the same months (VNQ only exists from 2004, so the index stands
# in for it)? Thresholds -8%, -10.07% (where the carry covers the fee), -10.1% (the rounded line I quote) and -12%, plus all weeks for comparison.
# Shown for every qualifying week and for separate episodes (first qualifying week after at least 60 days out).
from common import *
import numpy as np, warnings
warnings.filterwarnings("ignore")

w = weekly()
w["disc"] = (w.price / w.nav - 1) * 100
dv = dists().set_index("ex_date").amount
v = pd.read_excel(os.path.join(DATA, "nareit", "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
tri = pd.Series(pd.to_numeric(v[23], errors="coerce").values, index=pd.to_datetime(v[0], errors="coerce")).dropna()
tri.index = tri.index.to_period("M")
rows = []
dates = w.index
for i, d in enumerate(dates):
    j = dates.searchsorted(d + pd.Timedelta(days=364))
    if j >= len(dates) or (dates[j] - d).days > 371:
        continue
    e = dates[j]
    paid = dv[(dv.index > d) & (dv.index <= e)].sum()
    rt = ((w.price.iloc[j] + paid) / w.price.iloc[i] - 1) * 100
    a, b = d.to_period("M") - 1, e.to_period("M") - 1   # month-ends bracketing the window (index is month-end)
    if a not in tri.index or b not in tri.index:
        continue
    rows.append(dict(date=d, disc=w.disc.iloc[i], rfi=rt, reits=(tri[b] / tri[a] - 1) * 100))
T = pd.DataFrame(rows)
T["edge"] = T.rfi - T.reits


def episodes(sub):
    keep, last = [], None
    for _, r in sub.iterrows():
        if last is None or (r.date - last).days > 60:
            keep.append(r)
        last = r.date
    return pd.DataFrame(keep)


lines = [f"{len(T)} weekly starts, {T.date.iloc[0].date()} to {T.date.iloc[-1].date()}"]
for name, sub in [("all weeks", T), ("discount -8% or wider", T[T.disc <= -8]), ("discount -10.07% or wider", T[T.disc <= -10.07]), ("discount -10.1% or wider", T[T.disc <= -10.1]), ("discount -12% or wider", T[T.disc <= -12])]:
    lines.append(f"{name}: {len(sub)} weeks; RFI median {sub.rfi.median():+.1f}%, mean {sub.rfi.mean():+.1f}%, lost money {np.mean(sub.rfi<0)*100:.0f}%; "
                 f"beat REITs {np.mean(sub.edge>0)*100:.0f}%, median edge {sub.edge.median():+.1f} pts")
    if name != "all weeks" and len(sub):
        ep = episodes(sub)
        lines.append(f"   separate episodes: {len(ep)}; RFI median {ep.rfi.median():+.1f}%, beat REITs in {int((ep.edge>0).sum())} of {len(ep)}; "
                     + ", ".join(f"{r.date.date()} ({r.disc:.1f}%): {r.rfi:+.0f}% vs {r.reits:+.0f}%" for _, r in ep.iterrows()))
T.round(2).to_csv(os.path.join(RESULTS, "buy_rule_backtest.csv"), index=False)
save("buy_rule_backtest.txt", "\n".join(lines) + "\n")
