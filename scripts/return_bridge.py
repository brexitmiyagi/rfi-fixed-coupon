# Reconciling the two views of the manager: the annual reports (whole fund, after fees, total return) and the
# Brinson run (REIT stocks only, before fees, price only). Per period:
#   fund minus benchmark = REIT-stock picking (brinson active x the fund's REIT-stock weight)
#                        + stock/preferred mix ((REIT-stock weight - 80%) x (REIT index - preferred index))
#                        - fees (0.94% a year)
#                        + everything else (preferred and bond picking, income differences, cash, options, trading
#                          inside quarters, and the price-vs-total-return gap)
# The preferred index return isn't published in the reports, so it's backed out: P = (blend - 0.8 x REIT index) / 0.2.
from common import *

r = pd.read_csv(os.path.join(DATA, "annual_report_returns_vs_benchmark.csv"), dtype={"period": str}).set_index("period")
Q = pd.read_csv(os.path.join(RESULTS, "attribution_by_quarter.csv"))
B = pd.read_csv(os.path.join(RESULTS, "brinson_by_quarter_sector.csv"))
H = pd.read_csv(os.path.join(RESULTS, "nport_holdings_panel.csv"))
na = H.groupby("date").pct.sum()  # not used for weights; pct is already % of net assets
wts = H.groupby(["date", "cat"]).pct.sum().unstack().fillna(0)
act = B.groupby("quarter_end").apply(lambda g: (g.w_rfi * g.r_rfi).sum() - g.r_index.iloc[0])
periods = {"2023": ("2022-12-31", "2023-12-31"), "2024": ("2023-12-31", "2024-12-31"),
           "2025": ("2024-12-31", "2025-12-31"), "2026H1": ("2025-12-31", "2026-06-30")}
rows = []
for p, (a, b) in periods.items():
    qs = [q for q in act.index if a < q <= b]
    starts = [d for d in wts.index if a <= d < b]
    w_eq = wts.loc[starts, "EC"].mean() / 100
    w_fi = (wts.loc[starts, "EP"].mean() + wts.loc[starts, "DBT"].mean()) / 100
    Nret, Bret, F = r.loc[p, "nareit_equity_index"], r.loc[p, "blended_benchmark"], r.loc[p, "nav_total_return"]
    Pret = (Bret - 0.8 * Nret) / 0.2
    stock = w_eq * ((1 + act[qs]).prod() - 1) * 100
    mix = (w_eq - 0.8) * (Nret - Pret)
    fee = -0.94 * (0.5 if p.endswith("H1") else 1)
    fi = Q[(Q.cat.isin(["EP", "DBT"])) & Q.quarter_end.isin(qs)].copy()
    fi_ret = []
    for q in qs:
        g = fi[fi.quarter_end == q]
        fi_ret.append((g.v0 * g.move).sum() / g.v0.sum())
    fi_px = ((1 + pd.Series(fi_ret)).prod() - 1) * 100
    excess = F - Bret
    rows.append(dict(period=p, fund=F, benchmark=Bret, excess=round(excess, 2), reit_index=Nret, pref_index_implied=round(Pret, 2),
                     reit_stock_weight=round(w_eq * 100, 1), pref_bond_weight=round(w_fi * 100, 1),
                     reit_stock_picking=round(stock, 2), stock_pref_mix=round(mix, 2), fees=fee,
                     everything_else=round(excess - stock - mix - fee, 2), pref_bond_sleeve_price=round(fi_px, 2)))
T = pd.DataFrame(rows)
tot = T[["excess", "reit_stock_picking", "stock_pref_mix", "fees", "everything_else"]].sum()
T.to_csv(os.path.join(RESULTS, "return_bridge.csv"), index=False)
lines = [T.to_string(index=False),
         f"Jan 2023 to Jun 2026, simple sums: excess {tot.excess:+.2f} = REIT-stock picking {tot.reit_stock_picking:+.2f} + mix {tot.stock_pref_mix:+.2f} + fees {tot.fees:+.2f} + everything else {tot.everything_else:+.2f}"]
save("return_bridge.txt", "\n".join(lines) + "\n")
