# Brinson-Fachler attribution of RFI's REIT stocks against the FTSE Nareit All Equity REITs index, the equity
# part of RFI's own benchmark (80% All Equity REITs, 20% REIT preferreds), by Nareit property sector, quarter by quarter.
# RFI side: quarter-end N-PORT positions priced value/units (results/attribution_by_quarter.csv, so run
# holdings_attribution.py first). Index side: Nareit's monthly sector price indexes, and sector weights from
# Nareit's year-end constituent files, drifted to each quarter start with the sector price indexes.
# Price returns on both sides, so dividends are out of it. Positions sold inside a quarter drop out of that quarter.
from common import *
import warnings
warnings.filterwarnings("ignore")

NAR = os.path.join(DATA, "nareit")
SECTOR_FILES = {"Office": "Office", "Industrial": "Industrial", "Retail": "Retail", "Residential": "Residential",
                "Diversified": "Diversified", "Health Care": "HealthCare", "Lodging/Resorts": "Lodging-Resorts",
                "Self Storage": "SelfStorage", "Timberland": "Timberland", "Telecommunications": "Telecommunications",
                "Data Centers": "DataCenters", "Gaming": "Gaming", "Specialty": "Specialty"}
CAP_COLS = {"Office": "office_musd", "Industrial": "industrial_musd", "Retail": "retail_musd", "Residential": "residential_musd",
            "Diversified": "diversified_musd", "Health Care": "health_care_musd", "Lodging/Resorts": "lodging_musd",
            "Self Storage": "self_storage_musd", "Timberland": "timber_musd", "Telecommunications": "telecom_musd",
            "Data Centers": "data_centers_musd", "Gaming": "gaming_musd", "Specialty": "specialty_musd"}

# Nareit's sector for each REIT stock RFI held. Iron Mountain sat in Specialty in Nareit's files through 2025.
# VICI goes in Specialty before Nareit split out Gaming in mid-2023.
SECTOR = {
    "95040Q104": "Health Care", "42226K105": "Health Care", "42250P103": "Health Care", "681936100": "Health Care",
    "42225P501": "Health Care", "14174T107": "Health Care", "92276F100": "Health Care", "58463J304": "Health Care",
    "03027X100": "Telecommunications", "22822V101": "Telecommunications", "78410G104": "Telecommunications",
    "74340W103": "Industrial", "264411505": "Industrial", "277276101": "Industrial", "32054K103": "Industrial",
    "76169C100": "Industrial", "03064D108": "Industrial", "53566V106": "Industrial",
    "253868103": "Data Centers", "29444U700": "Data Centers",
    "74460D109": "Self Storage", "30225T102": "Self Storage",
    "828806109": "Retail", "756109104": "Retail", "49446R109": "Retail", "008492100": "Retail", "84860W300": "Retail",
    "29670E107": "Retail", "64119V303": "Retail",
    "46187W107": "Residential", "59522J103": "Residential", "866674104": "Residential", "902653104": "Residential",
    "297178105": "Residential", "29472R108": "Residential", "133131102": "Residential", "03750L109": "Residential",
    "02665T306": "Residential", "053484101": "Residential",
    "925652109": "Gaming", "44107P104": "Lodging/Resorts", "252784301": "Lodging/Resorts", "984017103": "Lodging/Resorts",
    "962166104": "Timberland", "754907103": "Timberland",
    "101121101": "Office", "49427F108": "Office", "431284108": "Office", "222795502": "Office",
    "444097109": "Office", "444097406": "Office",
    "92936U109": "Diversified", "512816109": "Specialty", "46284V101": "Specialty",
}
NOT_IN_INDEX = {"000000000", "09264B107"}  # a private joint venture and a non-traded REIT
GAMING_START = pd.Timestamp("2023-06-30")


def price_index(fname):
    v = pd.read_excel(os.path.join(NAR, fname + ".xls"), header=None)
    d = pd.to_datetime(v[0], errors="coerce")
    s = pd.Series(pd.to_numeric(v[6], errors="coerce").values, index=d)  # column 6 = price index
    return s[s.index.notna()].dropna()


def all_equity_price():
    v = pd.read_excel(os.path.join(NAR, "MonthlyHistoricalReturns.xls"), sheet_name="Index Data", header=None)
    assert str(v.iloc[5, 22]).strip() == "All Equity REITs" and str(v.iloc[7, 25]).strip() == "Index"
    d = pd.to_datetime(v[0], errors="coerce")
    s = pd.Series(pd.to_numeric(v[25], errors="coerce").values, index=d)
    return s[s.index.notna()].dropna()


PX = {k: price_index(f) for k, f in SECTOR_FILES.items()}
ALL = all_equity_price()


def at(s, date):
    return s[s.index <= pd.Timestamp(date) + pd.Timedelta(days=3)].iloc[-1]


caps = pd.read_csv(os.path.join(NAR, "nareit_constituent_caps.csv"), parse_dates=["snapshot_date"])
caps.loc[caps.snapshot_date.dt.year == 2022, "telecom_musd"] = caps.loc[caps.snapshot_date.dt.year == 2022, "infrastructure_2022_musd"]


def bench_weights(q):
    q = pd.Timestamp(q)
    snaps = caps.snapshot_date.sort_values()
    if q < GAMING_START:
        s = snaps.iloc[0]
    else:
        past = snaps[snaps <= q]
        s = past.iloc[-1] if len(past) and past.iloc[-1].year > 2022 else snaps.iloc[1]
    row = caps[caps.snapshot_date == s].iloc[0]
    w = {}
    for sec, col in CAP_COLS.items():
        c = row[col]
        if pd.isna(c) or (sec == "Gaming" and q < GAMING_START):
            continue
        if sec == "Gaming" and len(PX[sec][PX[sec].index <= s]) == 0:
            continue
        w[sec] = c * at(PX[sec], q) / at(PX[sec], s)
    tot = sum(w.values())
    return {k: v / tot for k, v in w.items()}


Q = pd.read_csv(os.path.join(RESULTS, "attribution_by_quarter.csv"), dtype={"cusip": str})
Q = Q[(Q.cat == "EC") & ~Q.cusip.isin(NOT_IN_INDEX)].copy()
missing = set(Q.cusip) - set(SECTOR)
assert not missing, missing
quarters = sorted(Q.quarter_end.unique())
prev = {b: a for a, b in zip(["2022-06-30"] + quarters[:-1], quarters)}
rows = []
for b in quarters:
    a = prev[b]
    if a < "2022-09-30":
        continue
    q = Q[Q.quarter_end == b].copy()
    q["sector"] = q.cusip.map(SECTOR)
    if pd.Timestamp(a) < GAMING_START:
        q.loc[q.sector == "Gaming", "sector"] = "Specialty"
    q["w"] = q.v0 / q.v0.sum()
    wb = bench_weights(a)
    rb_tot = at(ALL, b) / at(ALL, a) - 1
    for sec in sorted(set(wb) | set(q.sector)):
        g = q[q.sector == sec]
        wp = g.w.sum()
        rp = (g.w * g.move).sum() / wp if wp > 0 else 0.0
        rbs = at(PX[sec], b) / at(PX[sec], a) - 1 if sec in wb else 0.0
        wbs = wb.get(sec, 0.0)
        rows.append(dict(quarter_end=b, sector=sec, w_rfi=wp, w_index=wbs, r_rfi=rp, r_index_sector=rbs, r_index=rb_tot,
                         allocation=(wp - wbs) * (rbs - rb_tot), selection=wbs * (rp - rbs), interaction=(wp - wbs) * (rp - rbs)))
B = pd.DataFrame(rows)
B.to_csv(os.path.join(RESULTS, "brinson_by_quarter_sector.csv"), index=False)

per_q = B.groupby("quarter_end").agg(rfi=("w_rfi", lambda s: (s * B.loc[s.index, "r_rfi"]).sum()), idx=("r_index", "first"),
                                     allocation=("allocation", "sum"), selection=("selection", "sum"), interaction=("interaction", "sum"))
per_q["model_index"] = B.groupby("quarter_end").apply(lambda g: (g.w_index * g.r_index_sector).sum())
per_q["active"] = per_q.rfi - per_q.idx
by_sec = B.groupby("sector")[["allocation", "selection", "interaction"]].sum() * 100
by_sec["total"] = by_sec.sum(axis=1)
by_sec = by_sec.sort_values("total", ascending=False).round(2)
by_sec.to_csv(os.path.join(RESULTS, "brinson_by_sector.csv"))
hc = B[B.sector == "Health Care"]
yrs = len(per_q) / 4
cr = lambda s: ((1 + s).prod() - 1) * 100
lines = [
    f"{len(per_q)} quarters ending {per_q.index[0]} to {per_q.index[-1]} (from September 30, 2022); REIT stocks only, price returns",
    f"RFI REIT stocks compounded {cr(per_q.rfi):.1f}%, FTSE Nareit All Equity REITs price index {cr(per_q.idx):.1f}%",
    f"check: index rebuilt from sector weights x sector returns {cr(per_q.model_index):.1f}% vs the published index {cr(per_q.idx):.1f}%",
    f"active return, sum of quarters: {per_q.active.sum()*100:.2f} pts = allocation {per_q.allocation.sum()*100:.2f} + selection {per_q.selection.sum()*100:.2f} + interaction {per_q.interaction.sum()*100:.2f} (+ residual {(per_q.active - per_q.allocation - per_q.selection - per_q.interaction).sum()*100:.2f} from the rebuilt index not matching exactly)",
    f"Health Care: RFI weight {hc.w_rfi.iloc[0]*100:.1f}% -> {hc.w_rfi.iloc[-1]*100:.1f}%, index {hc.w_index.iloc[0]*100:.1f}% -> {hc.w_index.iloc[-1]*100:.1f}%",
    f"Health Care allocation {hc.allocation.sum()*100:.2f} pts, selection {hc.selection.sum()*100:.2f}, interaction {hc.interaction.sum()*100:.2f}",
    f"Health Care sector price return: RFI {cr(hc.r_rfi):.1f}%, index sector {cr(hc.r_index_sector):.1f}%",
    "by sector, pts summed over quarters:",
    by_sec.to_string(),
]
save("brinson.txt", "\n".join(lines) + "\n")
