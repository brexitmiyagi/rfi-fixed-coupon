# Checks the filing numbers I use add up. Fails loudly if anything is off.
from common import *

f = pd.read_csv(os.path.join(DATA, "ncsrs_2026_facts.csv")).set_index("item")["value"].astype(float)
assert abs(f["gross_unrealized_appreciation"] - f["gross_unrealized_depreciation"] - f["net_unrealized_appreciation"]) < 1
assert abs(f["h1_total_investment_income"] - f["h1_total_expenses"] - f["h1_net_investment_income"]) < 1
assert abs(f["net_assets_2026_06_30"] / f["shares_outstanding_2026_06_30"] - f["nav_2026_06_30"]) < 0.005
s19 = pd.read_csv(os.path.join(DATA, "section19_2026_ytd.csv"))
parts = s19[["ytd_nii", "ytd_st_gain", "ytd_lt_gain", "ytd_return_of_capital"]].sum(axis=1)
assert ((parts - s19.ytd_total).abs() < 0.0002).all(), "section 19 rows don't sum"
s = snap()
cef = pd.read_csv(os.path.join(DATA, "rfi_price_nav_daily_1y_cefconnect.csv")).iloc[-1]
assert cef.date == "2026-11-18" and abs(cef.price - s["rfi_close"]) < 0.005 and abs(cef.nav - s["rfi_nav"]) < 0.005
assert abs((s["rfi_close"] / s["rfi_nav"] - 1) * 100 - cef.discount_pct) < 0.02
a = pd.read_csv(os.path.join(DATA, "annual_report_per_share.csv"))
assert len(a) == 32 and a.year.min() == 1994 and a.year.max() == 2025
save("tieout.txt", "all checks pass\n")
