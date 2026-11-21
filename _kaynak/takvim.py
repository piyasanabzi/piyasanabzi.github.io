# Ekonomi takvimi: content.py tarafından exec edilir (page, urls, LM, ROOT, SITE, CTA kullanılabilir).
# Tarihleri güncellerken resmi kaynaklara bak:
#   TCMB PPK: tcmb.gov.tr > Duyurular > Takvim (karar 14:00 TSİ)
#   Fed FOMC: federalreserve.gov/monetarypolicy/fomccalendars.htm (karar 14:00 ABD Doğu saati)
#   TÜİK TÜFE: her ayın 3'ü 10:00, hafta sonuna denk gelirse ilk iş günü
#   ABD TÜFE ve istihdam: bls.gov/schedule (08:30 ABD Doğu saati)
# Liste bitmeden (en geç Haziran 2027) yeni tarihleri ekle.
import datetime as _dt, json as _json
from zoneinfo import ZoneInfo as _Z
_TR, _NY = _Z("Europe/Istanbul"), _Z("America/New_York")

TAKVIM_TUR = {
    "tcmb": ("TCMB faiz kararı", "🇹🇷", "Türkiye'nin politika faizini belirler. Faiz artışı ya da sabit tutulması genelde TL'yi destekler; beklenmedik indirimler dolar ve altına talebi artırabilir."),
    "fed": ("Fed faiz kararı", "🇺🇸", "ABD Merkez Bankası'nın faiz kararı. Dünya genelinde doları, ons altını ve borsaları etkiler. Faiz indirimi beklentisi genelde ons altını destekler, doları zayıflatabilir."),
    "tuik": ("Türkiye enflasyonu (TÜİK)", "🇹🇷", "Bir önceki ayın enflasyonu açıklanır. Kira artış oranı, maaş zamları ve Merkez Bankası'nın faiz kararları için kritik veridir."),
    "cpi": ("ABD enflasyonu (TÜFE)", "🇺🇸", "Beklentiden yüksek gelirse Fed'in faiz indirme ihtimali azalır; dolar güçlenebilir, ons altın baskı görebilir. Düşük gelirse tersi olabilir."),
    "nfp": ("ABD istihdam verisi", "🇺🇸", "Tarım dışı istihdam ve işsizlik oranı. Güçlü veri doları destekleyebilir; zayıf veri faiz indirimi beklentisini artırarak altını destekleyebilir."),
}
_AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

def _e(tur, gun, saat, tz, ek=""):
    y, m, d = map(int, gun.split("-")); hh, mm = map(int, saat.split(":"))
    t = _dt.datetime(y, m, d, hh, mm, tzinfo=tz).astimezone(_TR)
    return {"tur": tur, "tr": t, "ek": ek}

def _tuik(y, m):  # m: verinin ait olduğu ay; açıklama bir sonraki ayın 3'ü (hafta sonu ise pazartesi)
    ay = m % 12 + 1; yil = y + (1 if m == 12 else 0)
    d = _dt.date(yil, ay, 3)
    while d.weekday() >= 5: d += _dt.timedelta(days=1)
    return _e("tuik", d.isoformat(), "10:00", _TR, f"{_AY[m-1]} {y} verisi")

TAKVIM = sorted([
    # TCMB PPK (2026 ve 2027 ilk yarı takvimi)
    *[_e("tcmb", g, "14:00", _TR) for g in ["2026-12-10", "2027-01-21", "2027-03-18", "2027-04-22", "2027-06-10"]],
    # Fed FOMC karar günleri (2027 güncellenmiş takvim; 26-27 Ekim toplantısında karar yok)
    *[_e("fed", g, "14:00", _NY) for g in ["2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-11-17"]],
    # TÜİK TÜFE
    *[_tuik(y, m) for y, m in [(2026, 11), (2026, 12), (2027, 1), (2027, 2), (2027, 3), (2027, 4), (2027, 5)]],
    # ABD TÜFE (BLS)
    *[_e("cpi", g, "08:30", _NY, ek) for g, ek in [("2026-12-10", "Kasım verisi"), ("2027-01-13", "Aralık verisi"), ("2027-02-11", "Ocak verisi"), ("2027-03-10", "Şubat verisi"), ("2027-04-13", "Mart verisi"), ("2027-05-12", "Nisan verisi"), ("2027-06-10", "Mayıs verisi")]],
    # ABD istihdam (BLS)
    *[_e("nfp", g, "08:30", _NY, ek) for g, ek in [("2026-12-04", "Kasım verisi"), ("2027-01-08", "Aralık verisi"), ("2027-02-05", "Ocak verisi"), ("2027-03-05", "Şubat verisi"), ("2027-04-02", "Mart verisi")]],
], key=lambda x: x["tr"])

# --- tarayıcı için veri dosyası ---
_js = [{"k": e["tur"], "ts": int(e["tr"].timestamp() * 1000), "ek": e["ek"]} for e in TAKVIM]
_turler = {k: {"ad": v[0], "i": v[1], "a": v[2]} for k, v in TAKVIM_TUR.items()}
open(os.path.join(ROOT, "takvim.js"), "w", encoding="utf-8").write(
    "/* Ekonomi takvimi verisi: _kaynak/takvim.py ile üretilir, elle düzenleme. */\n"
    "window.PN_TAKVIM=" + _json.dumps({"turler": _turler, "olaylar": _js}, ensure_ascii=False, separators=(",", ":")) + ";\n")

# --- ekonomi-takvimi.html ---
def _satir(e):
    ad, ikon, _ = TAKVIM_TUR[e["tur"]]; t = e["tr"]
    ek = f' <span class="note">· {e["ek"]}</span>' if e["ek"] else ""
    return (f'<tr data-ts="{int(t.timestamp()*1000)}"><td><b>{t.day} {_AY[t.month-1]} {t.year}</b><br><span class="note">{_GUN[t.weekday()]} · {t:%H:%M}</span></td>'
            f'<td>{ikon} {ad}{ek}<div class="kalan note"></div></td></tr>')

_aylar = {}
for e in TAKVIM: _aylar.setdefault((e["tr"].year, e["tr"].month), []).append(e)
_tablo = "".join(f'<h2>{_AY[m-1]} {y}</h2><table class="tk"><tr><th style="width:38%">Tarih (TSİ)</th><th>Olay</th></tr>' + "".join(_satir(e) for e in ev) + "</table>" for (y, m), ev in _aylar.items())
_acik = "".join(f'<h2>{v[1]} {v[0]} nedir?</h2><p>{v[2]}</p>' for v in TAKVIM_TUR.values())
_ilk = TAKVIM[0]["tr"]; _son = TAKVIM[-1]["tr"]
_govde = f'''
<p>Dolar, euro ve altın fiyatlarını en çok etkileyen <b>faiz kararları</b> ve <b>enflasyon verileri</b>nin tarihleri. Saatler Türkiye saatiyle (TSİ) verilmiştir.</p>
<div class="box gold" id="siradaki"><b>Sıradaki önemli olay</b><div id="sirTxt" class="note" style="margin-top:4px">Yükleniyor…</div></div>
{_tablo}
<p class="note">Kaynaklar: TCMB, ABD Merkez Bankası (Fed), ABD Çalışma İstatistikleri Bürosu (BLS) ve TÜİK takvimleri. TÜİK verisi her ayın 3'ünde açıklanır; hafta sonuna denk gelirse ilk iş gününe kayar. Kurumlar tarihleri değiştirebilir; son karar için kurumların kendi duyurularına bakın.</p>
{_acik}
<h2>Bu veriler fiyatları neden etkiler?</h2>
<p>Faiz kararları ve enflasyon verileri, paranın değerine dair beklentileri değiştirir. Beklentiden farklı bir karar ya da veri geldiğinde dolar, euro ve altın fiyatları birkaç dakika içinde sert hareket edebilir. Bu yüzden önemli bir alım-satım yapmadan önce yaklaşan tarihlere göz atmak faydalıdır.</p>
<p>Ayrıntılı bilgi için <a href="/rehber/dolar-kuru-neden-yukselir.html">dolar kuru neden yükselir</a> ve <a href="/rehber/ons-altin-nedir.html">ons altın nedir</a> yazılarımıza bakabilirsin.</p>
''' + CTA + '''<p class="note">Bu sayfa genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.</p>
<style>.tk td{vertical-align:top}.tk tr.gecti{opacity:.45}.kalan{margin-top:3px;font-weight:700;color:var(--gold)}</style>
<script src="/takvim.js"></script>
<script>(function(){var T=window.PN_TAKVIM;if(!T)return;var now=Date.now();
var tz={timeZone:"Europe/Istanbul"};function gunNo(t){var p=new Date(t).toLocaleDateString("en-CA",tz).split("-");return Date.UTC(+p[0],+p[1]-1,+p[2])/864e5;}
function kalan(ts){var d=ts-now,s=Math.floor(d/36e5),g=gunNo(ts)-gunNo(now);if(d<0)return"Gerçekleşti";if(g===0)return s<1?"1 saatten az kaldı":"Bugün, "+s+" saat kaldı";if(g===1)return"Yarın";return g+" gün kaldı";}
var ilk=null;document.querySelectorAll("tr[data-ts]").forEach(function(r){var ts=+r.dataset.ts;r.querySelector(".kalan").textContent=kalan(ts);if(ts+2*36e5<now)r.classList.add("gecti");else if(!ilk)ilk=r;});
var sir=T.olaylar.find(function(e){return e.ts+2*36e5>=now;}),el=document.getElementById("sirTxt");
if(sir){var tr=T.turler[sir.k],d=new Date(sir.ts);el.innerHTML="<b style=\\"color:var(--ink);font-size:16px\\">"+tr.i+" "+tr.ad+"</b><br>"+d.toLocaleDateString("tr-TR",{day:"numeric",month:"long",weekday:"long",timeZone:"Europe/Istanbul"})+" · "+d.toLocaleTimeString("tr-TR",{hour:"2-digit",minute:"2-digit",timeZone:"Europe/Istanbul"})+" — <b>"+kalan(sir.ts)+"</b>";}
else el.textContent="Takvim güncelleniyor.";})();</script>
'''
_u = page("ekonomi-takvimi.html", "Ekonomi takvimi: TCMB ve Fed faiz kararları, enflasyon tarihleri",
          f"TCMB ve Fed faiz kararı ne zaman? Türkiye ve ABD enflasyon verileri, ABD istihdam verisi tarihleri ve saatleri. {_ilk.year}-{_son.year} ekonomi takvimi.",
          _govde, crumb="Ekonomi takvimi", article=False)
urls.insert(1, _u)
