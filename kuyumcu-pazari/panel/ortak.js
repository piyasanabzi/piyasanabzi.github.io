/* Kuyumcu paneli ve yönetim paneli için ortak arayüz yardımcıları.
   Kullanıcıdan gelen hiçbir metin innerHTML ile basılmaz; her şey textContent ile yazılır. */
(function () {
  "use strict";

  function h(etiket, oz) {
    var el = document.createElement(etiket);
    if (oz) Object.keys(oz).forEach(function (k) {
      var v = oz[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "on") Object.keys(v).forEach(function (o) { el.addEventListener(o, v[o]); });
      else if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k in el && typeof v !== "string") el[k] = v;
      else el.setAttribute(k, v === true ? "" : v);
    });
    for (var i = 2; i < arguments.length; i++) ekle(el, arguments[i]);
    return el;
  }
  function ekle(el, c) {
    if (c === null || c === undefined || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { ekle(el, x); }); return; }
    el.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  function bosalt(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }

  function bildirim(metin, tur) {
    var k = document.getElementById("kpBildirim");
    if (!k) { k = h("div", { id: "kpBildirim", role: "status", "aria-live": "polite" }); document.body.appendChild(k); }
    var b = h("div", { class: "kp-bil " + (tur || "ok"), text: metin });
    k.appendChild(b);
    setTimeout(function () { b.remove(); }, tur === "hata" ? 7000 : 3500);
  }

  // Bir düğmeye bağlı işlem: çift tıklamayı engeller, hatayı Türkçe gösterir
  function islem(btn, fn) {
    return async function (e) {
      if (e) e.preventDefault();
      if (btn.disabled) return;
      var eski = btn.textContent; btn.disabled = true; btn.textContent = "Lütfen bekleyin…";
      try { await fn(); } catch (err) { bildirim(err && err.message ? err.message : String(err), "hata"); }
      finally { btn.disabled = false; btn.textContent = eski; }
    };
  }

  var TL = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  function tl(n) { return n === null || n === undefined ? "—" : TL.format(+n) + " ₺"; }
  function zaman(s) {
    if (!s) return "—";
    return new Date(s).toLocaleString("tr-TR", { timeZone: "Europe/Istanbul", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }
  function saatOnce(s) { return (Date.now() - new Date(s).getTime()) / 3600000; }

  var ILLER = null;
  async function iller() {
    if (ILLER) return ILLER;
    var r = await fetch("/kuyumcu-pazari/iller.json"); ILLER = (await r.json()).iller; return ILLER;
  }
  // il + ilçe seçim kutuları
  async function ilIlceSec(ilDeger, ilceDeger) {
    var liste = await iller();
    var il = h("select", { name: "il", required: true }, h("option", { value: "", text: "İl seçin" }),
      liste.map(function (x) { return h("option", { value: x.slug, text: x.ad, selected: x.slug === ilDeger }); }));
    var ilce = h("select", { name: "ilce", required: true });
    function doldur(sec) {
      bosalt(ilce); ilce.appendChild(h("option", { value: "", text: "İlçe seçin" }));
      var x = liste.filter(function (i) { return i.slug === il.value; })[0];
      (x ? x.ilceler : []).forEach(function (z) { ilce.appendChild(h("option", { value: z.slug, text: z.ad, selected: z.slug === sec })); });
    }
    il.addEventListener("change", function () { doldur(""); });
    doldur(ilceDeger);
    return { il: il, ilce: ilce };
  }
  function ilAd(slug) { var x = (ILLER || []).filter(function (i) { return i.slug === slug; })[0]; return x ? x.ad : slug; }
  function ilceAd(il, slug) {
    var x = (ILLER || []).filter(function (i) { return i.slug === il; })[0];
    var z = x && x.ilceler.filter(function (i) { return i.slug === slug; })[0];
    return z ? z.ad : slug;
  }

  var GUNLER = [["pzt", "Pazartesi"], ["sal", "Salı"], ["car", "Çarşamba"], ["per", "Perşembe"], ["cum", "Cuma"], ["cmt", "Cumartesi"], ["paz", "Pazar"]];
  // Çalışma saatleri düzenleyici: her gün için açılış-kapanış ya da kapalı
  function saatEditoru(deger) {
    deger = deger || {};
    var satirlar = GUNLER.map(function (g) {
      var v = deger[g[0]] || (g[0] === "paz" ? "kapali" : "09:00-19:00");
      var kapali = v === "kapali";
      var ac = h("input", { type: "time", value: kapali ? "09:00" : v.slice(0, 5), "aria-label": g[1] + " açılış" });
      var kp = h("input", { type: "time", value: kapali ? "19:00" : v.slice(6, 11), "aria-label": g[1] + " kapanış" });
      var cb = h("input", { type: "checkbox", checked: kapali });
      function d() { ac.disabled = kp.disabled = cb.checked; }
      cb.addEventListener("change", d); d();
      return { g: g, ac: ac, kp: kp, cb: cb, el: h("div", { class: "kp-saat" }, h("b", { text: g[1] }), ac, h("span", { text: "–" }), kp, h("label", null, cb, " Kapalı")) };
    });
    return {
      el: h("div", { class: "kp-saatler" }, satirlar.map(function (s) { return s.el; })),
      deger: function () {
        var o = {};
        satirlar.forEach(function (s) {
          if (s.cb.checked) { o[s.g[0]] = "kapali"; return; }
          if (!s.ac.value || !s.kp.value || s.ac.value >= s.kp.value) throw new Error(s.g[1] + ": açılış saati kapanıştan önce olmalı (gece yarısını aşan saat desteklenmez)");
          o[s.g[0]] = s.ac.value + "-" + s.kp.value;
        });
        return o;
      }
    };
  }

  function tel(v) {
    v = String(v || "").replace(/[\s()-]/g, "");
    if (!v) return null;
    if (/^0\d{10}$/.test(v)) v = "+9" + v;
    else if (/^90\d{10}$/.test(v)) v = "+" + v;
    else if (/^\d{10}$/.test(v)) v = "+90" + v;
    if (!/^\+90\d{10}$/.test(v)) throw new Error("Telefon numarası geçersiz (ör. 0242 555 00 00)");
    return v;
  }

  // Fotoğrafı tarayıcıda küçültür ve yeniden kodlar: EXIF/konum bilgisi silinir, boyut düşer
  function fotoHazirla(dosya) {
    return new Promise(function (ok, red) {
      if (!/^image\/(jpeg|png|webp)$/.test(dosya.type)) return red(new Error("Yalnızca JPG, PNG veya WEBP yükleyebilirsiniz"));
      if (dosya.size > 15 * 1024 * 1024) return red(new Error("Dosya çok büyük (en fazla 15 MB)"));
      var img = new Image(), u = URL.createObjectURL(dosya);
      img.onload = function () {
        var M = 1600, w = img.naturalWidth, hh = img.naturalHeight, k = Math.min(1, M / Math.max(w, hh));
        var c = document.createElement("canvas"); c.width = Math.round(w * k); c.height = Math.round(hh * k);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(u);
        c.toBlob(function (b) {
          if (!b) return red(new Error("Fotoğraf işlenemedi"));
          if (b.size > 2 * 1024 * 1024) return red(new Error("Fotoğraf küçültüldükten sonra da 2 MB'tan büyük"));
          ok(b);
        }, "image/jpeg", 0.82);
      };
      img.onerror = function () { URL.revokeObjectURL(u); red(new Error("Fotoğraf okunamadı")); };
      img.src = u;
    });
  }

  // E-posta ile tek kullanımlık kodla giriş (şifre yok)
  function girisEkrani(kok, ayar) {
    bosalt(kok);
    var eposta = h("input", { type: "email", required: true, autocomplete: "email", placeholder: "ornek@eposta.com", name: "eposta" });
    var gonder = h("button", { type: "submit", text: "Giriş kodu gönder" });
    var f1 = h("form", { class: "kp-form" }, h("div", null, h("label", { text: "E-posta adresiniz" }), eposta), gonder,
      h("p", { class: "note", text: "Şifre kullanmıyoruz. E-posta adresinize tek kullanımlık bir giriş kodu ve bağlantı gönderilir. Hesabınız yoksa bu adımla oluşturulur ve e-posta adresiniz doğrulanmış olur." }));
    var kod = h("input", { type: "text", inputmode: "numeric", autocomplete: "one-time-code", pattern: "[0-9]{6,10}", maxlength: "10", required: true, name: "kod", placeholder: "123456" });
    var dogrula = h("button", { type: "submit", text: "Giriş yap" });
    var geri = h("button", { type: "button", class: "ikincil", text: "Farklı e-posta / kodu tekrar gönder" });
    var f2 = h("form", { class: "kp-form", hidden: true },
      h("p", { class: "kp-uyari", text: "E-postanıza gelen kodu girin ya da e-postadaki bağlantıya bu cihazda dokunun. Gelen kutusunda yoksa istenmeyen klasörüne bakın." }),
      h("div", null, h("label", { text: "Giriş kodu" }), kod), dogrula, geri);
    f1.addEventListener("submit", islem(gonder, async function () {
      var e = eposta.value.trim().toLowerCase();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) throw new Error("E-posta adresi geçersiz");
      await PN.kodGonder(e, location.href.split("#")[0]);
      f1.hidden = true; f2.hidden = false; kod.focus();
    }));
    f2.addEventListener("submit", islem(dogrula, async function () {
      var k = kod.value.replace(/\D/g, "");
      if (k.length < 6) throw new Error("Kodu eksiksiz girin");
      await PN.kodDogrula(eposta.value.trim().toLowerCase(), k);
      ayar.sonra();
    }));
    geri.addEventListener("click", function () { f2.hidden = true; f1.hidden = false; kod.value = ""; });
    kok.appendChild(h("div", { class: "kp-kutu" }, h("h2", { text: ayar.baslik }), ayar.aciklama ? h("p", { text: ayar.aciklama }) : null, f1, f2));
  }

  function baglantiYok(kok, ek) {
    bosalt(kok).appendChild(h("div", { class: "kp-bos" }, h("b", { text: "Panel henüz açılmadı" }),
      h("p", { text: "Kuyumcu Yönetim Sistemi hazırlık aşamasında; veritabanı bağlantısı henüz kurulmadı. Bu sayfada şu an hiçbir bilgi kaydedilmez." }),
      ek || null));
  }

  window.KP = { h: h, bosalt: bosalt, bildirim: bildirim, islem: islem, tl: tl, zaman: zaman, saatOnce: saatOnce,
    iller: iller, ilIlceSec: ilIlceSec, ilAd: ilAd, ilceAd: ilceAd, GUNLER: GUNLER, saatEditoru: saatEditoru,
    tel: tel, fotoHazirla: fotoHazirla, girisEkrani: girisEkrani, baglantiYok: baglantiYok,
    AYDINLATMA_SURUMU: "kp-panel-aydinlatma-2026-11-27", FIYAT_IZNI_SURUMU: "kp-fiyat-izni-2026-11-27" };
})();
