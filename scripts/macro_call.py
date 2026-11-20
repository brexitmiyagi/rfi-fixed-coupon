# Evidence behind the macro call: how often the FTSE Nareit All Equity REITs total return over the next 12 months
# came in below the 10-year Treasury yield at the start, when REITs yielded about as little relative to the
# 10-year as they do now (gap -1.30). Uses results/reit_yield_gap_monthly.csv from reit_valuation_return.py.
from common import *
import numpy as np

n = pd.read_csv(os.path.join(RESULTS, "reit_yield_gap_monthly.csv"), parse_dates=["date"]).dropna(subset=["fwd12"])
gap = 3.77 - snap()["ust_10y"]
lines = [f"today's gap {gap:+.2f}"]
for start in ["1972", "1990", "2000"]:
    d = n[n.date >= start]
    for name, sub in [("within 1 pt of today's gap", d[(d.gap - gap).abs() <= 1]), ("gap -1 or lower", d[d.gap <= -1]), ("all months", d)]:
        lines.append(f"since {start}, {name}: {len(sub)} months; REITs below the starting 10-year yield {np.mean(sub.fwd12 < sub.t10)*100:.0f}%; "
                     f"median REIT return {sub.fwd12.median():.1f}% vs median 10-year {sub.t10.median():.2f}%")
tight = n[(n.date >= "1990") & (n.gap <= -1)]
lines.append("post-1990 months at -1 or lower: " + ", ".join(f"{r.date.date()} gap {r.gap:+.2f}: REITs {r.fwd12:+.1f}% vs 10-year {r.t10:.2f}%" for r in tight.itertuples()))
save("macro_call.txt", "\n".join(lines) + "\n")
