# Is 38 times FFO high for Welltower's peers, or just for REITs? Two independent paths.
# 1. Company guidance: each health care REIT's own 2026 FFO guidance midpoint (Q3 2026 releases) against the
#    November 18 close (Nasdaq). Metrics differ a little by company (normalized FFO, FFO as adjusted, AFFO).
# 2. Nareit's REITWatch for October 2026 (prices at September 30, consensus FactSet 2026 FFO), which lists
#    price/FFO for every listed equity REIT. pdftotext -layout is needed to read it.
from common import *
import re, subprocess, statistics as st

g = pd.read_csv(os.path.join(DATA, "health_care_reit_guidance_2026.csv"))
g["mid"] = (g.guide_low + g.guide_high) / 2
g["p_ffo"] = g.close_2026_11_20 / g.mid
lines = ["Company guidance, Nov 20 close:"] + [f"  {r.ticker}: ${r.close_2026_11_20:.2f} / ${r.mid:.3f} ({r.metric}) = {r.p_ffo:.1f}x" for _, r in g.iterrows()]

txt = subprocess.run(["pdftotext", "-layout", os.path.join(DATA, "nareit", "RW2610.pdf"), "-"], capture_output=True, text=True).stdout.split("\n")
start = next(i for i, l in enumerate(txt) if "Price/FFO" in l and "Share Price" in l)
end = next(i for i, l in enumerate(txt) if l.strip() == "Home Financing")   # mortgage REITs start here; equity only above
hci = next(i for i in range(start, end) if txt[i].strip() == "Health Care")
hc_avg = float(next(l for l in txt[hci:end] if l.startswith("AVERAGE")).split()[6])
rows = []
for l in txt[start:end]:
    if l.startswith(("AVERAGE", "OVERALL")):
        continue
    m = re.match(r"^(\S.*?)\s{2,}([A-Z][A-Z.\-]{0,5})\s+(.*)$", l)
    if not m:
        continue
    tok = m.group(3).split()
    if len(tok) < 19:
        continue
    try:
        rows.append((m.group(2), float(tok[5]), float(tok[17].replace(",", "")), tok[6], tok[7]))
    except ValueError:
        continue
pf = [r for r in rows if r[1] > 0]
well = next(r for r in pf if r[0] == "WELL")
big = sorted([r for r in pf if r[2] >= 10000], key=lambda r: -r[1])
vtr = next(r for r in pf if r[0] == "VTR")
lines += [f"Nareit REITWatch, Sep 30, 2026 prices, FactSet 2026 FFO: {len(pf)} equity REITs with a multiple",
          f"  Welltower {well[1]:.1f}x 2026, {well[3]}x 2027 (consensus FFO growth {well[4]}%); Ventas {vtr[1]:.1f}x / {vtr[3]}x; health care sector simple average {hc_avg:.1f}x; all equity REITs median {st.median([r[1] for r in pf]):.1f}x, "
          f"market-cap weighted {sum(r[2] for r in pf)/sum(r[2]/r[1] for r in pf):.1f}x ({sum(r[2] for r in pf if r[0]!='WELL')/sum(r[2]/r[1] for r in pf if r[0]!='WELL'):.1f}x without Welltower)",
          f"  REITs over $10bn of market value, highest multiples: " + ", ".join(f"{t} {p:.1f}x" for t, p, c, *_ in big[:6])]
lines.append(f"  2026 multiple per point of 2026-27 consensus FFO growth: Welltower {well[1]/float(well[4]):.2f}, Ventas {vtr[1]/float(vtr[4]):.2f}")
save("welltower_peer_multiples.txt", "\n".join(lines) + "\n")
