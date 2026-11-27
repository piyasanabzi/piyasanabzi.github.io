#!/usr/bin/env python3
"""Kuyumcu Yönetim Sistemi → statik site senkronu.

Supabase'teki herkese açık yayin_* görünümlerini okur (yalnızca publishable anahtarla; RLS'in izin verdiği veri),
_kaynak/kuyumcu/isletmeler.json ve paketler.json dosyalarını yazar, onaylı fotoğrafları siteye indirir.
Ardından `python3 _kaynak/content.py && python3 _kaynak/nav.py` sayfaları üretir; mevcut doğrulayıcı
(kuyumcu.py) kurallara uymayan kayıt görürse build'i durdurur, site eski haliyle kalır.

Bağlantı: kuyumcu-pazari/ayar.js (ya da test için PN_SUPA_URL / PN_SUPA_KEY ortam değişkenleri).
Ayar boşsa hiçbir şey yapmaz.
"""
import json, os, re, sys, base64, datetime as dt, urllib.request, urllib.parse

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KD = os.path.join(KOK, "_kaynak", "kuyumcu")
FOTO = os.path.join(KOK, "kuyumcu-pazari", "foto")
TR = dt.timezone(dt.timedelta(hours=3))


def ayar():
    s = open(os.path.join(KOK, "kuyumcu-pazari", "ayar.js"), encoding="utf-8").read()
    u = os.environ.get("PN_SUPA_URL") or (re.search(r'url:\s*"([^"]*)"', s) or [None, ""])[1]
    k = os.environ.get("PN_SUPA_KEY") or (re.search(r'key:\s*"([^"]*)"', s) or [None, ""])[1]
    return u.rstrip("/"), k


def gizli_mi(k):
    if k.startswith("sb_secret_"): return True
    try:
        p = k.split(".")[1]; p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p)).get("role") == "service_role"
    except Exception:
        return False


def main():
    url, key = ayar()
    if not url or not key:
        print("kuyumcu senkron: bağlantı ayarı boş; atlandı"); return 0
    if gizli_mi(key):
        print("HATA: ayar.js içinde GİZLİ anahtar var. Yalnızca publishable anahtar kullanılmalı. Anahtarı hemen iptal edin.", file=sys.stderr)
        return 2

    def al(yol):
        r = urllib.request.Request(url + yol, headers={"apikey": key, "Accept": "application/json"})
        with urllib.request.urlopen(r, timeout=30) as c:
            return json.loads(c.read().decode("utf-8"))

    isl = al("/rest/v1/yayin_isletmeler?select=*&order=ad")
    fiy = {f["isletme_id"]: f for f in al("/rest/v1/yayin_fiyatlar?select=*")}
    fot = al("/rest/v1/yayin_fotograflar?select=*&order=sira,id")
    kam = al("/rest/v1/yayin_kampanyalar?select=*&order=bitis")
    pak = al("/rest/v1/paketler?select=*")

    tr_tarih = lambda s: dt.datetime.fromisoformat(s).astimezone(TR).date().isoformat()
    tr_zaman = lambda s: dt.datetime.fromisoformat(s).astimezone(TR).isoformat(timespec="seconds")

    os.makedirs(FOTO, exist_ok=True)
    gerekli, cikti = set(), []
    for i in isl:
        b = {"id": i["id"], "slug": i["slug"], "ad": i["ad"], "il": i["il"], "ilce": i["ilce"], "adres": i["adres"],
             "telefon": i["telefon"], "saatler": i["saatler"], "paket": i["paket"], "yayinda": True,
             "dogrulama": {"durum": "dogrulandi", "tarih": tr_tarih(i["dogrulandi_at"]), "yontemler": i["dogrulama_yontemleri"]},
             "fiyat_izni": {"verildi": bool(i["fiyat_izni"]), "tarih": tr_tarih(i["fiyat_izni_tarihi"]) if i.get("fiyat_izni_tarihi") else None}}
        if i.get("whatsapp"): b["whatsapp"] = i["whatsapp"]
        if i.get("aciklama"): b["aciklama"] = i["aciklama"]
        f = fiy.get(i["id"])
        if f and i["fiyat_izni"]:
            b["fiyatlar"] = {"guncelleme": tr_zaman(f["guncelleme"])}
            for k in ("gram", "ceyrek", "yarim", "tam"):
                if f.get(k + "_alis") is not None:
                    b["fiyatlar"][k] = {"alis": float(f[k + "_alis"]), "satis": float(f[k + "_satis"])}
        fotolar = []
        for p in [x for x in fot if x["isletme_id"] == i["id"]]:
            ad = re.sub(r"[^a-z0-9]", "", p["id"].lower())[:12]
            uz = p["yol"].rsplit(".", 1)[-1].lower()
            rel = f"kuyumcu-pazari/foto/{i['slug']}/{ad}.{uz}"
            hedef = os.path.join(KOK, rel)
            if not os.path.exists(hedef):
                os.makedirs(os.path.dirname(hedef), exist_ok=True)
                kaynak = url + "/storage/v1/object/public/isletme-fotolari/" + urllib.parse.quote(p["yol"])
                with urllib.request.urlopen(kaynak, timeout=60) as c:
                    veri = c.read()
                if len(veri) > 3 * 1024 * 1024 or veri[:3] not in (b"\xff\xd8\xff", b"\x89PN", b"RIF"):
                    print("fotoğraf atlandı (biçim/boyut):", p["yol"]); continue
                open(hedef, "wb").write(veri)
            gerekli.add(os.path.normpath(hedef))
            fotolar.append({"dosya": rel, "alt": p["aciklama"]})
        if fotolar: b["fotograflar"] = fotolar
        k = [{"baslik": x["baslik"], "aciklama": x["aciklama"], "baslangic": x["baslangic"], "bitis": x["bitis"]} for x in kam if x["isletme_id"] == i["id"]]
        if k: b["kampanyalar"] = k
        cikti.append(b)

    # yayından kalkan fotoğrafları sil
    for kok, _, dosyalar in os.walk(FOTO):
        for d in dosyalar:
            yol = os.path.normpath(os.path.join(kok, d))
            if yol not in gerekli: os.remove(yol)
        if kok != FOTO and not os.listdir(kok): os.rmdir(kok)

    eski = json.load(open(os.path.join(KD, "isletmeler.json"), encoding="utf-8"))
    eski["isletmeler"] = cikti
    json.dump(eski, open(os.path.join(KD, "isletmeler.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pj = json.load(open(os.path.join(KD, "paketler.json"), encoding="utf-8"))
    pj["paketler"] = {p["kod"]: {"ad": p["ad"], "satista": p["satista"], "foto_limit": p["foto_limit"], "fiyat_yayini": p["fiyat_yayini"],
                                 "one_cikan": p["one_cikan"], "rozet": p["rozet"], "istatistik": p["istatistik"]} for p in sorted(pak, key=lambda x: x["foto_limit"])}
    json.dump(pj, open(os.path.join(KD, "paketler.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"kuyumcu senkron: {len(cikti)} işletme, {len(gerekli)} fotoğraf")
    return 0


if __name__ == "__main__":
    sys.exit(main())
