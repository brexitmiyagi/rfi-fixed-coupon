# Can you put money into it, and what's the clean hedge?
# Size: common shares and net assets from the June 30, 2026 semi-annual report, valued at the Nov 20 close.
# Liquidity: daily volume from Nasdaq. Hedge: weekly price returns over the three years to Nov 20, 2026,
# RFI regressed on VNQ and on Welltower's return over VNQ, so the short is VNQ for sector beta plus WELL for the extra.
from common import *
import numpy as np
import warnings
warnings.filterwarnings("ignore")

s = snap()
f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
d = pd.read_csv(os.path.join(DATA, "daily_nasdaq_rfi_vnq_well_xlre_2021_2026.csv"), parse_dates=["date"])
px = d.pivot(index="date", columns="ticker", values="close").sort_index()
vol = d[d.ticker == "RFI"].set_index("date").sort_index()
vol["dollars"] = vol.volume * vol.close
end = vol.index[-1]
v3m = vol[vol.index > end - pd.Timedelta(days=91)]
v1y = vol[vol.index > end - pd.Timedelta(days=365)]
shares = f["shares_outstanding_2026_06_30"]
mcap = shares * s["rfi_close"]
adv_d = v3m.dollars.median()

wk = px.resample("W-FRI").last()
wk = wk[wk.index > end - pd.Timedelta(days=3 * 365)]
r = wk.pct_change().dropna()
X = np.column_stack([np.ones(len(r)), r.VNQ, r.WELL - r.VNQ])
b = np.linalg.lstsq(X, r.RFI.values, rcond=None)[0]
bn = np.linalg.lstsq(X, r.XRFIX.values, rcond=None)[0]
res = r.RFI.values - X @ b
r2 = 1 - res.var() / r.RFI.var()
b1 = np.linalg.lstsq(np.column_stack([np.ones(len(r)), r.VNQ]), r.RFI.values, rcond=None)[0]
# weights per $100 of RFI: short b_vnq - b_well of VNQ and b_well of WELL
w_well = b[2]
w_vnq = b[1] - b[2]
hedged = r.RFI - (w_vnq * r.VNQ + w_well * r.WELL)
v = pd.read_excel(os.path.join(DATA, "nareit", "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
reit_yield = float(pd.to_numeric(v[27], errors="coerce").dropna().iloc[-1])  # All Equity REITs dividend yield, latest month
well_yield = 0.85 * 4 / 240.34 * 100   # Welltower's $0.85 quarterly dividend at the Nov 20 close
rfi_yield = PAYOUT / s["rfi_close"] * 100
carry = rfi_yield - w_vnq * reit_yield - w_well * well_yield
lines = [
    f"common shares {shares:,.0f} (June 30, 2026); market cap at ${s['rfi_close']:.2f}: ${mcap/1e6:.0f} million; net assets at ${s['rfi_nav']:.2f} NAV: ${shares*s['rfi_nav']/1e6:.0f} million",
    f"volume, 3 months to {end.date()}: median {v3m.volume.median():,.0f} shares a day (${adv_d/1e6:.2f} million); 1 year median {v1y.volume.median():,.0f} (${v1y.dollars.median()/1e6:.2f} million)",
    f"a $1 million position is {1e6/adv_d:.1f} days of median 3-month volume; 20% participation means {1e6/(0.2*adv_d):.0f} trading days",
    f"weekly price returns, {len(r)} weeks to {end.date()}: RFI = {b[0]*100:.2f}% + {b[1]:.2f} x VNQ + {b[2]:.2f} x (WELL - VNQ), R2 {r2:.2f}",
    f"same for RFI's NAV (XRFIX): {bn[1]:.2f} x VNQ + {bn[2]:.2f} x (WELL - VNQ)",
    f"VNQ alone: beta {b1[1]:.2f}",
    f"hedge per $100 of RFI: short ${w_vnq*100:.0f} of VNQ and ${w_well*100:.0f} of WELL",
    f"carry of the hedged trade before borrow costs: {rfi_yield:.2f}% - {w_vnq:.2f} x {reit_yield:.2f}% (All Equity REITs yield as a stand-in for VNQ's) - {w_well:.2f} x {well_yield:.2f}% = {carry:.2f}% a year",
    f"weekly volatility annualized: RFI {r.RFI.std()*52**0.5*100:.1f}%, hedged {hedged.std()*52**0.5*100:.1f}%",
]
save("liquidity_and_hedge.txt", "\n".join(lines) + "\n")
