#!/usr/bin/env python3
"""Kuyumcu sistemi veritabanı güvenlik testleri (yerel Postgres + Supabase taklidi, ya da gerçek Supabase yerel yığını).
Kullanım: python3 rls_test.py "<psql bağlantı argümanları>" <migration klasörü> [--stub stub.sql]"""
import subprocess, sys, json, uuid, os, shlex

CONN = shlex.split(sys.argv[1]) if len(sys.argv) > 1 else ["-h", "/tmp/pgk", "-p", "54329", "-U", "postgres"]
MIG = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/piyasanabzi.github.io/supabase/migrations"
STUB = sys.argv[sys.argv.index("--stub") + 1] if "--stub" in sys.argv else None
DB = os.environ.get("KP_DB", "kp")
SONUC = []


def psql(sql, db=DB):
    hedef = CONN if CONN[0].startswith("postgres") else [*CONN, "-d", db]
    r = subprocess.run(["psql", *hedef, "-v", "ON_ERROR_STOP=1", "-q", "-At", "-X"], input=sql, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout.strip() if r.returncode == 0 else r.stderr.strip())


def as_(rol, uid, sql, aal="aal1"):
    claims = {"role": rol, "aal": aal}
    if uid: claims["sub"] = uid
    pre = f"begin; set local role {rol}; select set_config('request.jwt.claims', '{json.dumps(claims)}', true) \\g /dev/null\n"
    return psql(pre + sql + "\ncommit;")


def t(ad, kosul, ek=""):
    SONUC.append((ad, bool(kosul)))
    print(("GEÇTİ " if kosul else "KALDI ") + ad + ("" if kosul else f"  → {ek}"))
    return kosul


def hata(r, parca=""):
    return (not r[0]) and (parca.lower() in r[1].lower())


A, B, Y, N = (str(uuid.uuid4()) for _ in range(4))
SAAT = json.dumps({g: "09:00-19:00" for g in ["pzt", "sal", "car", "per", "cum", "cmt"]} | {"paz": "kapali"})
ISL = lambda ad, tel="+902125550000": (f"insert into public.isletmeler (ad, yetkili_ad, il, ilce, adres, telefon, saatler) values "
                                        f"('{ad}', 'Yetkili Kişi', 'antalya', 'gazipasa', 'Cumhuriyet Mah. 1. Sok. No:1', '{tel}', '{SAAT}')")

if STUB:
    ok, o = psql(f"drop database if exists {DB}", "postgres"); ok, o = psql(f"create database {DB}", "postgres")
    ok, o = psql(open(STUB).read()); assert ok, o
    for f in sorted(os.listdir(MIG)):
        ok, o = psql(open(os.path.join(MIG, f)).read()); assert ok, f + o
ok, o = psql(f"insert into auth.users (id, email) values ('{A}','a@test.invalid'),('{B}','b@test.invalid'),('{Y}','y@test.invalid'),('{N}','n@test.invalid');"
             f"insert into public.yoneticiler (user_id) values ('{Y}');")
assert ok, o

# ── anonim
t("anonim ana işletme tablosunu okuyamaz", hata(as_("anon", None, "select * from public.isletmeler;"), "permission denied"))
t("anonim fiyat tablosunu okuyamaz", hata(as_("anon", None, "select * from public.fiyatlar;"), "permission denied"))
t("anonim denetim kaydını okuyamaz", hata(as_("anon", None, "select * from public.denetim_kaydi;"), "permission denied"))
t("anonim işletme ekleyemez", hata(as_("anon", None, ISL("X") + ";"), "permission denied"))
t("anonim başvuru RPC çağıramaz", hata(as_("anon", None, "select public.basvuru_gonder('v1', true);"), "permission denied"))
t("anonim yönetici RPC çağıramaz", hata(as_("anon", None, f"select public.yonetici_onayla('{uuid.uuid4()}');"), "permission denied"))
r = as_("anon", None, "select count(*) from public.yayin_isletmeler;")
t("başlangıçta yayında işletme yok", r == (True, "0"), r)
t("anonim il/ilçe listesini okur (973)", as_("anon", None, "select count(*) from public.ilceler;") == (True, "973"))

# ── kayıt
r = as_("authenticated", A, ISL("Altın Kuyumcu") + " returning durum;")
t("kuyumcu A taslak işletme oluşturur", r == (True, "taslak"), r)
t("aynı hesap ikinci işletme açamaz", hata(as_("authenticated", A, ISL("İkinci") + ";"), "duplicate"))
t("istemci durum alanı gönderemez", hata(as_("authenticated", B, "insert into public.isletmeler (ad, yetkili_ad, il, ilce, adres, telefon, saatler, durum) values ('X','Y Z','antalya','gazipasa','adres 12345','+902125550000','%s','onayli');" % SAAT), "permission denied"))
t("istemci sahip_id gönderemez", hata(as_("authenticated", B, "insert into public.isletmeler (sahip_id, ad, yetkili_ad, il, ilce, adres, telefon, saatler) values ('%s','X','Y Z','antalya','gazipasa','adres 12345','+902125550000','%s');" % (A, SAAT)), "permission denied"))
t("geçersiz telefon reddedilir", hata(as_("authenticated", B, ISL("Beta", "05551112233") + ";"), "check"))
t("olmayan il/ilçe reddedilir", hata(as_("authenticated", B, ISL("Beta").replace("gazipasa", "yokilce") + ";"), "foreign key"))
t("geçersiz saat (gece yarısını aşan) reddedilir", hata(as_("authenticated", B, ISL("Beta").replace('"cmt": "09:00-19:00"', '"cmt": "22:00-02:00"') + ";"), "check"))
r = as_("authenticated", B, ISL("Beta Kuyumculuk", "+902425550000") + ";")
t("kuyumcu B işletme oluşturur", r[0], r)

t("B, A'nın işletmesini göremez", as_("authenticated", B, "select count(*) from public.isletmeler;") == (True, "1"))
r = as_("authenticated", B, "with u as (update public.isletmeler set ad='Ele Geçirildi' where ad='Altın Kuyumcu' returning 1) select count(*) from u;")
t("B, A'nın işletmesini güncelleyemez", r == (True, "0"), r)
r = as_("authenticated", B, "with u as (delete from public.isletmeler where ad='Altın Kuyumcu' returning 1) select count(*) from u;")
t("B, A'nın işletmesini silemez", r == (True, "0"), r)
t("sahip durumunu kendisi değiştiremez", hata(as_("authenticated", A, "update public.isletmeler set durum='onayli';"), "permission denied"))
t("sahip paketini kendisi değiştiremez", hata(as_("authenticated", A, "update public.isletmeler set paket='premium';"), "permission denied"))
t("sahip slug belirleyemez", hata(as_("authenticated", A, "update public.isletmeler set slug='sahte';"), "permission denied"))
t("sahip kendini yönetici yapamaz", hata(as_("authenticated", A, f"insert into public.yoneticiler values ('{A}');"), "permission denied"))
t("iç kayıt fonksiyonu çağrılamaz", hata(as_("authenticated", A, "select public._kaydet('x','y','z');"), "permission denied"))

# ── başvuru
t("beyan olmadan başvuru gönderilemez", hata(as_("authenticated", A, "select public.basvuru_gonder('kp-aydinlatma-v1', false);"), "gerekli"))
r = as_("authenticated", A, "select public.basvuru_gonder('kp-aydinlatma-v1', true); select durum from public.isletmeler;")
t("başvuru gönderilir (durum=basvuru)", r == (True, "\nbasvuru".strip()) or r[1].endswith("basvuru"), r)
t("onaysız işletme yayında değil", as_("anon", None, "select count(*) from public.yayin_isletmeler;") == (True, "0"))
t("onaysız işletme fotoğraf ekleyemez", hata(as_("authenticated", A, "insert into public.fotograflar (isletme_id, yol, tur, aciklama) select id, id||'/a.jpg', 'magaza', 'Vitrin' from public.isletmeler;"), "row-level security"))
t("onaysız işletme fiyat izni veremez", hata(as_("authenticated", A, "select public.fiyat_izni_ver('kp-fiyat-v1');"), "onaylı"))

# ── yönetici
IA = psql("select id from public.isletmeler where ad='Altın Kuyumcu';")[1]
IB = psql("select id from public.isletmeler where ad='Beta Kuyumculuk';")[1]
t("kuyumcu yönetici işlemi yapamaz", hata(as_("authenticated", A, f"select public.yonetici_onayla('{IA}');"), "yönetici"))
t("yönetici iki adımlı doğrulama olmadan (aal1) işlem yapamaz", hata(as_("authenticated", Y, f"select public.yonetici_onayla('{IA}');", "aal1"), "iki adımlı"))
t("yönetici aal1 iken işletmeleri listeleyemez", as_("authenticated", Y, "select count(*) from public.isletmeler;", "aal1") == (True, "0"))
t("yönetici aal2 ile işletmeleri görür", as_("authenticated", Y, "select count(*) from public.isletmeler;", "aal2") == (True, "2"))
as_("authenticated", Y, f"select public.yonetici_durum_degistir('{IA}', 'inceleniyor', null);", "aal2")
t("inceleme sürerken kritik bilgi değiştirilemez", hata(as_("authenticated", A, "update public.isletmeler set telefon='+902125559999';"), "incelenirken"))
t("ret açıklamasız yapılamaz", hata(as_("authenticated", Y, f"select public.yonetici_durum_degistir('{IB}', 'reddedildi', '');", "aal2"), "açıklama"))
as_("authenticated", Y, f"select public.yonetici_dogrulama_ekle('{IA}', 'telefon', 'arandı');", "aal2")
t("tek doğrulama yöntemiyle onay verilmez", hata(as_("authenticated", Y, f"select public.yonetici_onayla('{IA}');", "aal2"), "en az iki"))
t("geçersiz doğrulama yöntemi reddedilir", hata(as_("authenticated", Y, f"select public.yonetici_dogrulama_ekle('{IA}', 'tahmin', null);", "aal2"), "check"))
as_("authenticated", Y, f"select public.yonetici_dogrulama_ekle('{IA}', 'vergi_levhasi', 'görüntülü bakıldı');", "aal2")
r = as_("authenticated", Y, f"select public.yonetici_onayla('{IA}');", "aal2")
t("iki doğrulamayla onaylanır ve slug üretilir", r == (True, "altin-kuyumcu-gazipasa"), r)
r = as_("anon", None, "select ad || '|' || array_to_string(dogrulama_yontemleri, ',') from public.yayin_isletmeler;")
t("onaylı işletme herkese açık görünümde", r == (True, "Altın Kuyumcu|telefon,vergi_levhasi"), r)
r = as_("anon", None, "select to_jsonb(y) ? 'yetkili_ad' or to_jsonb(y) ? 'sahip_id' or to_jsonb(y) ? 'durum_notu' from public.yayin_isletmeler y;")
t("açık görünüm yetkili adı/sahip/not içermez", r == (True, "f"), r)

# ── onay sonrası değişiklik
as_("authenticated", A, "update public.isletmeler set ad='Yeni Ad Kuyumcu', saatler = jsonb_set(saatler, '{paz}', '\"10:00-16:00\"');")
r = psql(f"select ad || '|' || (saatler->>'paz') || '|' || (bekleyen_degisiklik->>'ad') from public.isletmeler where id='{IA}';")
t("onaylı işletmede ad değişikliği onaya düşer, saat doğrudan uygulanır", r == (True, "Altın Kuyumcu|10:00-16:00|Yeni Ad Kuyumcu"), r)
as_("authenticated", Y, f"select public.yonetici_degisiklik_karar('{IA}', true);", "aal2")
r = psql(f"select ad || '|' || coalesce(bekleyen_degisiklik::text,'-') from public.isletmeler where id='{IA}';")
t("yönetici onayıyla değişiklik uygulanır", r == (True, "Yeni Ad Kuyumcu|-"), r)

# ── fiyat
F = lambda isl, g=(5600, 5750), c=(9300, 9500), extra="": (f"insert into public.fiyatlar (isletme_id, gram_alis, gram_satis, ceyrek_alis, ceyrek_satis{extra and ', guncelleme'}) "
                                                         f"values ('{isl}', {g[0]}, {g[1]}, {c[0]}, {c[1]}{extra});")
t("fiyat izni olmadan fiyat girilemez", hata(as_("authenticated", A, F(IA)), "izniniz yok"))
r = as_("authenticated", A, "select public.fiyat_izni_ver('kp-fiyat-izni-v1');")
t("onaylı işletme fiyat izni verir", r[0], r)
t("istemci güncelleme zamanı gönderemez", hata(as_("authenticated", A, F(IA, extra=", '2020-01-01'")), "permission denied"))
t("alış > satış reddedilir", hata(as_("authenticated", A, F(IA, g=(5800, 5700))), "check"))
t("olağan dışı çeyrek/gram oranı reddedilir", hata(as_("authenticated", A, F(IA, c=(93000, 95000))), "oran"))
r = as_("authenticated", A, F(IA))
t("izinli kuyumcu fiyat girer", r[0], r)
t("dakikada birden fazla fiyat girilemez", hata(as_("authenticated", A, F(IA)), "dakikada"))
r=as_("authenticated", B, F(IA)); t("B, A adına fiyat giremez", hata(r, "izniniz yok"), r)
r = as_("anon", None, "select gram_satis || '|' || eski from public.yayin_fiyatlar;")
t("güncel fiyat herkese açık (eski=false)", r == (True, "5750.00|false"), r)
psql(f"update public.fiyatlar set guncelleme = now() - interval '30 hours' where isletme_id='{IA}';")
r=as_("anon", None, "select eski from public.yayin_fiyatlar;"); t("24 saati geçen fiyat 'eski' işaretlenir", r == (True, "t"), r)
psql(f"update public.fiyatlar set guncelleme = now() - interval '8 days' where isletme_id='{IA}';")
t("7 günü geçen fiyat yayından düşer", as_("anon", None, "select count(*) from public.yayin_fiyatlar;") == (True, "0"))
psql(f"update public.fiyatlar set guncelleme = now() - interval '2 minutes' where isletme_id='{IA}';")
FID = psql(f"select id from public.fiyatlar where isletme_id='{IA}';")[1]
t("kuyumcu fiyatı gizleyemez (yönetici işi)", hata(as_("authenticated", A, f"select public.yonetici_fiyat_gizle('{FID}', 'neden');"), "yönetici"))
as_("authenticated", Y, f"select public.yonetici_fiyat_gizle('{FID}', 'hatalı giriş');", "aal2")
t("yöneticinin gizlediği fiyat yayından düşer", as_("anon", None, "select count(*) from public.yayin_fiyatlar;") == (True, "0"))
as_("authenticated", A, F(IA))
t("yeni fiyat tekrar yayında", as_("anon", None, "select count(*) from public.yayin_fiyatlar;") == (True, "1"))
as_("authenticated", A, "select public.fiyat_izni_geri_al();")
t("izin geri alınınca fiyat yayından düşer", as_("anon", None, "select count(*) from public.yayin_fiyatlar;") == (True, "0"))
r=as_("authenticated", A, F(IA)); t("izin geri alınınca yeni fiyat girilemez", hata(r, "izniniz yok"), r)

# ── fotoğraf
FO = lambda isl, ad: f"insert into public.fotograflar (isletme_id, yol, tur, aciklama) values ('{isl}', '{isl}/{ad}.jpg', 'magaza', 'Vitrin görünümü');"
t("başka işletme klasörüne fotoğraf kaydı eklenemez", hata(as_("authenticated", A, f"insert into public.fotograflar (isletme_id, yol, tur, aciklama) values ('{IA}', '{IB}/x.jpg', 'magaza', 'Vitrin');"), "klasör"))
for i in range(3): as_("authenticated", A, FO(IA, f"f{i}"))
t("paket sınırı (3) aşılamaz", hata(as_("authenticated", A, FO(IA, "f3")), "sınırı"))
t("onaysız fotoğraf yayında değil", as_("anon", None, "select count(*) from public.yayin_fotograflar;") == (True, "0"))
t("istemci fotoğraf durumunu değiştiremez", hata(as_("authenticated", A, "update public.fotograflar set durum='onayli';"), "permission denied"))
PID = psql(f"select id from public.fotograflar where yol='{IA}/f0.jpg';")[1]
as_("authenticated", Y, f"select public.yonetici_foto_karar('{PID}', 'onayli');", "aal2")
t("yönetici onayından sonra fotoğraf yayında", as_("anon", None, "select count(*) from public.yayin_fotograflar;") == (True, "1"))
SO = lambda kl, ad: f"insert into storage.objects (bucket_id, name) values ('isletme-fotolari', '{kl}/{ad}.jpg');"
t("depoya kendi klasörüne yükler", as_("authenticated", A, SO(IA, "d1"))[0])
t("depoda başka işletmenin klasörüne yükleyemez", hata(as_("authenticated", A, SO(IB, "d1")), "row-level security"))
t("onaysız işletme depoya yükleyemez", hata(as_("authenticated", B, SO(IB, "d1")), "row-level security"))
as_("authenticated", A, SO(IA, "d2")); as_("authenticated", A, SO(IA, "d3"))
t("depoda paket sınırı aşılamaz", hata(as_("authenticated", A, SO(IA, "d4")), "row-level security"))
t("anonim depoya yükleyemez", hata(as_("anon", None, SO(IA, "z")), "row-level security"))

# ── kampanya
K = lambda isl, b: f"insert into public.kampanyalar (isletme_id, baslik, aciklama, baslangic, bitis) values ('{isl}', '{b}', 'Bilezik işçiliğinde indirim', current_date, current_date + 10);"
t("onaysız işletme kampanya açamaz", hata(as_("authenticated", B, K(IB, "Kampanya")), "row-level security"))
r = as_("authenticated", A, K(IA, "Bilezik haftası"))
t("kampanya oluşturulur", r[0], r)
t("kampanya onaysız yayında değil", as_("anon", None, "select count(*) from public.yayin_kampanyalar;") == (True, "0"))
t("ücretsiz paket kampanya sınırı (1) aşılamaz", hata(as_("authenticated", A, K(IA, "İkinci")), "sınırı"))
KID = psql(f"select id from public.kampanyalar where isletme_id='{IA}';")[1]
as_("authenticated", Y, f"select public.yonetici_kampanya_karar('{KID}', 'yayinda', null);", "aal2")
t("yönetici onayıyla kampanya yayında", as_("anon", None, "select count(*) from public.yayin_kampanyalar;") == (True, "1"))
as_("authenticated", A, "update public.kampanyalar set baslik='Değişti: EN UCUZ';")
t("düzenlenen kampanya yeniden onaya düşer", as_("anon", None, "select count(*) from public.yayin_kampanyalar;") == (True, "0"))
t("60 günden uzun kampanya reddedilir", hata(as_("authenticated", A, f"update public.kampanyalar set bitis = baslangic + 90;"), "check"))

# ── istatistik
as_("anon", None, f"select public.etkinlik_kaydet('{IA}', 'profil'); select public.etkinlik_kaydet('{IA}', 'profil'); select public.etkinlik_kaydet('{IA}', 'ara');")
as_("anon", None, f"select public.etkinlik_kaydet('{IB}', 'profil'); select public.etkinlik_kaydet('{IA}', 'sahte_tur');")
t("anonim istatistikleri okuyamaz", hata(as_("anon", None, "select * from public.etkinlik_gunluk;"), "permission denied"))
r = as_("authenticated", A, "select string_agg(tur||'='||adet, ',' order by tur) from public.etkinlik_gunluk;")
t("kuyumcu kendi istatistiğini görür; onaysız işletme ve geçersiz tür sayılmaz", r == (True, "ara=1,profil=2"), r)
t("B, A'nın istatistiğini göremez", as_("authenticated", B, "select count(*) from public.etkinlik_gunluk;") == (True, "0"))
r = as_("authenticated", Y, "select (public.yonetici_istatistik()->'etkinlik_30g'->>'profil');", "aal2")
t("yönetici platform istatistiğini görür", r == (True, "2"), r)
t("kuyumcu platform istatistiğini göremez", hata(as_("authenticated", A, "select public.yonetici_istatistik();"), "yönetici"))

# ── paket
t("satışta olmayan paket atanamaz", hata(as_("authenticated", Y, f"select public.yonetici_paket_ata('{IA}', 'premium');", "aal2"), "satışta"))
t("kuyumcu paket tanımlayamaz", hata(as_("authenticated", A, "select public.yonetici_paket_kaydet('bedava','Bedava',true,50,true,20,true,null,true,0);"), "yönetici"))
t("kuyumcu paket tablosuna yazamaz", hata(as_("authenticated", A, "update public.paketler set foto_limit=50;"), "permission denied"))

# ── askıya alma
as_("authenticated", Y, f"select public.yonetici_durum_degistir('{IA}', 'askida', 'Şikâyet inceleniyor');", "aal2")
t("askıya alınan işletme yayından kalkar", as_("anon", None, "select (select count(*) from public.yayin_isletmeler) + (select count(*) from public.yayin_fotograflar) + (select count(*) from public.yayin_kampanyalar);") == (True, "0"))
t("askıdaki işletme fiyat izni veremez", hata(as_("authenticated", A, "select public.fiyat_izni_ver('kp-fiyat-izni-v1');"), "onaylı"))
t("askıdaki işletme kendini silemez", as_("authenticated", A, "with u as (delete from public.isletmeler returning 1) select count(*) from u;") == (True, "0"))
t("kuyumcu denetim kaydını göremez", as_("authenticated", A, "select count(*) from public.denetim_kaydi;") == (True, "0"))
r = as_("authenticated", Y, "select count(*) > 10 from public.denetim_kaydi;", "aal2")
t("yönetici denetim kaydını görür", r == (True, "t"), r)
r = as_("authenticated", Y, f"select public.yonetici_onayla('{IA}');", "aal2")
t("askıdan çıkarılınca slug korunur", r == (True, "yeni-ad-kuyumcu-gazipasa") or r == (True, "altin-kuyumcu-gazipasa"), r)

# ── KVKK
r = as_("authenticated", A, "select string_agg(tur, ',' order by zaman, tur) from public.onaylar;")
t("onay kayıtları (aydınlatma, beyan, fiyat izni, geri alma) tutulur", r[0] and all(x in r[1] for x in ["aydinlatma", "beyan", "fiyat_izni", "fiyat_izni_geri"]), r)
r = as_("authenticated", A, "select public.silme_talep_et(); select silme_talebi is not null from public.isletmeler;")
t("silme talebi kaydedilir", r[0] and r[1].endswith("t"), r)
t("B, A'nın onay kayıtlarını göremez", as_("authenticated", B, "select count(*) from public.onaylar;") == (True, "0"))

g = sum(1 for _, k in SONUC if k)
print(f"\nTOPLAM {len(SONUC)} test, {g} geçti, {len(SONUC) - g} kaldı")
sys.exit(0 if g == len(SONUC) else 1)
