# Is the edge really Welltower, or health care in general? Stock-level check on top of brinson.py.
# For each quarter: Welltower's active weight (RFI's REIT-stock weight minus its weight in the Nareit All Equity index)
# times Welltower's return over the index. Then the same inside health care: RFI's Welltower share of its health care
# stocks minus Welltower's share of Nareit health care, times Welltower over the health care index, scaled by the
# index's health care weight (the Brinson selection convention). Index weights for Welltower come from Nareit's year-end
# files, drifted to each quarter start with Welltower's own price (Nasdaq) and the index price levels.
from common import *
import warnings
warnings.filterwarnings("ignore")

# reuse brinson.py's loaders without rerunning its output
src = open(os.path.join(HERE, "brinson.py")).read().split("Q = pd.read_csv")[0]
ns = {"__file__": os.path.join(HERE, "brinson.py")}
exec(compile(src, "brinson_head", "exec"), ns)
PX, ALL, at, caps, bench_weights, SECTOR, NOT_IN_INDEX = (ns[k] for k in ["PX", "ALL", "at", "caps", "bench_weights", "SECTOR", "NOT_IN_INDEX"])

WELL = "95040Q104"
d = pd.read_csv(os.path.join(DATA, "daily_nasdaq_rfi_vnq_well_xlre_2021_2026.csv"), parse_dates=["date"])
wpx = d[d.ticker == "WELL"].set_index("date").close.sort_index()
wpx_at = lambda t: wpx[wpx.index <= pd.Timestamp(t)].iloc[-1]


def well_index_weights(q):
    """Welltower's weight in All Equity REITs and in Nareit health care at date q."""
    q = pd.Timestamp(q)
    snaps = caps.snapshot_date.sort_values()
    s = snaps[snaps <= q].iloc[-1] if (snaps <= q).any() else snaps.iloc[0]
    row = caps[caps.snapshot_date == s].iloc[0]
    wcap = row.welltower_musd * wpx_at(q) / wpx_at(s)
    tot = row.equity_reits_total_musd * at(ALL, q) / at(ALL, s)
    hc = row.health_care_musd * at(PX["Health Care"], q) / at(PX["Health Care"], s)
    return wcap / tot, wcap / hc


Q = pd.read_csv(os.path.join(RESULTS, "attribution_by_quarter.csv"), dtype={"cusip": str})
Q = Q[(Q.cat == "EC") & ~Q.cusip.isin(NOT_IN_INDEX)].copy()
quarters = sorted(Q.quarter_end.unique())
prev = dict(zip(quarters, ["2022-06-30"] + quarters[:-1]))
B = pd.read_csv(os.path.join(RESULTS, "brinson_by_quarter_sector.csv"))
rows = []
for b in quarters:
    a = prev[b]
    if a < "2022-09-30":
        continue
    q = Q[Q.quarter_end == b].copy()
    q["w"] = q.v0 / q.v0.sum()
    q["sector"] = q.cusip.map(SECTOR)
    hcq = q[q.sector == "Health Care"]
    w_rfi = q.loc[q.cusip == WELL, "w"].sum()
    w_rfi_hc = w_rfi / hcq.w.sum()
    r_w = q.loc[q.cusip == WELL, "move"].iloc[0]
    w_idx, w_idx_hc = well_index_weights(a)
    r_idx = at(ALL, b) / at(ALL, a) - 1
    r_hc = at(PX["Health Care"], b) / at(PX["Health Care"], a) - 1
    bq = B[B.quarter_end == b]
    hc_b = bq[bq.sector == "Health Care"].iloc[0]
    rows.append(dict(quarter_end=b, w_rfi=w_rfi, w_index=w_idx, r_well=r_w, r_index=r_idx,
                     active_well=(w_rfi - w_idx) * (r_w - r_idx),
                     w_rfi_in_hc=w_rfi_hc, w_index_in_hc=w_idx_hc, r_hc_index=r_hc,
                     hc_selection=hc_b.selection, hc_selection_well=hc_b.w_index * (w_rfi_hc - w_idx_hc) * (r_w - r_hc),
                     total_active=(bq.w_rfi * bq.r_rfi).sum() - bq.r_index.iloc[0]))
W = pd.DataFrame(rows)
W.to_csv(os.path.join(RESULTS, "welltower_share_of_edge.csv"), index=False)
s = W.sum(numeric_only=True) * 100
lines = [
    f"{len(W)} quarters ending {W.quarter_end.iloc[0]} to {W.quarter_end.iloc[-1]}, price returns, REIT stocks vs FTSE Nareit All Equity REITs",
    f"Welltower weight: RFI {W.w_rfi.iloc[0]*100:.1f}% -> {W.w_rfi.iloc[-1]*100:.1f}% of REIT stocks; index {W.w_index.iloc[0]*100:.1f}% -> {W.w_index.iloc[-1]*100:.1f}% (quarter starts)",
    f"total active return (sum of quarters): {s.total_active:.2f} pts",
    f"Welltower alone, active weight x (Welltower - index): {s.active_well:.2f} pts = {s.active_well/s.total_active*100:.0f}% of it",
    f"everything else: {s.total_active - s.active_well:.2f} pts",
    f"health care selection effect {s.hc_selection:.2f} pts, of which Welltower's overweight within health care {s.hc_selection_well:.2f} and the other health care picks {s.hc_selection - s.hc_selection_well:.2f}",
    f"Welltower share of health care: RFI {W.w_rfi_in_hc.iloc[0]*100:.0f}% -> {W.w_rfi_in_hc.iloc[-1]*100:.0f}%, index {W.w_index_in_hc.iloc[0]*100:.0f}% -> {W.w_index_in_hc.iloc[-1]*100:.0f}%",
    f"Welltower price {((1+W.r_well).prod()-1)*100:.0f}% vs Nareit health care {((1+W.r_hc_index).prod()-1)*100:.0f}% and All Equity {((1+W.r_index).prod()-1)*100:.0f}% over the same quarters",
]
save("welltower_share_of_edge.txt", "\n".join(lines) + "\n")
