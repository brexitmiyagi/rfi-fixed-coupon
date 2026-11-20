# Is Welltower RFI's bet or Cohen & Steers'? Cohen & Steers, Inc. files a 13F for everything it manages.
# These are its information tables for Q3 2022, Q3 2023, Q3 2024 and Q3 2025 to Q3 2026 (values in $ thousands).
from common import *
import glob, re

rows = []
for f in sorted(glob.glob(os.path.join(DATA, "cns_13f", "*.xml"))):
    t = re.sub(r'<(/?)\w+:', r'<\1', open(f).read())
    period = None
    tot = sh = val = 0.0
    for b in re.findall(r'<infoTable>(.*?)</infoTable>', t, re.S):
        v = float(re.search(r'<value>([^<]*)', b).group(1))
        tot += v
        if re.search(r'<cusip>\s*95040Q104', b, re.I):
            val += v
            sh += float(re.search(r'<sshPrnamt>([^<]*)', b).group(1))
    rows.append(dict(accession=os.path.basename(f)[:-4], total_13f_thousands=tot, well_shares=sh, well_value_thousands=val))
periods = {"0001567619-22-019722": "2022-09-30", "0001284812-23-000286": "2023-09-30", "0001284812-24-000368": "2024-09-30",
           "0001193125-25-281706": "2025-09-30", "0001193125-26-049714": "2025-12-31", "0001193125-26-225177": "2026-03-31",
           "0001193125-26-350257": "2026-06-30", "0001193125-26-461871": "2026-09-30"}
c = pd.DataFrame(rows)
c["period"] = c.accession.map(periods)
c = c.sort_values("period").set_index("period")
c["well_pct_of_13f"] = c.well_value_thousands / c.total_13f_thousands * 100
c["implied_price"] = c.well_value_thousands * 1000 / c.well_shares
h = pd.read_csv(os.path.join(RESULTS, "welltower_position.csv")).set_index("date")
c["rfi_well_pct"] = h.pct.reindex(c.index)
c.round(2).to_csv(os.path.join(RESULTS, "house_bet.csv"))
so = pd.read_csv(os.path.join(DATA, "welltower_shares_outstanding.csv")).iloc[-1]
px = pd.read_csv(os.path.join(DATA, "welltower_daily_nasdaq_2026h2.csv"))
adv = px.volume.mean()
last = c.iloc[-1]
q3cut = last.well_shares / c.loc["2026-06-30", "well_shares"] - 1
rfi_sh = h.units.iloc[-1]
s = snap()
facts = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
well_px = float(px.close.iloc[-1])
nav_total = s["rfi_nav"] * facts["shares_outstanding_2026_06_30"]
lines = [c[["well_shares", "well_pct_of_13f", "implied_price", "rfi_well_pct"]].round(2).to_string(),
         f"Cohen & Steers Welltower stake at Sep 30, 2026: {last.well_shares:,.0f} shares, ${last.well_value_thousands/1e6:.2f}bn, {last.well_shares/so.shares_outstanding*100:.2f}% of the {so.shares_outstanding:,.0f} shares outstanding on {so.as_of}",
         f"that's {last.well_shares/adv:.1f} days of Welltower's average daily volume ({adv:,.0f} shares, {px.date.iloc[0]} to {px.date.iloc[-1]}, Nasdaq)",
         f"Q3 2026 change in the firm's Welltower shares: {q3cut*100:+.1f}%",
         f"if RFI cut by the same share in Q3: {rfi_sh*(1+q3cut):,.0f} shares x ${well_px} = ${rfi_sh*(1+q3cut)*well_px/1e6:.2f}m, {rfi_sh*(1+q3cut)*well_px/nav_total*100:.1f}% of NAV; if it didn't: {rfi_sh*well_px/nav_total*100:.1f}%",
         f"Welltower close Sep 30, 2026 (Nasdaq): ${float(px.set_index('date').close.loc['09/30/2026']):.2f}; implied from the 13F: ${last.implied_price:.2f}"]
save("house_bet.txt", "\n".join(lines) + "\n")

lo = rfi_sh * (1 + q3cut) * well_px / nav_total * 100
hi = rfi_sh * well_px / nav_total * 100
extra = (f"range for RFI's Welltower weight now: {lo:.1f}% to {hi:.1f}% of NAV; a 20% Welltower fall takes {lo*0.2:.2f}% to {hi*0.2:.2f}% off NAV "
         f"(${s['rfi_nav']*lo*0.002:.2f} to ${s['rfi_nav']*hi*0.002:.2f} a share); hedge {lo*s['rfi_nav']/s['rfi_close']:.1f}% to {hi*s['rfi_nav']/s['rfi_close']:.1f}% of the money in RFI\n")
with open(os.path.join(RESULTS, "house_bet.txt"), "a") as fh:
    fh.write(extra)
print(extra)
