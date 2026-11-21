# Joint simulation of the next 12 months for RFI, RQI and RNP, keeping the market, the fund's NAV and its discount
# tied together the way they actually moved. Each draw is one historical 12-month window (any month-end start since
# the fund has 3 years of history) plus, for Welltower, a random relative shock sized to each fund's overweight.
#   NAV total return = a + beta x (expected REIT return + that window's REIT surprise) + that window's NAV residual
#   discount in a year = the panel model's forecast for today + that window's (demeaned) miss for this fund
# so in a 2008-type window both the NAV and the discount get hit together.
# Expected REIT return: three settings from reit_valuation_return.py (valuation-adjusted base, regression, unconditional).
from common import *
import json, warnings
import numpy as np
warnings.filterwarnings("ignore")

s = snap()
P = os.path.join(DATA, "cef_panel")
# The discount forecast uses the panel model fitted on 2016 onward (panel_out_of_sample.py): the full-sample fit
# promised about twice the narrowing that actually showed up after 2016. Each window's miss is demeaned, so the
# simulation's average discount equals that forecast and the windows only supply the spread and the link to REITs.
PANEL = (0.4413, -0.0005, -0.2570)   # post-2016 fit in panel_out_of_sample.txt (after the SRV/TYG data fix, CHECKS.md item 17)
FUNDS = {  # Nov 20, 2026 close (Nasdaq / CEF Connect), current regular monthly payout x 12, Welltower % of net assets (Jun 30 N-PORT)
    "RFI": dict(price=10.21, nav=11.16, payout=0.96, well_pct=14.3),   # 13.8-14.8% today, midpoint
    "RQI": dict(price=11.10, nav=12.34, payout=1.08, well_pct=17.94),
    "RNP": dict(price=18.06, nav=20.40, payout=1.632, well_pct=11.18),
}
WELL_INDEX = 11.08   # Welltower % of FTSE Nareit All Equity REITs, Oct 30, 2026 (Nareit constituents file)


def weekly_fund(t):
    if t == "RFI":
        w = weekly()[["price", "nav"]]
        dv = dists().rename(columns={"ex_date": "ex_date"})[["ex_date", "amount"]]
    else:
        h = json.load(open(os.path.join(P, t + ".json")))["Data"]["PriceHistory"]
        w = pd.DataFrame({"price": [x["Data"] for x in h], "nav": [x["NAVData"] for x in h]},
                         index=pd.to_datetime([x["DataDateJs"] for x in h]))
        dv = pd.read_csv(os.path.join(P, t + "_distributions_cefconnect.csv"), parse_dates=["ex_date"])
    w = w.dropna()
    w["disc"] = (w.price / w.nav - 1) * 100
    dv = dv[dv.ex_date <= w.index[-1]].set_index("ex_date").amount
    tri, u = [1.0], 1.0
    for a, b in zip(w.index[:-1], w.index[1:]):
        paid = dv[(dv.index > a) & (dv.index <= b)].sum()
        u *= (w.nav[b] + paid) / w.nav[a]
        tri.append(u)
    w["tri"] = tri
    w["m3"] = w.disc.rolling(156, min_periods=104).mean().shift(1)
    return w


def bench_monthly():
    v = pd.read_excel(os.path.join(DATA, "nareit", "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
    return pd.Series(pd.to_numeric(v[23], errors="coerce").values, index=pd.to_datetime(v[0], errors="coerce")).dropna()


B = bench_monthly()
B.index = B.index.to_period("M")
d = pd.read_csv(os.path.join(DATA, "daily_nasdaq_rfi_vnq_well_xlre_2021_2026.csv"), parse_dates=["date"])
px = d.pivot(index="date", columns="ticker", values="close").sort_index()
rel = (px.WELL.pct_change(252) - px.VNQ.pct_change(252)).dropna() * 100
WELL_SD = rel.std()          # 12-month Welltower-minus-VNQ price return, overlapping, 2022-2026

vr = pd.read_csv(os.path.join(RESULTS, "reit_valuation_return.csv"))
base_E = 4.84     # post-1990 months within 1 pt of today's yield gap: median forward return (reit_valuation_return.txt)
settings = {"valuation-adjusted base": base_E,
            "regression since 1990": float(vr.loc[vr.start == "1990-01", "pred"].iloc[0]),
            "unconditional": None}
rng = np.random.default_rng(42)
summ, keep = [], {}
for t, f in FUNDS.items():
    w = weekly_fund(t)
    m = w.groupby(w.index.to_period("M")).last()
    m["bench"] = B.reindex(m.index)
    rows = []
    for i in range(len(m) - 12):
        a, b = m.iloc[i], m.iloc[i + 12]
        if np.isnan(a.m3) or np.isnan(a.bench) or np.isnan(b.bench):
            continue
        dev = a.disc - a.m3
        pred = a.disc + PANEL[0] + PANEL[1] * a.disc + PANEL[2] * dev
        rows.append(dict(start=str(m.index[i]), nav_tr=(b.tri / a.tri - 1) * 100, bench=(b.bench / a.bench - 1) * 100,
                         d0=a.disc, d1=b.disc, disc_miss=b.disc - pred))
    H = pd.DataFrame(rows)
    X = np.column_stack([np.ones(len(H)), H.bench])
    coef = np.linalg.lstsq(X, H.nav_tr, rcond=None)[0]
    H["nav_resid"] = H.nav_tr - X @ coef
    d0 = (f["price"] / f["nav"] - 1) * 100
    dev0 = d0 - w.m3.iloc[-1]
    pred0 = d0 + PANEL[0] + PANEL[1] * d0 + PANEL[2] * dev0
    over = f["well_pct"] - coef[1] * WELL_INDEX       # Welltower held beyond what the fund's REIT beta already carries
    H.to_csv(os.path.join(RESULTS, f"joint_windows_{t}.csv"), index=False)
    full_H = H
    for name, E in list(settings.items()) + [("valuation-adjusted base, common windows from 2005-07", base_E)]:
        H = full_H[full_H.start >= "2005-07"].reset_index(drop=True) if "common" in name else full_H
        E = H.bench.mean() if E is None else E
        N = 20000
        k = rng.integers(len(H), size=N)
        shock = rng.normal(0, WELL_SD, N) * over / 100
        bench_sim = E + (H.bench.values[k] - H.bench.mean())
        nav_tr = coef[0] + coef[1] * bench_sim + H.nav_resid.values[k] + shock
        nav1 = f["nav"] * (1 + nav_tr / 100) - f["payout"]
        d1 = np.clip(pred0 + (H.disc_miss.values - H.disc_miss.mean())[k], -60, 40)
        p1 = nav1 * (1 + d1 / 100)
        tot = ((p1 + f["payout"]) / f["price"] - 1) * 100
        edge = tot - bench_sim
        q = lambda v, p: np.percentile(v, p)
        summ.append(dict(fund=t, setting=name, expected_reit=round(E, 2), windows=len(H), first_window=H.start.iloc[0],
                         beta=round(coef[1], 2), alpha=round(coef[0], 2), discount_now=round(d0, 2), discount_forecast=round(pred0, 2),
                         welltower_extra_pct=round(over, 1), exp_price=round(p1.mean(), 2), median_price=round(np.median(p1), 2),
                         exp_total=round(tot.mean(), 1), p5=round(q(tot, 5), 1), p10=round(q(tot, 10), 1), p25=round(q(tot, 25), 1),
                         p50=round(q(tot, 50), 1), p75=round(q(tot, 75), 1), p90=round(q(tot, 90), 1), prob_loss=round((tot < 0).mean() * 100, 1),
                         exp_edge=round(edge.mean(), 1), sd=round(tot.std(), 1), excess_over_10y_per_risk=round((tot.mean() - s['ust_10y']) / tot.std(), 2), edge_sd=round(edge.std(), 1), prob_beat_reits=round((edge > 0).mean() * 100, 1),
                         corr_reit_vs_disc_change=round(np.corrcoef(H.bench, H.d1 - H.d0)[0, 1], 2)))
        if t == "RFI" and name == "valuation-adjusted base":
            keep = dict(total=tot, price=p1, bench=bench_sim)
S = pd.DataFrame(summ)
S.to_csv(os.path.join(RESULTS, "joint_simulation.csv"), index=False)
hist = np.histogram(keep["total"], bins=np.arange(-60, 85, 5))
pd.DataFrame({"from": hist[1][:-1], "to": hist[1][1:], "share_pct": (hist[0] / hist[0].sum() * 100).round(2)}).to_csv(
    os.path.join(RESULTS, "joint_simulation_rfi_histogram.csv"), index=False)
lines = [f"Welltower minus VNQ, 12-month price return, sd {WELL_SD:.1f} pts (daily overlapping windows, {rel.index[0].date()} to {rel.index[-1].date()})"]
for _, r in S.iterrows():
    lines.append(f"{r.fund} | {r.setting} (REITs {r.expected_reit:+.2f}%): beta {r.beta}, {r.windows} windows from {r.first_window}; discount {r.discount_now} -> forecast {r.discount_forecast}; "
                 f"expected price ${r.exp_price:.2f} (median ${r.median_price:.2f}); total return mean {r.exp_total:+.1f}%, 5/10/25/50/75/90th {r.p5}/{r.p10}/{r.p25}/{r.p50}/{r.p75}/{r.p90}; "
                 f"loss {r.prob_loss}%; sd {r.sd}, (mean - 10y)/sd {r.excess_over_10y_per_risk}; edge over REITs {r.exp_edge:+.1f} pts (sd {r.edge_sd}), beats REITs {r.prob_beat_reits}%; corr(REIT return, discount change) {r.corr_reit_vs_disc_change}")
for px_in in (10.21, 10.03, 9.94):
    tt = ((keep["price"] + FUNDS["RFI"]["payout"]) / px_in - 1) * 100
    lines.append(f"RFI bought at ${px_in:.2f}, valuation-adjusted base: mean {tt.mean():+.1f}%, median {np.median(tt):+.1f}%, 5th {np.percentile(tt,5):+.1f}%, loss {(tt<0).mean()*100:.1f}%, edge over REITs {(tt-keep['bench']).mean():+.1f} pts")
save("joint_simulation.txt", "\n".join(lines) + "\n")
