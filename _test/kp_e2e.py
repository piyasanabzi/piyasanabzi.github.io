#!/usr/bin/env python3
"""Kuyumcu Yönetim Sistemi uçtan uca testi: gerçek yerel Supabase (auth + REST + storage + e-posta) + Playwright.
Ortam: API_URL, KEY, DB_URL, MAIL_URL, SITE (http://127.0.0.1:8765)."""
import os, re, sys, json, time, hmac, base64, struct, hashlib, subprocess, urllib.request, glob
from playwright.sync_api import sync_playwright

API, KEY, DB, MAIL, SITE = (os.environ[k] for k in ("API_URL", "KEY", "DB_URL", "MAIL_URL", "SITE"))
KOK = os.environ.get("REPO", os.getcwd())
SONUC = []


def t(ad, kosul, ek=""):
    SONUC.append((ad, bool(kosul))); print(("GEÇTİ " if kosul else "KALDI ") + ad + ("" if kosul else f"  → {ek}"), flush=True)
    return kosul


def sql(q):
    r = subprocess.run(["psql", DB, "-At", "-v", "ON_ERROR_STOP=1", "-c", q], capture_output=True, text=True)
    if r.returncode: print("SQL HATA", r.stderr)
    return r.stdout.strip()


def http(yol):
    with urllib.request.urlopen(MAIL + yol, timeout=10) as c: return json.loads(c.read())


def kod_al(eposta, once):
    # Mailpit (yeni CLI) ya da Inbucket (eski CLI)
    for _ in range(40):
        try:
            m = http("/api/v1/messages")
            for x in m.get("messages", []):
                if any(eposta == a.get("Address") for a in x.get("To", [])) and x["ID"] not in once:
                    d = http("/api/v1/message/" + x["ID"])
                    k = re.search(r"\b(\d{6,10})\b", d.get("Text", "") or re.sub("<[^>]+>", " ", d.get("HTML", "")))
                    if k: once.add(x["ID"]); return k.group(1)
        except Exception as e:
            try:
                kutu = eposta.split("@")[0]
                for x in http(f"/api/v1/mailbox/{kutu}"):
                    if x["id"] in once: continue
                    d = http(f"/api/v1/mailbox/{kutu}/{x['id']}")
                    k = re.search(r"\b(\d{6,10})\b", d["body"]["text"] or d["body"]["html"])
                    if k: once.add(x["id"]); return k.group(1)
            except Exception:
                pass
        time.sleep(0.5)
    raise RuntimeError("e-posta gelmedi: " + eposta)


def totp(secret):
    k = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    h = hmac.new(k, struct.pack(">Q", int(time.time()) // 30), hashlib.sha1).digest()
    o = h[-1] & 15
    return str((struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000).zfill(6)


def ekran(pg, ad):
    yol = f"/tmp/ekran_{ad}.jpg"; pg.screenshot(path=yol, full_page=True, type="jpeg", quality=55)
    print(f"===EKRAN {ad}===\n" + base64.b64encode(open(yol, "rb").read()).decode() + f"\n===SON {ad}===", flush=True)


GOREN = set()
with sync_playwright() as p:
    tarayici = p.chromium.launch()
    hatalar = []

    def sayfa():
        c = tarayici.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", timezone_id="Europe/Istanbul")
        pg = c.new_page()
        pg.on("pageerror", lambda e: hatalar.append(str(e)))
        pg.on("dialog", lambda d: d.accept())
        return pg

    def giris(pg, yol, eposta):
        pg.goto(SITE + yol); pg.wait_for_selector("input[name=eposta]")
        pg.fill("input[name=eposta]", eposta); pg.click("text=Giriş kodu gönder")
        pg.wait_for_selector("input[name=kod]", state="visible")
        pg.fill("input[name=kod]", kod_al(eposta, GOREN)); pg.click("button:has-text('Giriş yap')")

    def bekle_metin(pg, metin, sure=15000):
        pg.wait_for_selector(f"text={metin}", timeout=sure)

    # ── Kuyumcu kaydı ve başvuru
    k = sayfa()
    giris(k, "/kuyumcu-pazari/panel/", "kuyumcu1@ornek.test")
    k.wait_for_selector("text=İşletmenizi ekleyin")
    t("kuyumcu e-posta koduyla kayıt olup giriş yaptı", True)
    t("e-posta doğrulandı (auth.users.email_confirmed_at)", sql("select email_confirmed_at is not null from auth.users where email='kuyumcu1@ornek.test'") == "t")
    k.fill("input[name=ad]", "Deneme Kuyumculuk"); k.fill("input[name=yetkili_ad]", "Test Yetkili")
    k.select_option("select[name=il]", "antalya"); k.select_option("select[name=ilce]", "gazipasa")
    k.fill("textarea[name=adres]", "Test Mah. Deneme Sok. No:1"); k.fill("input[name=telefon]", "0242 555 00 00")
    k.fill("input[name=whatsapp]", "0555 555 55 55"); k.fill("textarea[name=aciklama]", "Uçtan uca test işletmesi")
    ekran(k, "1_kuyumcu_form")
    k.click("text=Kaydet ve devam et"); bekle_metin(k, "Başvuruyu gönder")
    t("işletme taslak olarak kaydedildi", sql("select durum from public.isletmeler") == "taslak")
    k.click("button:has-text('Başvuruyu gönder')")
    time.sleep(1)
    t("onay kutuları işaretlenmeden başvuru gönderilmez", sql("select durum from public.isletmeler") == "taslak")
    for cb in k.query_selector_all("form.kp-kutu input[type=checkbox]"): cb.check()
    k.click("button:has-text('Başvuruyu gönder')"); bekle_metin(k, "Başvuru alındı")
    t("başvuru gönderildi", sql("select durum from public.isletmeler") == "basvuru")
    t("aydınlatma ve beyan onayı kaydedildi", sql("select count(*) from public.onaylar where tur in ('aydinlatma','beyan')") == "2")
    ekran(k, "2_kuyumcu_basvuru")

    # tarayıcıdan yetkisiz işlem denemesi (kendi oturum anahtarıyla)
    r = k.evaluate("""async () => { const o = JSON.parse(localStorage.getItem('pn-kp-oturum'));
        const h = {apikey: window.PN_SUPA.key, Authorization: 'Bearer ' + o.access_token, 'Content-Type': 'application/json', Prefer: 'return=representation'};
        const a = await fetch(window.PN_SUPA.url + '/rest/v1/isletmeler?id=not.is.null', {method: 'PATCH', headers: h, body: JSON.stringify({durum: 'onayli'})});
        const b = await fetch(window.PN_SUPA.url + '/rest/v1/rpc/yonetici_onayla', {method: 'POST', headers: h, body: JSON.stringify({p_id: '00000000-0000-0000-0000-000000000000'})});
        const c = await fetch(window.PN_SUPA.url + '/rest/v1/yoneticiler', {method: 'POST', headers: h, body: JSON.stringify({user_id: o.user ? o.user.id : null})});
        return [a.status, b.status, c.status]; }""")
    t("kuyumcu tarayıcıdan kendini onaylayamaz / yönetici olamaz (403)", all(s in (401, 403) for s in r), r)

    # ── Yönetici
    y = sayfa()
    giris(y, "/kuyumcu-pazari/yonetim/", "yonetici@ornek.test")
    bekle_metin(y, "Bu hesap yönetici değil")
    t("yönetici olmayan hesap yönetim paneline giremez", True)
    sql("insert into public.yoneticiler (user_id) select id from auth.users where email='yonetici@ornek.test'")
    y.reload(); y.wait_for_selector(".kp-anahtar")
    ekran(y, "3_yonetici_iki_adim")
    gizli = y.inner_text(".kp-anahtar").strip()
    y.fill("input[autocomplete=one-time-code]", "000000"); y.click("button:has-text('Doğrula')"); time.sleep(1.5)
    t("yanlış TOTP kodu reddedilir", y.query_selector(".kp-anahtar") is not None)
    y.fill("input[autocomplete=one-time-code]", totp(gizli)); y.click("button:has-text('Doğrula')")
    bekle_metin(y, "Yönetici ·")
    t("yönetici iki adımlı doğrulamayla (aal2) panele girdi", True)
    y.click("button[role=tab]:has-text('İşletmeler')"); y.click("text=Deneme Kuyumculuk")
    y.wait_for_selector("text=Doğrulama (en az 2 yöntem)")
    y.click("button:has-text('Onayla ve yayınla')"); time.sleep(1.5)
    t("doğrulamasız onay verilmez", sql("select durum from public.isletmeler") == "basvuru")
    if not y.is_visible("text=Doğrulama (en az 2 yöntem)"): y.click("text=Deneme Kuyumculuk")
    y.locator(".kp-dogrulama", has_text="Telefonla teyit").locator("button").click(); time.sleep(1)
    y.locator(".kp-dogrulama", has_text="Vergi levhası").locator("button").click(); time.sleep(1)
    t("iki doğrulama kaydedildi", sql("select count(*) from public.dogrulamalar") == "2")
    ekran(y, "4_yonetici_dogrulama")
    y.click("button:has-text('Onayla ve yayınla')"); time.sleep(2)
    t("yönetici işletmeyi onayladı", sql("select durum || '|' || slug from public.isletmeler") == "onayli|deneme-kuyumculuk-gazipasa")

    # ── Kuyumcu: fiyat, fotoğraf, kampanya
    k.reload(); bekle_metin(k, "Onaylı · yayında")
    k.click("button[role=tab]:has-text('Fiyatlar')"); k.wait_for_selector("text=Fiyat yayınlama izni")
    k.check("form.kp-kutu input[type=checkbox]"); k.click("button:has-text('Fiyat yayınlama izni ver')")
    k.wait_for_selector("text=Fiyat güncelle")
    t("fiyat yayınlama izni verildi", sql("select count(*) from public.fiyat_izinleri where geri_alindi is null") == "1")
    ins = k.query_selector_all(".kp-fiyat-satir input")
    for el, v in zip(ins, ["5.600", "5.750,50", "9.300", "9.500"]): el.fill(v)
    k.click("button:has-text('Fiyatları yayınla')"); time.sleep(2)
    t("fiyat girildi (Türkçe sayı biçimi)", sql("select gram_satis || '|' || ceyrek_alis from public.fiyatlar") == "5750.50|9300.00")
    ekran(k, "5_kuyumcu_fiyat")
    k.click("button[role=tab]:has-text('Fotoğraflar')"); k.wait_for_selector("input[type=file]")
    subprocess.run(["convert", "-size", "1200x900", "gradient:gold-orange", "/tmp/foto.jpg"], check=True)
    k.set_input_files("input[type=file]", "/tmp/foto.jpg"); k.fill("input[placeholder='Ör. Dükkân vitrini']", "Test vitrini")
    k.click("button:has-text('Fotoğrafı yükle')"); k.wait_for_selector("text=Onay bekliyor", timeout=20000)
    t("fotoğraf depoya yüklendi ve onaya düştü", sql("select count(*) from storage.objects where bucket_id='isletme-fotolari'") == "1" and sql("select durum from public.fotograflar") == "bekliyor")
    k.click("button[role=tab]:has-text('Kampanyalar')"); k.wait_for_selector("text=Yeni kampanya")
    kf = k.locator("form", has_text="Yeni kampanya")
    kf.locator("input[type=text]").fill("Bilezik haftası"); kf.locator("textarea").fill("Bilezik işçiliğinde yüzde on indirim")
    import datetime as dt
    kf.locator("input[type=date]").nth(1).fill((dt.date.today() + dt.timedelta(days=10)).isoformat())
    kf.locator("button").click(); time.sleep(1.5)
    t("kampanya onaya gönderildi", sql("select durum from public.kampanyalar") == "bekliyor")

    # ── Yönetici onayları
    y.click("button[role=tab]:has-text('Fotoğraflar')"); y.wait_for_selector("img.kp-onizle")
    ekran(y, "6_yonetici_foto")
    y.click("button:has-text('Onayla')"); time.sleep(1.5)
    y.click("button[role=tab]:has-text('Kampanyalar')"); y.click("button:has-text('Yayına al')"); time.sleep(1.5)
    t("yönetici fotoğrafı ve kampanyayı onayladı", sql("select (select durum from public.fotograflar) || '|' || (select durum from public.kampanyalar)") == "onayli|yayinda")
    y.click("button[role=tab]:has-text('Fiyatlar')"); y.wait_for_selector("text=Deneme Kuyumculuk")
    y.click("button[role=tab]:has-text('Özet')"); y.wait_for_selector("text=Onay bekleyen fotoğraf")
    ekran(y, "7_yonetici_ozet")

    # ── Statik siteye senkron
    env = dict(os.environ, PN_SUPA_URL=API, PN_SUPA_KEY=KEY)
    r = subprocess.run(["python3", "_kaynak/kuyumcu_senkron.py"], cwd=KOK, env=env, capture_output=True, text=True); print(r.stdout, r.stderr)
    r2 = subprocess.run("cd _kaynak && python3 content.py && python3 nav.py", shell=True, cwd=KOK, capture_output=True, text=True); print(r2.stdout[-300:], r2.stderr[-2000:])
    prof = os.path.join(KOK, "kuyumcu-pazari/antalya/deneme-kuyumculuk-gazipasa.html")
    t("senkron + build başarılı, profil sayfası üretildi", r.returncode == 0 and r2.returncode == 0 and os.path.exists(prof), (r.returncode, r2.returncode))
    h = open(prof).read() if os.path.exists(prof) else ""
    t("profilde fiyat, fotoğraf, kampanya ve açıklama var", "5.750,50" in h and "kuyumcu-pazari/foto/deneme-kuyumculuk-gazipasa/" in h and "Bilezik haftası" in h and "Uçtan uca test işletmesi" in h)
    t("profilde yetkili adı ve e-posta yok", "Test Yetkili" not in h and "kuyumcu1@ornek.test" not in h)
    v = sayfa(); v.goto(SITE + "/kuyumcu-pazari/antalya/deneme-kuyumculuk-gazipasa.html"); time.sleep(2)
    ekran(v, "8_profil")
    t("profil görüntülenme sayıldı", sql("select coalesce(sum(adet),0) from public.etkinlik_gunluk where tur='profil'") == "1")
    v.goto(SITE + "/kuyumcu-pazari/"); time.sleep(1)
    t("pazar listesinde işletme görünüyor", "Deneme Kuyumculuk" in v.inner_text("main"))

    # izin geri alınınca profil anında fiyatı gizler (sayfa yeniden üretilmeden)
    k.click("button[role=tab]:has-text('Fiyatlar')"); k.wait_for_selector("text=Fiyat yayınlama iznini geri al")
    k.click("button:has-text('Fiyat yayınlama iznini geri al')"); time.sleep(1.5)
    v.goto(SITE + "/kuyumcu-pazari/antalya/deneme-kuyumculuk-gazipasa.html"); time.sleep(2)
    t("izin geri alınınca profil fiyatı hemen gizler", v.query_selector("#kpFiyatBlok table") is None and "şu an yayında değil" in v.inner_text("#kpFiyatBlok"))

    # askıya alınca senkron profili kaldırır
    y.click("button[role=tab]:has-text('İşletmeler')"); y.click("button:has-text('Onaylı')"); y.click("text=Deneme Kuyumculuk")
    y.wait_for_selector("text=Askıya al"); y.fill("textarea[placeholder^='İşletmeye gösterilecek']", "Test askısı"); y.click("button:has-text('Askıya al')"); time.sleep(1.5)
    subprocess.run(["python3", "_kaynak/kuyumcu_senkron.py"], cwd=KOK, env=env, check=True)
    subprocess.run("cd _kaynak && python3 content.py >/dev/null && python3 nav.py >/dev/null", shell=True, cwd=KOK, check=True)
    t("askıya alınan işletmenin sayfası ve fotoğrafı silindi", not os.path.exists(prof) and not glob.glob(os.path.join(KOK, "kuyumcu-pazari/foto/*/*")))
    t("panel ve yönetim sayfaları build sonrası yerinde", os.path.exists(os.path.join(KOK, "kuyumcu-pazari/panel/index.html")) and os.path.exists(os.path.join(KOK, "kuyumcu-pazari/yonetim/index.html")))
    t("tarayıcıda JavaScript hatası yok", not hatalar, hatalar)
    tarayici.close()

g = sum(1 for _, x in SONUC if x)
print(f"\nTOPLAM {len(SONUC)} test, {g} geçti, {len(SONUC) - g} kaldı")
sys.exit(0 if g == len(SONUC) else 1)
