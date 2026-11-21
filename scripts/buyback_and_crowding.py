# Two questions the post's discount and Welltower sections leave open.
# 1. Would a buyback cost the manager much? A 10% buyback at today's price hands remaining holders the discount
#    on the shares bought, once. It also shrinks net assets, and with them the adviser's fee (0.70% advisory plus
#    0.04% administration, both on average daily net assets, per the June 30 N-CSRS), every year after.
# 2. How crowded is the house Welltower position? Cohen & Steers, Inc.'s September 30 13F shares in its 15 largest
#    REIT positions, against each stock's average daily volume over the three months to November 18 (Nasdaq),
#    as days to sell at 20% of average volume. 20% is a common participation cap, not a rule.
from common import *
import re
s = snap()
px, nav = s["rfi_close"], s["rfi_nav"]
ft = pd.read_csv(os.path.join(DATA, "fee_terms_2026.csv")).set_index("item").value
shares = ft["common_shares_outstanding_2026_06_30"]
bought = shares * ft["repurchase_authority_pct_2026"] / 100
spent = bought * px
gain = bought * (nav - px)
fee_rate = (ft["advisory_fee_pct_of_avg_daily_net_assets"] + ft["administration_fee_to_adviser_pct"]) / 100
fee_lost = spent * fee_rate
lines = [f"10% buyback at ${px:.2f} (NAV ${nav:.2f}): {bought:,.0f} shares, ${spent/1e6:.2f}m spent",
         f"  one-time gain to remaining holders ${gain/1e6:.2f}m, ${gain/(shares-bought):.3f} a share",
         f"  adviser fees lost {fee_rate*100:.2f}% x ${spent/1e6:.2f}m = ${fee_lost/1e3:.0f}k a year, {fee_lost/ft['cohen_steers_inc_revenue_2025_usd']*100:.3f}% of Cohen & Steers' 2025 revenue; "
         f"the holders' gain equals {gain/fee_lost:.1f} years of those fees"]

t = open(os.path.join(DATA, "cns_13f", "0001193125-26-461871.xml")).read()
t = re.sub(r"<(/?)\w+:", r"<\1", t)
rows = []
for r in re.findall(r"<infoTable>(.*?)</infoTable>", t, re.S):
    g = lambda k: re.search(rf"<{k}>(.*?)</{k}>", r, re.S).group(1).strip()
    rows.append(dict(name=g("nameOfIssuer"), cusip=g("cusip"), value_k=float(g("value")), shares=float(g("sshPrnamt"))))
h = pd.DataFrame(rows).groupby(["name", "cusip"], as_index=False).sum().sort_values("value_k", ascending=False)
book = h.value_k.sum()
tick = {"95040Q104": "WELL", "253868103": "DLR", "74340W103": "PLD", "29444U700": "EQIX", "22822V101": "CCI", "03027X100": "AMT",
        "30225T102": "EXR", "866674104": "SUI", "101121101": "BXP", "681936100": "OHI", "74460D109": "PSA", "297178105": "ESS",
        "46284V101": "IRM", "49446R109": "KIM", "828806109": "SPG"}
top = h[h.cusip.isin(tick)].copy()
top["ticker"] = top.cusip.map(tick)
v = pd.read_csv(os.path.join(DATA, "nasdaq_volume_2026_08_19_to_11_18.csv"))
top = top.merge(v, on="ticker")
top["days_at_20pct"] = top.shares / (0.2 * top.avg_daily_volume)
top = top.sort_values("days_at_20pct", ascending=False).reset_index(drop=True)
w = top[top.ticker == "WELL"].iloc[0]
lines += [f"Cohen & Steers 13F Sep 30: Welltower {w.shares/1e6:.1f}m shares, ${w.value_k/1e6:.2f}bn, {w.value_k/book*100:.1f}% of a ${book/1e6:.1f}bn book",
          f"  days to sell at 20% of Aug 19-Nov 18 average volume: Welltower {w.days_at_20pct:.0f}, rank {top.index[top.ticker=='WELL'][0]+1} of {len(top)}; "
          f"median of the 15 {top.days_at_20pct.median():.0f}; longest {top.ticker.iloc[0]} {top.days_at_20pct.iloc[0]:.0f}"]
for _, r in top.iterrows():
    lines.append(f"  {r.ticker}: {r.shares/1e6:.1f}m shares, ADV {r.avg_daily_volume/1e6:.2f}m, {r.days_at_20pct:.0f} days")
top.round(2).to_csv(os.path.join(RESULTS, "cns_crowding.csv"), index=False)
save("buyback_and_crowding.txt", "\n".join(lines) + "\n")
