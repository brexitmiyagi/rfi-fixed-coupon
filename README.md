# rfi-fixed-coupon

This is the data and code behind my Seeking Alpha piece on Cohen & Steers Total Return Realty Fund (RFI), "RFI: Take Out Welltower And 15 Quarters Of Everything Else Added 0.2 Points" (November 2026).

The idea is simple. RFI paid $0.08 a share in November 1993 and still pays $0.08 a month. In 1995 net investment income paid for almost all of it. Now it pays for under a third. I wanted to see what pays for the rest, what that means for the NAV and the return of capital labels, and whether buying at an 8.65% discount makes sense. The answer to the first one turned out to be mostly Welltower, and most of the manager's recent edge over its own benchmark is the same stock. The view (HOLD against Treasuries, OVERWEIGHT against REITs while the discount is expected to narrow, 12-month price target $9.94, buy at a discount of 10.1% or wider, about $10.28 at the November 18 NAV) comes from a joint simulation that keeps the REIT market, the fund's NAV and its discount tied together, run the same way on RQI and RNP. CHECKS.md has the clean-room rerun, the second-path checks and the error log.

Everything is priced at the November 20, 2026 close. The first drafts used November 18; data/snapshot_2026_11_18.csv and the other dated 11_18 files are kept so you can see what moved.

## How to run it

You need Python 3 with pandas, numpy, statsmodels and xlrd (for Nareit's .xls files).

```
pip install pandas numpy statsmodels xlrd
(welltower_peer_multiples.py also needs pdftotext, from poppler-utils)
python scripts/tieout.py
python scripts/holdings_attribution.py
python scripts/lookthrough_valuation.py
python scripts/holders_13f.py
python scripts/house_bet.py
python scripts/benchmark_overweight.py
python scripts/brinson.py
python scripts/welltower_share_of_edge.py
python scripts/manager_record.py
python scripts/discount_panel.py
python scripts/payout_cut_risk.py
python scripts/liquidity_and_hedge.py
python scripts/scenarios.py
python scripts/reit_valuation_return.py
python scripts/joint_simulation.py
python scripts/return_bridge.py
python scripts/options_overlay.py
python scripts/rate_sensitivity.py
python scripts/discount_signal.py
python scripts/filings_checks.py
python scripts/section19_vs_tax.py
python scripts/panel_out_of_sample.py
python scripts/signal_backtest.py
python scripts/simulation_calibration.py
python scripts/buy_rule_backtest.py
python scripts/buy_rule_independence.py
python scripts/bias_correction_check.py
python scripts/price_target.py
python scripts/relative_call.py
python scripts/buyback_and_crowding.py
python scripts/macro_call.py
python scripts/peer_concentration.py
python scripts/welltower_insiders_short.py
python scripts/welltower_peer_multiples.py
python scripts/dead_fund_points.py
python scripts/survivorship_check.py
python scripts/nport_engine.py data/peer_nport 1157842_ 2022-09-30 95040Q104
python scripts/coupon_history.py
python scripts/who_pays.py
python scripts/fixed_point.py
python scripts/payout_episodes.py
python scripts/discount.py
python scripts/peers.py
python scripts/carry_and_target.py
python scripts/chart_data.py
```

Each script reads from `data/` and writes to `results/`. You can run them from any folder. Run holdings_attribution.py before lookthrough_valuation.py and brinson.py, and run everything else before chart_data.py, since they read each other's output.

## What each script backs up in the post

- `tieout.py` checks the filing numbers add up (unrealized gains, net investment income, NAV per share, the Section 19 rows, and that my Nov 18 price and NAV match CEF Connect). It fails loudly if anything is off.
- `coupon_history.py` the first and latest $0.08, and what $0.96 a year is worth in November 1993 dollars ($0.415, down 56.7%).
- `who_pays.py` net investment income against the $0.96 every year from 1994 to 2025 (92% in 1995, 31% in 2025), the book's income yield against the 10-year, the 2026 Section 19 split (29.9% income, 7.4% short-term gains, 62.7% return of capital), and the $2.17 a share of unsold gains at June 30.
- `fixed_point.py` the balance point idea. NAV total return since September 30, 2022 (8.49% a year against an 8.27% average payout), the balance-point NAV at different returns ($15.41 at 6.23%), and the 5.80% a year of price gains the book needs to hold NAV flat.
- `payout_episodes.py` every month since 1996 where $0.96 was 8% of NAV or more, and the NAV total return over the next three years.
- `discount.py` where today's -8.51% sits in RFI's history, what the discount did a year after past drops below -8% (weekly and as 8 separate episodes: narrower in 7, median -1.37%), the mid-November to end-January pattern (narrower in 22 of 28 seasons), and the check that weekly discount changes don't track the 10-year.
- `peers.py` one-year discount changes across 11 real estate, preferred and infrastructure CEFs, and RFI against RQI.
- `carry_and_target.py` the carry from buying at a discount (0.80 points a year vs a 0.94% fee), the discount where carry covers the fee (-9.85%), what a 10% buyback would add ($0.11 a share), the yield-buyer view ($10.10 at the median spread), and a grid of returns for different NAV moves and discounts. The target itself is in scenarios.py.
- `holdings_attribution.py` prices every position in the 17 quarterly N-PORT filings (value over units at each quarter-end) and adds up each holding's contribution to the book's price return from September 2022 to June 2026. Welltower 10.81 of 24.61 points (44%), with the three data center names 78%. Book price return 6.00% a year, 3.10% without Welltower. Also the Welltower share count and weight over time.
- `lookthrough_valuation.py` Welltower, Digital Realty, Equinix and Iron Mountain on their own 2026 guidance (37.0x, 19.5x, 22.1x, 17.1x), their combined 3.87% cash-earnings yield, Welltower's likely weight today (about 14.8% if unchanged since June), what a 20% fall does to NAV, and the hedge size (16.1%).
- `holders_13f.py` every 13F listing RFI's CUSIP, Q4 2025 to Q3 2026. Matched filers down 5.4%, the biggest sellers, and the (lack of) arbitrage funds.
- `house_bet.py` Cohen & Steers, Inc.'s own 13F filings (Q3 2022 to Q3 2026) against RFI's N-PORTs. Welltower's weight in the whole firm vs in RFI each quarter (13.22% vs 13.15% at June 30, 2026), the firm's 34.3 million shares (4.68% of Welltower, about 12 days of average volume), the 6.9% cut in Q3 2026, and the 13.8% to 14.8% range for RFI's Welltower weight today.
- `benchmark_overweight.py` Welltower's weight in RFI against VNQ and XLRE (both from their own N-PORTs) and against Cohen & Steers' other real estate funds. VNQ holds part of its portfolio through Vanguard Real Estate II Index Fund, so its Welltower weight is looked through that fund too. RFI holds about 1.7x VNQ's weight and 1.5x XLRE's. At index weight Welltower would have added 5.48 to 7.17 points instead of 10.81, and the book's price return would have been 4.69% to 5.10% a year instead of 6.00%, against the 5.80% the payout needs.
- `brinson.py` Brinson-Fachler attribution of RFI's REIT stocks against the FTSE Nareit All Equity REITs index (the equity part of RFI's own benchmark), by Nareit property sector, 15 quarters from September 2022 to June 2026. Active return 5.58 points (price), sector effects 5.08 of it, health care 4.62 (allocation 1.15, selection 2.78, interaction 0.69). Everything outside health care about half a point.
- `manager_record.py` RFI's NAV return against its blended benchmark every year from 2005, from the annual reports. Ahead in 8 of 9 years from 2017 (average +1.65 points), 5 of 12 from 2005 to 2016 (+0.02).
- `discount_panel.py` the discount study across 36 real estate, preferred, MLP and infrastructure CEFs. Regression puts RFI's discount a year out at -5.48% (95% interval -6.99% to -3.67% resampling years); the 1,028 most similar fund-weeks have a median of -7.22% with quartiles -10.63% and -3.48%.
- `payout_cut_risk.py` payout as a % of NAV since 1996, the March 2009 cut, and a block bootstrap of RFI's own monthly NAV returns: NAV reaches the pre-2008 high payout level ($9.04) within 13 months in 12.5% of 20,000 paths.
- `liquidity_and_hedge.py` fund size ($273 million market value), daily trading (median about 97,000 shares, $1.0 million), and the hedge: short $72 of VNQ and $10 of Welltower per $100 of RFI.
- `scenarios.py` the bear, base and bull cases and the $10.82 probability-weighted target (12.7% total vs 9.7% for the benchmark in the same cases), entry prices, the $10.74 break-even and a stress case.
- `welltower_share_of_edge.py` the stock-level check: Welltower's active weight times its return over the index is 5.38 of the 5.58 points of edge; every other REIT position adds 0.20.
- `manager_record.py` also gives t-stats (2017-2025: 5.28), rolling 5-year information ratios and a break test: a split as sharp as 2016/2017 shows up in 2.7% of 10,000 reshuffles.
- `reit_valuation_return.py` forward REIT returns against the starting gap between REIT yields and the 10-year. Since 1990 the gap predicts (-0.5% at today's gap); since 1972 it doesn't. The base case uses 4.8%, the post-1990 median at similar gaps (it was 5.7% on the Nov 18 close, so this input is jumpy).
- `joint_simulation.py` the 12-month simulation for RFI, RQI and RNP: each draw takes the REIT surprise, the NAV residual and the discount miss from the same historical window, plus a Welltower shock. RFI: expected price $10.52, mean 9.8%, 28% chance of loss, beats REITs 71% (before the correction in price_target.py).
- `return_bridge.py` reconciles the annual-report record with the Brinson run: Jan 2023 to Jun 2026, excess +2.5 = REIT picking +5.1 + mix 0.0 + fees -3.3 + everything else +0.7.
- `options_overlay.py` the options RFI writes, from the N-PORT derivative fields (June 30, 2026: 14 written, $10.2m notional, 3.2% of net assets).
- `rate_sensitivity.py` NAV and discount against moves in the 10-year (since October 2016: NAV -6.3% per point).
- `discount_signal.py` the monthly ranking of 36 CEFs by expected discount change. The November 20, 2026 run is results/discount_signal_2026_11_20.csv (26 of the 36 funds only had November 19 prices on CEF Connect when I pulled it); the November 18 run is kept next to it.
- `nport_engine.py` the holdings attribution as a reusable tool for any fund's N-PORT filings.
- `filings_checks.py` Welltower's 2026 stock issuance ($7.5bn, 56% of $13.3bn of investments), RFI's fair-value levels (0.83% Level 3), the staggered board, and the 13D/13G record.
- `section19_vs_tax.py` every monthly Section 19 estimate since mid-2017 against the final tax character. Return of capital showed up in the notices in 7 of 9 years and in the final figures in 2.
- `panel_out_of_sample.py` the discount model fitted before 2016 and tested after: right on ranking, about two and a half times too big on size. The simulation uses the post-2016 fit.
- `signal_backtest.py` long the top five, short the bottom five by the signal, from 2016. After skipping a month, +1.8 to +3.6 points a year on annual holds, not statistically significant.
- `simulation_calibration.py` the simulation rebuilt in real time since 2005, and where outcomes landed in its ranges.
- `buy_rule_backtest.py` RFI's next 12 months after the discount hit -8%, -10.07%, -10.1% and -12% since 1996, against the REIT index, with "separate episodes" only 60 days apart (their windows overlap).
- `buy_rule_independence.py` the same with episodes at least a year apart, so no two windows share a month. At -10.1%: four (Oct 2008, Oct 2009, Sep 2014, Nov 2015), all beat REITs, median edge +21 pts. It also prints the REIT-minus-Treasury yield gap at each start (+0.7 to +1.6 for those four) and the mid-2006 weeks that are the closest match to today.
- `bias_correction_check.py` tests whether the -5.9 pt correction double-counts: miss on the assumption (no slope, t -0.85), on the yield gap (bigger misses when REITs are expensive, t 1.8), and in months that started with a negative gap (-5.8). Average miss -5.92, 95% interval -13.0 to +1.2.
- `price_target.py` the $9.61 price target (and $8.93 to $10.28 across the correction's interval; the absolute call flips to BUY below a 4.4 pt correction), the OVERWEIGHT/NEUTRAL line vs REITs (discount about 6.1% to 6.6%), the -8% to +14% range for the HOLD call, the fair-value discount (-4.8% / -4.2%), where the corrected case clears the 10-year (below $10.07, a 9.8% discount), and the spread of corrected 12-month returns for the histogram (results/charts/c22_corrected_distribution.csv, results/price_target_distribution.txt: 47% of runs lose money, 43% beat the 10-year, 74% beat REITs) and the buy-level returns. It lowers the REIT input by the average miss found in simulation_calibration.py (-5.9 pts a year) and reruns RFI's simulation.
- `relative_call.py` the relative call taken apart: +4.65 pt edge = discount narrowing +2.72, manager's NAV edge +0.71, beta below 1 +0.12, carry and the rest +1.10; the edge falls to +1.9 if the discount stays at -8.51% and +1.6 at the post-2016 median of -8.88% (NEUTRAL). Welltower at -30% / flat / +20%: RFI total return -0.6% / +3.6% / +6.5%, edge +3.7 / +4.7 / +5.3. Alternatives 2016-2025 from their prospectuses (data/alternatives_2025.csv): RFI price 7.2%, RFI NAV 6.1%, Cohen & Steers Realty Shares L 6.32%, VNQ 5.13%, benchmark 5.28%.
- `buyback_and_crowding.py` a 10% buyback at $10.21: $27.32m spent, $2.54m ($0.106 a share) to remaining holders once, $202k a year of adviser fees lost (0.74% of net assets; 0.036% of Cohen & Steers' 2025 revenue). And the house Welltower position: 34.3m shares, 13.2% of the firm's 13F book, about 62 trading days to sell at 20% of three-month average volume, 3rd of its 15 largest REIT positions (median 45). Inputs: data/fee_terms_2026.csv, data/nasdaq_volume_2026_08_19_to_11_18.csv.
- `welltower_peer_multiples.py` Welltower 37.0x 2026 FFO guidance against Ventas 22.3x and American Healthcare REIT 25.6x (company guidance, Nov 20 close), and against Nareit's REITWatch (Sep 30): median equity REIT 12.5x, health care average 15.4x, 2.2 vs 2.0 times per point of consensus growth for Welltower vs Ventas.
- `dead_fund_points.py` NAV and market price for 35 dead real estate, MLP, infrastructure and preferred CEFs from their own annual reports on EDGAR (downloads about 170 MB the first time).
- `survivorship_check.py` reruns the discount model on June/December points with and without those dead funds and their endings. RFI's forecast: -5.96% either way.
- `macro_call.py` the evidence for the macro call (REITs trail the 10-year yield over the next 12 months): post-2000 months near today's gap trailed 59% of the time; the three post-1990 months at -1 or lower all trailed.
- `peer_concentration.py` Welltower and top-holding weights in every listed real estate CEF's latest N-PORT (data/peer_cef_nport/): 15.9% to 16.5% of stocks in the four Cohen & Steers funds, 4.4% to 11.5% elsewhere.
- `welltower_insiders_short.py` Welltower Form 4s (no open-market sales Nov 2025 to Sep 2026; one director bought 10,000 shares) and FINRA short interest (up 57% in a year to 17.5 million shares).
- `simulation_calibration.py` also runs a valuation-aware version; it was no better.
- `chart_data.py` the exact CSVs behind the charts.

## Data

- `annual_report_per_share.csv` net investment income per share, total distributions, and the income and expense ratios, typed in from each annual report. The SEC accession number for each year is in the file. 1994 and 1995 are from the 1995 report, 1996 to 2000 from the 2000 report, and so on in five-year blocks.
- `ncsrs_2026_facts.csv` numbers from the June 30, 2026 semi-annual report and the 2025 annual report.
- `section19_2026_ytd.csv` year-to-date sources of the 2026 distributions. January to June are from the Section 19 notices filed as an exhibit to the semi-annual report. October is from the October 27, 2026 release.
- `rfi_price_nav_weekly_cefconnect.csv` and `rfi_price_nav_daily_1y_cefconnect.csv` price, NAV and discount from CEF Connect.
- `rfi_distributions_cefconnect.csv` every distribution since 1993 from CEF Connect.
- `peer_cef_daily_1y_cefconnect.csv` and `rfi_rqi_rnp_weekly_cefconnect.csv` the same for the other funds.
- `fred_dgs10.csv` and `fred_cpiaucsl.csv` from FRED. `treasury_par_curve_2026.csv` from the US Treasury.
- `snapshot_2026_11_18.csv` the closing numbers I priced everything on.
- `nport/` the 17 quarterly N-PORT filings (June 2022 to June 2026) as filed with the SEC, named by accession number.
- `lookthrough_valuation_2026_11_18.csv` prices and 2026 guidance for Welltower, Digital Realty, Equinix and Iron Mountain, with the filing each came from.
- `peer_nport/` N-PORT filings for VNQ, XLRE, Cohen & Steers Realty Shares, RQI, RNP and RLTY, with a README saying which file is which.
- `cns_13f/` Cohen & Steers, Inc.'s 13F information tables for Q3 2022, Q3 2023, Q3 2024 and Q3 2025 to Q3 2026, as filed, named by accession number.
- `welltower_shares_outstanding.csv` from Welltower's 10-Q and 10-K covers (SEC XBRL). `welltower_daily_nasdaq_2026h2.csv` Welltower closes and volume from Nasdaq, June 29 to November 20, 2026.
- `rfi_13f_positions_2025q4_2026q3.csv` RFI shares in every 13F information table that lists CUSIP 19247R103, with the link to each one.
- `nareit/` Nareit's monthly index file (MonthlyHistoricalReturns.xls), the 13 equity sector index files, and `nareit_constituent_caps.csv`, typed from Nareit's year-end constituent PDFs (2022 to 2025, plus October 30, 2026): the equity REIT total, every sector total and the big names.
- `annual_report_returns_vs_benchmark.csv` RFI's NAV return, its blended benchmark and the Nareit equity index for each year from 2005, as printed in each annual report, with the accession number.
- `cef_panel/` the list of 36 funds (universe.csv) and CEF Connect's price/NAV history files. Only RFI, RQI and RNP are included; discount_panel.py downloads the rest.
- `portfolio_manager_letters.csv` who signed each annual report's letter, 2005-2025.
- `cef_panel/RQI_distributions_cefconnect.csv`, `cef_panel/RNP_distributions_cefconnect.csv` and `cef_panel/current_discounts_2026_11_18.csv` for the RQI/RNP simulation and the signal.
- `daily_nasdaq_rfi_vnq_well_xlre_2021_2026.csv` daily closes and volume from Nasdaq, including XRFIX (RFI's NAV).

## Sources

- RFI annual and semi-annual reports on EDGAR: https://www.sec.gov/edgar/browse/?CIK=891290
- 1995 annual report: https://www.sec.gov/Archives/edgar/data/891290/0000950117-96-000137.txt
- 2025 annual report: https://www.sec.gov/Archives/edgar/data/891290/000119312526096898/d51323dncsr.htm
- June 30, 2026 semi-annual report: https://www.sec.gov/Archives/edgar/data/891290/000119312526383174/d131749dncsrs.htm
- Section 19 notices, January to June 2026: https://www.sec.gov/Archives/edgar/data/891290/000119312526383174/d131749dex9919c.htm
- October 2026 Section 19 release: https://www.placera.se/pressmeddelanden/cohen-steers-cohen-steers-total-return-realty-fund-inc-rfi-notification-of-sources-of-distribution-under-section-19-a-20261027
- CEF Connect: https://www.cefconnect.com/fund/RFI
- Nasdaq closes for RFI and its NAV ticker XRFIX: https://api.nasdaq.com/api/quote/RFI/historical?assetclass=stocks&fromdate=2026-11-01&limit=20&todate=2026-11-19 and https://api.nasdaq.com/api/quote/XRFIX/historical?assetclass=mutualfunds&fromdate=2026-11-01&limit=20&todate=2026-11-19
- FRED 10-year: https://fred.stlouisfed.org/series/DGS10
- FRED CPI: https://fred.stlouisfed.org/series/CPIAUCSL
- US Treasury par yield curve: https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026
- Welltower Q3 2026 release: https://www.sec.gov/Archives/edgar/data/766704/000076670426000043/a3q26pressreleaseprnnewswi.htm
- Digital Realty Q3 2026 release: https://www.sec.gov/Archives/edgar/data/1297996/000110465926120212/dlr-ex99d1.htm
- Equinix Q3 2026 release: https://www.sec.gov/Archives/edgar/data/1101239/000110123926000178/a991eqix-q326xpr.htm
- Iron Mountain Q3 2026 release: https://www.sec.gov/Archives/edgar/data/1020569/000102056926000081/q32026earningspressrelea.htm
- Cohen & Steers, Inc. 13F filings: https://www.sec.gov/edgar/browse/?CIK=1284812
- Welltower shares outstanding (XBRL): https://data.sec.gov/api/xbrl/companyconcept/CIK0000766704/dei/EntityCommonStockSharesOutstanding.json
- SEC full-text search for 13F information tables by CUSIP: https://efts.sec.gov/LATEST/search-index?q=%2219247R103%22&forms=13F-HR
- Nareit, REIT dividend yield at end of October 2026: https://www.reit.com/news/blog/market-commentary/reits-rebounded-october-leading-broader-equities
- Nareit monthly index values and returns: https://www.reit.com/sites/default/files/returns/MonthlyHistoricalReturns.xls
- Nareit sector index files: https://www.reit.com/data-research/reit-indexes/monthly-property-index-values-returns
- Nareit constituent files: https://www.reit.com/sites/default/files/returns/FNUSIC2022.pdf (and 2023, 2024, 2025, 2026)
- RFI annual reports, 2005 to 2025: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000891290&type=N-CSR
- CEF Connect price history: https://www.cefconnect.com/api/v3/pricinghistory/RFI/All (same pattern for every ticker)
- NIC MAP third-quarter 2026 occupancy release: https://www.nic.org/news-press/senior-housing-occupancy-nears-record-high-as-majority-of-markets-surpass-90/

## Things to be careful with

- The Section 19 numbers are estimates. The final split shows up on the 1099 and can look very different.
- "Book income yield" is net investment income plus expenses over average net assets. It's a fund-level number, not the dividend yield of the holdings on any one day.
- The NAV total return index reinvests distributions at the weekly NAV nearest the ex-date. It won't match Cohen & Steers' published numbers to the decimal.
- The 8%-of-NAV table uses overlapping three-year windows and has only a handful of real episodes. 1999 and 2009 drive most of it.
- scenarios.py (three cases weighted 25/50/25) is the earlier version of the target, kept for comparison; joint_simulation.py replaces it. The REIT market cases are percentiles of only 21 benchmark years, and the bear case only takes a 20% fall in Welltower relative to the index. The weights are my call.
- RFI's own 8 discount episodes (median -1.37% a year later) were too generous next to the 36-fund panel, so the target uses the panel. The panel only has funds alive today. survivorship_check.py adds the dead funds I could find and read (27 with readable points, 20 priced endings) and the forecast doesn't change, but it's not a full census: funds that died before 2003 and a few whose reports I couldn't read are missing, and the dead funds only have one or two points a year.
- CEF Connect's NAV for SRV wasn't adjusted for its 2015 reverse split until September 2015 (an "-83%" discount for eight years) and TYG's wasn't for four weeks in June 2008. discount_panel.py drops those weeks.
- I ran the panel on CEF Connect files pulled on November 20, 2026. results/discount_panel.txt, panel_out_of_sample.txt, signal_backtest.txt and discount_signal_2026_11_18.csv are from that run. CEF Connect may block scripted downloads, in which case save the files into data/cef_panel/ by hand. The bootstrap interval will move a little between runs.
- The Brinson run drifts Nareit's year-end sector weights to each quarter with the sector price indexes, puts VICI in Specialty before Nareit created Gaming in mid-2023 and keeps Iron Mountain in Specialty. Its rebuilt index returns 23.5% against 23.0% published.
- The annual-report record compares an after-fee fund with a no-fee benchmark.
- The payout simulation draws from RFI's own monthly NAV returns since 1996, which averaged 10.2% a year. That's richer than I'd assume going forward, so the cut odds are on the low side.
- The hedge ratios are fitted on the last three years of weekly prices and the volatility drop is in-sample. Borrow costs aren't in the carry.
- VNQ's quarters end Jan/Apr/Jul/Oct, so its Welltower weight is interpolated to RFI's quarter-ends. Neither VNQ nor XLRE is RFI's actual benchmark (80% FTSE Nareit All Equity REITs, 20% REIT preferreds).
- The 1990s ratios are the "net of expense reduction" versions from those reports.
- Discount history before 2026 comes from CEF Connect weekly data, which has a few missing weeks (a gap in early 2020 among them).

- The attribution only sees quarter-end positions. Anything bought and sold inside a quarter is missed, and dividends aren't in it. It's a price-return map, not the fund's official return.
- "Without Welltower" just removes Welltower's contribution each quarter. It doesn't assume the money would've been in something else.
- Welltower's weight today assumes the fund still holds the June 30 share count. The September N-PORT, due around November 29, will show the real number.
- The four companies' guidance metrics aren't identical (normalized FFO, core FFO, AFFO), so the multiples are close cousins, not the same measure.
- 13F only covers managers who have to file. Those filers held about 18% of RFI at September 30, and a few may not have filed yet for Q3.

- Cohen & Steers' 13F covers everything the firm reports, not just its REIT funds, so "weight in the firm" is weight in its whole US-listed 13F book.
- The 13.8% low end of RFI's Welltower weight assumes RFI cut by the same 6.9% as the firm in Q3. That's an assumption until the September N-PORT is out.

## Corrections

None so far.
