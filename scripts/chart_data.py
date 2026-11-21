# Writes the exact CSVs behind each chart in the post.
from common import *
import numpy as np

a = pd.read_csv(os.path.join(DATA, "annual_report_per_share.csv"))
y = pd.read_csv(os.path.join(DATA, "fred_dgs10.csv"), parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
y = pd.to_numeric(y, errors="coerce")
yavg = y.groupby(y.index.year).mean()
out = os.path.join(RESULTS, "charts")
os.makedirs(out, exist_ok=True)

d = dists()
# CEF Connect only flags some extras with "S". Two more are year-end gains payouts on top of December's regular
# $0.08 (Dec 23, 2020: $0.05; Dec 27, 2022: $0.266), so I leave them out of the regular line by date.
extra = d.ex_date.isin(pd.to_datetime(["2020-12-23", "2022-12-27"]))
reg = d[d.special.isna() & ~extra].groupby(d.ex_date.dt.year).amount.sum()
c1 = pd.DataFrame({"Year": a.year, "Net investment income per share": a.nii_per_share,
                   "Regular payout per share (no year-end extras)": a.year.map(reg).round(4)})
c1.to_csv(os.path.join(out, "c1_who_pays.csv"), index=False)

c2 = pd.DataFrame({"Year": a.year, "RFI book income yield (NII + expenses, % of net assets)": (a.nii_ratio_pct + a.expense_ratio_pct).round(2),
                   "10-year Treasury (annual average)": a.year.map(yavg).round(2)})
c2.to_csv(os.path.join(out, "c2_book_vs_treasury.csv"), index=False)

w = weekly()
c4 = w["2019":][["nav"]].resample("2W").last().rename(columns={"nav": "NAV per share"})
c4.index = c4.index.date
c4.to_csv(os.path.join(out, "c4_nav_since_2019.csv"), index_label="Week")

r = pd.read_csv(os.path.join(DATA, "rfi_rqi_rnp_weekly_cefconnect.csv"), parse_dates=["date"]).pivot(index="date", columns="ticker", values="discount_pct")
c6 = r["2016":][["RFI", "RQI"]].dropna().resample("ME").last().rename(columns={"RFI": "RFI (no leverage)", "RQI": "RQI (leveraged sibling)"})
c6.index = c6.index.date
c6.to_csv(os.path.join(out, "c6_rfi_vs_rqi.csv"), index_label="Week")

pc = pd.read_csv(os.path.join(RESULTS, "peer_discount_change_1y.csv"))
pc[["ticker", "change"]].rename(columns={"ticker": "Fund", "change": "Change in discount, pts"}).to_csv(os.path.join(out, "c7_peer_change.csv"), index=False)

nj = pd.read_csv(os.path.join(RESULTS, "nov_to_jan.csv"))
nj["Season"] = nj.year.astype(str) + "/" + (nj.year + 1).astype(str).str[-2:]
nj[["Season", "change"]].rename(columns={"change": "Mid-Nov to end-Jan change (pts)"}).to_csv(os.path.join(out, "c9_nov_jan.csv"), index=False, float_format="%.2f")
f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
s19 = pd.read_csv(os.path.join(DATA, "section19_2026_ytd.csv")).set_index("month").loc["October"]
sh = f["shares_outstanding_2026_06_30"]
c3 = pd.DataFrame([
    ["Paid January to October 2026", f"${s19.ytd_total:.3f}", "ten checks of $0.08"],
    ["Labelled net investment income", f"${s19.ytd_nii:.3f}", f"{s19.ytd_nii/s19.ytd_total*100:.1f}%"],
    ["Labelled short-term gains", f"${s19.ytd_st_gain:.3f}", f"{s19.ytd_st_gain/s19.ytd_total*100:.1f}%"],
    ["Labelled return of capital", f"${s19.ytd_return_of_capital:.3f}", f"{s19.ytd_return_of_capital/s19.ytd_total*100:.1f}%"],
    ["Gains realized, first half 2026", f"${f['h1_net_realized_gain']/sh:.3f}", f"${f['h1_net_realized_gain']/1e6:.2f}m"],
    ["Gains left unrealized, first half 2026", f"${f['h1_change_unrealized']/sh:.3f}", f"${f['h1_change_unrealized']/1e6:.2f}m"],
    ["Unsold gains in the book, June 30", f"${f['net_unrealized_appreciation']/sh:.2f}", f"${f['net_unrealized_appreciation']/1e6:.2f}m over a ${f['tax_cost_investments']/1e6:.1f}m tax cost"],
    ["Return of capital on the final 2025 tax numbers", f"${f['tax_roc_per_share_2025']:.2f}", "of $0.96"],
], columns=["Item", "Per share", "Detail"])
c3.to_csv(os.path.join(out, "c3_roc_vs_book.csv"), index=False)
ep = pd.read_csv(os.path.join(RESULTS, "payout_8pct_episodes.csv"), parse_dates=["start", "end"])
def label(r):
    a, b = r.start.strftime("%b %Y"), r.end.strftime("%b %Y")
    if r.end >= pd.Timestamp("2026-11-01"):
        return f"{a} to now"
    if a == b:
        return a
    if r.start.year == r.end.year:
        return f"{r.start.strftime('%b')} to {b}"
    return f"{a} to {b}"
star = lambda r: "*" if r.end >= pd.Timestamp("2026-11-01") else ""
c5 = pd.DataFrame({"Episode": ep.apply(label, axis=1), "Months at 8%+": ep.months,
                   "Peak payout/NAV": ep.max_payout.map(lambda v: f"{v:.1f}%"), "Low NAV": ep.min_nav.map(lambda v: f"${v:.2f}"),
                   "Next 3 yrs NAV return (avg)": [f"{v:.1f}% a yr{star(r)}" for v, (_, r) in zip(ep.fwd3y_mean, ep.iterrows())],
                   "Next 3 yrs (worst)": [f"{v:.1f}% a yr{star(r)}" for v, (_, r) in zip(ep.fwd3y_min, ep.iterrows())]})
c5.to_csv(os.path.join(out, "c5_episodes.csv"), index=False)
sc = pd.read_csv(os.path.join(RESULTS, "scenarios.csv"))
pv = sc.pivot(index="nav_change_pct", columns="discount_pct", values="total_return_pct").sort_index(ascending=False)
pv.columns = [f"Discount {c:.2f}%" for c in pv.columns]
pv.index = [f"NAV {i:+d}%" for i in pv.index]
pv = pv.map(lambda v: f"{v:+.1f}%")
pv.to_csv(os.path.join(out, "c8_scenarios.csv"), index_label="12-month NAV change")
print("chart csvs written")

# run holdings_attribution.py and lookthrough_valuation.py first
t = pd.read_csv(os.path.join(RESULTS, "attribution_total_by_security.csv"))
short = {"Welltower Inc": "Welltower", "Simon Property Group Inc": "Simon Property", "Digital Realty Trust Inc": "Digital Realty",
         "Iron Mountain Inc": "Iron Mountain", "Equinix Inc": "Equinix", "Prologis Inc": "Prologis", "Lamar Advertising Co": "Lamar",
         "Kimco Realty Corp": "Kimco", "Crown Castle Inc": "Crown Castle", "Weyerhaeuser Co": "Weyerhaeuser",
         "Invitation Homes Inc": "Invitation Homes", "Mid-America Apartment Communities Inc": "Mid-America Apartment"}
c10 = pd.concat([t.head(8), t.tail(4)])
c10 = pd.DataFrame({"Holding": c10.name.map(lambda n: short.get(n, n)), "Contribution to book price return, pts": c10.contrib_pts})
c10.to_csv(os.path.join(out, "c10_contributors.csv"), index=False)
v = pd.read_csv(os.path.join(RESULTS, "lookthrough_valuation.csv"))
c11 = pd.DataFrame({"Holding": v.name, "Weight in RFI (Jun 30)": v.weight_jun30_pct.map(lambda x: f"{x:.2f}%"),
                    "Price (Nov 20)": v.price_2026_11_20.map(lambda x: f"${x:.2f}"),
                    "2026 guidance": [f"${lo:.2f}-{hi:.2f} {k.replace(' per share','')}" for lo, hi, k in zip(v.metric_2026_low, v.metric_2026_high, v.metric)],
                    "Multiple": v.multiple.map(lambda x: f"{x:.1f}x"), "Cash-earnings yield": v.earnings_yield_pct.map(lambda x: f"{x:.2f}%")})
c11.to_csv(os.path.join(out, "c11_lookthrough.csv"), index=False)
print("added c10, c11")

wb = pd.read_csv(os.path.join(RESULTS, "welltower_weights_vs_benchmarks.csv"), index_col=0).loc["2022-09-30":]
caps = pd.read_csv(os.path.join(DATA, "nareit", "nareit_constituent_caps.csv"), parse_dates=["snapshot_date"])
nw = pd.Series((caps.welltower_musd / caps.equity_reits_total_musd * 100).values, index=caps.snapshot_date)
qd = pd.to_datetime(wb.index)
nareit_q = pd.Series(np.interp(qd.astype("int64"), nw.index.astype("int64"), nw.values), index=wb.index)
nareit_q[qd < nw.index[0]] = np.nan
pd.DataFrame({"Quarter end": wb.index, "FTSE Nareit All Equity REITs (from year-end files)": nareit_q.round(2), "RFI (share of its REIT stocks)": wb["RFI Welltower as % of its REIT stocks"].round(2),
              "Cohen & Steers Realty Shares (CSRSX)": wb.CSRSX.round(2), "XLRE": wb.XLRE.round(2),
              "VNQ (interpolated to quarter-ends)": wb["VNQ (interpolated to quarter-end)"].round(2)}).to_csv(os.path.join(out, "c12_overweight.csv"), index=False)
print("added c12")

b = pd.read_csv(os.path.join(RESULTS, "brinson_by_sector.csv"))
b[["sector", "allocation", "selection", "interaction"]].rename(columns={"sector": "Sector", "allocation": "Sector weight (allocation)",
    "selection": "Stock picking (selection)", "interaction": "Interaction"}).to_csv(os.path.join(out, "c13_brinson_sector.csv"), index=False)
m = pd.read_csv(os.path.join(RESULTS, "manager_record.csv"), dtype={"period": str})
m = m[m.period != "2026H1"]
m[["period", "excess"]].rename(columns={"period": "Year", "excess": "RFI NAV return minus its blended benchmark, pts"}).to_csv(os.path.join(out, "c14_manager_excess.csv"), index=False)
pdv = pd.read_csv(os.path.join(RESULTS, "discount_panel_by_deviation.csv"))
pdv[["deviation_from_own_3yr_avg_pts", "median_1y_change_pts", "pct_narrower", "fund_weeks"]].rename(columns={
    "deviation_from_own_3yr_avg_pts": "Discount vs the fund's own 3-year average, pts", "median_1y_change_pts": "Median change a year later, pts",
    "pct_narrower": "% narrower a year later", "fund_weeks": "Fund-weeks"}).to_csv(os.path.join(out, "c15_panel.csv"), index=False)
sc = pd.read_csv(os.path.join(RESULTS, "scenarios_weighted.csv"))
pd.DataFrame({"Case": sc.case.str.title() + " (" + (sc.prob * 100).astype(int).astype(str) + "%)",
              "REIT benchmark year": sc.reit_market.map(lambda x: f"{x:+.1f}%"), "Manager vs benchmark": sc.manager_vs_benchmark.map(lambda x: f"{x:+.1f} pts"),
              "NAV in 12 months": sc.nav_in_12m.map(lambda x: f"${x:.2f}"), "Discount": sc.discount.map(lambda x: f"{x:.1f}%"),
              "Price": sc.price_in_12m.map(lambda x: f"${x:.2f}"), "Total return": sc.total_return.map(lambda x: f"{x:+.1f}%"),
              "vs benchmark": sc.vs_benchmark.map(lambda x: f"{x:+.1f} pts")}).to_csv(os.path.join(out, "c16_scenarios.csv"), index=False)
print("added c13-c16")

ws = pd.read_csv(os.path.join(RESULTS, "welltower_share_of_edge.csv")).sum(numeric_only=True) * 100
pd.DataFrame({"Source": ["Welltower overweight", "Every other REIT position"],
              "Points of edge over the index": [round(ws.active_well, 2), round(ws.total_active - ws.active_well, 2)]}).to_csv(os.path.join(out, "c17_welltower_vs_rest.csv"), index=False)
js = pd.read_csv(os.path.join(RESULTS, "joint_simulation.csv"))
b = js[js.setting == "valuation-adjusted base"].set_index("fund")
lev = {"RFI": "almost none", "RQI": "24.9%", "RNP": "26.7%"}
pd.DataFrame({"Fund": b.index, "Discount Nov 20": b.discount_now.map(lambda x: f"{x:.2f}%"), "Borrowing / assets": [lev[f] for f in b.index],
              "REIT beta": b.beta, "Expected total return": b.exp_total.map(lambda x: f"{x:+.1f}%"), "Worst 5% from": b.p5.map(lambda x: f"{x:+.1f}%"),
              "Chance of loss": b.prob_loss.map(lambda x: f"{x:.0f}%"), "Edge over REITs": b.exp_edge.map(lambda x: f"{x:+.1f} pts"),
              "Beats REITs": b.prob_beat_reits.map(lambda x: f"{x:.0f}%"), "If valuations bite": js[js.setting == "regression since 1990"].set_index("fund").exp_total.map(lambda x: f"{x:+.1f}%")}).to_csv(
    os.path.join(out, "c18_three_funds.csv"), index=False)
r = js[(js.fund == "RFI") & ~js.setting.str.contains("common")]
names = {"valuation-adjusted base": "Base: REITs earn 4.8%", "regression since 1990": "Valuations bite: REITs -0.5%", "unconditional": "History repeats: REITs 11.4%"}
pd.DataFrame({"Case": r.setting.map(names), "Expected price in 12 months": r.exp_price.map(lambda x: f"${x:.2f}"),
              "Expected total return": r.exp_total.map(lambda x: f"{x:+.1f}%"), "Median": r.p50.map(lambda x: f"{x:+.1f}%"),
              "5th percentile": r.p5.map(lambda x: f"{x:+.1f}%"), "90th percentile": r.p90.map(lambda x: f"{x:+.1f}%"),
              "Chance of loss": r.prob_loss.map(lambda x: f"{x:.0f}%"), "Beats REITs": r.prob_beat_reits.map(lambda x: f"{x:.0f}%")}).to_csv(
    os.path.join(out, "c19_simulation.csv"), index=False)
pt = os.path.join(RESULTS, "price_target.csv")   # run price_target.py first
if os.path.exists(pt):
    b_ = pd.read_csv(pt).iloc[1]
    c19 = pd.read_csv(os.path.join(out, "c19_simulation.csv"))
    c19.loc[len(c19)] = [f"Corrected for past optimism: REITs {b_.reits:+.1f}%", f"${b_.exp_price:.2f}", f"{b_.exp_total:+.1f}%", f"{b_.p50:+.1f}%",
                         f"{b_.p5:+.1f}%", f"{b_.p90:+.1f}%", f"{b_.prob_loss:.0f}%", f"{b_.prob_beat:.0f}%"]
    c19.to_csv(os.path.join(out, "c19_simulation.csv"), index=False)
h = pd.read_csv(os.path.join(RESULTS, "joint_simulation_rfi_histogram.csv"))
h["Bucket"] = h["from"].astype(int).astype(str) + " to " + h["to"].astype(int).astype(str)
h[["Bucket", "share_pct"]].rename(columns={"share_pct": "% of 20,000 runs"}).to_csv(os.path.join(out, "c20_histogram.csv"), index=False)
print("added c17-c20")

g = pd.read_csv(os.path.join(RESULTS, "reit_yield_gap_monthly.csv"), parse_dates=["date"])
g = g[g.date.dt.month.isin([3, 6, 9, 12]) | (g.date == g.date.max())]
g.assign(Date=g.date.dt.strftime("%Y-%m"))[["Date", "gap"]].rename(columns={"gap": "REIT dividend yield minus 10-year Treasury, pts"}).to_csv(
    os.path.join(out, "c21_yield_gap_quarterly.csv"), index=False)
print("added c21")
