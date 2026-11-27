/* Piyasa Nabzı · küçük, bağımlılıksız Supabase istemcisi (Auth + REST + Storage).
   Yalnızca herkese açık "publishable" anahtar kullanılır; gizli anahtar asla tarayıcıya konmaz.
   Tüm yetki kontrolleri veritabanında (RLS) yapılır. */
(function () {
  "use strict";
  var C = window.PN_SUPA || {};
  var URL_ = (C.url || "").replace(/\/+$/, "");
  var KEY = C.key || "";
  var LS = "pn-kp-oturum";
  var BUCKET = "isletme-fotolari";
  var oturum = null, tazeleniyor = null;

  function oku() { try { oturum = JSON.parse(localStorage.getItem(LS) || "null"); } catch (e) { oturum = null; } }
  function yaz(o) {
    oturum = o || null;
    try { if (o) localStorage.setItem(LS, JSON.stringify(o)); else localStorage.removeItem(LS); } catch (e) {}
  }
  function oturumKur(v) {
    if (!v || !v.access_token) throw new Error("Oturum açılamadı");
    var exp = v.expires_at || (Math.floor(Date.now() / 1000) + (+v.expires_in || 3600));
    yaz({ access_token: v.access_token, refresh_token: v.refresh_token, expires_at: +exp, user: v.user || (oturum && oturum.user) || null });
  }
  function jwt(t) {
    try { return JSON.parse(decodeURIComponent(escape(atob(t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))))); } catch (e) { return {}; }
  }

  var CEVIRI = [
    [/rate limit|too many/i, "Çok fazla deneme yapıldı. Lütfen birkaç dakika sonra tekrar deneyin."],
    [/token has expired|invalid.*token|otp.*expired|otp_expired/i, "Kod geçersiz ya da süresi dolmuş. Yeni kod isteyin."],
    [/email address not authorized/i, "E-posta gönderimi henüz yapılandırılmadı. Site yöneticisine bildirin."],
    [/invalid.*email|unable to validate email/i, "E-posta adresi geçersiz."],
    [/signups not allowed/i, "Yeni kayıtlar şu an kapalı."],
    [/row-level security|permission denied|42501/i, "Bu işlem için yetkiniz yok."],
    [/violates check constraint/i, "Girilen bilgilerden biri geçersiz. Lütfen alanları kontrol edin."],
    [/violates foreign key.*(il|ilce)/i, "İl/ilçe seçimi geçersiz."],
    [/duplicate key/i, "Bu kayıt zaten var."],
    [/JWT expired/i, "Oturum süresi doldu. Lütfen tekrar giriş yapın."],
    [/Failed to fetch|NetworkError|Load failed/i, "Sunucuya ulaşılamadı. İnternet bağlantınızı kontrol edin."],
    [/invalid totp|invalid mfa|code.*invalid/i, "Doğrulama kodu hatalı."]
  ];
  function turkce(m) {
    m = String(m || "Bilinmeyen hata");
    for (var i = 0; i < CEVIRI.length; i++) if (CEVIRI[i][0].test(m)) return CEVIRI[i][1];
    return m;
  }

  async function istek(yol, o) {
    o = o || {};
    if (!KEY || !URL_) throw new Error("Sistem henüz bağlanmadı");
    var h = Object.assign({ apikey: KEY }, o.headers || {});
    if (o.auth !== false && oturum) { await tazeleGerekirse(); if (oturum) h.Authorization = "Bearer " + oturum.access_token; }
    var body = o.body;
    if (body !== undefined && !(typeof Blob !== "undefined" && body instanceof Blob)) { h["Content-Type"] = "application/json"; body = JSON.stringify(body); }
    var r;
    try { r = await fetch(URL_ + yol, { method: o.method || "GET", headers: h, body: body }); }
    catch (e) { throw new Error(turkce(e.message)); }
    var txt = await r.text(), veri = null;
    try { veri = txt ? JSON.parse(txt) : null; } catch (e) { veri = txt; }
    if (!r.ok) {
      if (r.status === 401 && oturum && o.auth !== false && !o._tekrar) {
        // süresi dolmuş erişim anahtarı: bir kez yenileyip tekrar dene
        try { await tazele(true); return istek(yol, Object.assign({}, o, { _tekrar: true })); } catch (e) {}
      }
      var m = veri && typeof veri === "object" ? (veri.msg || veri.message || veri.error_description || veri.error || veri.code) : veri;
      var err = new Error(turkce(m || ("HTTP " + r.status)));
      err.status = r.status; err.veri = veri; err.ham = m;
      throw err;
    }
    return veri;
  }

  async function tazele(zorla) {
    if (!oturum || !oturum.refresh_token) return;
    if (!zorla && oturum.expires_at - 60 > Date.now() / 1000) return;
    if (!tazeleniyor) {
      tazeleniyor = (async function () {
        try {
          var v = await istek("/auth/v1/token?grant_type=refresh_token", { method: "POST", auth: false, body: { refresh_token: oturum.refresh_token } });
          oturumKur(v);
        } catch (e) { yaz(null); throw e; }
        finally { tazeleniyor = null; }
      })();
    }
    return tazeleniyor;
  }
  function tazeleGerekirse() { return tazele(false); }

  // E-postadaki bağlantıyla dönüldüğünde (#access_token=... ya da #error=...)
  function adresiIsle() {
    var hsh = location.hash || "";
    if (hsh.indexOf("access_token=") < 0 && hsh.indexOf("error=") < 0) return null;
    var p = new URLSearchParams(hsh.slice(1));
    history.replaceState(null, "", location.pathname + location.search);
    if (p.get("error")) return turkce(p.get("error_description") || p.get("error"));
    oturumKur({ access_token: p.get("access_token"), refresh_token: p.get("refresh_token"), expires_at: p.get("expires_at"), expires_in: p.get("expires_in") });
    return null;
  }

  function q(o) {
    return Object.keys(o || {}).map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(o[k]); }).join("&");
  }

  oku();
  window.PN = {
    hazir: !!(KEY && URL_),
    turkce: turkce,
    adresiIsle: adresiIsle,
    oturum: function () { return oturum; },
    aal: function () { return oturum ? (jwt(oturum.access_token).aal || "aal1") : ""; },
    kodGonder: function (email, donus) {
      return istek("/auth/v1/otp?redirect_to=" + encodeURIComponent(donus || location.href.split("#")[0]),
        { method: "POST", auth: false, body: { email: email, create_user: true } });
    },
    kodDogrula: async function (email, kod) {
      var v = await istek("/auth/v1/verify", { method: "POST", auth: false, body: { type: "email", email: email, token: kod } });
      oturumKur(v); return v;
    },
    kullanici: async function () { var u = await istek("/auth/v1/user"); if (oturum) { oturum.user = u; yaz(oturum); } return u; },
    cikis: async function () { try { await istek("/auth/v1/logout?scope=local", { method: "POST" }); } catch (e) {} yaz(null); },
    // İki adımlı doğrulama (TOTP)
    totpOlustur: function () { return istek("/auth/v1/factors", { method: "POST", body: { factor_type: "totp", friendly_name: "Piyasa Nabzı yönetim " + Date.now() } }); },
    totpSil: function (id) { return istek("/auth/v1/factors/" + encodeURIComponent(id), { method: "DELETE" }); },
    totpDogrula: async function (id, kod) {
      var c = await istek("/auth/v1/factors/" + encodeURIComponent(id) + "/challenge", { method: "POST", body: {} });
      var v = await istek("/auth/v1/factors/" + encodeURIComponent(id) + "/verify", { method: "POST", body: { challenge_id: c.id, code: kod } });
      oturumKur(v); return v;
    },
    // Veritabanı (PostgREST)
    sec: function (tablo, sorgu) { return istek("/rest/v1/" + tablo + "?" + q(sorgu)); },
    ekle: function (tablo, veri) { return istek("/rest/v1/" + tablo, { method: "POST", body: veri, headers: { Prefer: "return=representation" } }); },
    guncelle: function (tablo, filtre, veri) { return istek("/rest/v1/" + tablo + "?" + q(filtre), { method: "PATCH", body: veri, headers: { Prefer: "return=representation" } }); },
    sil: function (tablo, filtre) { return istek("/rest/v1/" + tablo + "?" + q(filtre), { method: "DELETE", headers: { Prefer: "return=representation" } }); },
    rpc: function (ad, arg) { return istek("/rest/v1/rpc/" + ad, { method: "POST", body: arg || {} }); },
    // Fotoğraf deposu
    yukle: function (yol, blob) {
      return istek("/storage/v1/object/" + BUCKET + "/" + yol, { method: "POST", body: blob, headers: { "Content-Type": blob.type, "x-upsert": "false", "cache-control": "31536000" } });
    },
    depoSil: function (yollar) { return istek("/storage/v1/object/" + BUCKET, { method: "DELETE", body: { prefixes: yollar } }); },
    acikUrl: function (yol) { return URL_ + "/storage/v1/object/public/" + BUCKET + "/" + yol.split("/").map(encodeURIComponent).join("/"); }
  };
})();
