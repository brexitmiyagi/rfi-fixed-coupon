# Is RFI's Welltower bet unusual? Top holding and Welltower weight in every listed real estate CEF's latest N-PORT,
# measured against each fund's common stock (so leverage and preferred sleeves don't distort the comparison).
from common import *
import glob, re
import xml.etree.ElementTree as ET

MGR = {"RFI": "Cohen & Steers", "RQI": "Cohen & Steers", "RNP": "Cohen & Steers", "RLTY": "Cohen & Steers", "NRO": "Neuberger Berman",
       "PGZ": "Principal", "JRS": "Nuveen", "AWP": "abrdn (global)", "IGR": "CBRE (global)", "BPRE": "Bluerock (private real estate)"}
rows = []
for f in sorted(glob.glob(os.path.join(DATA, "peer_cef_nport", "*.xml"))):
    t = open(f).read()
    t = re.sub(r'\s\w+:\w+="[^"]*"', '', t); t = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', t); t = re.sub(r'<(/?)\w+:', r'<\1', t)
    r = ET.fromstring(t)
    H = pd.DataFrame([dict(cusip=s.findtext("cusip"), name=s.findtext("name"), pct=float(s.findtext("pctVal") or 0), cat=s.findtext("assetCat")) for s in r.iter("invstOrSec")])
    ec = H[(H.cat == "EC") & (H.pct > 0)].groupby(["cusip", "name"]).pct.sum().sort_values(ascending=False).reset_index()
    fund = os.path.basename(f).split("_")[0]
    if ec.empty:
        rows.append(dict(fund=fund, manager=MGR[fund], period=r.findtext(".//repPdDate"), note="no listed common stock"))
        continue
    eq = ec.pct.sum()
    rows.append(dict(fund=fund, manager=MGR[fund], period=r.findtext(".//repPdDate"), stocks=len(ec), top_holding=ec.name.iloc[0],
                     top_pct_of_stocks=round(ec.pct.iloc[0] / eq * 100, 2), top10_pct_of_stocks=round(ec.pct.head(10).sum() / eq * 100, 1),
                     welltower_pct_of_stocks=round(ec[ec.cusip == "95040Q104"].pct.sum() / eq * 100, 2)))
P = pd.DataFrame(rows).sort_values("welltower_pct_of_stocks", ascending=False)
P.to_csv(os.path.join(RESULTS, "peer_concentration.csv"), index=False)
cs = P[P.manager == "Cohen & Steers"]
ot = P[(P.manager != "Cohen & Steers") & P.welltower_pct_of_stocks.notna()]
lines = [P.to_string(index=False),
         f"Welltower is the top stock in {int((P.top_holding.fillna('').str.upper().str.startswith('WELLTOWER')).sum())} of {P.stocks.notna().sum()} funds with listed stocks",
         f"Cohen & Steers funds: Welltower {cs.welltower_pct_of_stocks.min():.1f}% to {cs.welltower_pct_of_stocks.max():.1f}% of stocks; other managers {ot.welltower_pct_of_stocks.min():.1f}% to {ot.welltower_pct_of_stocks.max():.1f}%"]
save("peer_concentration.txt", "\n".join(lines) + "\n")
