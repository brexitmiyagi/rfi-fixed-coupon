# Survivorship check on the discount model. The panel in discount_panel.py only has funds alive today. Here I add
# 35 real estate, MLP, infrastructure and preferred CEFs that merged, liquidated or delisted, using the year-end
# and half-year NAV and market price printed in their own annual and semi-annual reports (dead_fund_points.py
# builds data/cef_panel_dead/dead_points.csv from EDGAR), and what happened at the end (Form N-8F, in
# data/cef_panel_dead/dead_funds.csv).
# Dead funds only have two points a year, so everything here is run on June and December points for the live funds
# too (the last weekly price in each month), with the same model as the weekly panel:
#   fwd - d = a + b*d + c*(d - average of the fund's points over the prior 3 years, at least 3 of them, since dead funds mostly have one a year)
# fwd = the discount 12 months later (point within 45 days of that date).
# The end of a dead fund counts as one more observation: start = its last point 6 to 18 months before delisting,
# fwd = 0 if holders got NAV (liquidation, or a merger into an open-end fund or ETF), or the acquiring fund's
# discount on the delisting date if it merged into another listed CEF. Funds whose end I couldn't price are left out
# of that step only.
from common import *
import numpy as np
import discount_panel as dp

s = snap()
D_NOW = (s["rfi_close"] / s["rfi_nav"] - 1) * 100
P = os.path.join(DATA, "cef_panel_dead")
fates = pd.read_csv(os.path.join(P, "dead_funds.csv"), parse_dates=["delisted"]).fillna({"into": ""})
dead = pd.read_csv(os.path.join(P, "dead_points.csv"), parse_dates=["date"])[["ticker", "date", "disc"]]
cat = dict(zip(fates.ticker, fates.category))
cat.update(dict(zip(dp.U.ticker, dp.U.cef_connect_category)))


def semiannual(t):
    w = dp.load(t)
    w = w[w.date.dt.month.isin([6, 12])]
    w = w.groupby([w.date.dt.year, w.date.dt.month]).last().reset_index(drop=True)
    w["date"] = w.date + pd.offsets.MonthEnd(0)
    w["ticker"] = t
    return w[["ticker", "date", "disc"]]


live = pd.concat([semiannual(t) for t in dp.U.ticker])


def pairs(pts, kind):
    out = []
    for t, g in pts.sort_values("date").groupby("ticker"):
        g = g.reset_index(drop=True)
        for i, r in g.iterrows():
            past = g[(g.date < r.date) & (g.date >= r.date - pd.DateOffset(months=36))]
            if len(past) < 3:
                continue
            tgt = r.date + pd.DateOffset(months=12)
            f = g[(g.date - tgt).abs() <= pd.Timedelta(days=45)]
            out.append(dict(ticker=t, date=r.date, d=r.disc, dev=r.disc - past.disc.mean(), fwd=f.disc.iloc[0] if len(f) else np.nan, kind=kind))
    return pd.DataFrame(out)


def disc_on(t, day):
    if t in dp.U.ticker.values or os.path.exists(os.path.join(DATA, "cef_panel", t + ".json")):
        w = dp.load(t)
        w = w[w.date <= day]
        return w.disc.iloc[-1] if len(w) and (day - w.date.iloc[-1]).days <= 14 else np.nan
    g = dead[(dead.ticker == t)]
    g = g.iloc[(g.date - day).abs().argsort()[:1]]
    return g.disc.iloc[0] if len(g) and abs((g.date.iloc[0] - day).days) <= 92 else np.nan


Lp = pairs(live, "live")
Dp = pairs(dead, "dead, while listed")
term = []
for _, f in fates.iterrows():
    if pd.isna(f.delisted) or f.fate == "not checked":
        continue
    g = dead[(dead.ticker == f.ticker)]
    g = g[(g.date <= f.delisted - pd.DateOffset(months=6)) & (g.date >= f.delisted - pd.DateOffset(months=18))]
    if not len(g):
        continue
    end = 0.0 if f.fate != "merger" else disc_on(f.into, f.delisted)
    if np.isnan(end):
        continue
    r = g.iloc[-1]
    hist = dead[(dead.ticker == f.ticker) & (dead.date < r.date) & (dead.date >= r.date - pd.DateOffset(months=36))]
    if len(hist) < 3:
        hist_dev = np.nan
    else:
        hist_dev = r.disc - hist.disc.mean()
    term.append(dict(ticker=f.ticker, date=r.date, d=r.disc, dev=hist_dev, fwd=end, kind="dead, at the end", fate=f.fate, into=f.into, delisted=f.delisted.date()))
T = pd.DataFrame(term)
A = pd.concat([Lp, Dp, T.drop(columns=["fate", "into", "delisted"])], ignore_index=True)
A["category"] = A.ticker.map(cat)
A.to_csv(os.path.join(RESULTS, "survivorship_pairs.csv"), index=False)
T.to_csv(os.path.join(RESULTS, "survivorship_terminal.csv"), index=False)

rfi = live[live.ticker == "RFI"].sort_values("date")
dev_now = D_NOW - rfi[rfi.date >= rfi.date.iloc[-1] - pd.DateOffset(months=36)].disc.iloc[:-1].mean()
lines = [f"live funds: {Lp.ticker.nunique()} funds, {Lp.fwd.notna().sum()} half-year pairs; dead funds: {Dp.ticker.nunique()} funds with usable points, "
         f"{Dp.fwd.notna().sum()} pairs while listed, {len(T)} priced endings ({(T.fwd==0).sum()} at NAV, {(T.fwd!=0).sum()} into another CEF)",
         f"RFI on this half-year basis: discount {D_NOW:.2f}%, {dev_now:.2f} pts from its average of the last 3 years' June/December points"]
for name, X in [("live only (what the article used)", A[A.kind == "live"]), ("live + dead while listed", A[A.kind != "dead, at the end"]), ("live + dead incl. their endings", A)]:
    for per, Y in [("all years", X), ("start 2016+", X[X.date >= "2016-01-01"])]:
        Y = Y.dropna(subset=["fwd", "dev"])
        b = dp.fit(Y)
        pred = D_NOW + b[0] + b[1] * D_NOW + b[2] * dev_now
        C = Y[(Y.d >= D_NOW - 2) & (Y.d <= D_NOW + 2) & (Y.dev <= -6)]
        lines.append(f"{name}, {per}: {len(Y)} pairs, {Y.ticker.nunique()} funds; fit {b[0]:.3f} {b[1]:+.4f} d {b[2]:+.4f} dev; RFI in a year {pred:.2f}%; "
                     f"RFI-like cases {len(C)}: median a year later {C.fwd.median():.2f}%, narrower {np.mean(C.fwd > C.d)*100:.0f}%")
lines.append("endings (start point -> value at the end):")
for _, r in T.sort_values("delisted").iterrows():
    lines.append(f"  {r.ticker} {r.date.date()} {r.d:+.1f}% -> {r.fwd:+.1f}% ({r.fate}{' into ' + r.into if r.into else ''}, delisted {r.delisted})")
lines.append(f"endings: median start {T.d.median():+.1f}%, median end {T.fwd.median():+.1f}%, narrowed in {int((T.fwd > T.d).sum())} of {len(T)}; "
             f"live pairs starting at -6% or wider narrowed {np.mean(Lp[Lp.d<=-6].dropna().pipe(lambda x: x.fwd > x.d))*100:.0f}% of the time")
save("survivorship_check.txt", "\n".join(lines) + "\n")
