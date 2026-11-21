import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)

PAYOUT = 0.96  # $0.08 a month, every month since the 2016 switch back to monthly


def snap():
    s = pd.read_csv(os.path.join(DATA, "snapshot_2026_11_20.csv")).set_index("item")["value"]
    return s.astype(float)


def weekly():
    df = pd.read_csv(os.path.join(DATA, "rfi_price_nav_weekly_cefconnect.csv"), parse_dates=["date"])
    return df.set_index("date")


def dists():
    d = pd.read_csv(os.path.join(DATA, "rfi_distributions_cefconnect.csv"), parse_dates=["ex_date"])
    return d.sort_values("ex_date")


def nav_total_return_index(df):
    # reinvest every distribution at that week's NAV
    d = dists().set_index("ex_date")["amount"]
    out, u, prev = [], 1.0, None
    for day, row in df.iterrows():
        if prev is not None:
            paid = d[(d.index > prev) & (d.index <= day)].sum()
            u *= (row.nav + paid) / df.loc[prev, "nav"]
        out.append(u)
        prev = day
    return pd.Series(out, index=df.index)


def save(name, text):
    with open(os.path.join(RESULTS, name), "w") as f:
        f.write(text)
    print(text)
