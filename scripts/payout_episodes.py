# Every month since 1996 where the $0.96 ran at 8% of NAV or more, and what NAV total return did over the next 3 years.
from common import *
import numpy as np
import statsmodels.api as sm

df = weekly()
df["tri"] = nav_total_return_index(df)
m = df.resample("ME").last()
m["payout_pct"] = PAYOUT / m.nav * 100
m["fwd3y"] = ((m.tri.shift(-36) / m.tri) ** (1 / 3) - 1) * 100
hi = m[m.payout_pct >= 8.0].copy()
# group into episodes: a new episode starts after a gap of more than 6 months
hi["ep"] = (hi.index.to_series().diff().dt.days > 185).cumsum()
eps = hi.groupby("ep").agg(start=("nav", lambda x: x.index[0].date()), end=("nav", lambda x: x.index[-1].date()),
                           months=("nav", "size"), max_payout=("payout_pct", "max"), min_nav=("nav", "min"),
                           fwd3y_mean=("fwd3y", "mean"), fwd3y_min=("fwd3y", "min"))
eps.round(2).to_csv(os.path.join(RESULTS, "payout_8pct_episodes.csv"), index=False)
done = m.dropna(subset=["fwd3y"])
X = sm.add_constant(done.payout_pct)
fit = sm.OLS(done.fwd3y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 36})
lines = [eps.round(2).to_string(),
         f"completed months at >=8%: {hi.fwd3y.notna().sum()}, mean next-3y NAV TR {hi.fwd3y.mean():.1f}%, lowest {hi.fwd3y.min():.1f}%",
         f"months below 8%: mean next-3y NAV TR {done[done.payout_pct<8].fwd3y.mean():.1f}%",
         f"regression next-3y NAV TR on payout/NAV, 1996-2023 starts: slope {fit.params['payout_pct']:.2f}, HAC t {fit.tvalues['payout_pct']:.2f}, R2 {fit.rsquared:.2f}, n {len(done)} (overlapping windows, few independent episodes)"]
save("payout_episodes.txt", "\n".join(lines) + "\n")
