# Where the discount sits against its own history, what happened after past drops below -8%, and the Nov-to-Jan pattern.
from common import *
import numpy as np

df = weekly()
s = snap()
disc_now = (s["rfi_close"] / s["rfi_nav"] - 1) * 100
lines = [f"discount 20 Nov 2026: {disc_now:.2f}% (close {s['rfi_close']}, NAV {s['rfi_nav']})"]
for a in ["1996", "2016-10"]:
    x = df[a:].discount_pct
    lines.append(f"weekly since {a}: median {x.median():.2f}%, share of weeks at or below today {(x<=disc_now).mean()*100:.1f}%")
w = df.discount_pct
prior = w[(w <= disc_now) & (w.index < "2026-01-01")]
lines.append(f"last weeks at or below today before 2026: {', '.join(str(i.date()) for i in prior.index[-3:])}")
fwd = w.shift(-52)
for a in ["1996", "2016-10"]:
    x = df[a:].discount_pct; f = fwd[a:]
    msk = (x <= -8) & f.notna()
    lines.append(f"since {a}, weeks at or below -8% with a year of data after: {msk.sum()}; discount 52 weeks later median {f[msk].median():.2f}%, narrower in {( (f[msk]-x[msk])>0).mean()*100:.0f}% of them")
lines.append(f"Dec 2022 year-end discount: {w['2022-12'].iloc[-1]:+.2f}%")
rows = []
for y in range(1996, 2026):
    a = w[f"{y}-11-12":f"{y}-11-20"]; c = w[f"{y+1}-01-24":f"{y+1}-01-31"]
    if len(a) and len(c):
        rows.append((y, a.iloc[0], c.iloc[-1], c.iloc[-1] - a.iloc[0]))
seas = pd.DataFrame(rows, columns=["year", "mid_nov", "end_jan", "change"])
seas.round(2).to_csv(os.path.join(RESULTS, "nov_to_jan.csv"), index=False)
lines.append(f"mid-Nov to end-Jan: {len(seas)} years, narrower in {(seas.change>0).sum()}, median change {seas.change.median():+.2f} pts, mean {seas.change.mean():+.2f}")
save("discount.txt", "\n".join(lines) + "\n")

# is the discount just a rates trade? weekly change in discount on weekly change in the 10-year, with NAV return as a control
import statsmodels.api as sm
y = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
df["y10"] = pd.to_numeric(y, errors="coerce").ffill().reindex(df.index, method="ffill")
r = pd.DataFrame({"dd": df.discount_pct.diff(), "dy": df.y10.diff(), "rn": np.log(df.nav).diff() * 100})
r = r[df.index.to_series().diff().dt.days == 7].dropna()["2016-10":]
fit = sm.OLS(r.dd, sm.add_constant(r[["dy", "rn"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
extra = f"weekly discount change on 10-year change since Oct 2016: {fit.params['dy']:.2f} pts per 1pt, HAC t {fit.tvalues['dy']:.2f}, n {len(r)}, R2 {fit.rsquared:.3f}\n"
with open(os.path.join(RESULTS, "discount.txt"), "a") as fh:
    fh.write(extra)
print(extra)

# the weekly counts above overlap, so also count separate episodes: the first week at or below -8% after at least
# 60 days above it, and where the discount was 52 weeks later
x = df.discount_pct
hit = x[x <= -8]
starts = hit[~(hit.index.to_series().diff().dt.days <= 60)]
ep = pd.DataFrame({"start_discount": starts, "a_year_later": [x.shift(-52).loc[d] for d in starts.index]}).dropna()
ep.round(2).to_csv(os.path.join(RESULTS, "discount_episodes.csv"))
extra = (f"separate episodes since 1996 at or below -8% with a year after: {len(ep)}; narrower a year later in {(ep.a_year_later > ep.start_discount).sum()}; "
         f"year-later discount median {ep.a_year_later.median():.2f}%, range {ep.a_year_later.min():.2f}% to {ep.a_year_later.max():.2f}%\n"
         + ep.round(2).to_string() + "\n")
with open(os.path.join(RESULTS, "discount.txt"), "a") as fh:
    fh.write(extra)
print(extra)
