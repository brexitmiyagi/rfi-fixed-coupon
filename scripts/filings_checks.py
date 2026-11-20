# Four filing checks: how Welltower pays for its buying, how much of RFI's book has no market price,
# what stands between RFI and an activist, and who has ever filed as a 5% holder.
from common import *

w = pd.read_csv(os.path.join(DATA, "welltower_equity_issuance.csv"))
cf = w[(w["item"].str.startswith("Proceeds")) & (w.period.str.startswith("2026"))].value_usd.iloc[0]
eq = w[(w["item"].str.startswith("StockIssued")) & (w.period.str.startswith("2026 Q"))].value_usd.sum()
inv = w[w["item"] == "pro rata gross investments completed"].value_usd.iloc[0]
so = pd.read_csv(os.path.join(DATA, "welltower_shares_outstanding.csv"))
fv = pd.read_csv(os.path.join(DATA, "fair_value_levels_2026_06_30.csv")).set_index("level").value_usd
g = pd.read_csv(os.path.join(DATA, "governance_checks.csv"))
inv_total = fv[["Level 1", "Level 2", "Level 3"]].sum()
lines = [
    f"Welltower new common stock, Jan-Sep 2026: ${cf/1e9:.2f}bn (cash flow) and ${eq/1e9:.2f}bn (equity statement, three quarters); investments completed ${inv/1e9:.1f}bn, so stock covered {cf/inv*100:.0f}%",
    f"Welltower shares outstanding {so.shares_outstanding.iloc[1]:,.0f} ({so.as_of.iloc[1]}) -> {so.shares_outstanding.iloc[-1]:,.0f} ({so.as_of.iloc[-1]}), +{(so.shares_outstanding.iloc[-1]/so.shares_outstanding.iloc[1]-1)*100:.1f}%",
    f"RFI June 30, 2026 investments: Level 1 {fv['Level 1']/inv_total*100:.1f}%, Level 2 {fv['Level 2']/inv_total*100:.1f}%, Level 3 {fv['Level 3']/inv_total*100:.2f}% (${fv['Level 3']/1e6:.2f}m, {fv['Level 3']/fv['net_assets']*100:.2f}% of net assets); a 30% markdown of Level 3 = {0.3*fv['Level 3']/fv['net_assets']*100:.2f}% of NAV",
] + [f"{r.check}: {r.finding}" for r in g.itertuples()]
save("filings_checks.txt", "\n".join(lines) + "\n")
