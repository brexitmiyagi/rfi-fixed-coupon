# The check: what RFI paid in 1993, what it pays now, and what inflation did to it.
from common import *

d = dists()
reg = d[d.special.isna()]
first = reg.iloc[0]
last = reg.iloc[-1]
monthly8 = (reg.amount == 0.08).sum()

cpi = pd.read_csv(os.path.join(DATA, "fred_cpiaucsl.csv"), parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
c0, c1 = cpi.loc["1993-11-01"], cpi.iloc[-1]
real = PAYOUT * c0 / c1

y = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
y = pd.to_numeric(y, errors="coerce")
s = snap()

lines = [
    f"first regular distribution: ex {first.ex_date.date()} ${first.amount:.2f}",
    f"latest regular distribution: ex {last.ex_date.date()} ${last.amount:.2f}",
    f"regular payments of exactly $0.08 on record: {monthly8}",
    f"CPI Nov 1993 {c0:.1f}, latest ({cpi.index[-1].date()}) {c1:.3f}, ratio {c1/c0:.4f}",
    f"$0.96 a year in Nov 1993 dollars: ${real:.3f} ({(real/PAYOUT-1)*100:.1f}%)",
    f"10-year Treasury, Nov 1993 average {y['1993-11'].mean():.2f}%, Dec 1995 average {y['1995-12'].mean():.2f}%, 18 Nov 2026 {s['ust_10y']:.2f}%",
]
save("coupon_history.txt", "\n".join(lines) + "\n")
