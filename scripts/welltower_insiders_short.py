# Two outside reads on Welltower: what its insiders did on the open market (Form 4, Nov 2025 to Sep 2026,
# every Form 4 in Welltower's EDGAR filing list) and what short sellers did (FINRA consolidated short interest).
from common import *

f4 = pd.read_csv(os.path.join(DATA, "welltower_form4_2025_11_to_2026_09.csv"))
si = pd.read_csv(os.path.join(DATA, "welltower_short_interest_finra.csv"))
so = pd.read_csv(os.path.join(DATA, "welltower_shares_outstanding.csv"))
P, S = f4[f4.code == "P"], f4[f4.code == "S"]
last = si.iloc[-1]
target = pd.Timestamp(last.settlementDate) - pd.DateOffset(years=1)
yr = si.iloc[(pd.to_datetime(si.settlementDate) - target).abs().argmin()]
lines = [
    f"Form 4 filers {f4.who.nunique()}, transactions {len(f4)}, {f4.date.min()} to {f4.date.max()}; codes: " + ", ".join(f"{k} {v}" for k, v in f4.code.value_counts().items()),
    f"open-market sales: {len(S)}; open-market purchases: {len(P)} ({P.shares.sum():,.0f} shares, ${(P.shares*P.price).sum()/1e6:.2f}m, by {', '.join(P.who.unique())}, {P.date.min()} to {P.date.max()})",
    f"short interest {last.settlementDate}: {last.currentShortPositionQuantity:,.0f} shares, {last.daysToCoverQuantity} days to cover, {last.currentShortPositionQuantity/so.shares_outstanding.iloc[-1]*100:.2f}% of shares outstanding",
    f"a year earlier ({yr.settlementDate}): {yr.currentShortPositionQuantity:,.0f} shares, {yr.daysToCoverQuantity} days; change {(last.currentShortPositionQuantity/yr.currentShortPositionQuantity-1)*100:+.0f}%",
    f"peak in the series since mid-2025: {si.currentShortPositionQuantity.max():,.0f} ({si.loc[si.currentShortPositionQuantity.idxmax(),'settlementDate']})",
]
save("welltower_insiders_short.txt", "\n".join(lines) + "\n")
