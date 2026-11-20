# Do the monthly Section 19 notices overstate return of capital? Every notice from January 2018 to June 2026
# (plus July-December 2017) carries a year-to-date estimate of where the distributions came from. The annual
# report then gives the final tax character. This lines the October estimate and the year's peak estimate up
# against the final figure.
from common import *

n = pd.read_csv(os.path.join(DATA, "section19_notices_2017_2026.csv"))
oct26 = pd.read_csv(os.path.join(DATA, "section19_2026_ytd.csv")).set_index("month").loc["October"]
n = pd.concat([n, pd.DataFrame([dict(year=2026, month_num=10, month="October", ytd_total=oct26.ytd_total,
                                      ytd_nii=oct26.ytd_nii, ytd_roc=oct26.ytd_return_of_capital,
                                      ytd_roc_pct=oct26.ytd_return_of_capital / oct26.ytd_total * 100)])])
f = pd.read_csv(os.path.join(DATA, "final_tax_character_2016_2025.csv")).set_index("year")
f["final_roc_pct"] = f.tax_return_of_capital / f.total_distributions * 100
rows = []
for y, g in n.groupby("year"):
    o = g[g.month_num == 10]
    rows.append(dict(year=y, months_seen=len(g), peak_estimate_pct=g.ytd_roc_pct.max(),
                     peak_month=g.loc[g.ytd_roc_pct.idxmax(), "month"],
                     october_estimate_pct=o.ytd_roc_pct.iloc[0] if len(o) else None,
                     december_estimate_pct=g[g.month_num == 12].ytd_roc_pct.iloc[0] if (g.month_num == 12).any() else None,
                     final_pct=f.final_roc_pct.get(y)))
T = pd.DataFrame(rows).round(2)
T.to_csv(os.path.join(RESULTS, "section19_vs_tax.csv"), index=False)
done = T[T.final_pct.notna()]
over = done[done.october_estimate_pct > done.final_pct + 1]
under = done[done.october_estimate_pct < done.final_pct - 1]
lines = [T.to_string(index=False),
         f"years with a final figure: {len(done)}; any notice showed return of capital in {(done.peak_estimate_pct > 0).sum()}; final return of capital above zero in {(done.final_pct > 0).sum()}",
         f"October estimate above the final by more than 1 pt: {len(over)} years ({', '.join(map(str, over.year))}); below by more than 1 pt: {len(under)} ({', '.join(map(str, under.year))})",
         f"average October estimate {done.october_estimate_pct.mean():.1f}% vs average final {done.final_pct.mean():.1f}%",
         f"2026 October estimate {T[T.year==2026].october_estimate_pct.iloc[0]:.1f}%, highest October reading since 2017 (previous high {done.october_estimate_pct.max():.1f}%)"]
save("section19_vs_tax.txt", "\n".join(lines) + "\n")
