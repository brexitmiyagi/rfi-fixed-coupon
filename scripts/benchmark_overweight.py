# Is Welltower RFI's bet, or just the REIT index? Welltower's weight in RFI against two index funds (VNQ, XLRE)
# and against Cohen & Steers' other real estate funds, all from their own N-PORT filings.
# Then: what RFI's book would have returned with Welltower at index weight and the difference spread over the rest of its book.
from common import *
import glob, re
import numpy as np

names = {"1064641": "XLRE", "734383": "VNQ direct", "874505": "CSRSX", "1157842": "RQI", "1224450": "RNP", "1866874": "RLTY", "106444": "RE II"}
rows = []
for f in sorted(glob.glob(os.path.join(DATA, "peer_nport", "*_20*.xml"))):
    t = open(f).read()
    cik, period = os.path.basename(f)[:-4].split("_")
    blocks = re.findall(r'<invstOrSec>(.*?)</invstOrSec>', t, re.S)
    w = sum(float(re.search(r'<pctVal>([^<]+)', b).group(1)) for b in blocks if re.search(r'<cusip>\s*95040Q104', b))
    rows.append(dict(fund=names[cik], period=period, well_pct=w))
    if cik == "734383":  # VNQ's stake in Vanguard Real Estate II Index Fund (CUSIP 922031695)
        s = sum(float(re.search(r'<pctVal>([^<]+)', b).group(1)) for b in blocks if re.search(r'<cusip>\s*922031695', b))
        rows.append(dict(fund="VNQ stake in RE II", period=period, well_pct=s))
P = pd.DataFrame(rows).pivot(index="period", columns="fund", values="well_pct")
# VNQ look-through: direct Welltower + (stake in Real Estate II x Real Estate II's Welltower weight)
P["VNQ"] = P["VNQ direct"] + P["VNQ stake in RE II"] / 100 * P["RE II"]
P.round(3).to_csv(os.path.join(RESULTS, "vnq_lookthrough.csv"))
h = pd.read_csv(os.path.join(RESULTS, "nport_holdings_panel.csv"))
rfi = h[h.cusip == "95040Q104"].groupby("date").pct.sum()
eq = h[h.cat == "EC"].groupby("date").pct.sum()
vnq = P["VNQ"].dropna()
vnq.index = pd.to_datetime(vnq.index)
def vnq_at(d):
    s = vnq.copy()
    d = pd.Timestamp(d)
    if d not in s.index:
        s.loc[d] = np.nan
    return s.sort_index().interpolate(method="time").loc[d]
qe = sorted(rfi.index)
T = pd.DataFrame({"RFI": rfi, "RFI REIT stock sleeve": eq,
                  "VNQ (interpolated to quarter-end)": [vnq_at(d) for d in qe]}, index=qe)
T = T.join(P.drop(columns=["VNQ", "VNQ direct", "VNQ stake in RE II", "RE II"]))
T["RFI Welltower as % of its REIT stocks"] = T.RFI / T["RFI REIT stock sleeve"] * 100
T.round(2).to_csv(os.path.join(RESULTS, "welltower_weights_vs_benchmarks.csv"))

# counterfactual: hold Welltower at index weight (index weight x RFI's REIT-stock share), spread the rest over the rest of the book
A = pd.read_csv(os.path.join(RESULTS, "attribution_by_quarter.csv"))
out = {}
for bench in ["VNQ (interpolated to quarter-end)", "XLRE"]:
    tot_c, cf_c = [], []
    for a, b in zip(qe[:-1], qe[1:]):
        if a < "2022-09-30":
            continue
        q = A[A.quarter_end == b]
        wl = q[q.cusip == "95040Q104"]
        w_rfi = rfi.loc[a] / 100
        w_b = T.loc[a, bench] / 100 * eq.loc[a] / 100
        r_w = wl.move.iloc[0]
        w_rest = h[h.date == a].pct.sum() / 100 - w_rfi
        r_rest = (q.contrib.sum() - wl.contrib.iloc[0]) / w_rest
        tot_c.append(q.contrib.sum())
        cf_c.append(q.contrib.sum() - (w_rfi - w_b) * (r_w - r_rest))
    yrs = (pd.Timestamp(qe[-1]) - pd.Timestamp("2022-09-30")).days / 365.25
    out[bench] = (((1 + np.array(tot_c)).prod()) ** (1 / yrs) - 1, ((1 + np.array(cf_c)).prod()) ** (1 / yrs) - 1,
                  (np.array(tot_c) - np.array(cf_c)).sum())
r0 = T.loc["2022-09-30"]; r1 = T.loc[qe[-1]]
lines = [T.round(2).to_string(),
         f"Sep 2022: RFI {r0.RFI:.2f}% vs VNQ {r0['VNQ (interpolated to quarter-end)']:.2f}% and XLRE {r0.XLRE:.2f}%; Jun 2026: RFI {r1.RFI:.2f}% vs VNQ {r1['VNQ (interpolated to quarter-end)']:.2f}% and XLRE {r1.XLRE:.2f}%",
         f"VNQ look-through (direct + via Real Estate II): {vnq.index[0].date()} {vnq.iloc[0]:.2f}%, {vnq.index[-1].date()} {vnq.iloc[-1]:.2f}%; direct only {P['VNQ direct'].dropna().iloc[0]:.2f}% and {P['VNQ direct'].dropna().iloc[-1]:.2f}%",
         f"RFI's Welltower as a share of its REIT stocks, Jun 2026: {r1['RFI Welltower as % of its REIT stocks']:.2f}%; Cohen & Steers Realty Shares (CSRSX) {r1.CSRSX:.2f}%, RQI {r1.RQI:.2f}%, RLTY {r1.RLTY:.2f}%, RNP {r1.RNP:.2f}% (% of net assets)"]
for k, (act, cf, diff) in out.items():
    lines.append(f"book price return with Welltower at {k} weight: {cf*100:.2f}% a year vs actual {act*100:.2f}%; the overweight added {diff*100:.2f} pts over the period")
save("benchmark_overweight.txt", "\n".join(lines) + "\n")

extra = []
for bench in ["VNQ (interpolated to quarter-end)", "XLRE"]:
    s = 0.0
    for a, b in zip(qe[:-1], qe[1:]):
        if a < "2022-09-30":
            continue
        r = A[(A.quarter_end == b) & (A.cusip == "95040Q104")].move.iloc[0]
        s += T.loc[a, bench] / 100 * eq.loc[a] / 100 * r
    extra.append(f"Welltower's contribution at {bench} weight: {s*100:.2f} pts (actual 10.81)")
with open(os.path.join(RESULTS, "benchmark_overweight.txt"), "a") as fh:
    fh.write("\n".join(extra) + "\n")
print("\n".join(extra))
