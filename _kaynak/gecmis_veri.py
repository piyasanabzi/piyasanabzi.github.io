"""Geçmiş yatırım hesaplayıcısı için aylık veri üretir.

Kaynaklar (aylık ortalama / ay sonu):
  - Ons altın (USD): github.com/datasets/gold-prices (aylık)
  - USD/TRY ve EUR/USD: Avrupa Merkez Bankası kurları (api.frankfurter.dev), günlük kurların aylık ortalaması
  - Bitcoin (USD): Binance BTCUSDT aylık mum, kapanış (2017-08 sonrası)

Çalıştırma (depo kökünde): python3 _kaynak/gecmis_veri.py
gecmis-yatirim.html içindeki /*VERI*/ ... /*VERI_SON*/ arasını yeniler.
"""
import json, os, re, urllib.request, datetime, collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START=2005  # 1 Ocak 2005'te 6 sıfır atıldı (YTL); öncesi karşılaştırılamaz

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"piyasanabzi-veri/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r: return r.read().decode()

gold={}
for line in get("https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv").splitlines()[1:]:
    d,p=line.split(","); 
    if int(d[:4])>=START: gold[d]=float(p)

fx=collections.defaultdict(lambda:{"try":[],"eur":[]})
this_year=datetime.date.today().year
for y in range(START,this_year+1):
    d=json.loads(get(f"https://api.frankfurter.dev/v1/{y}-01-01..{y}-12-31?base=USD&symbols=TRY,EUR"))
    for day,r in d["rates"].items():
        m=day[:7]
        if "TRY" in r: fx[m]["try"].append(r["TRY"])
        if "EUR" in r: fx[m]["eur"].append(1/r["EUR"])

btc={}
for k in json.loads(get("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1M&limit=1000")):
    m=datetime.datetime.fromtimestamp(k[0]/1000,datetime.timezone.utc).strftime("%Y-%m"); btc[m]=round(float(k[4]))

cur=datetime.date.today().strftime("%Y-%m")
rows=[]
for m in sorted(gold):
    if m>=cur or not fx[m]["try"]: continue  # yalnızca tamamlanmış aylar
    t=sum(fx[m]["try"])/len(fx[m]["try"]); e=sum(fx[m]["eur"])/len(fx[m]["eur"])
    rows.append([m,round(gold[m],2),round(t,4),round(e,4),btc.get(m)])

js="const D="+json.dumps(rows,separators=(",",":"))+";"
p=os.path.join(ROOT,"gecmis-yatirim.html"); s=open(p).read()
s2=re.sub(r"/\*VERI\*/.*?/\*VERI_SON\*/",lambda _:"/*VERI*/"+js+"/*VERI_SON*/",s,count=1,flags=re.S)
assert "/*VERI*/" in s2
open(p,"w").write(s2)
print(len(rows),"ay:",rows[0][0],"→",rows[-1][0]); print(rows[-1])
