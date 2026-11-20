# A fixed dollar payout D on a book that earns r a year has a balance point at NAV = D / r.
# Above it NAV grows, below it NAV shrinks. This checks where RFI has actually been sitting.
from common import *
import numpy as np

df = weekly()
s = snap()
tri = nav_total_return_index(df)
end_day = pd.Timestamp("2026-11-18")
d = dists().set_index("ex_date")["amount"]

def ann_tr(start):
    t0 = df.index[df.index >= start][0]
    u = tri.iloc[-1] / tri.loc[t0] * s["rfi_nav"] / df.nav.iloc[-1]
    yrs = (end_day - t0).days / 365.25
    return t0, (u ** (1 / yrs) - 1) * 100, yrs

lines = []
for start in ["2022-09-30", "2016-10-14"]:
    t0, r, yrs = ann_tr(start)
    po = (PAYOUT / df.loc[t0:, "nav"]).mean() * 100
    lines.append(f"since {t0.date()}: NAV {df.loc[t0,'nav']:.2f} -> {s['rfi_nav']:.2f}, NAV total return {r:.2f}% a year over {yrs:.2f} yrs, average payout/NAV {po:.2f}%, paid ${d[(d.index>t0)&(d.index<=end_day)].sum():.2f}")

for r in [0.0623, 0.0849, PAYOUT / s["rfi_nav"]]:
    lines.append(f"balance-point NAV at r={r*100:.2f}%: ${PAYOUT/r:.2f}")
lines.append(f"payout / NAV today: {PAYOUT/s['rfi_nav']*100:.2f}%")
f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
lines.append(f"10-year NAV return to June 30 2026 (N-CSRS): {f['nav_tr_10y_to_2026_06_30_pct']}%")
save("fixed_point.txt", "\n".join(lines) + "\n")

a = pd.read_csv(os.path.join(DATA, "annual_report_per_share.csv")).set_index("year").loc[2025]
gross_need = PAYOUT / s["rfi_nav"] * 100 + a.expense_ratio_pct
income = a.nii_ratio_pct + a.expense_ratio_pct
extra = f"to hold NAV flat the book needs {gross_need:.2f}% gross a year; 2025 book income yield {income:.2f}%; so {gross_need-income:.2f}% a year has to come from price gains\n"
with open(os.path.join(RESULTS, "fixed_point.txt"), "a") as fh:
    fh.write(extra)
print(extra)
