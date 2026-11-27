/* Kuyumcu paneli: kayıt/giriş, işletme bilgileri, başvuru, fiyat, fotoğraf, kampanya, istatistik. */
(function () {
  "use strict";
  var h = KP.h, kok = document.getElementById("kpPanel");
  var DURUM = {
    taslak: ["Taslak", "Bilgileriniz kaydedildi ama başvurunuz henüz gönderilmedi."],
    basvuru: ["Başvuru alındı", "Başvurunuz sırada. Doğrulama için sizi arayacağız; bu süreçte bilgileriniz yayınlanmaz."],
    inceleniyor: ["İnceleniyor", "Başvurunuz inceleniyor. İnceleme bitene kadar işletme bilgileri değiştirilemez."],
    eksik_bilgi: ["Eksik bilgi", "Başvurunuz için ek bilgi gerekiyor. Aşağıdaki notu okuyup bilgileri düzelttikten sonra tekrar gönderin."],
    onayli: ["Onaylı · yayında", "İşletmeniz doğrulandı ve Kuyumcu Pazarı'nda yayınlanıyor. Sayfa en geç birkaç saat içinde güncellenir."],
    reddedildi: ["Reddedildi", "Başvurunuz onaylanmadı."],
    askida: ["Askıya alındı", "İşletmeniz geçici olarak yayından kaldırıldı."]
  };
  var isl = null, paket = null, sekme = "bilgiler";

  if (!PN.hazir) {
    KP.baglantiYok(kok, h("p", null, "Başvurular şimdilik ", h("a", { href: "/kuyumcu-pazari/basvuru.html", text: "e-posta ile başvuru formundan" }), " alınıyor."));
    return;
  }
  var donusHata = PN.adresiIsle();
  if (donusHata) KP.bildirim(donusHata, "hata");
  basla();

  async function basla() {
    if (!PN.oturum()) {
      KP.girisEkrani(kok, { baslik: "Kuyumcu girişi", aciklama: "İşletmenizi Kuyumcu Pazarı'na eklemek ya da bilgilerinizi güncellemek için giriş yapın.", sonra: basla });
      return;
    }
    try {
      var r = await PN.sec("isletmeler", { select: "*" });
      isl = r[0] || null;
      if (isl) paket = (await PN.sec("paketler", { select: "*", kod: "eq." + isl.paket }))[0];
      await KP.iller();
      ciz();
    } catch (e) {
      if (e.status === 401) { await PN.cikis(); return basla(); }
      KP.bosalt(kok).appendChild(h("div", { class: "kp-bos" }, h("b", { text: "Bilgiler yüklenemedi" }), h("p", { text: e.message })));
    }
  }

  function ust() {
    var u = PN.oturum() && PN.oturum().user;
    var cik = h("button", { type: "button", class: "ikincil kucuk", text: "Çıkış" });
    cik.addEventListener("click", async function () { await PN.cikis(); basla(); });
    return h("div", { class: "kp-ust" }, h("span", { class: "note", text: u && u.email ? u.email : "Giriş yapıldı" }), cik);
  }

  function ciz() {
    KP.bosalt(kok);
    kok.appendChild(ust());
    if (!isl) { kok.appendChild(bilgiFormu(null)); return; }
    var d = DURUM[isl.durum] || [isl.durum, ""];
    kok.appendChild(h("div", { class: "kp-durum d-" + isl.durum },
      h("b", { text: isl.ad + " · " + d[0] }), h("p", { text: d[1] }),
      isl.durum_notu ? h("p", { class: "kp-not" }, h("b", { text: "Yönetici notu: " }), isl.durum_notu) : null,
      isl.durum === "onayli" && isl.slug ? h("a", { href: "/kuyumcu-pazari/" + isl.il + "/" + isl.slug + ".html", text: "Herkese açık sayfanızı görün →" }) : null));
    if (isl.silme_talebi) kok.appendChild(h("p", { class: "kp-uyari", text: "Hesap ve işletme silme talebiniz alındı (" + KP.zaman(isl.silme_talebi) + "). En geç 30 gün içinde işleme alınır." }));

    var sekmeler = [["bilgiler", "Bilgiler"]];
    if (isl.durum === "onayli") sekmeler.push(["fiyat", "Fiyatlar"], ["foto", "Fotoğraflar"], ["kampanya", "Kampanyalar"], ["istatistik", "İstatistik"]);
    sekmeler.push(["hesap", "Hesap"]);
    if (!sekmeler.some(function (s) { return s[0] === sekme; })) sekme = "bilgiler";
    var nav = h("div", { class: "kp-sekmeler", role: "tablist" }, sekmeler.map(function (s) {
      var b = h("button", { type: "button", role: "tab", "aria-selected": s[0] === sekme ? "true" : "false", text: s[1] });
      b.addEventListener("click", function () { sekme = s[0]; ciz(); });
      return b;
    }));
    kok.appendChild(nav);
    var alan = h("div", { class: "kp-alan" }); kok.appendChild(alan);
    ({ bilgiler: function () { alan.appendChild(bilgiFormu(isl)); if (["taslak", "eksik_bilgi"].indexOf(isl.durum) >= 0) alan.appendChild(basvuruKutusu()); },
       fiyat: function () { fiyatSekmesi(alan); }, foto: function () { fotoSekmesi(alan); },
       kampanya: function () { kampanyaSekmesi(alan); }, istatistik: function () { istatistikSekmesi(alan); },
       hesap: function () { hesapSekmesi(alan); } })[sekme]();
  }

  function alan(etiket, input, ipucu) {
    return h("div", null, h("label", { text: etiket }), input, ipucu ? h("small", { class: "note", text: ipucu }) : null);
  }

  function bilgiFormu(x) {
    x = x || {};
    var kilitli = x.durum === "inceleniyor";
    var ad = h("input", { name: "ad", required: true, maxlength: "120", value: x.ad || "" });
    var yetkili = h("input", { name: "yetkili_ad", required: true, maxlength: "120", value: x.yetkili_ad || "", autocomplete: "name" });
    var adres = h("textarea", { name: "adres", required: true, maxlength: "300", rows: "2" }); adres.value = x.adres || "";
    var tel = h("input", { name: "telefon", required: true, type: "tel", value: x.telefon || "", placeholder: "0242 555 00 00" });
    var wa = h("input", { name: "whatsapp", type: "tel", value: x.whatsapp || "", placeholder: "0555 555 55 55" });
    var ep = h("input", { name: "eposta", type: "email", value: x.eposta || "" });
    var ac = h("textarea", { name: "aciklama", maxlength: "1000", rows: "3", placeholder: "Ör. 1985'ten beri hizmet veren aile işletmesi. Bilezik ve set işçiliği." }); ac.value = x.aciklama || "";
    var saat = KP.saatEditoru(x.saatler);
    var kaydet = h("button", { type: "submit", text: x.id ? "Bilgileri kaydet" : "Kaydet ve devam et" });
    var form = h("form", { class: "kp-form" });
    var ilAlan = h("div", { class: "iki" });
    KP.ilIlceSec(x.il, x.ilce).then(function (s) {
      ilAlan.appendChild(alan("İl", s.il)); ilAlan.appendChild(alan("İlçe", s.ilce));
      form._il = s.il; form._ilce = s.ilce;
    });
    form.append(
      h("h2", { text: x.id ? "İşletme bilgileri" : "İşletmenizi ekleyin" }),
      x.id ? null : h("p", { class: "note", text: "Bu bilgiler doğrulama için kullanılır ve yalnızca onaydan sonra yayınlanır. T.C. kimlik numarası, vergi numarası ya da belge yüklemeniz istenmez." }),
      kilitli ? h("p", { class: "kp-uyari", text: "Başvurunuz incelenirken işletme bilgileri değiştirilemez; çalışma saatlerini değiştirebilirsiniz." }) : null,
      x.durum === "onayli" || x.durum === "askida" ? h("p", { class: "kp-uyari", text: "Ad, adres, il/ilçe, telefon, WhatsApp ve açıklama değişiklikleri yönetici onayından sonra yayına girer. Çalışma saatleri hemen güncellenir." }) : null,
      x.bekleyen_degisiklik ? h("div", { class: "kp-uyari" }, h("b", { text: "Onay bekleyen değişiklik: " }),
        Object.keys(x.bekleyen_degisiklik).map(function (k) { return k + " → " + (x.bekleyen_degisiklik[k] === null ? "(boş)" : x.bekleyen_degisiklik[k]); }).join(" · ")) : null,
      alan("İşletme adı", ad), alan("Yetkili adı soyadı", yetkili, "Yayınlanmaz; yalnızca doğrulama için."),
      ilAlan, alan("Açık adres", adres),
      h("div", { class: "iki" }, alan("Telefon", tel), alan("WhatsApp (isteğe bağlı)", wa)),
      alan("İletişim e-postası (isteğe bağlı, yayınlanmaz)", ep),
      alan("Kısa açıklama (isteğe bağlı)", ac),
      h("div", null, h("label", { text: "Çalışma saatleri" }), saat.el),
      kaydet);
    [ad, yetkili, adres, tel, wa, ep, ac].forEach(function (i) { i.disabled = kilitli; });
    form.addEventListener("submit", KP.islem(kaydet, async function () {
      var v = { ad: ad.value.trim(), yetkili_ad: yetkili.value.trim(), adres: adres.value.trim(), telefon: KP.tel(tel.value),
        whatsapp: KP.tel(wa.value), eposta: ep.value.trim() || null, aciklama: ac.value.trim() || null, saatler: saat.deger() };
      if (!form._il || !form._il.value || !form._ilce.value) throw new Error("İl ve ilçe seçin");
      v.il = form._il.value; v.ilce = form._ilce.value;
      if (v.ad.length < 2) throw new Error("İşletme adı en az 2 karakter olmalı");
      if (v.yetkili_ad.length < 2) throw new Error("Yetkili adını yazın");
      if (v.adres.length < 5) throw new Error("Açık adresi yazın");
      if (kilitli) v = { saatler: v.saatler };
      if (x.id) { var r = await PN.guncelle("isletmeler", { id: "eq." + x.id }, v); isl = r[0]; KP.bildirim(isl.bekleyen_degisiklik ? "Kaydedildi. Bazı değişiklikler yönetici onayını bekliyor." : "Bilgiler kaydedildi"); }
      else { isl = (await PN.ekle("isletmeler", v))[0]; paket = (await PN.sec("paketler", { select: "*", kod: "eq." + isl.paket }))[0]; KP.bildirim("Kaydedildi. Şimdi başvurunuzu gönderin."); }
      ciz();
    }));
    return form;
  }

  function basvuruKutusu() {
    var c1 = h("input", { type: "checkbox", required: true }), c2 = h("input", { type: "checkbox", required: true });
    var b = h("button", { type: "submit", text: "Başvuruyu gönder" });
    var f = h("form", { class: "kp-form kp-kutu" }, h("h2", { text: "Başvuruyu gönder" }),
      h("p", { class: "note", text: "Başvurunuzu aldıktan sonra sizi arayıp en az iki yöntemle doğrularız (ör. telefon ve vergi levhası görüntüsü). Belge kopyası saklanmaz." }),
      h("label", { class: "onay" }, c1, h("span", null, h("a", { href: "/kuyumcu-pazari/panel-aydinlatma.html", target: "_blank", rel: "noopener", text: "Aydınlatma metnini" }), " okudum.")),
      h("label", { class: "onay" }, c2, h("span", { text: "İşletmenin yetkilisi olduğumu ve verdiğim bilgilerin doğru olduğunu beyan ederim." })), b);
    f.addEventListener("submit", KP.islem(b, async function () {
      if (!c1.checked || !c2.checked) throw new Error("İki onay kutusunu da işaretleyin");
      await PN.rpc("basvuru_gonder", { p_aydinlatma_surumu: KP.AYDINLATMA_SURUMU, p_beyan: true });
      KP.bildirim("Başvurunuz alındı"); await basla();
    }));
    return f;
  }

  async function fiyatSekmesi(el) {
    var izin = await PN.sec("fiyat_izinleri", { select: "*", geri_alindi: "is.null" });
    var son = await PN.sec("fiyatlar", { select: "*", order: "guncelleme.desc", limit: "10" });
    if (!paket.fiyat_yayini) { el.appendChild(h("p", { class: "kp-uyari", text: "Paketiniz fiyat yayınını içermiyor." })); return; }
    if (!izin.length) {
      var c = h("input", { type: "checkbox" }), b = h("button", { type: "submit", text: "Fiyat yayınlama izni ver" });
      var f = h("form", { class: "kp-form kp-kutu" }, h("h2", { text: "Fiyat yayınlama izni" }),
        h("p", { text: "Fiyatlarınızın Kuyumcu Pazarı'ndaki sayfanızda yayınlanması için açık izniniz gerekir. İzni istediğiniz an geri alabilirsiniz; geri aldığınızda fiyatlarınız hemen yayından kalkar." }),
        h("label", { class: "onay" }, c, h("span", null, h("a", { href: "/kuyumcu-pazari/fiyat-izni.html", target: "_blank", rel: "noopener", text: "Fiyat yayınlama izin metnini" }), " okudum; girdiğim fiyatların tarih ve saatiyle yayınlanmasına izin veriyorum.")), b);
      f.addEventListener("submit", KP.islem(b, async function () {
        if (!c.checked) throw new Error("İzin kutusunu işaretleyin");
        await PN.rpc("fiyat_izni_ver", { p_metin_surumu: KP.FIYAT_IZNI_SURUMU }); KP.bildirim("İzin kaydedildi"); ciz();
      }));
      el.appendChild(f);
    } else {
      var alanlar = {}, tablo = h("div", { class: "kp-fiyat-gir" });
      [["gram", "Gram altın"], ["ceyrek", "Çeyrek altın"], ["yarim", "Yarım altın"], ["tam", "Tam altın"]].forEach(function (a) {
        var al = h("input", { type: "text", inputmode: "decimal", placeholder: "Alış", "aria-label": a[1] + " alış", value: son[0] && son[0][a[0] + "_alis"] ? String(son[0][a[0] + "_alis"]).replace(".", ",") : "" });
        var st = h("input", { type: "text", inputmode: "decimal", placeholder: "Satış", "aria-label": a[1] + " satış", value: son[0] && son[0][a[0] + "_satis"] ? String(son[0][a[0] + "_satis"]).replace(".", ",") : "" });
        alanlar[a[0]] = [al, st];
        tablo.appendChild(h("div", { class: "kp-fiyat-satir" }, h("b", { text: a[1] }), al, st));
      });
      var gb = h("button", { type: "submit", text: "Fiyatları yayınla" });
      var sayi = function (s) { s = String(s).trim().replace(/\./g, "").replace(",", "."); return s === "" ? null : +s; };
      var f2 = h("form", { class: "kp-form kp-kutu" }, h("h2", { text: "Fiyat güncelle" }),
        h("p", { class: "note", text: "Fiyatlar TL olarak, girildiği tarih ve saatle yayınlanır. 24 saati geçen fiyat sitede 'eski' diye işaretlenir, 7 günü geçen fiyat gösterilmez. Gram zorunlu, diğerleri isteğe bağlı." }),
        tablo, gb);
      f2.addEventListener("submit", KP.islem(gb, async function () {
        var v = { isletme_id: isl.id };
        Object.keys(alanlar).forEach(function (k) {
          var a = sayi(alanlar[k][0].value), s = sayi(alanlar[k][1].value);
          if ((a === null) !== (s === null)) throw new Error("Her altın türü için alış ve satışı birlikte girin");
          if (a !== null && (isNaN(a) || isNaN(s) || a <= 0 || s < a)) throw new Error("Fiyatlar geçersiz: satış, alıştan küçük olamaz");
          v[k + "_alis"] = a; v[k + "_satis"] = s;
        });
        if (v.gram_satis === null) throw new Error("Gram altın fiyatı zorunlu");
        await PN.ekle("fiyatlar", v); KP.bildirim("Fiyatlar yayınlandı"); ciz();
      }));
      if (son[0]) {
        var yas = KP.saatOnce(son[0].guncelleme);
        el.appendChild(h("p", { class: yas > 24 ? "kp-uyari" : "note", text: "Son güncelleme: " + KP.zaman(son[0].guncelleme) + (yas > 24 ? " · 24 saatten eski; sitede 'eski fiyat' olarak işaretleniyor" + (yas > 168 ? " ve artık gösterilmiyor" : "") : "") }));
      }
      el.appendChild(f2);
      if (son.length) el.appendChild(h("details", null, h("summary", { text: "Son girilen fiyatlar" }),
        h("table", null, h("thead", null, h("tr", null, h("th", { text: "Zaman" }), h("th", { text: "Gram alış/satış" }), h("th", { text: "Durum" }))),
          h("tbody", null, son.map(function (s) {
            return h("tr", null, h("td", { text: KP.zaman(s.guncelleme) }), h("td", { text: KP.tl(s.gram_alis) + " / " + KP.tl(s.gram_satis) }),
              h("td", { text: s.durum === "gizlendi" ? "Gizlendi: " + (s.gizleme_nedeni || "") : "Yayında" }));
          })))));
      var gr = h("button", { type: "button", class: "ikincil", text: "Fiyat yayınlama iznini geri al" });
      gr.addEventListener("click", KP.islem(gr, async function () {
        if (!confirm("İzni geri alırsanız fiyatlarınız hemen yayından kalkar. Devam edilsin mi?")) return;
        await PN.rpc("fiyat_izni_geri_al"); KP.bildirim("İzin geri alındı"); ciz();
      }));
      el.appendChild(h("p", { class: "note" }, "İzin tarihi: " + KP.zaman(izin[0].verildi) + " "));
      el.appendChild(gr);
    }
  }

  async function fotoSekmesi(el) {
    var fotolar = await PN.sec("fotograflar", { select: "*", order: "olusturuldu.asc" });
    var aktif = fotolar.filter(function (f) { return f.durum !== "reddedildi"; }).length;
    el.appendChild(h("p", { class: "note", text: "Paketiniz: " + paket.ad + " · en fazla " + paket.foto_limit + " fotoğraf. Yüklenen fotoğraflar yönetici onayından sonra yayınlanır. Fotoğraflar yüklenmeden önce küçültülür ve konum bilgisi silinir." }));
    var liste = h("div", { class: "kp-foto-liste" }, fotolar.map(function (f) {
      var sil = h("button", { type: "button", class: "ikincil kucuk", text: "Sil" });
      sil.addEventListener("click", KP.islem(sil, async function () {
        if (!confirm("Fotoğraf silinsin mi?")) return;
        await PN.sil("fotograflar", { id: "eq." + f.id });
        try { await PN.depoSil([f.yol]); } catch (e) {}
        KP.bildirim("Silindi"); ciz();
      }));
      return h("figure", null, h("img", { src: PN.acikUrl(f.yol), alt: f.aciklama, loading: "lazy" }),
        h("figcaption", null, h("b", { text: { bekliyor: "Onay bekliyor", onayli: "Yayında", reddedildi: "Reddedildi" }[f.durum] }), " · ", f.aciklama, " ", sil));
    }));
    el.appendChild(liste);
    if (aktif >= paket.foto_limit) { el.appendChild(h("p", { class: "kp-uyari", text: "Fotoğraf sınırına ulaştınız. Yeni fotoğraf için önce birini silin." })); return; }
    var dosya = h("input", { type: "file", accept: "image/jpeg,image/png,image/webp", required: true });
    var tur = h("select", null, h("option", { value: "magaza", text: "Mağaza / vitrin" }), h("option", { value: "urun", text: "Ürün" }));
    var ac = h("input", { required: true, maxlength: "150", placeholder: "Ör. Dükkân vitrini" });
    var b = h("button", { type: "submit", text: "Fotoğrafı yükle" });
    var f = h("form", { class: "kp-form kp-kutu" }, h("h2", { text: "Fotoğraf ekle" }), alan("Fotoğraf", dosya), h("div", { class: "iki" }, alan("Tür", tur), alan("Kısa açıklama", ac)),
      h("p", { class: "note", text: "Yalnızca kendi işletmenize ait, insan yüzü ve kişisel bilgi içermeyen fotoğraflar yükleyin." }), b);
    f.addEventListener("submit", KP.islem(b, async function () {
      if (!dosya.files[0]) throw new Error("Fotoğraf seçin");
      if (ac.value.trim().length < 3) throw new Error("Kısa bir açıklama yazın");
      var blob = await KP.fotoHazirla(dosya.files[0]);
      var yol = isl.id + "/" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8) + ".jpg";
      await PN.yukle(yol, blob);
      try { await PN.ekle("fotograflar", { isletme_id: isl.id, yol: yol, tur: tur.value, aciklama: ac.value.trim(), sira: aktif }); }
      catch (e) { try { await PN.depoSil([yol]); } catch (x) {} throw e; }
      KP.bildirim("Yüklendi; yönetici onayından sonra yayınlanacak"); ciz();
    }));
    el.appendChild(f);
  }

  async function kampanyaSekmesi(el) {
    var k = await PN.sec("kampanyalar", { select: "*", order: "olusturuldu.desc" });
    var DUR = { bekliyor: "Onay bekliyor", yayinda: "Yayında", reddedildi: "Reddedildi", gizlendi: "Gizlendi" };
    el.appendChild(h("p", { class: "note", text: "Paketiniz aynı anda en fazla " + paket.kampanya_limit + " aktif kampanyaya izin verir. Kampanyalar yönetici onayından sonra yayınlanır; her düzenleme yeniden onaya düşer. Yanıltıcı ifadeler ('en ucuz', 'garanti kazanç' vb.) onaylanmaz." }));
    k.forEach(function (x) {
      var sil = h("button", { type: "button", class: "ikincil kucuk", text: "Sil" });
      sil.addEventListener("click", KP.islem(sil, async function () { if (!confirm("Kampanya silinsin mi?")) return; await PN.sil("kampanyalar", { id: "eq." + x.id }); ciz(); }));
      el.appendChild(h("div", { class: "kp-kutu" }, h("b", { text: x.baslik }), h("p", { text: x.aciklama }),
        h("p", { class: "note", text: DUR[x.durum] + " · " + x.baslangic + " – " + x.bitis + (x.yonetici_notu ? " · Not: " + x.yonetici_notu : "") }), sil));
    });
    var bugun = new Date().toISOString().slice(0, 10);
    var bas = h("input", { type: "text", maxlength: "80", required: true }), ac = h("textarea", { maxlength: "500", rows: "3", required: true });
    var t1 = h("input", { type: "date", value: bugun, min: bugun, required: true }), t2 = h("input", { type: "date", required: true, min: bugun });
    var b = h("button", { type: "submit", text: "Kampanyayı onaya gönder" });
    var f = h("form", { class: "kp-form kp-kutu" }, h("h2", { text: "Yeni kampanya" }), alan("Başlık", bas), alan("Açıklama", ac),
      h("div", { class: "iki" }, alan("Başlangıç", t1), alan("Bitiş (en fazla 60 gün)", t2)), b);
    f.addEventListener("submit", KP.islem(b, async function () {
      await PN.ekle("kampanyalar", { isletme_id: isl.id, baslik: bas.value.trim(), aciklama: ac.value.trim(), baslangic: t1.value, bitis: t2.value });
      KP.bildirim("Kampanya onaya gönderildi"); ciz();
    }));
    el.appendChild(f);
  }

  async function istatistikSekmesi(el) {
    var once = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
    var r = await PN.sec("etkinlik_gunluk", { select: "gun,tur,adet", gun: "gte." + once, order: "gun.desc" });
    var TUR = [["profil", "Profil görüntülenme"], ["ara", "Ara düğmesi"], ["whatsapp", "WhatsApp düğmesi"], ["yol_tarifi", "Yol tarifi"]];
    var g7 = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
    function top(t, gun) { return r.filter(function (x) { return x.tur === t && x.gun >= gun; }).reduce(function (a, x) { return a + x.adet; }, 0); }
    el.appendChild(h("table", null, h("thead", null, h("tr", null, h("th", { text: "" }), h("th", { text: "Son 7 gün" }), h("th", { text: "Son 30 gün" }))),
      h("tbody", null, TUR.map(function (t) { return h("tr", null, h("td", { text: t[1] }), h("td", { text: String(top(t[0], g7)) }), h("td", { text: String(top(t[0], once)) })); }))));
    el.appendChild(h("p", { class: "note", text: "Sayılar, sayfanızdaki düğmelere yapılan dokunuşları gösterir; gerçekleşen arama veya satış sayısı değildir. Ziyaretçilerin kişisel bilgisi (IP, konum vb.) tutulmaz." }));
  }

  function hesapSekmesi(el) {
    var sil = h("button", { type: "button", class: "ikincil", text: "Hesabımın ve işletme bilgilerimin silinmesini talep et" });
    sil.addEventListener("click", KP.islem(sil, async function () {
      if (!confirm("Silme talebi gönderilsin mi? İşletmeniz yayından kaldırılır ve bilgileriniz en geç 30 gün içinde silinir.")) return;
      await PN.rpc("silme_talep_et"); KP.bildirim("Talebiniz alındı"); await basla();
    }));
    el.appendChild(h("div", { class: "kp-kutu" }, h("h2", { text: "Hesap" }),
      h("p", null, "Paket: ", h("b", { text: paket ? paket.ad : isl.paket }), paket && paket.rozet ? " · Rozet: " + paket.rozet : ""),
      h("p", { class: "note", text: "Ücretli paketler henüz satışta değil; ödeme alınmıyor." }),
      h("p", null, h("a", { href: "/kuyumcu-pazari/panel-aydinlatma.html", text: "Aydınlatma metni" }), " · ", h("a", { href: "/kuyumcu-pazari/fiyat-izni.html", text: "Fiyat yayınlama izin metni" }), " · ", h("a", { href: "/kuyumcu-pazari/kurallar.html", text: "Kurallar" })),
      isl.silme_talebi ? null : sil));
  }
})();
