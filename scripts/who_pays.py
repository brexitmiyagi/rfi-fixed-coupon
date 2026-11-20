# Who pays the $0.96. Net investment income per share from every annual report since 1995,
# set against the same check. Plus where 2026's check came from per the Section 19 notices.
from common import *

a = pd.read_csv(os.path.join(DATA, "annual_report_per_share.csv"))
a["income_cover_pct"] = a.nii_per_share / PAYOUT * 100
a["gross_income_yield_pct"] = a.nii_ratio_pct + a.expense_ratio_pct
a.to_csv(os.path.join(RESULTS, "income_cover_by_year.csv"), index=False)

def row(y):
    return a.set_index("year").loc[y]

r95, r25 = row(1995), row(2025)
s = snap()
s19 = pd.read_csv(os.path.join(DATA, "section19_2026_ytd.csv")).set_index("month")
f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
oct_ = s19.loc["October"]
lines = [
    f"1995: NII ${r95.nii_per_share:.2f} a share = {r95.income_cover_pct:.0f}% of $0.96; NII ratio {r95.nii_ratio_pct}% + expenses {r95.expense_ratio_pct}% = gross income yield {r95.gross_income_yield_pct:.2f}%",
    f"2025: NII ${r25.nii_per_share:.2f} a share = {r25.income_cover_pct:.0f}% of $0.96; NII ratio {r25.nii_ratio_pct}% + expenses {r25.expense_ratio_pct}% = gross income yield {r25.gross_income_yield_pct:.2f}%",
    f"peak NII year: {int(a.loc[a.nii_per_share.idxmax(),'year'])} at ${a.nii_per_share.max():.2f} ({a.income_cover_pct.max():.0f}% of $0.96)",
    f"years since 2010 where NII covered more than 40% of $0.96: {(a[a.year>=2010].income_cover_pct>40).sum()}",
    f"book gross income yield minus 10-year: 1995 {r95.gross_income_yield_pct - 5.71:+.2f} pts (Dec 1995 10y 5.71), 2025 book vs 18 Nov 2026 10y {r25.gross_income_yield_pct - s['ust_10y']:+.2f} pts",
    f"Nareit All Equity REITs dividend yield 31 Oct 2026 {s['nareit_all_equity_div_yield_2026_10_31']}% vs 10-year {s['ust_10y_2026_10_31']}% that day: {s['nareit_all_equity_div_yield_2026_10_31']-s['ust_10y_2026_10_31']:+.2f} pts",
    f"2025 tax return of capital ${f['tax_roc_per_share_2025']:.2f} a share",
    f"2026 Section 19 YTD through October: NII ${oct_.ytd_nii:.4f} ({oct_.ytd_nii/oct_.ytd_total*100:.1f}%), ST gains ${oct_.ytd_st_gain:.4f} ({oct_.ytd_st_gain/oct_.ytd_total*100:.1f}%), LT gains ${oct_.ytd_lt_gain:.4f}, return of capital ${oct_.ytd_return_of_capital:.4f} ({oct_.ytd_return_of_capital/oct_.ytd_total*100:.1f}%)",
    f"June 30 2026 net unrealized appreciation ${f['net_unrealized_appreciation']/1e6:.2f}m = ${f['net_unrealized_appreciation']/f['shares_outstanding_2026_06_30']:.2f} a share",
    f"H1 2026: realized gains ${f['h1_net_realized_gain']/1e6:.2f}m, unrealized gains ${f['h1_change_unrealized']/1e6:.2f}m, distributions ${f['h1_distributions_common']/1e6:.2f}m, NII ${f['h1_net_investment_income']/1e6:.2f}m",
]
save("who_pays.txt", "\n".join(lines) + "\n")
