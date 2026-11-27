/* Site sahibi yönetim paneli. Her işlem veritabanında ayrıca yönetici + iki adımlı doğrulama (aal2) kontrolünden geçer. */
(function () {
  "use strict";
  var h = KP.h, kok = document.getElementById("kpPanel");
  var sekme = "ozet", filtre = "bekleyen";
  var DURUM = { taslak: "Taslak", basvuru: "Yeni başvuru", inceleniyor: "İnceleniyor", eksik_bilgi: "Eksik bilgi", onayli: "Onaylı", reddedildi: "Reddedildi", askida: "Askıda" };
  var YONTEM = { vergi_levhasi: "Vergi levhası", esnaf_sicil: "Esnaf sicil kaydı", oda_kaydi: "Meslek odası kaydı", telefon: "Telefonla teyit", yerinde_goruntulu: "Görüntülü işyeri kontrolü", adres_ziyaret: "Adres ziyareti" };

  if (!PN.hazir) { KP.baglantiYok(kok); return; }
  var dh = PN.adresiIsle(); if (dh) KP.bildirim(dh, "hata");
  basla();

  async function basla() {
    if (!PN.oturum()) { KP.girisEkrani(kok, { baslik: "Yönetici girişi", sonra: basla }); return; }
    var d;
    try { d = await PN.rpc("hesap_durumu"); }
    catch (e) { if (e.status === 401) { await PN.cikis(); return basla(); } return hata(e); }
    if (!d.yonetici_hesabi) {
      KP.bosalt(kok).appendChild(h("div", { class: "kp-bos" }, h("b", { text: "Bu hesap yönetici değil" }), h("p", { text: "Yönetici yetkisi yalnızca veritabanından verilir." }), cikisBtn()));
      return;
    }
    if (d.aal !== "aal2") return ikiAdim();
    await KP.iller();
    ciz();
  }
  function hata(e) { KP.bosalt(kok).appendChild(h("div", { class: "kp-bos" }, h("b", { text: "Hata" }), h("p", { text: e.message }), cikisBtn())); }
  function cikisBtn() { var b = h("button", { type: "button", class: "ikincil kucuk", text: "Çıkış" }); b.addEventListener("click", async function () { await PN.cikis(); basla(); }); return b; }

  async function ikiAdim() {
    KP.bosalt(kok);
    var u = await PN.kullanici();
    var dogrulu = (u.factors || []).filter(function (f) { return f.factor_type === "totp" && f.status === "verified"; })[0];
    var kod = h("input", { inputmode: "numeric", autocomplete: "one-time-code", maxlength: "6", required: true, placeholder: "123456" });
    var b = h("button", { type: "submit", text: "Doğrula" });
    var f = h("form", { class: "kp-form" }, h("div", null, h("label", { text: "Doğrulama uygulamasındaki 6 haneli kod" }), kod), b);
    var kutu = h("div", { class: "kp-kutu" }, h("h2", { text: "İki adımlı doğrulama" }));
    kok.appendChild(kutu);
    var faktor = dogrulu;
    if (!dogrulu) {
      // yarım kalmış kayıtları temizle, yenisini oluştur
      for (var i = 0; i < (u.factors || []).length; i++) if (u.factors[i].status !== "verified") { try { await PN.totpSil(u.factors[i].id); } catch (e) {} }
      var yeni = await PN.totpOlustur();
      faktor = yeni;
      kutu.append(h("p", { text: "Yönetim paneli için iki adımlı doğrulama zorunludur. Telefonunuzdaki doğrulama uygulamasıyla (Google Authenticator, Microsoft Authenticator vb.) bu kodu okutun ya da anahtarı elle girin:" }),
        h("img", { class: "kp-qr", src: yeni.totp.qr_code, alt: "Doğrulama uygulaması için QR kodu", width: "200", height: "200" }),
        h("p", null, "Anahtar: ", h("code", { class: "kp-anahtar", text: yeni.totp.secret })));
    }
    kutu.append(f, cikisBtn());
    f.addEventListener("submit", KP.islem(b, async function () {
      await PN.totpDogrula(faktor.id, kod.value.replace(/\D/g, ""));
      KP.bildirim("Doğrulandı"); basla();
    }));
  }

  function ciz() {
    KP.bosalt(kok);
    kok.appendChild(h("div", { class: "kp-ust" }, h("span", { class: "note", text: "Yönetici · " + ((PN.oturum().user || {}).email || "") }), cikisBtn()));
    var S = [["ozet", "Özet"], ["isletme", "İşletmeler"], ["degisiklik", "Değişiklikler"], ["foto", "Fotoğraflar"], ["fiyat", "Fiyatlar"], ["kampanya", "Kampanyalar"], ["paket", "Paketler"], ["kayit", "Kayıt"]];
    kok.appendChild(h("div", { class: "kp-sekmeler", role: "tablist" }, S.map(function (s) {
      var b = h("button", { type: "button", role: "tab", "aria-selected": s[0] === sekme ? "true" : "false", text: s[1] });
      b.addEventListener("click", function () { sekme = s[0]; ciz(); }); return b;
    })));
    var alan = h("div", { class: "kp-alan" }); kok.appendChild(alan);
    var f = { ozet: ozet, isletme: isletmeler, degisiklik: degisiklikler, foto: fotolar, fiyat: fiyatlar, kampanya: kampanyalar, paket: paketler, kayit: kayit }[sekme];
    f(alan).catch(function (e) { alan.appendChild(h("p", { class: "kp-uyari", text: e.message })); });
  }

  async function ozet(el) {
    var s = await PN.rpc("yonetici_istatistik");
    var satir = function (a, b) { return h("tr", null, h("td", { text: a }), h("td", { text: String(b) })); };
    el.appendChild(h("table", null, h("tbody", null,
      Object.keys(DURUM).map(function (k) { return satir("İşletme · " + DURUM[k], (s.durumlar || {})[k] || 0); }),
      satir("Onay bekleyen fotoğraf", s.bekleyen_foto), satir("Onay bekleyen kampanya", s.bekleyen_kampanya),
      satir("Onay bekleyen bilgi değişikliği", s.bekleyen_degisiklik), satir("Silme talebi", s.silme_talebi),
      satir("Son 24 saatte fiyat güncellemesi", s.fiyat_24s),
      satir("Son 30 gün profil görüntülenme", (s.etkinlik_30g || {}).profil || 0),
      satir("Son 30 gün ara / WhatsApp / yol tarifi", ((s.etkinlik_30g || {}).ara || 0) + " / " + ((s.etkinlik_30g || {}).whatsapp || 0) + " / " + ((s.etkinlik_30g || {}).yol_tarifi || 0)))));
    var il = s.il_dagilimi || {};
    if (Object.keys(il).length) el.appendChild(h("p", { class: "note", text: "Onaylı işletmelerin illere dağılımı: " + Object.keys(il).map(function (k) { return KP.ilAd(k) + " " + il[k]; }).join(", ") }));
  }

  async function isletmeler(el) {
    var FL = { bekleyen: "durum=in.(basvuru,inceleniyor,eksik_bilgi)", onayli: "durum=eq.onayli", askida: "durum=eq.askida", reddedildi: "durum=eq.reddedildi", taslak: "durum=eq.taslak", silme: "silme_talebi=not.is.null" };
    el.appendChild(h("div", { class: "kp-filtreler" }, Object.keys(FL).map(function (k) {
      var b = h("button", { type: "button", class: k === filtre ? "secili" : "", text: { bekleyen: "Bekleyen", onayli: "Onaylı", askida: "Askıda", reddedildi: "Reddedilen", taslak: "Taslak", silme: "Silme talebi" }[k] });
      b.addEventListener("click", function () { filtre = k; ciz(); }); return b;
    })));
    var p = FL[filtre].split("="), sorgu = { select: "*", order: "guncellendi.desc", limit: "200" }; sorgu[p[0]] = p.slice(1).join("=");
    var r = await PN.sec("isletmeler", sorgu);
    if (!r.length) el.appendChild(h("p", { class: "note", text: "Kayıt yok." }));
    r.forEach(function (x) { el.appendChild(isletmeKarti(x)); });
  }

  function isletmeKarti(x) {
    var detay = h("div", { hidden: true });
    var baslik = h("button", { type: "button", class: "kp-kart-bas" }, h("b", { text: x.ad }), " · ", KP.ilceAd(x.il, x.ilce) + ", " + KP.ilAd(x.il), " · ", h("span", { class: "kp-etiket d-" + x.durum, text: DURUM[x.durum] }));
    baslik.addEventListener("click", async function () {
      detay.hidden = !detay.hidden;
      if (!detay.hidden && !detay.firstChild) { try { await isletmeDetay(detay, x); } catch (e) { detay.appendChild(h("p", { class: "kp-uyari", text: e.message })); } }
    });
    return h("div", { class: "kp-kutu" }, baslik, detay);
  }

  async function isletmeDetay(el, x) {
    var dg = await PN.sec("dogrulamalar", { select: "*", isletme_id: "eq." + x.id });
    var sat = function (a, b) { return h("tr", null, h("th", { text: a }), h("td", { text: b === null || b === undefined || b === "" ? "—" : String(b) })); };
    el.appendChild(h("table", null, h("tbody", null,
      sat("Yetkili", x.yetkili_ad), sat("Adres", x.adres), sat("Telefon", x.telefon), sat("WhatsApp", x.whatsapp), sat("E-posta", x.eposta),
      sat("Açıklama", x.aciklama), sat("Saatler", KP.GUNLER.map(function (g) { return g[1].slice(0, 3) + " " + (x.saatler[g[0]] === "kapali" ? "kapalı" : x.saatler[g[0]]); }).join(" · ")),
      sat("Paket", x.paket), sat("Başvuru", KP.zaman(x.basvuru_at)), sat("Doğrulandı", KP.zaman(x.dogrulandi_at)), sat("Not", x.durum_notu),
      sat("Silme talebi", x.silme_talebi ? KP.zaman(x.silme_talebi) : null))));
    el.appendChild(h("p", { class: "note" }, "Telefonla teyit için: ", h("a", { href: "tel:" + x.telefon, text: x.telefon })));

    // doğrulama kontrol listesi
    var var_ = {}; dg.forEach(function (d) { var_[d.yontem] = d; });
    el.appendChild(h("h3", { text: "Doğrulama (en az 2 yöntem)" }));
    Object.keys(YONTEM).forEach(function (y) {
      var not = h("input", { placeholder: "Kısa not (belge numarası yazmayın)", maxlength: "500", value: var_[y] ? var_[y].notlar || "" : "" });
      var b = h("button", { type: "button", class: var_[y] ? "ikincil kucuk" : "kucuk", text: var_[y] ? "Kaldır" : "Yapıldı olarak işaretle" });
      b.addEventListener("click", KP.islem(b, async function () {
        if (var_[y]) await PN.rpc("yonetici_dogrulama_sil", { p_id: x.id, p_yontem: y });
        else await PN.rpc("yonetici_dogrulama_ekle", { p_id: x.id, p_yontem: y, p_not: not.value.trim() || null });
        KP.bosalt(el); await isletmeDetay(el, x);
      }));
      el.appendChild(h("div", { class: "kp-dogrulama" + (var_[y] ? " ok" : "") }, h("b", { text: (var_[y] ? "✓ " : "") + YONTEM[y] }),
        var_[y] ? h("small", { class: "note", text: " " + KP.zaman(var_[y].zaman) }) : null, not, b));
    });

    var not = h("textarea", { rows: "2", maxlength: "1000", placeholder: "İşletmeye gösterilecek açıklama (ret, eksik bilgi ve askı için zorunlu)" });
    var dugmeler = h("div", { class: "kp-dugmeler" });
    function dugme(metin, fn, sinif) {
      var b = h("button", { type: "button", class: sinif || "", text: metin });
      b.addEventListener("click", KP.islem(b, async function () { await fn(); KP.bildirim("Kaydedildi"); ciz(); }));
      dugmeler.appendChild(b);
    }
    var durum = function (d) { return function () { return PN.rpc("yonetici_durum_degistir", { p_id: x.id, p_durum: d, p_not: not.value.trim() || null }); }; };
    if (["basvuru", "eksik_bilgi"].indexOf(x.durum) >= 0) dugme("İncelemeye al", durum("inceleniyor"), "ikincil");
    if (["basvuru", "inceleniyor", "eksik_bilgi", "askida"].indexOf(x.durum) >= 0) dugme(x.durum === "askida" ? "Yeniden yayına al" : "Onayla ve yayınla", async function () {
      if (!confirm("İşletme doğrulandı ve yayınlanacak. Emin misiniz?")) throw new Error("İptal edildi");
      var slug = await PN.rpc("yonetici_onayla", { p_id: x.id }); KP.bildirim("Yayın adresi: " + slug);
    });
    if (["basvuru", "inceleniyor"].indexOf(x.durum) >= 0) dugme("Eksik bilgi iste", durum("eksik_bilgi"), "ikincil");
    if (["basvuru", "inceleniyor", "eksik_bilgi"].indexOf(x.durum) >= 0) dugme("Reddet", durum("reddedildi"), "tehlike");
    if (x.durum === "onayli") dugme("Askıya al", durum("askida"), "tehlike");
    dugme("Kalıcı olarak sil", async function () {
      if (prompt("Bu işletme ve tüm fiyat, fotoğraf, kampanya kayıtları silinecek. Onaylamak için SİL yazın") !== "SİL") throw new Error("İptal edildi");
      var fo = await PN.sec("fotograflar", { select: "yol", isletme_id: "eq." + x.id });
      if (fo.length) { try { await PN.depoSil(fo.map(function (f) { return f.yol; })); } catch (e) {} }
      await PN.rpc("yonetici_isletme_sil", { p_id: x.id });
    }, "tehlike");
    el.append(h("h3", { text: "Karar" }), not, dugmeler);

    var pk = await PN.sec("paketler", { select: "kod,ad,satista", order: "kod" });
    var sec = h("select", null, pk.map(function (p) { return h("option", { value: p.kod, text: p.ad + (p.satista ? "" : " (satışta değil)"), selected: p.kod === x.paket, disabled: !p.satista }); }));
    var pb = h("button", { type: "button", class: "ikincil kucuk", text: "Paketi ata" });
    pb.addEventListener("click", KP.islem(pb, async function () { await PN.rpc("yonetici_paket_ata", { p_id: x.id, p_kod: sec.value }); KP.bildirim("Paket atandı"); }));
    el.append(h("h3", { text: "Paket" }), h("div", { class: "kp-satir" }, sec, pb));
  }

  async function degisiklikler(el) {
    var r = await PN.sec("isletmeler", { select: "*", bekleyen_degisiklik: "not.is.null" });
    if (!r.length) el.appendChild(h("p", { class: "note", text: "Onay bekleyen değişiklik yok." }));
    r.forEach(function (x) {
      var b = x.bekleyen_degisiklik;
      var tablo = h("table", null, h("thead", null, h("tr", null, h("th", { text: "Alan" }), h("th", { text: "Şu an" }), h("th", { text: "İstenen" }))),
        h("tbody", null, Object.keys(b).map(function (k) { return h("tr", null, h("td", { text: k }), h("td", { text: x[k] === null ? "—" : String(x[k]) }), h("td", { text: b[k] === null ? "—" : String(b[k]) })); })));
      var on = h("button", { type: "button", text: "Onayla" }), red = h("button", { type: "button", class: "tehlike", text: "Reddet" });
      on.addEventListener("click", KP.islem(on, async function () { await PN.rpc("yonetici_degisiklik_karar", { p_id: x.id, p_onay: true }); ciz(); }));
      red.addEventListener("click", KP.islem(red, async function () { await PN.rpc("yonetici_degisiklik_karar", { p_id: x.id, p_onay: false }); ciz(); }));
      el.appendChild(h("div", { class: "kp-kutu" }, h("b", { text: x.ad }), tablo,
        h("p", { class: "note", text: "Adres veya telefon değiştiyse yeniden teyit etmeniz önerilir." }), h("div", { class: "kp-dugmeler" }, on, red)));
    });
  }

  async function fotolar(el) {
    var r = await PN.sec("fotograflar", { select: "*,isletmeler(ad)", durum: "eq.bekliyor", order: "olusturuldu.asc", limit: "100" });
    if (!r.length) el.appendChild(h("p", { class: "note", text: "Onay bekleyen fotoğraf yok." }));
    r.forEach(function (f) {
      var on = h("button", { type: "button", text: "Onayla" }), red = h("button", { type: "button", class: "tehlike", text: "Reddet ve sil" });
      on.addEventListener("click", KP.islem(on, async function () { await PN.rpc("yonetici_foto_karar", { p_foto: f.id, p_durum: "onayli" }); ciz(); }));
      red.addEventListener("click", KP.islem(red, async function () {
        await PN.rpc("yonetici_foto_karar", { p_foto: f.id, p_durum: "reddedildi" });
        try { await PN.depoSil([f.yol]); } catch (e) {}
        ciz();
      }));
      el.appendChild(h("figure", { class: "kp-kutu" }, h("img", { src: PN.acikUrl(f.yol), alt: f.aciklama, class: "kp-onizle" }),
        h("figcaption", null, h("b", { text: (f.isletmeler || {}).ad || "" }), " · ", f.tur === "urun" ? "Ürün" : "Mağaza", " · ", f.aciklama),
        h("p", { class: "note", text: "Yüz, plaka, kişisel bilgi, başka işletmeye ait ya da yanıltıcı görsel varsa reddedin." }),
        h("div", { class: "kp-dugmeler" }, on, red)));
    });
  }

  async function fiyatlar(el) {
    var r = await PN.sec("fiyatlar", { select: "*,isletmeler(ad)", order: "guncelleme.desc", limit: "150" });
    // her işletmenin son yayındaki gram satışına göre medyan; %5'ten fazla sapanlar işaretlenir
    var son = {}; r.forEach(function (f) { if (f.durum === "yayinda" && !son[f.isletme_id] && KP.saatOnce(f.guncelleme) < 24) son[f.isletme_id] = +f.gram_satis; });
    var v = Object.keys(son).map(function (k) { return son[k]; }).sort(function (a, b) { return a - b; });
    var med = v.length ? (v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2) : null;
    el.appendChild(h("p", { class: "note", text: med ? "Son 24 saatte fiyat giren " + v.length + " işletmenin gram satış medyanı: " + KP.tl(med) + ". %5'ten fazla sapan girişler işaretlenir." : "Karşılaştırma için yeterli güncel fiyat yok." }));
    if (!r.length) { el.appendChild(h("p", { class: "note", text: "Henüz fiyat girilmedi." })); return; }
    el.appendChild(h("table", null, h("thead", null, h("tr", null, h("th", { text: "İşletme / zaman" }), h("th", { text: "Gram" }), h("th", { text: "Çeyrek" }), h("th", { text: "" }))),
      h("tbody", null, r.map(function (f) {
        var sap = med && v.length >= 3 ? Math.abs(f.gram_satis / med - 1) : 0;
        var g = h("button", { type: "button", class: "tehlike kucuk", text: "Gizle" });
        g.addEventListener("click", KP.islem(g, async function () {
          var n = prompt("Gizleme nedeni (işletme görür):"); if (!n) throw new Error("İptal edildi");
          await PN.rpc("yonetici_fiyat_gizle", { p_fiyat: f.id, p_neden: n }); ciz();
        }));
        return h("tr", { class: sap > 0.05 ? "kp-sapma" : "" },
          h("td", null, h("b", { text: (f.isletmeler || {}).ad || "" }), h("br"), h("small", { text: KP.zaman(f.guncelleme) + (KP.saatOnce(f.guncelleme) > 24 ? " · eski" : "") })),
          h("td", { text: KP.tl(f.gram_alis) + " / " + KP.tl(f.gram_satis) + (sap > 0.05 ? " ⚠ %" + (sap * 100).toFixed(1) : "") }),
          h("td", { text: f.ceyrek_satis ? KP.tl(f.ceyrek_alis) + " / " + KP.tl(f.ceyrek_satis) : "—" }),
          h("td", null, f.durum === "gizlendi" ? h("small", { text: "Gizlendi: " + (f.gizleme_nedeni || "") }) : g));
      }))));
  }

  async function kampanyalar(el) {
    var r = await PN.sec("kampanyalar", { select: "*,isletmeler(ad)", order: "olusturuldu.desc", limit: "100" });
    if (!r.length) el.appendChild(h("p", { class: "note", text: "Kampanya yok." }));
    r.forEach(function (k) {
      var not = h("input", { placeholder: "Not (isteğe bağlı, işletme görür)", maxlength: "300" });
      var d = h("div", { class: "kp-dugmeler" });
      [["yayinda", "Yayına al", ""], ["reddedildi", "Reddet", "tehlike"], ["gizlendi", "Gizle", "ikincil"]].forEach(function (a) {
        if (a[0] === k.durum) return;
        var b = h("button", { type: "button", class: a[2], text: a[1] });
        b.addEventListener("click", KP.islem(b, async function () { await PN.rpc("yonetici_kampanya_karar", { p_id: k.id, p_durum: a[0], p_not: not.value.trim() || null }); ciz(); }));
        d.appendChild(b);
      });
      el.appendChild(h("div", { class: "kp-kutu" }, h("b", { text: k.baslik }), " · ", (k.isletmeler || {}).ad || "", h("p", { text: k.aciklama }),
        h("p", { class: "note", text: k.durum + " · " + k.baslangic + " – " + k.bitis }), not, d));
    });
  }

  async function paketler(el) {
    var r = await PN.sec("paketler", { select: "*", order: "foto_limit" });
    el.appendChild(h("p", { class: "kp-uyari", text: "Ödeme sistemi kurulu değil. 'Satışta' işaretli olmayan paket hiçbir işletmeye atanamaz. Ücret alanı yalnızca bilgi içindir." }));
    r.forEach(function (p) {
      var g = {
        ad: h("input", { value: p.ad, maxlength: "40" }), satista: h("input", { type: "checkbox", checked: p.satista }),
        foto: h("input", { type: "number", min: "0", max: "50", value: String(p.foto_limit) }), fiyat: h("input", { type: "checkbox", checked: p.fiyat_yayini }),
        kamp: h("input", { type: "number", min: "0", max: "20", value: String(p.kampanya_limit) }), ist: h("input", { type: "checkbox", checked: p.istatistik }),
        rozet: h("input", { value: p.rozet || "", maxlength: "30" }), one: h("input", { type: "checkbox", checked: p.one_cikan }),
        ucret: h("input", { type: "number", min: "0", step: "0.01", value: p.aylik_ucret_tl === null ? "" : String(p.aylik_ucret_tl) })
      };
      var b = h("button", { type: "button", text: "Kaydet" });
      b.addEventListener("click", KP.islem(b, async function () {
        await PN.rpc("yonetici_paket_kaydet", { p_kod: p.kod, p_ad: g.ad.value.trim(), p_satista: g.satista.checked, p_foto_limit: +g.foto.value,
          p_fiyat_yayini: g.fiyat.checked, p_kampanya_limit: +g.kamp.value, p_istatistik: g.ist.checked, p_rozet: g.rozet.value, p_one_cikan: g.one.checked,
          p_aylik_ucret_tl: g.ucret.value === "" ? null : +g.ucret.value });
        KP.bildirim("Paket kaydedildi"); ciz();
      }));
      var s = function (et, i) { return h("label", { class: "kp-paket-alan" }, h("span", { text: et }), i); };
      el.appendChild(h("div", { class: "kp-kutu kp-paket" }, h("h3", { text: p.kod }), s("Ad", g.ad), s("Satışta", g.satista), s("Fotoğraf sınırı", g.foto),
        s("Fiyat yayını", g.fiyat), s("Kampanya sınırı", g.kamp), s("İstatistik", g.ist), s("Rozet", g.rozet), s("Öne çıkan", g.one), s("Aylık ücret (TL, bilgi)", g.ucret), b));
    });
  }

  async function kayit(el) {
    var r = await PN.sec("denetim_kaydi", { select: "*", order: "zaman.desc", limit: "100" });
    el.appendChild(h("table", null, h("thead", null, h("tr", null, h("th", { text: "Zaman" }), h("th", { text: "İşlem" }), h("th", { text: "Ayrıntı" }))),
      h("tbody", null, r.map(function (k) { return h("tr", null, h("td", { text: KP.zaman(k.zaman) }), h("td", { text: k.islem }), h("td", null, h("small", { text: k.tablo + " " + (k.kayit_id || "").slice(0, 8) + " " + (Object.keys(k.ayrinti || {}).length ? JSON.stringify(k.ayrinti) : "") }))); }))));
  }
})();
