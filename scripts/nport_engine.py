# A reusable version of the holdings attribution: point it at any folder of N-PORT XML filings for one fund
# and it prices every position at each quarter-end (value / units), adds up each holding's contribution to the
# book's price return, and reports the top and bottom names and one holding's weight path.
# Usage: python nport_engine.py <folder> [file prefix] [start date] [cusip to track]
#   e.g. python nport_engine.py ../data/peer_nport 1157842_ 2022-09-30 95040Q104   (RQI, Welltower)
from common import *
import sys, glob, re
import xml.etree.ElementTree as ET


def parse(f):
    t = open(f).read()
    t = re.sub(r'\s\w+:\w+="[^"]*"', '', t)
    t = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', t)
    t = re.sub(r'<(/?)\w+:', r'<\1', t)
    r = ET.fromstring(t)
    d, na = r.find(".//repPdDate").text, float(r.find(".//netAssets").text)
    rows = []
    for s in r.iter("invstOrSec"):
        g = lambda k: s.findtext(k)
        rows.append(dict(date=d, name=g("name"), cusip=g("cusip"), units=float(g("balance") or 0),
                         value=float(g("valUSD") or 0), pct=float(g("pctVal") or 0), cat=g("assetCat")))
    return d, na, rows


def run(folder, prefix="", start=None, track=None):
    rows, na = [], {}
    for f in sorted(glob.glob(os.path.join(folder, prefix + "*.xml"))):
        d, n, r = parse(f)
        rows += r
        na[d] = n
    H = pd.DataFrame(rows)
    H = H[H.units > 0]
    dates = sorted(H.date.unique())
    rec = []
    for a, b in zip(dates[:-1], dates[1:]):
        A = H[H.date == a].groupby("cusip").agg(name=("name", "first"), v0=("value", "sum"), u0=("units", "sum"))
        B = H[H.date == b].groupby("cusip").agg(v1=("value", "sum"), u1=("units", "sum"))
        j = A.join(B, how="inner")
        j["contrib"] = j.v0 / na[a] * ((j.v1 / j.u1) / (j.v0 / j.u0) - 1)
        j["quarter_end"] = b
        rec.append(j.reset_index())
    Q = pd.concat(rec)
    if start:
        Q = Q[Q.quarter_end > start]
    per_q = Q.groupby("quarter_end").contrib.sum()
    tot = Q.groupby(["cusip"]).agg(name=("name", "first"), contrib=("contrib", "sum")).sort_values("contrib", ascending=False)
    out = dict(quarters=len(per_q), first=per_q.index[0], last=per_q.index[-1], book=((1 + per_q).prod() - 1) * 100, by_name=tot)
    if track:
        out["track"] = H[H.cusip == track].groupby("date").pct.sum()
    return out


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, "nport")
    prefix = sys.argv[2] if len(sys.argv) > 2 else ""
    start = sys.argv[3] if len(sys.argv) > 3 else None
    track = sys.argv[4] if len(sys.argv) > 4 else None
    o = run(folder, prefix, start, track)
    print(f"{o['quarters']} quarters ending {o['first']} to {o['last']}; book price return {o['book']:.1f}% (sum of contributions {o['by_name'].contrib.sum()*100:.2f} pts)")
    print((o["by_name"].head(5).contrib * 100).round(2).to_string())
    print((o["by_name"].tail(3).contrib * 100).round(2).to_string())
    if track:
        tr = o["track"]
        print(f"{track} weight: {tr.iloc[0]:.2f}% ({tr.index[0]}) -> {tr.iloc[-1]:.2f}% ({tr.index[-1]}); contribution {o['by_name'].loc[track,'contrib']*100:.2f} pts")
