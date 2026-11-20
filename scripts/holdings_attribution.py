# Who paid for the check. Every quarterly N-PORT from June 2022 to June 2026, priced position by position.
# For each security held at both quarter-ends: price move = (value/units at the end) / (value/units at the start) - 1,
# contribution = weight at the start x price move. Price only, no dividends, and trades inside a quarter aren't seen.
from common import *
import glob, re
import numpy as np
import xml.etree.ElementTree as ET

def parse(f):
    t = open(f).read()
    t = re.sub(r'\s\w+:\w+="[^"]*"', '', t)
    t = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', t)
    t = re.sub(r'<(/?)\w+:', r'<\1', t)
    r = ET.fromstring(t)
    d = r.find('.//repPdDate').text
    na = float(r.find('.//netAssets').text)
    rows = []
    for s in r.iter('invstOrSec'):
        g = lambda k: s.find(k).text if s.find(k) is not None else None
        rows.append(dict(date=d, name=g('name'), cusip=g('cusip'), units=float(g('balance') or 0),
                         value=float(g('valUSD') or 0), pct=float(g('pctVal') or 0), cat=g('assetCat')))
    return d, na, rows

rows, na = [], {}
for f in sorted(glob.glob(os.path.join(DATA, "nport", "*.xml"))):
    d, n, r = parse(f)
    rows += r
    na[d] = n
H = pd.DataFrame(rows)
H = H[H.units > 0]
H.to_csv(os.path.join(RESULTS, "nport_holdings_panel.csv"), index=False)
dates = sorted(H.date.unique())
rec = []
for a, b in zip(dates[:-1], dates[1:]):
    A = H[H.date == a].groupby("cusip").agg(name=("name", "first"), cat=("cat", "first"), v0=("value", "sum"), u0=("units", "sum"))
    B = H[H.date == b].groupby("cusip").agg(v1=("value", "sum"), u1=("units", "sum"))
    j = A.join(B, how="inner")
    j["move"] = (j.v1 / j.u1) / (j.v0 / j.u0) - 1
    j["contrib"] = j.v0 / na[a] * j.move
    j["quarter_end"] = b
    rec.append(j.reset_index())
Q = pd.concat(rec)
Q.to_csv(os.path.join(RESULTS, "attribution_by_quarter.csv"), index=False)

WELL = "95040Q104"
start = "2022-09-30"
S = Q[Q.quarter_end > start]
by_q = S.groupby("quarter_end").contrib.sum()
well_q = S[S.cusip == WELL].groupby("quarter_end").contrib.sum().reindex(by_q.index, fill_value=0)
yrs = (pd.Timestamp(dates[-1]) - pd.Timestamp(start)).days / 365.25
all_c = (1 + by_q).prod() - 1
ex_c = (1 + by_q - well_q).prod() - 1
tot = S.groupby("cusip").agg(name=("name", "first"), contrib=("contrib", "sum")).sort_values("contrib", ascending=False)
tot["contrib_pts"] = (tot.contrib * 100).round(2)
tot[["name", "contrib_pts"]].to_csv(os.path.join(RESULTS, "attribution_total_by_security.csv"))
dc = ["253868103", "29444U700", "46284V101"]  # Digital Realty, Equinix, Iron Mountain
w = H[H.cusip == WELL].groupby("date").agg(units=("units", "sum"), value=("value", "sum"), pct=("pct", "sum"))
w["price"] = w.value / w.units
w.round(2).to_csv(os.path.join(RESULTS, "welltower_position.csv"))
lines = [
    f"quarters {start} to {dates[-1]} ({yrs:.2f} years)",
    f"sum of all price contributions: {S.contrib.sum()*100:.2f} pts; Welltower {tot.loc[WELL,'contrib']*100:.2f} pts = {tot.loc[WELL,'contrib']/S.contrib.sum()*100:.0f}%",
    f"Digital Realty + Equinix + Iron Mountain: {tot.loc[dc,'contrib'].sum()*100:.2f} pts; with Welltower {(tot.loc[dc,'contrib'].sum()+tot.loc[WELL,'contrib'])/S.contrib.sum()*100:.0f}% of the total",
    f"compounded holdings price return: {all_c*100:.1f}% = {((1+all_c)**(1/yrs)-1)*100:.2f}% a year; without Welltower's contribution {ex_c*100:.1f}% = {((1+ex_c)**(1/yrs)-1)*100:.2f}% a year",
    f"Welltower: {w.units.iloc[1]:,.0f} shares at ${w.price.iloc[1]:.2f} ({w.pct.iloc[1]:.2f}% of net assets) on {w.index[1]} -> {w.units.iloc[-1]:,.0f} shares at ${w.price.iloc[-1]:.2f} ({w.pct.iloc[-1]:.2f}%) on {w.index[-1]}",
    "top five and bottom three contributors (pts):",
    tot.head(5)[["name", "contrib_pts"]].to_string(),
    tot.tail(3)[["name", "contrib_pts"]].to_string(),
]
save("holdings_attribution.txt", "\n".join(lines) + "\n")
