# The options RFI writes. Every N-PORT lists option positions with put/call, written/purchased, strike, expiry and
# contracts. This sums the written ones per quarter: count, market value (a liability), and notional
# (contracts x shares per contract x strike) as a % of net assets.
from common import *
import glob, re
import xml.etree.ElementTree as ET


def load(f):
    t = open(f).read()
    t = re.sub(r'\s\w+:\w+="[^"]*"', '', t)
    t = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', t)
    t = re.sub(r'<(/?)\w+:', r'<\1', t)
    return ET.fromstring(t)


rows = []
for f in glob.glob(os.path.join(DATA, "nport", "*.xml")):
    r = load(f)
    d, na = r.find(".//repPdDate").text, float(r.find(".//netAssets").text)
    for s in r.iter("invstOrSec"):
        o = s.find(".//optionSwaptionWarrantDeriv")
        if o is None:
            continue
        ref = o.find(".//descRefInstrmnt")
        rows.append(dict(date=d, net_assets=na, underlying=ref.findtext(".//issuerName") if ref is not None else s.findtext("name"),
                         put_call=o.findtext("putOrCall"), written=o.findtext("writtenOrPur"), contracts=abs(float(s.findtext("balance") or 0)),
                         shares_per=float(o.findtext("shareNo") or 0), strike=float(o.findtext("exercisePrice") or 0),
                         expiry=o.findtext("expDt"), value=float(s.findtext("valUSD") or 0)))
O = pd.DataFrame(rows).sort_values(["date", "underlying"])
O.to_csv(os.path.join(RESULTS, "options_positions.csv"), index=False)
w = O[O.written == "Written"].copy()
w["notional"] = w.contracts * w.shares_per * w.strike
g = w.groupby("date").agg(n=("underlying", "size"), calls=("put_call", lambda x: (x == "Call").sum()),
                          puts=("put_call", lambda x: (x == "Put").sum()), value=("value", "sum"),
                          notional=("notional", "sum"), na=("net_assets", "first"))
g["notional_pct"] = g.notional / g.na * 100
g["value_pct"] = g.value / g.na * 100
g.round(3).to_csv(os.path.join(RESULTS, "options_written_by_quarter.csv"))
last = g.iloc[-1]
war = O[(O.written == "Purchased") & O.underlying.str.contains("Hudson", case=False)]
lines = [
    f"written options at {g.index[-1]}: {int(last.n)} positions ({int(last.calls)} calls, {int(last.puts)} puts), market value ${last.value:,.0f} ({last.value_pct:.2f}% of net assets), notional ${last.notional/1e6:.1f}m ({last.notional_pct:.1f}% of net assets)",
    f"average across {len(g)} quarters: {g.n.mean():.1f} positions, notional {g.notional_pct.mean():.1f}% of net assets (max {g.notional_pct.max():.1f}% at {g.notional_pct.idxmax()})",
    f"Hudson Pacific warrants at {war.date.max()}: ${war[war.date == war.date.max()].value.sum():,.0f}",
]
save("options_overlay.txt", "\n".join(lines) + "\n")

# What the option writing earned: realized gains on written options plus the change in their unrealized value,
# from each annual report's statement of operations (2017 had no option line). Caveat: when a written call is
# assigned, the premium goes into the proceeds of the stock sold, not this line, so this is a floor-and-ceiling
# view of the overlay, not an exact one.
p = pd.read_csv(os.path.join(DATA, "written_options_pnl_annual_reports.csv"))
p["total"] = p.realized_written_options + p.unrealized_change_written_options
shares = 26_761_638
years = len(p) - 0.5
avg_na = O.groupby("date").net_assets.first().mean()
tot = p.total.sum()
extra = [
    p[["period", "realized_written_options", "unrealized_change_written_options", "total"]].to_string(index=False),
    f"2018 to June 2026: ${tot:,.0f} in total, ${tot/years:,.0f} a year, about {tot/years/avg_na*100:.2f}% of average net assets (${avg_na/1e6:.0f}m, N-PORT quarters) or {tot/years/shares*100:.1f} cents a share a year; losing years: {', '.join(p[p.total<0].period)}",
]
with open(os.path.join(RESULTS, "options_overlay.txt"), "a") as f:
    f.write("\n".join(extra) + "\n")
print("\n".join(extra))
