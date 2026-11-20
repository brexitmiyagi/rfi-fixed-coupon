# Does the manager's active management pay? RFI's NAV total return against its own blended benchmark
# (80% Nareit equity REITs, 20% REIT preferreds), as printed in each annual report's letter, 2005 to June 2026.
# The fund's return is after its fees; the benchmark has none.
from common import *

r = pd.read_csv(os.path.join(DATA, "annual_report_returns_vs_benchmark.csv"), dtype={"period": str})
r["excess"] = r.nav_total_return - r.blended_benchmark
r.round(2).to_csv(os.path.join(RESULTS, "manager_record.csv"), index=False)
full = r[r.period != "2026H1"].copy()
full["year"] = full.period.astype(int)
cg = lambda s: ((1 + s / 100).prod() - 1) * 100
early, late = full[full.year <= 2016], full[full.year >= 2017]
win = r[r.period.isin(["2023", "2024", "2025", "2026H1"])]
lines = [
    f"years ahead of the blended benchmark: {(full.excess > 0).sum()} of {len(full)} (2005-2025)",
    f"2005-2016: ahead in {(early.excess > 0).sum()} of {len(early)}, average {early.excess.mean():+.2f} pts a year",
    f"2017-2025: ahead in {(late.excess > 0).sum()} of {len(late)}, average {late.excess.mean():+.2f} pts a year",
    f"2005-2025 compounded: fund {cg(full.nav_total_return):.1f}%, blended benchmark {cg(full.blended_benchmark):.1f}%",
    f"Jan 2023 to Jun 2026: fund {cg(win.nav_total_return):.1f}%, blended benchmark {cg(win.blended_benchmark):.1f}%, gap {cg(win.nav_total_return)-cg(win.blended_benchmark):+.1f} pts",
    f"first half of 2026: fund {r.iloc[-1].nav_total_return}% vs blended {r.iloc[-1].blended_benchmark}% and All Equity REITs {r.iloc[-1].nareit_equity_index}%",
]
save("manager_record.txt", "\n".join(lines) + "\n")

# How much should anyone lean on the post-2016 run? t-stats, rolling 5-year information ratio,
# and a test of whether any break point looks special once you allow for having picked it after the fact.
import numpy as np
x = full.set_index("year").excess
t = lambda v: v.mean() / (v.std(ddof=1) / len(v) ** 0.5)
roll = pd.DataFrame({"mean": x.rolling(5).mean(), "sd": x.rolling(5).std(ddof=1)})
roll["info_ratio"] = roll["mean"] / roll["sd"]
roll.round(2).to_csv(os.path.join(RESULTS, "manager_rolling_5y.csv"))


def best_break(v):
    best = 0
    for k in range(4, len(v) - 3):     # at least 4 years on each side
        a, b = v[:k], v[k:]
        best = max(best, abs(b.mean() - a.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))
    return best


obs = best_break(x.values)
rng = np.random.default_rng(2017)
perm = np.array([best_break(rng.permutation(x.values)) for _ in range(10000)])
lines2 = [
    f"t-stat of the average excess: 2005-2025 {t(x):.2f} (mean {x.mean():+.2f}, sd {x.std(ddof=1):.2f}); 2017-2025 {t(x.loc[2017:]):.2f} (mean {x.loc[2017:].mean():+.2f}, sd {x.loc[2017:].std(ddof=1):.2f}); 2005-2016 {t(x.loc[:2016]):.2f}",
    f"rolling 5-year information ratio (mean excess / sd): last {roll.info_ratio.iloc[-1]:.2f} (2021-2025); highest {roll.info_ratio.max():.2f} ({int(roll.info_ratio.idxmax())}); lowest {roll.info_ratio.min():.2f} ({int(roll.info_ratio.idxmin())})",
    f"break test: the biggest before/after difference over every split point scores {obs:.2f}; random reorderings of the same 21 years beat that in {(perm >= obs).mean()*100:.1f}% of 10,000 tries",
    f"years ahead since 2017 under a coin flip: chance of 8 or more of 9 = {sum(__import__('math').comb(9,k) for k in (8,9))/2**9*100:.1f}%",
]
with open(os.path.join(RESULTS, "manager_record.txt"), "a") as f:
    f.write("\n".join(lines2) + "\n")
print("\n".join(lines2))
