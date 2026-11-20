# Does a wide discount close? Not just RFI's 8 episodes: every real estate, preferred, MLP and infrastructure/utility
# CEF on CEF Connect, weekly, since each fund's first price.
# For each fund-week: d = discount, m = the fund's own average discount over the prior 156 weeks (needs 104),
# dev = d - m, and fwd = the discount 361-371 days later.
# Model: fwd - d = a + b*d + c*dev, pooled OLS. Confidence interval: resample calendar years with replacement
# (1,000 times), because funds move together within a year.
# Data: data/cef_panel/<TICKER>.json is CEF Connect's /api/v3/pricinghistory/<TICKER>/All. If a file is missing the
# script downloads it. The list of funds is data/cef_panel/universe.csv (CEF Connect categories, November 2026).
# Only funds alive today are in it, so funds that were merged or liquidated are missing (survivorship).
from common import *
import json, urllib.request
import numpy as np

P = os.path.join(DATA, "cef_panel")
U = pd.read_csv(os.path.join(P, "universe.csv"))
s = snap()
D_NOW = (s["rfi_close"] / s["rfi_nav"] - 1) * 100


# Bad data found in November 2026 (CHECKS.md item 17): SRV's NAV is unadjusted for its 2015 reverse split until
# September 18, 2015, which shows as an -83% discount for eight years; TYG's NAV is unadjusted for four weeks in
# June 2008 (+250% to +334% "premiums"). Both stretches are dropped.
BAD = {"SRV": (pd.Timestamp("1900-01-01"), pd.Timestamp("2015-09-11")), "TYG": (pd.Timestamp("2008-06-06"), pd.Timestamp("2008-06-27"))}


def load(t):
    f = os.path.join(P, t + ".json")
    if not os.path.exists(f):
        req = urllib.request.Request(f"https://www.cefconnect.com/api/v3/pricinghistory/{t}/All", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(f, "wb") as out:
            out.write(r.read())
    h = json.load(open(f))["Data"]["PriceHistory"]
    df = pd.DataFrame({"date": pd.to_datetime([x["DataDateJs"] for x in h]), "disc": [x["DiscountData"] for x in h]})
    if t in BAD:   # weeks where CEF Connect's NAV was never adjusted for a reverse split (price was), so the discount is wrong
        df = df[(df.date < BAD[t][0]) | (df.date > BAD[t][1])]
    return df.dropna()


def build(tickers):
    rows = []
    for t in tickers:
        try:
            df = load(t)
        except Exception as e:
            print("skip", t, e)
            continue
        dd = df.date.values.astype("datetime64[D]").astype(np.int64)
        x = df.disc.values
        for i in range(len(df)):
            lo = np.searchsorted(dd, dd[i] - 1092, side="left")
            past = x[lo:i]
            if len(past) < 104:
                continue
            j = np.searchsorted(dd, dd[i] + 361, side="left")
            fwd = x[j] if j < len(df) and dd[j] - dd[i] <= 371 else np.nan
            m = past.mean()
            rows.append((t, df.date.iloc[i], x[i], m, past.std(), fwd))
    o = pd.DataFrame(rows, columns=["ticker", "date", "d", "m", "sd", "fwd"])
    o["dev"] = o.d - o.m
    o["year"] = o.date.dt.year
    return o


def fit(o):
    X = np.column_stack([np.ones(len(o)), o.d, o.dev])
    return np.linalg.lstsq(X, (o.fwd - o.d).values, rcond=None)[0]


if __name__ == "__main__":
    O = build(U.ticker)
    O = O.merge(U, on="ticker")
    rfi = O[O.ticker == "RFI"].iloc[-1]
    W = O.dropna(subset=["fwd"]).copy()
    b = fit(W)
    dev_now = D_NOW - rfi.m
    pred = lambda bb: D_NOW + bb[0] + bb[1] * D_NOW + bb[2] * dev_now
    yrs = np.array(sorted(W.year.unique()))
    by = {y: W[W.year == y] for y in yrs}
    rng = np.random.default_rng(1996)
    boot = np.array([pred(fit(pd.concat([by[y] for y in rng.choice(yrs, len(yrs))]))) for _ in range(1000)])
    lo_d, hi_d = D_NOW - 2, D_NOW + 2
    C = W[(W.d >= lo_d) & (W.d <= hi_d) & (W.dev <= -6)]
    nov = []
    for t, g in C.sort_values("date").groupby("ticker"):
        last = None
        for _, r in g.iterrows():
            if last is None or (r.date - last).days >= 364:
                nov.append(r)
                last = r.date
    NO = pd.DataFrame(nov)
    pct = lambda v: " / ".join(f"{np.percentile(v, p):.2f}" for p in (10, 25, 50, 75, 90))
    lines = [
        f"{W.ticker.nunique()} funds, {len(W):,} fund-weeks with a 1-year-forward discount, start dates {W.year.min()}-{W.year.max()}",
        f"fwd - d = {b[0]:.3f} {b[1]:+.4f} x d {b[2]:+.4f} x (d - own 3-yr average)",
        f"RFI now: d {D_NOW:.2f}%, own 3-yr average {rfi.m:.2f}% (through {rfi.date.date()}), so {dev_now:.2f} pts below it",
        f"model's expected discount a year out: {pred(b):.2f}%, 95% interval (year-block bootstrap) {np.percentile(boot,2.5):.2f}% to {np.percentile(boot,97.5):.2f}%",
        f"comparable weeks (d within 2 pts of {D_NOW:.2f}% and at least 6 pts below the fund's 3-yr average): {len(C):,} weeks, {C.ticker.nunique()} funds, {C.year.nunique()} years",
        f"  discount a year later, 10th/25th/50th/75th/90th percentile: {pct(C.fwd)}",
        f"  narrower a year later: {(C.fwd > C.d).mean()*100:.1f}%; wider by more than 3 pts: {(C.fwd < C.d - 3).mean()*100:.1f}%",
        f"  one per fund per year (non-overlapping): {len(NO)} cases, median {NO.fwd.median():.2f}%, narrower in {(NO.fwd > NO.d).mean()*100:.1f}%, average change {(NO.fwd - NO.d).mean():+.2f} pts",
        f"  start dates 2016 and later: {len(C[C.year>=2016]):,} weeks, median {C[C.year>=2016].fwd.median():.2f}%, narrower {(C[C.year>=2016].fwd > C[C.year>=2016].d).mean()*100:.1f}%",
    ]
    for cat, g in C.groupby("cef_connect_category"):
        lines.append(f"  {cat}: {len(g)} weeks, {g.ticker.nunique()} funds, median {g.fwd.median():.2f}%, narrower {(g.fwd > g.d).mean()*100:.1f}%")
    edges = [-99, -8, -6, -4, -2, 0, 2, 4, 99]
    labels = ["-8 or less", "-8 to -6", "-6 to -4", "-4 to -2", "-2 to 0", "0 to 2", "2 to 4", "above 4"]
    W["bucket"] = pd.cut(W.dev, edges, labels=labels)
    W["chg"] = W.fwd - W.d
    g = W.groupby("bucket", observed=True).chg
    pd.DataFrame({"fund_weeks": g.size(), "median_1y_change_pts": g.median(), "p25_change": g.quantile(.25),
                  "p75_change": g.quantile(.75), "pct_narrower": g.apply(lambda v: (v > 0).mean() * 100)}).round(2)         .rename_axis("deviation_from_own_3yr_avg_pts").to_csv(os.path.join(RESULTS, "discount_panel_by_deviation.csv"))
    C[["ticker", "cef_connect_category", "date", "d", "m", "dev", "fwd"]].to_csv(os.path.join(RESULTS, "discount_panel_comparables.csv"), index=False)
    save("discount_panel.txt", "\n".join(lines) + "\n")
