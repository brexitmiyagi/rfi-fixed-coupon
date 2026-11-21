# One year of discounts across real estate, preferred and infrastructure CEFs, and RFI against its levered sibling RQI.
from common import *

p = pd.read_csv(os.path.join(DATA, "peer_cef_daily_1y_cefconnect.csv"), parse_dates=["date"])
first = p.sort_values("date").groupby("ticker").first()
last = p.sort_values("date").groupby("ticker").last()
t = pd.DataFrame({"start_date": first.date.dt.date, "start": first.discount_pct, "end_date": last.date.dt.date, "end": last.discount_pct})
t["change"] = t.end - t.start
t = t.sort_values("change")
t.round(2).to_csv(os.path.join(RESULTS, "peer_discount_change_1y.csv"))
w = pd.read_csv(os.path.join(DATA, "rfi_rqi_rnp_weekly_cefconnect.csv"), parse_dates=["date"]).pivot(index="date", columns="ticker", values="discount_pct").dropna()
w["rfi_minus_rqi"] = w.RFI - w.RQI
s = snap()
gap_now = (s["rfi_close"]/s["rfi_nav"] - s["rqi_close"]/s["rqi_nav"]) * 100
lines = [t.round(2).to_string(),
         f"RFI minus RQI discount, 20 Nov 2026: {gap_now:+.2f} pts"]
for a in ["2016", "2021"]:
    x = w[a:].rfi_minus_rqi
    lines.append(f"weekly since {a}: median {x.median():+.2f} pts, share of weeks at or below today {(x<=gap_now).mean()*100:.1f}%")
w[["RFI", "RQI", "rfi_minus_rqi"]].round(2).to_csv(os.path.join(RESULTS, "rfi_vs_rqi_weekly.csv"))
save("peers.txt", "\n".join(lines) + "\n")

wider = w[w.RFI < w.RQI]
extra = (f"weeks RFI traded at a wider discount than RQI: 2020 to 2025 {len(wider['2020':'2025'])}, "
         f"last before 2026 {wider[:'2025'].index[-1].date()}, in 2026 {len(wider['2026':])} ({wider['2026':].index[0].date()} to {wider['2026':].index[-1].date()})\n")
with open(os.path.join(RESULTS, "peers.txt"), "a") as fh:
    fh.write(extra)
print(extra)
