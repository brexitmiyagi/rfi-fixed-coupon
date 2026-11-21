# The monthly discount signal: for every fund in data/cef_panel/universe.csv, today's discount, its average over the
# last 156 weekly readings, and the 36-fund panel model's discount a year from now (discount_panel.py coefficients).
# Ranked by expected narrowing. Today's discounts come from a small CSV (ticker,discount) you update each month;
# history comes from the CEF Connect files in data/cef_panel/. Usage: python discount_signal.py <current_discounts.csv>
from common import *
import sys, json

A, B_D, C_DEV = 0.2822, -0.0923, -0.3200
P = os.path.join(DATA, "cef_panel")
U = pd.read_csv(os.path.join(P, "universe.csv"))
cur = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, "cef_panel", "current_discounts_2026_11_20.csv")).set_index("ticker").discount
rows = []
for t in U.ticker:
    f = os.path.join(P, t + ".json")
    if not os.path.exists(f) or t not in cur:
        continue
    h = [x["DiscountData"] for x in json.load(open(f))["Data"]["PriceHistory"] if x["DiscountData"] is not None]
    if len(h) < 104:
        continue
    m = sum(h[-156:]) / len(h[-156:])
    d = cur[t]
    pred = d + A + B_D * d + C_DEV * (d - m)
    rows.append(dict(ticker=t, discount=d, avg_last_156_weeks=round(m, 2), gap_to_own_average=round(d - m, 2),
                     model_discount_in_1y=round(pred, 2), expected_change_pts=round(pred - d, 2)))
R = pd.DataFrame(rows).sort_values("expected_change_pts", ascending=False)
R.insert(0, "rank", range(1, len(R) + 1))
R.to_csv(os.path.join(RESULTS, "discount_signal_latest.csv"), index=False)
print(R.to_string(index=False))
