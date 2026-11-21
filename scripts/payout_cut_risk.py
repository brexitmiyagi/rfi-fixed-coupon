# How close is the $0.96 to being cut? Two parts.
# 1. History: the payout as a % of NAV every week since 1996, and where it stood when the board cut in March 2009.
# 2. Simulation: bootstrap RFI's own monthly NAV total returns (1996-2026, in 12-month blocks so bad years stay
#    together), pay $0.08 a month out of NAV, and count how often payout/NAV crosses the levels history gives.
from common import *
import numpy as np

w = weekly()
s = snap()
nav0 = s["rfi_nav"]


def annual_rate(d):
    # regular rate in force, from the distribution history: $0.96 to 2002, ~$1.00 in 2003-04, $1.32 from 2005,
    # $1.35 from April 2007, $0.60 a year (quarterly) from March 2009, $0.50 from June 2009, $0.88 from
    # September 2010, $0.96 from September 2014 (monthly again from October 2016)
    for start, r in [("2014-09-01", 0.96), ("2010-09-01", 0.88), ("2009-06-01", 0.50), ("2009-03-01", 0.60),
                     ("2007-04-01", 1.35), ("2005-01-01", 1.32), ("2003-01-01", 1.00)]:
        if d >= pd.Timestamp(start):
            return r
    return 0.96


w["rate"] = [annual_rate(d) for d in w.index]
w["payout_nav"] = w.rate / w.nav * 100
pre_cut = w.loc["2008-06":"2009-02", "payout_nav"]
since = w.loc["2009-07":, "payout_nav"]
post_max, post_week = since.max(), since.idxmax().date()
before = w.loc[:"2008-05", "payout_nav"]
no_cut_max = max(before.max(), since.max())
no_cut_week = (since.idxmax() if since.max() >= before.max() else before.idxmax()).date()

tri = nav_total_return_index(w)
m = tri.resample("ME").last().pct_change().dropna()
m = m[m.index >= "1996-12-31"]
blocks = [m.iloc[i:i + 12].values for i in range(0, len(m) - 11)]
rng = np.random.default_rng(1993)
N, H = 20000, 36
first_cross, first_18, nav13 = [], [], []
for _ in range(N):
    path = np.concatenate([blocks[rng.integers(len(blocks))] for _ in range(H // 12)])
    nav, fc, f18 = nav0, None, None
    for k, r in enumerate(path):
        nav = nav * (1 + r) - PAYOUT / 12
        pn = PAYOUT / nav * 100 if nav > 0 else 999
        if fc is None and pn >= no_cut_max:
            fc = k + 1
        if f18 is None and pn >= 18:
            f18 = k + 1
        if k == 12:
            nav13.append(nav)
    first_cross.append(fc or 99)
    first_18.append(f18 or 99)
fc, f18 = np.array(first_cross), np.array(first_18)
c13, hit10, hit18 = (fc <= 13).sum(), (fc <= 36).sum(), (f18 <= 36).sum()
low13 = nav13
lines = [
    f"payout/NAV on Nov 20: {PAYOUT/nav0*100:.2f}% at NAV ${nav0:.2f}",
    f"March 2009 cut ($1.35 to $0.60 a year): payout/NAV ran {pre_cut.min():.1f}% to {pre_cut.max():.1f}% from June 2008 to February 2009",
    f"highest payout/NAV before June 2008, when the run-up to the cut began: {before.max():.2f}% (week of {before.idxmax().date()}); threshold used below: {no_cut_max:.2f}%",
    f"since the 2009 reset the high was {post_max:.2f}% (week of {post_week}), no cut",
    f"NAV at which $0.96 is {no_cut_max:.2f}% of NAV: ${PAYOUT/(no_cut_max/100):.2f} ({(PAYOUT/(no_cut_max/100)/nav0-1)*100:.1f}% from here); at 18%: ${PAYOUT/0.18:.2f}",
    f"monthly NAV total returns used: {len(m)} months, {m.index[0].date()} to {m.index[-1].date()}, mean {m.mean()*12*100:.1f}% a year",
    f"simulated, {N:,} paths: payout/NAV reaches {no_cut_max:.2f}% within 13 months in {c13/N*100:.1f}% of paths; within 3 years {hit10/N*100:.1f}%; reaches 18% within 13 months {(f18 <= 13).sum()/N*100:.1f}%, within 3 years {hit18/N*100:.1f}%",
    f"simulated NAV after 13 months: median ${np.median(low13):.2f}, 10th percentile ${np.percentile(low13,10):.2f}, 90th ${np.percentile(low13,90):.2f}",
]
save("payout_cut_risk.txt", "\n".join(lines) + "\n")
