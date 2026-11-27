# Kuyumcu Pazarı sayfaları — content.py içinden exec edilir (page, ROOT, SITE, urls, LM, TODAY hazırdır).
# Yalnızca doğrulanmış ve yayın izni verilmiş GERÇEK işletmeler yayınlanır. Örnek/sahte işletme yoktur.
# Test için başka bir veri dosyası: KP_DATA=/yol/isletmeler.json python3 _kaynak/content.py
import json as _json, re as _re, html as _h, os as _os, datetime as _dt
from urllib.parse import quote_plus as _qp, quote as _q

_KD = _os.path.join(HERE, "kuyumcu")
_DATA = _os.environ.get("KP_DATA") or _os.path.join(_KD, "isletmeler.json")
_PAK = _json.load(open(_os.path.join(_KD, "paketler.json"), encoding="utf-8"))["paketler"]
_ILLER = _json.load(open(_os.path.join(ROOT, "kuyumcu-pazari", "iller.json"), encoding="utf-8"))["iller"]
_IL = {i["slug"]: i for i in _ILLER}
_ILCE = {(i["slug"], z["slug"]): z["ad"] for i in _ILLER for z in i["ilceler"]}
_GUN = [("pzt", "Pazartesi"), ("sal", "Salı"), ("car", "Çarşamba"), ("per", "Perşembe"), ("cum", "Cuma"), ("cmt", "Cumartesi"), ("paz", "Pazar")]
_YONTEM = {"vergi_levhasi": "Vergi levhası", "esnaf_sicil": "Esnaf sicil kaydı", "oda_kaydi": "Meslek odası kaydı",
           "telefon": "Telefon doğrulaması", "yerinde_goruntulu": "Görüntülü görüşmeyle işyeri kontrolü", "adres_ziyaret": "Adres ziyareti"}
_ALTIN = [("gram", "Gram altın"), ("ceyrek", "Çeyrek altın"), ("yarim", "Yarım altın"), ("tam", "Tam altın")]
E = _h.escape


_BUGUN = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=3))).date()  # İstanbul


class KPHata(Exception):
    pass


def _tel_ok(t):
    return isinstance(t, str) and _re.fullmatch(r"\+90\d{10}", t) is not None


def _saat_ok(v):
    # gece yarısını aşan saatler (ör. 10:00-02:00) desteklenmez: açılış < kapanış olmalı
    if v == "kapali": return True
    return isinstance(v, str) and _re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d", v) is not None and v[:5] < v[6:]


def _tarih(s):
    return _dt.date.fromisoformat(s)


def _dogrula(b, slugs):
    """Kayıt kurallara uymuyorsa KPHata; yayınlanmayacaksa None; yayınlanacaksa temizlenmiş kayıt."""
    ad = b.get("ad", "?")
    def hata(m): raise KPHata(f"{ad}: {m}")
    if not b.get("yayinda"): return None
    d = b.get("dogrulama") or {}
    if d.get("durum") != "dogrulandi": return None
    try: _tarih(d.get("tarih", ""))
    except Exception: hata("doğrulama tarihi geçersiz")
    ys = d.get("yontemler") or []
    if len(ys) < 2 or any(y not in _YONTEM for y in ys): hata("en az iki geçerli doğrulama yöntemi gerekli")
    for k in ("id", "slug", "ad", "il", "ilce", "adres", "telefon", "saatler", "paket"):
        if not b.get(k): hata(f"'{k}' eksik")
    if not _re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", b["slug"]): hata("slug yalnızca küçük harf, rakam ve tire içerebilir")
    if b["slug"] in slugs: hata("slug tekrar ediyor")
    if b["il"] not in _IL or (b["il"], b["ilce"]) not in _ILCE: hata("il/ilçe iller.json'da yok")
    if not _tel_ok(b["telefon"]): hata("telefon +90XXXXXXXXXX biçiminde olmalı")
    if b.get("whatsapp") and not _tel_ok(b["whatsapp"]): hata("WhatsApp +90XXXXXXXXXX biçiminde olmalı")
    if set(b["saatler"]) != {g for g, _ in _GUN} or not all(_saat_ok(v) for v in b["saatler"].values()): hata("çalışma saatleri 7 gün için SS:DD-SS:DD ya da 'kapali' olmalı")
    p = _PAK.get(b["paket"])
    if not p: hata("paket tanımsız")
    if not p.get("satista"): hata(f"'{b['paket']}' paketi henüz satışta değil; atanamaz")
    fotos = b.get("fotograflar") or []
    if len(fotos) > p["foto_limit"]: hata(f"paket en fazla {p['foto_limit']} fotoğraf içerir")
    for f in fotos:
        if not f.get("alt") or not _re.fullmatch(r"kuyumcu-pazari/foto/[a-z0-9-]+/[a-z0-9_-]+\.(jpg|jpeg|png|webp)", f.get("dosya", "")): hata("fotoğraf yolu/alt metni geçersiz")
        if not _os.path.exists(_os.path.join(ROOT, f["dosya"])): hata(f"fotoğraf dosyası yok: {f['dosya']}")
    fiyat = None
    fi = b.get("fiyat_izni") or {}
    if fi.get("verildi") and p["fiyat_yayini"] and b.get("fiyatlar"):
        fy = b["fiyatlar"]
        try: g = _dt.datetime.fromisoformat(fy["guncelleme"])
        except Exception: hata("fiyat güncelleme zamanı geçersiz (ISO 8601, saat dilimiyle)")
        if g.tzinfo is None: hata("fiyat güncelleme zamanında saat dilimi yok")
        for k, _ in _ALTIN:
            x = fy.get(k)
            if x is None: continue
            if not (isinstance(x.get("alis"), (int, float)) and isinstance(x.get("satis"), (int, float)) and 0 < x["alis"] <= x["satis"]): hata(f"{k} fiyatı geçersiz (alış ≤ satış, pozitif)")
        if not any(fy.get(k) for k, _ in _ALTIN): hata("fiyat izni var ama fiyat yok")
        fiyat = fy
    kamp = []
    for k in b.get("kampanyalar") or []:
        try: k1, k2 = _tarih(k["baslangic"]), _tarih(k["bitis"])
        except Exception: hata("kampanya tarihi geçersiz")
        if not (3 <= len(str(k.get("baslik", "")).strip()) <= 80 and 3 <= len(str(k.get("aciklama", "")).strip()) <= 500) or k2 < k1 or (k2 - k1).days > 60: hata("kampanya geçersiz")
        if k2 >= _BUGUN: kamp.append(k)
    out = dict(b); out["_fiyat"] = fiyat; out["_paket"] = p; out["_kampanya"] = kamp
    out["_il"] = _IL[b["il"]]["ad"]; out["_ilce"] = _ILCE[(b["il"], b["ilce"])]
    out["_url"] = f"/kuyumcu-pazari/{b['il']}/{b['slug']}.html"
    return out


def _yukle():
    d = _json.load(open(_DATA, encoding="utf-8"))
    yay, slugs = [], set()
    for b in d.get("isletmeler", []):
        r = _dogrula(b, slugs)
        if r: yay.append(r); slugs.add(r["slug"])
    # öne çıkan paket önce, sonra ada göre
    yay.sort(key=lambda x: (not x["_paket"].get("one_cikan"), x["ad"].lower()))
    return yay


_tr = lambda n: f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
_tr0 = lambda n: f"{n:,.0f}".replace(",", ".")

KP_CSS = """<style>
.kp-lead{color:var(--muted);font-size:16px;line-height:1.55;margin:4px 0 16px}
.kp-filter{display:grid;grid-template-columns:1fr 1fr;gap:10px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px}
.kp-filter label{display:block;font-size:12.5px;font-weight:700;color:var(--muted);margin-bottom:5px}
.kp-filter select,.kp-form input,.kp-form select,.kp-form textarea{width:100%;font:inherit;font-size:15px;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:11px 12px}
.kp-filter .full{grid-column:1/-1;display:flex;align-items:center;gap:8px;font-size:14px;color:var(--ink);font-weight:600}
.kp-filter .full input{width:auto}
.kp-sayi{font-size:13px;color:var(--muted);margin:12px 2px}
.kp-list{display:grid;gap:12px;margin:10px 0 18px}
.kp-card{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;color:var(--ink);text-decoration:none}
.kp-card h3{margin:0 0 4px;font-size:17px}.kp-card .yer{color:var(--muted);font-size:13.5px}
.kp-rozet{display:inline-block;font-size:11.5px;font-weight:800;border-radius:999px;padding:3px 8px;margin:6px 6px 0 0;border:1px solid var(--line);color:var(--muted)}
.kp-rozet.ok{color:#16a34a;border-color:color-mix(in srgb,#16a34a 45%,var(--line))}
.kp-rozet.gold{color:var(--gold);border-color:color-mix(in srgb,var(--gold) 50%,var(--line))}
.kp-bos{text-align:center;background:var(--card);border:1px dashed var(--line);border-radius:18px;padding:26px 18px;margin:14px 0}
.kp-bos b{display:block;font-size:17px;margin-bottom:6px}.kp-bos p{color:var(--muted);margin:6px 0 12px;line-height:1.5}
.kp-adim{display:grid;gap:10px;margin:12px 0;counter-reset:a}
.kp-adim div{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px 12px 48px;position:relative;line-height:1.45}
.kp-adim div::before{counter-increment:a;content:counter(a);position:absolute;left:14px;top:12px;width:24px;height:24px;border-radius:50%;background:var(--gold);color:#1a1200;font-weight:800;text-align:center;line-height:24px;font-size:13px}
.kp-btns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}
.kp-btns a{display:block;text-align:center;font-weight:800;text-decoration:none;border-radius:14px;padding:12px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.kp-btns a.wa{background:#16a34a;border-color:#16a34a;color:#fff}
.kp-foto{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:12px 0}
.kp-foto img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:12px;display:block}
.kp-acik{font-weight:800}.kp-acik.evet{color:#16a34a}.kp-acik.hayir{color:#dc2626}
.kp-fiyat.eski table{opacity:.55}
.kp-kampanya{background:color-mix(in srgb,var(--gold) 10%,var(--card));border:1px solid color-mix(in srgb,var(--gold) 45%,var(--line));border-radius:14px;padding:12px 14px;margin:10px 0}
.kp-kampanya p{margin:6px 0;line-height:1.45}
.kp-uyari{background:color-mix(in srgb,#f59e0b 14%,var(--card));border:1px solid color-mix(in srgb,#f59e0b 45%,var(--line));border-radius:12px;padding:10px 12px;font-size:13.5px;margin:8px 0}
.kp-form{display:grid;gap:12px;margin:12px 0}
.kp-form .iki{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.kp-form label{font-size:13px;font-weight:700;color:var(--muted);display:block;margin-bottom:5px}
.kp-form .onay{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;line-height:1.45;color:var(--ink);font-weight:500}
.kp-form .onay input{width:20px;height:20px;flex:none;margin-top:1px}
.kp-form .hata{color:#dc2626;font-size:13px;font-weight:700;min-height:1em}
.kp-form button{font:inherit;font-weight:800;font-size:16px;background:var(--gold);color:#1a1200;border:0;border-radius:14px;padding:14px;cursor:pointer}
.kp-sonuc{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:12px 0}
.kp-sonuc textarea{width:100%;min-height:160px;font:13px/1.45 ui-monospace,monospace;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:10px}
@media (max-width:520px){.kp-filter,.kp-form .iki,.kp-btns{grid-template-columns:1fr}}
</style>"""

_GUVEN = ('<p class="note">Piyasa Nabzı işletmeler adına satış yapmaz ve aracılık ücreti almaz. Listelenen işletmeler '
          '<a href="/kuyumcu-pazari/kurallar.html">doğrulama kurallarımıza</a> göre kontrol edilir; işletme fiyatlarını işletmenin kendisi girer '
          've Piyasa Nabzı bu fiyatları garanti etmez. Alım satımdan önce fiyatı işletmeyle teyit et.</p>')


def _kart(b):
    rz = '<span class="kp-rozet ok">✓ Doğrulandı</span>'
    if b["_fiyat"]: rz += '<span class="kp-rozet gold">Fiyat paylaşıyor</span>'
    if b["_paket"].get("rozet"): rz += f'<span class="kp-rozet gold">{E(b["_paket"]["rozet"])}</span>'
    return (f'<a class="kp-card" href="{b["_url"]}" data-il="{b["il"]}" data-ilce="{b["ilce"]}" data-fiyat="{1 if b["_fiyat"] else 0}">'
            f'<h3>{E(b["ad"])}</h3><div class="yer">{E(b["_ilce"])}, {E(b["_il"])}</div>{rz}</a>')


def _pazar(yay):
    il_opts = "".join(f'<option value="{i["slug"]}">{E(i["ad"])}</option>' for i in _ILLER)
    kartlar = "".join(_kart(b) for b in yay)
    n = len(yay)
    bos_genel = ('<div class="kp-bos" id="kpBosGenel"><b>Kuyumcu Pazarı yeni açılıyor</b>'
                 '<p>Henüz doğrulaması tamamlanmış bir işletme yok. İlk kuyumcular doğrulandıkça burada il ve ilçeye göre listelenecek. '
                 'Burada hiçbir zaman örnek ya da doğrulanmamış işletme gösterilmez.</p>'
                 '<a class="cta" href="/kuyumcu-pazari/basvuru.html">İşletmeni ekle — başvuru ücretsiz</a></div>')
    bos_filtre = ('<div class="kp-bos" id="kpBosFiltre" hidden><b>Bu bölgede henüz kayıtlı kuyumcu yok</b>'
                  '<p>Seçtiğin il veya ilçede doğrulanmış işletme bulunmuyor. Filtreyi genişletebilir ya da bu bölgedeki bir kuyumcuya bizi önerebilirsin.</p>'
                  '<a class="cta" href="/kuyumcu-pazari/basvuru.html">İşletme başvurusu</a></div>')
    body = f"""<p class="kp-lead">Türkiye genelindeki <b>doğrulanmış</b> kuyumcuları il ve ilçeye göre bul; adres, telefon, WhatsApp, çalışma saatleri ve işletmenin paylaştığı altın fiyatlarını tek yerde gör.</p>
<form class="kp-filter" id="kpFiltre" onsubmit="return false">
  <div><label for="kpIl">İl</label><select id="kpIl"><option value="">Tüm iller (81)</option>{il_opts}</select></div>
  <div><label for="kpIlce">İlçe</label><select id="kpIlce" disabled><option value="">Önce il seç</option></select></div>
  <label class="full"><input type="checkbox" id="kpFiyat"> Yalnızca fiyat paylaşan işletmeler</label>
</form>
<div class="kp-sayi" id="kpSayi">{"Doğrulanmış işletme sayısı: " + str(n) if n else ""}</div>
<div class="kp-list" id="kpListe">{kartlar}</div>
{bos_genel if n == 0 else ""}{bos_filtre}
<h2>Nasıl çalışır?</h2>
<div class="kp-adim">
  <div><b>İşletme başvurur.</b> Kuyumcu, başvuru formunu doldurup e-postayla gönderir.</div>
  <div><b>Biz doğrularız.</b> Vergi levhası veya esnaf kaydı, telefon ve işyeri kontrolüyle işletmenin gerçek olduğunu teyit ederiz.</div>
  <div><b>Profil yayınlanır.</b> Yalnızca doğrulanan işletmeler listelenir. Fiyat paylaşmak, işletmenin ayrıca yazılı izin vermesine bağlıdır.</div>
</div>
<div class="box gold"><b>Canlı Kapalıçarşı fiyatları:</b> Kuyumcuya gitmeden önce güncel piyasa fiyatına bak.<br><a class="cta" href="/">Canlı altın fiyatları →</a></div>
{_GUVEN}
<script>
(function(){{
  var il=document.getElementById("kpIl"), ilce=document.getElementById("kpIlce"), fy=document.getElementById("kpFiyat");
  var kart=[].slice.call(document.querySelectorAll("#kpListe .kp-card")), bos=document.getElementById("kpBosFiltre"), sayi=document.getElementById("kpSayi");
  var IL=null;
  function q(){{ var u=new URLSearchParams(location.search); return {{il:u.get("il")||"",ilce:u.get("ilce")||"",f:u.get("fiyat")==="1"}}; }}
  function yaz(){{ var u=new URLSearchParams(); if(il.value) u.set("il",il.value); if(ilce.value) u.set("ilce",ilce.value); if(fy.checked) u.set("fiyat","1");
    history.replaceState(null,"",location.pathname+(u.toString()?"?"+u:"")); }}
  function ilceDoldur(sec){{
    ilce.innerHTML=""; var o=document.createElement("option"); o.value=""; o.textContent=il.value?"Tüm ilçeler":"Önce il seç"; ilce.appendChild(o);
    if(!il.value||!IL){{ ilce.disabled=true; return; }}
    var x=IL.find(function(i){{return i.slug===il.value;}}); if(!x){{ ilce.disabled=true; return; }}
    x.ilceler.forEach(function(z){{ var o=document.createElement("option"); o.value=z.slug; o.textContent=z.ad; ilce.appendChild(o); }});
    ilce.disabled=false; if(sec) ilce.value=sec;
  }}
  function suz(){{
    var n=0; kart.forEach(function(k){{ var ok=(!il.value||k.dataset.il===il.value)&&(!ilce.value||k.dataset.ilce===ilce.value)&&(!fy.checked||k.dataset.fiyat==="1"); k.hidden=!ok; if(ok) n++; }});
    if(kart.length){{ bos.hidden=n>0; sayi.textContent=(il.value||fy.checked?"Bu seçimde ":"")+"doğrulanmış işletme sayısı: "+n; }}
  }}
  il.addEventListener("change",function(){{ ilceDoldur(""); suz(); yaz(); }});
  ilce.addEventListener("change",function(){{ suz(); yaz(); }});
  fy.addEventListener("change",function(){{ suz(); yaz(); }});
  var p=q(); il.value=p.il; fy.checked=p.f;
  fetch("/kuyumcu-pazari/iller.json").then(function(r){{return r.json();}}).then(function(d){{ IL=d.iller; ilceDoldur(p.ilce); suz(); }}).catch(function(){{ ilce.innerHTML='<option value="">İlçe listesi yüklenemedi</option>'; }});
  suz();
}})();
</script>"""
    return body


def _profil(b):
    p = b["_paket"]
    rz = '<span class="kp-rozet ok">✓ Doğrulandı</span>' + (f'<span class="kp-rozet gold">{E(p["rozet"])}</span>' if p.get("rozet") else "")
    tel = b["telefon"]; wa = b.get("whatsapp")
    btn = f'<a href="tel:{tel}" data-kp-say="ara">📞 Ara</a>' + (f'<a class="wa" href="https://wa.me/{wa[1:]}" rel="nofollow noopener" target="_blank" data-kp-say="whatsapp">WhatsApp</a>' if wa else "")
    harita = E("https://www.google.com/maps/search/?api=1&query=" + _qp(f'{b["ad"]} {b["adres"]} {b["_ilce"]} {b["_il"]}'))
    saat_rows = "".join(f'<tr><td>{g}</td><td>{"Kapalı" if b["saatler"][k] == "kapali" else E(b["saatler"][k].replace("-", " – "))}</td></tr>' for k, g in _GUN)
    foto = ""
    if b.get("fotograflar"):
        foto = '<div class="kp-foto">' + "".join(f'<img src="/{E(f["dosya"])}" alt="{E(f["alt"])}" loading="lazy">' for f in b["fotograflar"]) + "</div>"
    fiyat = ""
    if b["_fiyat"]:
        fy = b["_fiyat"]; g = _dt.datetime.fromisoformat(fy["guncelleme"])
        rows = "".join((f'<tr data-tur="{k}"><td>{ad}</td><td data-a>₺{_tr(fy[k]["alis"]) if k=="gram" else _tr0(fy[k]["alis"])}</td><td data-s>₺{_tr(fy[k]["satis"]) if k=="gram" else _tr0(fy[k]["satis"])}</td></tr>'
                        if fy.get(k) else f'<tr data-tur="{k}" hidden><td>{ad}</td><td data-a></td><td data-s></td></tr>') for k, ad in _ALTIN)
        ay = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
        gyaz = f"{g.day} {ay[g.month-1]} {g.year}, {g:%H:%M}"
        fiyat = (f'<h2>İşletmenin altın fiyatları</h2><div class="kp-fiyat" id="kpFiyatBlok" data-guncelleme="{E(fy["guncelleme"])}">'
                 f'<div class="kp-uyari" id="kpEski" hidden></div>'
                 f'<table><tr><th>Ürün</th><th>Alış</th><th>Satış</th></tr>{rows}</table>'
                 f'<p class="note">Fiyatları işletme girmiştir · Son güncelleme: <b id="kpFiyatZaman">{gyaz}</b>. Fiyatlar anlık değildir; alım satımdan önce işletmeyle teyit et. '
                 f'Karşılaştırma için <a href="/">canlı Kapalıçarşı fiyatlarına</a> bakabilirsin.</p></div>')
    else:
        fiyat = '<h2>Altın fiyatları</h2><p class="note">Bu işletme Kuyumcu Pazarı üzerinden fiyat paylaşmıyor. Güncel fiyat için işletmeyi arayabilir ya da <a href="/">canlı Kapalıçarşı fiyatlarına</a> bakabilirsin.</p>'
    yontem = ", ".join(_YONTEM[y] for y in b["dogrulama"]["yontemler"])
    ld = {"@context": "https://schema.org", "@type": "JewelryStore", "name": b["ad"], "telephone": tel,
          "address": {"@type": "PostalAddress", "streetAddress": b["adres"], "addressLocality": b["_ilce"], "addressRegion": b["_il"], "addressCountry": "TR"},
          "url": SITE + b["_url"],
          "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": d, "opens": b["saatler"][k].split("-")[0], "closes": b["saatler"][k].split("-")[1]}
                                        for (k, _), d in zip(_GUN, ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]) if b["saatler"][k] != "kapali"]}
    if b.get("fotograflar"): ld["image"] = [SITE + "/" + f["dosya"] for f in b["fotograflar"]]
    head = KP_CSS + '<script type="application/ld+json">' + _json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    saatjs = _json.dumps(b["saatler"])
    kamp = "".join(f'<div class="kp-kampanya" data-bitis="{E(k["bitis"])}"><b>🎁 {E(k["baslik"])}</b><p>{E(k["aciklama"])}</p><small class="note">Son gün: {E(_tarihtr(k["bitis"]))} · Kampanya koşullarını işletmeyle teyit et.</small></div>' for k in b.get("_kampanya", []))
    body = f"""<div class="kp-lead" data-kp-id="{E(b["id"])}">{E(b["_ilce"])}, {E(b["_il"])}<br>{rz}</div>
<div class="kp-btns">{btn}</div>
{kamp}
<p><span class="kp-acik" id="kpAcik"></span></p>
{('<p>' + E(b["aciklama"]) + '</p>') if b.get("aciklama") else ""}
{foto}
<h2>Adres</h2><p>{E(b["adres"])}<br>{E(b["_ilce"])} / {E(b["_il"])}<br><a href="{harita}" rel="nofollow noopener" target="_blank" data-kp-say="yol_tarifi">Haritada aç →</a></p>
<h2>Çalışma saatleri</h2><table>{saat_rows}</table>
{fiyat}
<h2>Doğrulama</h2><p class="note">Bu işletme {E(b["dogrulama"]["tarih"])} tarihinde doğrulandı ({E(yontem)}). <a href="/kuyumcu-pazari/kurallar.html">Doğrulama kurallarımız</a></p>
<p class="note">Bilgilerde hata mı var? <a href="mailto:piyasanabzi.iletisim@gmail.com?subject={E(_q('Kuyumcu Pazarı düzeltme: ' + b['id']))}">Bize bildir</a></p>
{_GUVEN}
<script>
(function(){{
  var S={saatjs}, G=["paz","pzt","sal","car","per","cum","cmt"];
  try{{
    var f=new Intl.DateTimeFormat("en-GB",{{timeZone:"Europe/Istanbul",weekday:"short",hour:"2-digit",minute:"2-digit",hour12:false}}).formatToParts(new Date());
    var w={{Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6}}[f.find(function(x){{return x.type==="weekday";}}).value];
    var hm=f.find(function(x){{return x.type==="hour";}}).value+":"+f.find(function(x){{return x.type==="minute";}}).value;
    var s=S[G[w]], e=document.getElementById("kpAcik");
    if(s==="kapali"){{ e.textContent="Bugün kapalı"; e.className="kp-acik hayir"; }}
    else {{ var a=s.split("-"); var ac=hm>=a[0]&&hm<a[1]; e.textContent=ac?"Şu an açık · "+a[0]+"–"+a[1]:"Şu an kapalı · bugün "+a[0]+"–"+a[1]; e.className="kp-acik "+(ac?"evet":"hayir"); }}
  }}catch(x){{}}
  var fb=document.getElementById("kpFiyatBlok");
  if(fb){{ var t=Date.parse(fb.dataset.guncelleme), y=(Date.now()-t)/36e5, u=document.getElementById("kpEski");
    if(y>24*7){{ fb.querySelector("table").remove(); u.hidden=false; u.textContent="Bu işletmenin fiyatları 7 günden eski olduğu için gösterilmiyor. Güncel fiyat için işletmeyi ara."; }}
    else if(y>24){{ fb.classList.add("eski"); u.hidden=false; u.textContent="Dikkat: bu fiyatlar "+Math.floor(y/24)+" gün önce güncellendi; şu anki fiyat farklı olabilir."; }} }}
  try{{ var bg=new Intl.DateTimeFormat("en-CA",{{timeZone:"Europe/Istanbul"}}).format(new Date());
    Array.prototype.forEach.call(document.querySelectorAll(".kp-kampanya"),function(k){{ if(k.getAttribute("data-bitis")<bg) k.remove(); }}); }}catch(x){{}}
}})();
</script>"""
    head += '<script src="/kuyumcu-pazari/ayar.js" defer></script><script src="/kuyumcu-pazari/sayac.js" defer></script>'
    return head, body


def _tarihtr(s):
    d = _tarih(s); ay = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    return f"{d.day} {ay[d.month-1]} {d.year}"


def _kurallar():
    yon = "".join(f"<li>{v}</li>" for v in _YONTEM.values())
    return f"""<p class="kp-lead">Kuyumcu Pazarı'nda yalnızca gerçek olduğu doğrulanan işletmeler listelenir. Bu sayfa doğrulamayı, fiyat yayınlamayı ve kaldırma kurallarını açıklar.</p>
<h2>1. Başvuru</h2><p>İşletme sahibi ya da yetkilisi <a href="/kuyumcu-pazari/basvuru.html">başvuru formunu</a> doldurur. Form, bilgileri hazır bir e-posta olarak açar; başvuru, bu e-posta gönderildiğinde bize ulaşır. Başvuru ve listelenme şu an ücretsizdir.</p>
<h2>2. Doğrulama</h2><p>Bir işletme en az iki farklı yöntemle doğrulanmadan yayınlanmaz:</p><ul>{yon}</ul>
<p>Belgeler başvuru formuyla istenmez; doğrulama görüşmesinde yalnızca görülür ve kopyası saklanmaz. Doğrulama tarihi ve kullanılan yöntemler işletme sayfasında gösterilir.</p>
<h2>3. Fiyat yayınlama izni</h2><ul>
<li>Fiyatlar yalnızca işletmenin yazılı izniyle ve işletmenin kendi bildirdiği değerlerle yayınlanır; Piyasa Nabzı işletme adına fiyat girmez veya tahmin etmez.</li>
<li>Her fiyatın yanında son güncelleme tarihi ve saati yazar. 24 saatten eski fiyatlarda uyarı çıkar, 7 günden eski fiyatlar gizlenir.</li>
<li>İşletme izni istediği zaman geri alabilir; fiyatlar aynı gün kaldırılır.</li>
<li>Piyasa fiyatlarından açıkça sapan, yanıltıcı veya tutarsız fiyatlar yayınlanmaz.</li></ul>
<h2>4. Yorumlar ve puanlar</h2><p>Kuyumcu Pazarı'nda şu an yorum ve puan sistemi yoktur. Hiçbir işletme için yorum, puan veya müşteri görüşü yazılmaz ya da satın alınmaz.</p>
<h2>5. Kaldırma ve şikâyet</h2><p>Kapanan, bilgileri değişen veya kurallara uymayan işletmeler kaldırılır. Hatalı bilgi veya şikâyet için: <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a></p>
<h2>6. Üyelik paketleri</h2><p>İleride işletmelere ek özellikler sunan ücretli paketler olabilir. Ücretli bir paket başlatıldığında içeriği ve ücreti önceden açıkça duyurulur; doğrulama kuralları paketten bağımsız olarak herkes için aynıdır.</p>
{_GUVEN}"""


def _kvkk():
    return """<div class="kp-uyari"><b>Taslak metin.</b> Bu aydınlatma metni yayın öncesi hukuki incelemeden geçirilecektir.</div>
<p>Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu'nun (KVKK) 10. maddesi uyarınca, Kuyumcu Pazarı işletme başvurusu sırasında işlenen kişisel veriler hakkında bilgi vermek için hazırlanmıştır.</p>
<h2>Veri sorumlusu</h2><p>Piyasa Nabzı (piyasanabzi.site) işletmecisi. İletişim: <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a></p>
<h2>İşlenen veriler</h2><ul>
<li><b>Kimlik:</b> başvuruyu yapan yetkilinin adı ve soyadı</li>
<li><b>İletişim:</b> telefon, WhatsApp numarası, e-posta adresi</li>
<li><b>İşletme bilgileri:</b> işletme adı, adresi, il/ilçe, çalışma saatleri, fiyat paylaşım tercihi</li></ul>
<p>Başvuru formunda T.C. kimlik numarası, vergi numarası veya belge kopyası <b>istenmez</b>. Doğrulama sırasında gösterilen belgelerin kopyası saklanmaz.</p>
<h2>İşleme amaçları ve hukuki sebepler</h2><ul>
<li>Başvurunun değerlendirilmesi ve işletmenin doğrulanması: bir sözleşmenin kurulmasıyla doğrudan ilgili olması (KVKK m.5/2-c)</li>
<li>Doğrulanan işletme bilgilerinin Kuyumcu Pazarı'nda yayınlanması: sözleşmenin ifası (m.5/2-c) ve işletmenin kendisi tarafından alenileştirilmesi (m.5/2-d)</li>
<li>Başvuruyla ilgili iletişim: meşru menfaat (m.5/2-f)</li></ul>
<h2>Toplama yöntemi</h2><p>Veriler, başvuru formunun hazırladığı e-postayı göndermenle elektronik ortamda toplanır. Form verileri tarayıcında hazırlanır; e-postayı göndermedikçe bize hiçbir bilgi ulaşmaz.</p>
<h2>Aktarım</h2><p>Başvuru e-postaları Google LLC'nin e-posta hizmeti (Gmail) üzerinden alınır; bu hizmetin sunucuları yurt dışında bulunabilir. Yurt dışına aktarım KVKK m.9'daki usullere uygun şekilde yapılır. Veriler başka hiçbir üçüncü kişiyle paylaşılmaz ve satılmaz.</p>
<h2>Saklama süresi</h2><p>Reddedilen veya geri çekilen başvurular en geç 6 ay içinde, yayından kalkan işletmelerin bilgileri en geç 1 yıl içinde silinir.</p>
<h2>Haklarınız</h2><p>KVKK m.11 uyarınca verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, düzeltilmesini veya silinmesini isteme ve itiraz etme haklarına sahipsiniz. Talepleriniz için: <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a></p>"""


def _basvuru():
    il_opts = "".join(f'<option value="{i["slug"]}">{E(i["ad"])}</option>' for i in _ILLER)
    return f"""<p class="kp-lead">Kuyumcu Pazarı'nda listelenmek için işletme bilgilerini doldur. Başvuru ücretsizdir. Doğrulamadan sonra işletme sayfan yayınlanır.</p>
<div class="box"><b>Bu form nasıl çalışır?</b> Şu an çevrimiçi bir kayıt sistemimiz yok. "Başvuruyu hazırla" düğmesi, bilgilerini içeren hazır bir e-postayı telefonundaki e-posta uygulamasında açar. <b>Başvurun, o e-postayı gönderdiğinde bize ulaşır.</b> Fotoğraf eklemek istersen açılan e-postaya ek olarak ekleyebilirsin.</div>
<form class="kp-form" id="kpForm" novalidate>
  <div><label for="fAd">İşletme adı *</label><input id="fAd" maxlength="80" required autocomplete="organization"></div>
  <div><label for="fYetkili">Yetkili adı soyadı *</label><input id="fYetkili" maxlength="60" required autocomplete="name"></div>
  <div class="iki"><div><label for="fIl">İl *</label><select id="fIl" required><option value="">Seç</option>{il_opts}</select></div>
    <div><label for="fIlce">İlçe *</label><select id="fIlce" required disabled><option value="">Önce il seç</option></select></div></div>
  <div><label for="fAdres">Açık adres *</label><textarea id="fAdres" rows="2" maxlength="250" required autocomplete="street-address"></textarea></div>
  <div class="iki"><div><label for="fTel">İşletme telefonu *</label><input id="fTel" type="tel" inputmode="tel" maxlength="20" required placeholder="0212 000 00 00"></div>
    <div><label for="fWa">WhatsApp (isteğe bağlı)</label><input id="fWa" type="tel" inputmode="tel" maxlength="20" placeholder="05xx xxx xx xx"></div></div>
  <div><label for="fEposta">E-posta (isteğe bağlı)</label><input id="fEposta" type="email" maxlength="80" autocomplete="email"></div>
  <div><label for="fSaat">Çalışma saatleri *</label><textarea id="fSaat" rows="2" maxlength="200" required placeholder="Örn. Hafta içi 09:00–19:00, Cumartesi 10:00–18:00, Pazar kapalı"></textarea></div>
  <div><label for="fFiyat">Altın fiyatlarınızı sitede paylaşmak ister misiniz?</label>
    <select id="fFiyat"><option value="Hayır">Hayır, yalnızca iletişim bilgilerim listelensin</option><option value="Evet">Evet, fiyat paylaşmak istiyorum (ayrıca yazılı izin alınır)</option></select></div>
  <div><label for="fNot">Eklemek istedikleriniz (isteğe bağlı)</label><textarea id="fNot" rows="2" maxlength="300"></textarea></div>
  <label class="onay"><input type="checkbox" id="fKvkk" required> <span><a href="/kuyumcu-pazari/kvkk.html" target="_blank">Aydınlatma metnini</a> okudum. *</span></label>
  <label class="onay"><input type="checkbox" id="fBeyan" required> <span>Bu işletmenin sahibi veya yetkilisiyim; verdiğim bilgiler doğrudur. Doğrulama için benimle iletişime geçilmesini kabul ediyorum. *</span></label>
  <div class="hata" id="fHata" role="alert"></div>
  <button type="submit">Başvuruyu hazırla</button>
</form>
<div class="kp-sonuc" id="kpSonuc" hidden>
  <b>E-posta taslağın hazırlandı.</b>
  <p class="note" style="font-size:14px">E-posta uygulaman açıldıysa <b>Gönder</b>'e bas; başvurun ancak gönderildiğinde bize ulaşır. Uygulama açılmadıysa aşağıdaki metni kopyalayıp <b>piyasanabzi.iletisim@gmail.com</b> adresine e-postayla gönderebilirsin.</p>
  <textarea id="kpMetin" readonly></textarea>
  <div class="kp-btns"><a href="#" id="kpKopya">Metni kopyala</a><a href="#" id="kpTekrar">E-postayı tekrar aç</a></div>
</div>
<p class="note">Başvurular sırayla incelenir. Doğrulama için verdiğin telefon numarasından aranırsın. Kurallar: <a href="/kuyumcu-pazari/kurallar.html">doğrulama ve yayın kuralları</a>.</p>
<script>
(function(){{
  var $=function(i){{return document.getElementById(i);}}, IL=null, mailto="";
  fetch("/kuyumcu-pazari/iller.json").then(function(r){{return r.json();}}).then(function(d){{IL=d.iller;}}).catch(function(){{}});
  $("fIl").addEventListener("change",function(){{
    var s=$("fIlce"); s.innerHTML='<option value="">Seç</option>';
    var x=IL&&IL.find(function(i){{return i.slug===$("fIl").value;}});
    if(!x){{ s.disabled=true; if($("fIl").value&&!IL) s.innerHTML='<option value="">İlçe listesi yüklenemedi</option>'; return; }}
    x.ilceler.forEach(function(z){{ var o=document.createElement("option"); o.value=z.slug; o.textContent=z.ad; s.appendChild(o); }}); s.disabled=false;
  }});
  function tel(v){{ var d=String(v||"").replace(/\\D/g,""); if(d.indexOf("90")===0&&d.length===12) d=d.slice(2); if(d.charAt(0)==="0") d=d.slice(1); return d.length===10?"+90"+d:null; }}
  function ad(sel){{ return sel.options[sel.selectedIndex]?sel.options[sel.selectedIndex].text:""; }}
  $("kpForm").addEventListener("submit",function(e){{
    e.preventDefault(); var h=$("fHata"); h.textContent="";
    var zor=[["fAd","İşletme adı"],["fYetkili","Yetkili adı"],["fIl","İl"],["fIlce","İlçe"],["fAdres","Adres"],["fTel","Telefon"],["fSaat","Çalışma saatleri"]];
    for(var i=0;i<zor.length;i++){{ if(!$(zor[i][0]).value.trim()){{ h.textContent=zor[i][1]+" gerekli."; $(zor[i][0]).focus(); return; }} }}
    var t=tel($("fTel").value); if(!t){{ h.textContent="Telefon numarası 10 haneli olmalı (ör. 0212 000 00 00)."; $("fTel").focus(); return; }}
    var w=""; if($("fWa").value.trim()){{ w=tel($("fWa").value); if(!w){{ h.textContent="WhatsApp numarası geçersiz."; $("fWa").focus(); return; }} }}
    var ep=$("fEposta").value.trim(); if(ep&&!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(ep)){{ h.textContent="E-posta adresi geçersiz."; $("fEposta").focus(); return; }}
    if(!$("fKvkk").checked||!$("fBeyan").checked){{ h.textContent="Devam etmek için iki onay kutusunu da işaretle."; return; }}
    var metin=["KUYUMCU PAZARI İŞLETME BAŞVURUSU","",
      "İşletme adı: "+$("fAd").value.trim(),"Yetkili: "+$("fYetkili").value.trim(),
      "İl / İlçe: "+ad($("fIl"))+" / "+ad($("fIlce")),"Adres: "+$("fAdres").value.trim(),
      "Telefon: "+t,"WhatsApp: "+(w||"-"),"E-posta: "+(ep||"-"),
      "Çalışma saatleri: "+$("fSaat").value.trim(),"Fiyat paylaşımı: "+$("fFiyat").value,
      "Not: "+($("fNot").value.trim()||"-"),"",
      "Aydınlatma metnini okudum: Evet","İşletme yetkilisi olduğumu ve bilgilerin doğru olduğunu beyan ederim: Evet",
      "Form sürümü: 1 · "+new Date().toISOString()].join("\\n");
    $("kpMetin").value=metin;
    mailto="mailto:piyasanabzi.iletisim@gmail.com?subject="+encodeURIComponent("Kuyumcu Pazarı başvurusu: "+$("fAd").value.trim())+"&body="+encodeURIComponent(metin);
    $("kpSonuc").hidden=false; $("kpSonuc").scrollIntoView({{behavior:"smooth",block:"start"}});
    location.href=mailto;
  }});
  $("kpTekrar").addEventListener("click",function(e){{ e.preventDefault(); if(mailto) location.href=mailto; }});
  $("kpKopya").addEventListener("click",function(e){{ e.preventDefault(); var m=$("kpMetin");
    (navigator.clipboard?navigator.clipboard.writeText(m.value):Promise.reject()).then(function(){{ $("kpKopya").textContent="Kopyalandı ✓"; }}).catch(function(){{ m.select(); try{{document.execCommand("copy"); $("kpKopya").textContent="Kopyalandı ✓";}}catch(x){{}} }}); }});
}})();
</script>"""


_YAY = _yukle()
_NOINDEX = '<meta name="robots" content="noindex,follow">'
_KPT = "2026-11-27"  # Kuyumcu Pazarı sayfalarının son değişiklik tarihi (sitemap)
_crumb = '<a href="/kuyumcu-pazari/">Kuyumcu Pazarı</a>'
# Pazar ana sayfası: işletme yokken arama motorlarında dizine alınmaz (boş sayfa "ince içerik" sayılmasın)
_u = page("kuyumcu-pazari/index.html", "Kuyumcu Pazarı: il ve ilçeye göre doğrulanmış kuyumcular",
          "Türkiye'nin 81 il ve 973 ilçesinde doğrulanmış kuyumcuları bul: adres, telefon, WhatsApp, çalışma saatleri ve işletmenin paylaştığı altın fiyatları.",
          _pazar(_YAY), article=False, head=KP_CSS + ("" if _YAY else _NOINDEX), h1="Kuyumcu Pazarı")
if _YAY: urls.append(_u); LM[_u] = _KPT
_u = (page("kuyumcu-pazari/basvuru.html", "Kuyumcu Pazarı işletme başvurusu",
                 "Kuyumcunuzu Kuyumcu Pazarı'na ücretsiz ekleyin: başvuru, doğrulama ve yayınlama adımları.",
                 _basvuru(), crumb=_crumb, article=False, head=KP_CSS, h1="İşletme başvurusu")); urls.append(_u); LM[_u] = _KPT
_u = (page("kuyumcu-pazari/kurallar.html", "Kuyumcu Pazarı doğrulama ve yayın kuralları",
                 "Kuyumcu Pazarı'nda işletmeler nasıl doğrulanır, fiyatlar hangi izinle yayınlanır, yorum ve kaldırma kuralları nelerdir?",
                 _kurallar(), crumb=_crumb, article=False, head=KP_CSS, h1="Doğrulama ve yayın kuralları")); urls.append(_u); LM[_u] = _KPT
page("kuyumcu-pazari/kvkk.html", "Kuyumcu Pazarı başvuru aydınlatma metni",
     "Kuyumcu Pazarı işletme başvurusunda işlenen kişisel veriler hakkında KVKK aydınlatma metni.",
     _kvkk(), crumb=_crumb, article=False, head=KP_CSS, h1="Başvuru aydınlatma metni (KVKK)")
# İşletme profilleri; artık yayında olmayanların eski sayfaları silinir
_var = set()
for _b in _YAY:
    _hd, _bd = _profil(_b)
    _u = page(_b["_url"].lstrip("/"), f'{_b["ad"]} – {_b["_ilce"]}, {_b["_il"]} kuyumcu',
              f'{_b["ad"]}: {_b["_ilce"]}, {_b["_il"]} kuyumcusu. Adres, telefon, çalışma saatleri' + (" ve altın fiyatları." if _b["_fiyat"] else "."),
              _bd, crumb=_crumb + f' › {E(_b["_il"])}', article=False, head=_hd, h1=_b["ad"])
    urls.append(_u); _var.add(_os.path.join(ROOT, _b["_url"].lstrip("/")))
for _p in glob.glob(_os.path.join(ROOT, "kuyumcu-pazari", "*", "*.html")):
    if _p not in _var and _os.path.basename(_os.path.dirname(_p)) in _IL: _os.remove(_p)
print("kuyumcu pazarı:", len(_YAY), "yayında işletme")


# ───────────── Kuyumcu Yönetim Sistemi: panel sayfaları (reklamsız, dizine kapalı, CSP'li) ─────────────
PANEL_CSS = """<style>
.kp-kutu{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:12px 0}
.kp-kutu h2{margin:0 0 8px;font-size:19px}.kp-kutu h3{margin:14px 0 6px;font-size:16px}
.kp-ust{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:6px 0 10px}
.kp-sekmeler{display:flex;gap:6px;overflow-x:auto;padding:4px 0 8px;scrollbar-width:none}
.kp-sekmeler button,.kp-filtreler button{flex:none;font:700 13.5px/1 Inter,system-ui,sans-serif;color:var(--muted);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:9px 13px;cursor:pointer}
.kp-sekmeler button[aria-selected=true],.kp-filtreler button.secili{color:#1a1200;background:var(--gold);border-color:var(--gold)}
.kp-filtreler{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}
.kp-durum{border-radius:16px;padding:12px 14px;margin:8px 0 12px;border:1px solid var(--line);background:var(--card)}
.kp-durum p{margin:6px 0;line-height:1.45}.kp-durum.d-onayli{border-color:#16a34a}.kp-durum.d-reddedildi,.kp-durum.d-askida{border-color:#dc2626}
.kp-durum.d-eksik_bilgi{border-color:#f59e0b}.kp-not{background:var(--bg);border-radius:10px;padding:8px 10px}
.kp-form button.ikincil,button.ikincil{background:var(--card);color:var(--ink);border:1px solid var(--line)}
button.ikincil,button.tehlike,button.kucuk,.kp-dugmeler button,.kp-kutu>button{font:inherit;font-weight:800;border-radius:12px;padding:10px 14px;cursor:pointer;border:1px solid var(--line)}
.kp-dugmeler button:not(.ikincil):not(.tehlike),.kp-kutu>button:not(.ikincil):not(.tehlike){background:var(--gold);color:#1a1200;border-color:var(--gold)}
button.tehlike{background:#dc2626;color:#fff;border-color:#dc2626}
button.kucuk{padding:7px 10px;font-size:13px}
button:disabled{opacity:.6;cursor:wait}
.kp-dugmeler{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.kp-satir{display:flex;gap:8px;align-items:center}.kp-satir select{flex:1}
.kp-kutu select,.kp-kutu input:not([type=checkbox]),.kp-kutu textarea{width:100%;font:inherit;font-size:15px;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:4px 0}
.kp-saatler{display:grid;gap:6px}
.kp-saat{display:grid;grid-template-columns:92px 1fr auto 1fr auto;gap:6px;align-items:center;font-size:14px}
.kp-saat input[type=time]{padding:8px}
.kp-saat label{display:flex;gap:4px;align-items:center;font-weight:600;color:var(--muted);margin:0}
.kp-fiyat-gir{display:grid;gap:8px}
.kp-fiyat-satir{display:grid;grid-template-columns:110px 1fr 1fr;gap:8px;align-items:center}
.kp-foto-liste{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:10px 0}
.kp-foto-liste figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.kp-foto-liste img,.kp-onizle{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;border-radius:10px}
.kp-foto-liste figcaption{padding:8px;font-size:13px}
.kp-dogrulama{display:grid;grid-template-columns:1fr;gap:4px;border-top:1px solid var(--line);padding:8px 0}
.kp-dogrulama.ok b{color:#16a34a}
.kp-etiket{font-size:12px;font-weight:800;border-radius:999px;padding:2px 8px;border:1px solid var(--line)}
.kp-kart-bas{all:unset;cursor:pointer;display:block;width:100%;line-height:1.5}
.kp-sapma td{background:color-mix(in srgb,#f59e0b 14%,var(--card))}
.kp-qr{background:#fff;padding:8px;border-radius:12px;display:block;margin:8px 0}
.kp-anahtar{word-break:break-all;font-size:14px}
.kp-paket{display:grid;gap:6px}.kp-paket-alan{display:grid;grid-template-columns:150px 1fr;align-items:center;gap:8px;font-size:14px}
.kp-paket-alan input[type=checkbox]{width:20px;height:20px}
#kpBildirim{position:fixed;left:12px;right:12px;bottom:14px;z-index:50;display:grid;gap:8px;max-width:520px;margin:0 auto}
.kp-bil{padding:12px 14px;border-radius:14px;font-weight:700;font-size:14px;box-shadow:0 6px 20px rgba(0,0,0,.25);background:#16a34a;color:#fff}
.kp-bil.hata{background:#dc2626}
@media (max-width:520px){.kp-saat{grid-template-columns:1fr 1fr auto;}.kp-saat b{grid-column:1/-1}.kp-saat span{display:none}.kp-fiyat-satir{grid-template-columns:1fr 1fr}.kp-fiyat-satir b{grid-column:1/-1}.kp-paket-alan{grid-template-columns:1fr}}
</style>"""
_CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; '
        'img-src \'self\' data: blob: https://*.supabase.co; connect-src \'self\' https://*.supabase.co; object-src \'none\'; base-uri \'none\'; form-action \'self\'">'
        '<meta name="referrer" content="no-referrer"><meta name="robots" content="noindex,nofollow">')
_PJS = '<script src="/kuyumcu-pazari/ayar.js" defer></script><script src="/kuyumcu-pazari/panel/pn-supa.js" defer></script><script src="/kuyumcu-pazari/panel/ortak.js" defer></script>'
_PBODY = '<div id="kpPanel"><noscript><p class="kp-uyari">Panel için tarayıcınızda JavaScript açık olmalı.</p></noscript><p class="note">Yükleniyor…</p></div>'
page("kuyumcu-pazari/panel/index.html", "Kuyumcu paneli", "Kuyumcu Pazarı işletme paneli: giriş, işletme bilgileri, fiyat, fotoğraf ve kampanya yönetimi.",
     _PBODY, crumb=_crumb, article=False, h1="Kuyumcu paneli", reklam=False,
     head=_CSP + KP_CSS + PANEL_CSS + _PJS + '<script src="/kuyumcu-pazari/panel/kuyumcu.js" defer></script>')
page("kuyumcu-pazari/yonetim/index.html", "Yönetim paneli", "Kuyumcu Pazarı yönetim paneli.",
     _PBODY, crumb=_crumb, article=False, h1="Yönetim paneli", reklam=False,
     head=_CSP + KP_CSS + PANEL_CSS + _PJS + '<script src="/kuyumcu-pazari/yonetim/yonetim.js" defer></script>')

_TASLAK = '<div class="kp-uyari"><b>Taslak metin.</b> Bu metin yayın öncesi hukuki incelemeden geçirilecektir.</div>'
page("kuyumcu-pazari/panel-aydinlatma.html", "Kuyumcu paneli aydınlatma metni",
     "Kuyumcu Pazarı işletme paneli üyeliğinde işlenen kişisel veriler hakkında KVKK aydınlatma metni.", _TASLAK + """
<p class="note">Sürüm: kp-panel-aydinlatma-2026-11-27</p>
<p>Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu'nun (KVKK) 10. maddesi uyarınca Kuyumcu Pazarı işletme paneli üyeliği sırasında işlenen kişisel veriler hakkında bilgi vermek için hazırlanmıştır.</p>
<h2>Veri sorumlusu</h2><p>Piyasa Nabzı (piyasanabzi.site) işletmecisi. İletişim: <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a></p>
<h2>İşlenen veriler</h2><ul>
<li><b>Hesap:</b> e-posta adresi, giriş zamanları, oturum bilgileri</li>
<li><b>Kimlik:</b> işletme yetkilisinin adı ve soyadı (yayınlanmaz)</li>
<li><b>İletişim:</b> işletme telefonu, WhatsApp numarası, isteğe bağlı iletişim e-postası</li>
<li><b>İşletme bilgileri:</b> işletme adı, adresi, il/ilçe, çalışma saatleri, açıklama, fotoğraflar, kampanyalar ve fiyatlar</li>
<li><b>İşlem kayıtları:</b> başvuru, onay, izin ve değişiklik kayıtları (kim, ne zaman)</li></ul>
<p>T.C. kimlik numarası, vergi numarası veya belge kopyası istenmez ve saklanmaz. Fotoğraflar yüklenmeden önce tarayıcınızda küçültülür ve içindeki konum bilgisi silinir.</p>
<h2>Amaçlar ve hukuki sebepler</h2><ul>
<li>Hesabın açılması, başvurunun değerlendirilmesi, işletmenin doğrulanması ve yayınlanması: sözleşmenin kurulması ve ifası (KVKK m.5/2-c)</li>
<li>İşletme bilgilerinin, fotoğrafların ve izin verilmişse fiyatların herkese açık yayınlanması: sözleşmenin ifası (m.5/2-c), işletme tarafından alenileştirilmesi (m.5/2-d)</li>
<li>Güvenlik ve kötüye kullanımın önlenmesi için işlem kayıtları: meşru menfaat (m.5/2-f) ve hukuki yükümlülük (m.5/2-ç)</li></ul>
<h2>Aktarım</h2><p>Veriler; veritabanı, kimlik doğrulama ve dosya depolama hizmeti için Supabase'e, giriş e-postalarının gönderimi için e-posta hizmet sağlayıcısına aktarılır. Bu hizmetlerin sunucuları yurt dışında bulunabilir; aktarım KVKK m.9'daki usullere (standart sözleşme ve Kurul'a bildirim) uygun yapılır. Veriler satılmaz ve reklam amacıyla paylaşılmaz.</p>
<h2>Saklama süresi</h2><p>Reddedilen başvurular 6 ay, yayından kalkan veya silme talebinde bulunulan hesaplar en geç 30 gün içinde silinir; güvenlik amaçlı işlem kayıtları en fazla 2 yıl saklanır.</p>
<h2>Haklarınız</h2><p>KVKK m.11 uyarınca verilerinize erişme, düzeltilmesini veya silinmesini isteme ve itiraz etme haklarına sahipsiniz. Silme talebini panelin "Hesap" bölümünden ya da <a href="mailto:piyasanabzi.iletisim@gmail.com">e-postayla</a> iletebilirsiniz.</p>""",
     crumb=_crumb, article=False, head=KP_CSS + _NOINDEX, h1="Kuyumcu paneli aydınlatma metni (KVKK)")
page("kuyumcu-pazari/fiyat-izni.html", "Kuyumcu Pazarı fiyat yayınlama izni",
     "Kuyumcu Pazarı'nda işletme fiyatlarının yayınlanmasına ilişkin izin metni.", _TASLAK + """
<p class="note">Sürüm: kp-fiyat-izni-2026-11-27</p>
<p>Bu izinle, işletme yetkilisi olarak panelden girdiğiniz altın alış ve satış fiyatlarının Kuyumcu Pazarı'ndaki işletme sayfanızda yayınlanmasına izin verirsiniz.</p>
<ul>
<li>Fiyatları yalnızca siz girersiniz; Piyasa Nabzı fiyat üretmez, değiştirmez ve garanti etmez.</li>
<li>Her fiyat, girildiği tarih ve saatle birlikte gösterilir. 24 saati geçen fiyat "eski" olarak işaretlenir, 7 günü geçen fiyat gösterilmez.</li>
<li>Girilen fiyatların gerçeği yansıtmasından siz sorumlusunuz. Yanıltıcı olduğu düşünülen fiyatları yönetici gizleyebilir.</li>
<li>Bu izni panelden istediğiniz an geri alabilirsiniz; geri aldığınızda fiyatlarınız yayından kalkar.</li>
<li>İzin verme ve geri alma işlemleri tarih ve saatiyle kaydedilir.</li></ul>""",
     crumb=_crumb, article=False, head=KP_CSS + _NOINDEX, h1="Fiyat yayınlama izni")
