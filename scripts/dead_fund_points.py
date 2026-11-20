# Year-end and half-year NAV and market price for CEFs that no longer exist, read from their own annual (N-CSR)
# and semi-annual (N-CSRS) reports on EDGAR. Feeds survivorship_check.py.
# data/cef_panel_dead/dead_fund_filings.csv lists every report each fund filed (from the SEC submissions API). I read
# every fourth annual report (each prints five years, so neighbouring reports overlap by a year and can be checked
# against each other) plus the last semi-annual. The documents are about 170 MB, so they aren't in the repo; this
# script downloads them into data/cef_panel_dead/docs/ the first time. The SEC asks for a contact in the User-Agent:
# put yours in SEC_UA below.
# Reading rule: the "Net asset value, end of period" and "Market value (or price), end of period" rows of the
# financial highlights, most recent column first. Nuveen prints years as rows instead, so it gets its own reader.
# A few funds can't be read this way (combined reports with no fund label, or highlights printed as images); the
# script lists them. Every date that two reports both cover gave the same discount to within 0.3 points.
import os, re, html, glob, time, urllib.request
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..", "data", "cef_panel_dead")
DOCS = os.path.join(P, "docs")
SEC_UA = {"User-Agent": "your name your@email"}
os.makedirs(DOCS, exist_ok=True)
F0 = pd.read_csv(os.path.join(P, "dead_fund_filings.csv"))
pick = []
for t in dict.fromkeys(F0.ticker):
    a = F0[(F0.ticker == t) & (F0.form == "N-CSR")].sort_values("period", ascending=False)
    pick += [a.iloc[i] for i in range(0, len(a), 4)]
    s_ = F0[(F0.ticker == t) & (F0.form == "N-CSRS")].sort_values("period", ascending=False)
    if len(s_):
        pick.append(s_.iloc[0])
for r in pick:
    f = os.path.join(DOCS, f"{r.ticker}_{r.form}_{r.period}_{r.acc}_{r.doc}")
    if os.path.exists(f):
        continue
    u = f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{r.acc.replace('-', '')}/{r.doc}"
    try:
        open(f, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers=SEC_UA), timeout=60).read())
    except Exception as e:
        print("could not download", u, e)
    time.sleep(0.15)


def text(f):
    t=open(f,'rb').read().decode('latin1')
    t=re.sub(r'(?is)<(script|style).*?</\1>',' ',t)
    t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=t.replace('\xa0',' ')
    return re.sub(r'\s+',' ',t)
NUMS=r'(?<![\d.])\$?\s?(\d{1,4}\.\d{2,4})(?![\d.%])'
navre=re.compile(r'net asset value[^.$\d]{0,60}?end of (?:the )?(?:year|period|fiscal year)',re.I)
mktre=re.compile(r'(?:market (?:value|price)|closing market price|market price per (?:common )?share|common share fair value)[^$\d]{0,60}?end of (?:the )?(?:year|period|fiscal year)',re.I)
F=pd.read_csv(os.path.join(P, 'dead_fund_filings.csv'))
fye={t:int(pd.to_datetime(g[g.form=='N-CSR'].period).dt.month.mode().iloc[0]) for t,g in F.groupby('ticker') if (g.form=='N-CSR').any()}
def rows_after(t,rx,start=0,n=1):
    out=[]
    for m in rx.finditer(t,start):
        nums=re.findall(NUMS,t[m.end():m.end()+260])
        if nums: out.append((m.start(),[float(x) for x in nums[:6]]))
        if len(out)>=n: break
    return out
def section_start(t,tick):
    # nearest "(TICK)" before a NAV row, when the document covers several funds
    toks=[(m.start(),m.group(1)) for m in re.finditer(r'\((?:NYSE(?: MKT| American)?: ?)?([A-Z]{2,5})\)',t)]
    navs=[m.start() for m in navre.finditer(t)]
    for p in navs:
        prev=[x for x in toks if x[0]<p and p-x[0]<6000]
        if prev and prev[-1][1]==tick: return p
    return None
def nuveen(t,tick):
    i=t.find('Ending NAV Ending Share Price')
    if i<0: return []
    out=[]
    for m in re.finditer(r'\(%s\)\s*(?:Year|Six Months) Ended (\d{1,2})/(\d{1,2}):'%tick,t[i:]):
        seg=t[i+m.end():i+m.end()+1500]
        seg=re.split(r'\([A-Z]{2,5}\) (?:Year|Six)|Borrowings|Ratios|Preferred|MuniFund|\(a\)',seg)[0]
        for r in re.finditer(r'(20\d\d|19\d\d)(?:\([a-z]\))?\s+(.*?)(?=\s(?:20\d\d|19\d\d)(?:\([a-z]\))?\s|$)',seg):
            nums=re.findall(r'(?<![\d.])(\d{1,4}\.\d{2})(?![\d.%])',r.group(2))
            if len(nums)>=3:
                out.append((int(r.group(1)),int(m.group(1)),float(nums[-2]),float(nums[-1])))
        break
    return out
recs=[];bad=[]
for f in sorted(glob.glob(os.path.join(DOCS, '*'))):
    b=os.path.basename(f); t,form,period=b.split('_')[:3]; PER=pd.Timestamp(period)
    tx=text(f)
    nv=nuveen(tx,t)
    if nv:
        for (y,mo,nav,px) in nv:
            d=pd.Timestamp(y,mo,1)+pd.offsets.MonthEnd(0)
            recs.append(dict(ticker=t,date=d.date(),nav=nav,price=px,src=b,form=form,doc_period=period))
        continue
    st=section_start(tx,t)
    multi=len({tuple(x[1][:2]) for x in rows_after(tx,navre,0,10)})>1
    if st is None and multi and t in ('NTG','TTP','NDP','TPZ'):
        bad.append((b,'combined report, fund not identifiable')); continue
    N=rows_after(tx,navre,st or 0); M=rows_after(tx,mktre,st or 0)
    if not N or not M: bad.append((b,'no rows')); continue
    nav,mkt=N[0][1],M[0][1]
    k=nav.index(mkt[0]) if mkt[0] in nav[1:] else len(nav)
    k=min(k,len(mkt),5 if form=='N-CSR' else 6)
    m=fye[t]
    for j in range(k):
        if form=='N-CSR': d=PER-pd.DateOffset(years=j)
        elif j==0: d=PER
        else:
            last=pd.Timestamp(PER.year if PER.month>=m else PER.year-1, m, 1)+pd.offsets.MonthEnd(0)
            if last>=PER: last=last-pd.DateOffset(years=1)
            d=last-pd.DateOffset(years=j-1)
        d=d+pd.offsets.MonthEnd(0)
        recs.append(dict(ticker=t,date=d.date(),nav=nav[j],price=mkt[j],src=b,form=form,doc_period=period))
R=pd.DataFrame(recs); R['disc']=(R.price/R.nav-1)*100
g=R.groupby(['ticker','date'])
inc=g.filter(lambda x: x.disc.max()-x.disc.min()>0.3)
print('bad',len(bad)); [print('  ',x) for x in bad]
print('points',len(R),'unique',g.ngroups,'inconsistent (discount differs >0.3 pt)',inc.groupby(['ticker','date']).ngroups)
print(inc.sort_values(['ticker','date'])[['ticker','date','nav','price','disc','src']].to_string())
R=R.sort_values('doc_period').groupby(['ticker','date']).last().reset_index()
R.to_csv(os.path.join(P, 'dead_points.csv'), index=False)
print(R.groupby('ticker').agg(n=('disc','size'),first=('date','min'),last=('date','max'),dmin=('disc','min'),dmax=('disc','max')).round(1).to_string())
