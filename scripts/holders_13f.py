# Who owns RFI and who sold, from every 13F information table that lists RFI's CUSIP (19247R103), Q4 2025 to Q3 2026.
from common import *

p = pd.read_csv(os.path.join(DATA, "rfi_13f_positions_2025q4_2026q3.csv"))
tot = p.groupby("period").shares.sum()
a = p[p.period == "2025-12-31"].set_index("cik").shares
b = p[p.period == "2026-09-30"].set_index("cik").shares
both = a.index.intersection(b.index)
chg = (b[both] - a[both])
names = p.drop_duplicates("cik").set_index("cik").name
lines = [f"13F shares by quarter-end: " + ", ".join(f"{k} {v/1e6:.2f}m" for k, v in tot.items()),
         f"filers in both Dec 2025 and Sep 2026: {len(both)}, {a[both].sum()/1e6:.2f}m -> {b[both].sum()/1e6:.2f}m ({(b[both].sum()/a[both].sum()-1)*100:+.1f}%), {(chg<0).sum()} cut, {(chg>0).sum()} added",
         "five biggest cuts:", chg.sort_values().head(5).rename(index=names).to_string(),
         f"13F holders at Sep 30 own {tot.iloc[-1]/26761638*100:.1f}% of the 26.76m shares (June 30 count)",
         f"known CEF arbitrage or activist names at Sep 30: " + ", ".join(f"{n.split('  ')[0]} {s:,.0f}" for n, s in p[(p.period=='2026-09-30') & p.name.str.split('(CIK', regex=False).str[0].str.contains('Almitas|Saba|Karpus|RiverNorth|1607 Capital|Bulldog', case=False)][['name','shares']].values)]
save("holders_13f.txt", "\n".join(lines) + "\n")
