"""Piyasa gündemi: ekonomi haber başlıklarını RSS kaynaklarından toplar.

Yalnızca BAŞLIK, KAYNAK ADI, SAAT ve BAĞLANTI saklanır; haber metni alınmaz.
GitHub Actions (.github/workflows/haberler.yml) her 30 dakikada bir çalıştırır ve
sonucu `veri` dalına haberler.json olarak yazar. Site bu dosyayı
raw.githubusercontent.com üzerinden okur.

Kullanım: python3 _kaynak/haberler.py CIKTI.json
"""
import sys, json, re, html, datetime, urllib.request, email.utils, xml.etree.ElementTree as ET

KAYNAKLAR = [
    ("AA", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
    ("TRT Haber", "https://www.trthaber.com/ekonomi_articles.rss"),
    ("NTV", "https://www.ntv.com.tr/ekonomi.rss"),
    ("Bloomberg HT", "https://www.bloomberght.com/rss"),
    ("Habertürk", "https://www.haberturk.com/rss/ekonomi.xml"),
    ("CNN Türk", "https://www.cnnturk.com/feed/rss/ekonomi/news"),
    ("Dünya", "https://www.dunya.com/rss"),
]

# (etiket, anahtar kelimeler) - ilk eşleşen etiket kullanılır
ETIKETLER = [
    ("Altın", ["altın", "ons ", "gümüş", "kuyumcu", "çeyrek"]),
    ("Faiz", ["faiz", "merkez bankası", "tcmb", "ppk", " fed", "fed'", "fomc", "ecb", "avrupa merkez", "powell", "warsh", "lagarde", "karahan"]),
    ("Döviz", ["dolar", "euro", "avro", "kur ", "kuru", "döviz", "sterlin", "yen ", "yuan", "parite", "rezerv"]),
    ("Enflasyon", ["enflasyon", "tüfe", "üfe", "fiyat artış"]),
    ("Petrol", ["petrol", "brent", "opec", "doğal gaz", "doğalgaz", "akaryakıt"]),
    ("Kripto", ["bitcoin", "kripto", "ethereum"]),
    ("Borsa", ["borsa", "bist", "hisse", "nasdaq", "dow jones", "s&p", "tahvil", "cds"]),
    ("Dünya", ["abd ", "çin", "avrupa", "japonya", "ingiltere", "almanya", "küresel", "trump", "gümrük vergi", "tarife", "resesyon", "büyüme"]),
]
HARIC = ["burç", "maç", "transfer", "magazin", "dizi ", "tarif:", "hava durumu"]


def getir(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (piyasanabzi.site haber basliklari)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def tarih(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
    return d.astimezone(datetime.timezone.utc)


def temizle(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    return re.sub(r"\s+", " ", t)


def etiket(baslik):
    b = " " + baslik.lower().replace("İ", "i").replace("I", "ı") + " "
    if any(h in b for h in HARIC):
        return None
    for ad, kel in ETIKETLER:
        if any(k in b for k in kel):
            return ad
    return None


def oku(kaynak, url):
    kok = ET.fromstring(getir(url))
    out = []
    for it in kok.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        g = {c.tag.split("}")[-1]: c for c in it}
        baslik = temizle(g["title"].text if "title" in g else "")
        link = ""
        if "link" in g:
            link = (g["link"].text or g["link"].get("href") or "").strip()
        tk = next((k for k in ("pubDate", "published", "updated", "date") if k in g), None)
        d = tarih(g[tk].text if tk else None)
        if not baslik or not link.startswith("http") or not d:
            continue
        e = etiket(baslik)
        if e:
            out.append({"t": baslik, "u": link, "k": kaynak, "e": e, "d": d.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return out


def main(cikti):
    simdi = datetime.datetime.now(datetime.timezone.utc)
    hepsi, durum = [], {}
    for kaynak, url in KAYNAKLAR:
        try:
            x = oku(kaynak, url)
            durum[kaynak] = len(x)
            hepsi += x
        except Exception as ex:
            durum[kaynak] = "hata: " + type(ex).__name__
    print(json.dumps(durum, ensure_ascii=False))
    gorulen, secili = set(), []
    for h in sorted(hepsi, key=lambda h: h["d"], reverse=True):
        d = datetime.datetime.strptime(h["d"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        if d > simdi + datetime.timedelta(hours=1) or d < simdi - datetime.timedelta(hours=48):
            continue
        anahtar = re.sub(r"[^a-z0-9çğıöşü]", "", h["t"].lower())[:60]
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        secili.append(h)
        if len(secili) >= 30:
            break
    if len(secili) < 3:
        print("Yeterli haber yok, dosya yazılmadı")
        sys.exit(2)
    with open(cikti, "w", encoding="utf-8") as f:
        json.dump({"guncelleme": simdi.strftime("%Y-%m-%dT%H:%M:%SZ"), "kaynaklar": durum, "haberler": secili}, f, ensure_ascii=False, separators=(",", ":"))
    print(len(secili), "haber yazıldı")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "haberler.json")
