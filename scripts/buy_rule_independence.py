# Two problems with the buy-rule backtest, checked here.
# 1. Overlap. "Separate episodes" in buy_rule_backtest.py only need 60 days between them, so their 12-month
#    windows share most of their months. Here an episode only counts if it starts at least 365 days after the
#    last counted one, so no two windows share a month.
# 2. Regime. Today the REIT dividend yield is below the 10-year. Were any of the buy-rule weeks like that?
#    Gap = Nareit All Equity dividend yield at the previous month-end minus the 10-year at that month-end.
from common import *
import numpy as np, warnings
warnings.filterwarnings("ignore")

T = pd.read_csv(os.path.join(RESULTS, "buy_rule_backtest.csv"), parse_dates=["date"])
v = pd.read_excel(os.path.join(DATA, "nareit", "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
assert str(v.iloc[6, 27]).strip() == "Dividend"
n = pd.DataFrame({"date": pd.to_datetime(v[0], errors="coerce"), "yld": pd.to_numeric(v[27], errors="coerce")}).dropna()
n["ym"] = n.date.dt.to_period("M")
t10 = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"])
t10["DGS10"] = pd.to_numeric(t10.DGS10, errors="coerce")
t10 = t10.dropna().groupby(t10.observation_date.dt.to_period("M")).DGS10.last()
gap = (n.set_index("ym").yld - t10).dropna()
T["gap"] = (T.date.dt.to_period("M") - 1).map(gap)


def independent(sub):
    keep, last = [], None
    for _, r in sub.iterrows():
        if last is None or (r.date - last).days >= 365:
            keep.append(r)
            last = r.date
    return pd.DataFrame(keep)


lines = []
for th in [-8, -10.07, -10.1, -12]:
    sub = T[T.disc <= th]
    ep = independent(sub)
    lines.append(f"discount {th}% or wider: {len(sub)} weeks, {len(ep)} non-overlapping episodes; beat REITs in {int((ep.edge>0).sum())}, "
                 f"lost money in {int((ep.rfi<0).sum())}; median RFI {ep.rfi.median():+.1f}%, median edge {ep.edge.median():+.1f} pts")
    for _, r in ep.iterrows():
        lines.append(f"   {r.date.date()} disc {r.disc:.1f}%  gap {r.gap:+.2f}  RFI {r.rfi:+.1f}%  REITs {r.reits:+.1f}%")
    lines.append(f"   weeks in this set with the REIT yield below the 10-year: {int((sub.gap<0).sum())}; lowest gap {sub.gap.min():+.2f}")
neg = T[T.gap < 0]
lines.append(f"all weeks with the gap below zero: {len(neg)} ({neg.date.min().date() if len(neg) else '-'} to {neg.date.max().date() if len(neg) else '-'}); "
             f"widest discount among them {neg.disc.min():.1f}%; RFI median {neg.rfi.median():+.1f}%, beat REITs {np.mean(neg.edge>0)*100:.0f}%")
lo = T[T.gap < 1]
lines.append(f"weeks with the gap below +1 point: {len(lo)}; with discount -8% or wider among them: {int((lo.disc<=-8).sum())}; "
             f"of those, median RFI {lo[lo.disc<=-8].rfi.median():+.1f}%, beat REITs {np.mean(lo[lo.disc<=-8].edge>0)*100:.0f}%")
for lo_g, hi_g in [(-9, 0), (0, 2), (2, 4), (4, 99)]:
    s2 = T[(T.gap >= lo_g) & (T.gap < hi_g)]
    if len(s2) > 20:
        b = np.polyfit(s2.disc, s2.edge, 1)[0]
        lines.append(f"gap {lo_g} to {hi_g}: {len(s2)} weeks, discount range {s2.disc.min():.1f}% to {s2.disc.max():.1f}%, "
                     f"edge per 1 pt wider discount {-b:+.2f} pts")
T.round(3).to_csv(os.path.join(RESULTS, "buy_rule_independence.csv"), index=False)
save("buy_rule_independence.txt", "\n".join(lines) + "\n")
