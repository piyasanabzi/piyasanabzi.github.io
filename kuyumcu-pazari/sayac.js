/* Kuyumcu profil sayfası: anonim etkileşim sayacı ve canlı fiyat kontrolü.
   Kişisel veri (IP, konum, çerez) gönderilmez; yalnızca "bu işletmenin sayfası açıldı / düğmesine dokunuldu" sayılır. */
(function () {
  "use strict";
  var C = window.PN_SUPA || {};
  if (!C.url || !C.key) return;
  var kutu = document.querySelector("[data-kp-id]");
  if (!kutu) return;
  var id = kutu.getAttribute("data-kp-id"), U = C.url.replace(/\/+$/, "");
  function say(t) {
    try {
      fetch(U + "/rest/v1/rpc/etkinlik_kaydet", { method: "POST", keepalive: true,
        headers: { apikey: C.key, "Content-Type": "application/json" }, body: JSON.stringify({ p_isletme: id, p_tur: t }) }).catch(function () {});
    } catch (e) {}
  }
  try { var k = "kp-g-" + id; if (!sessionStorage.getItem(k)) { sessionStorage.setItem(k, "1"); say("profil"); } } catch (e) { say("profil"); }
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest && e.target.closest("a[data-kp-say]");
    if (a) say(a.getAttribute("data-kp-say"));
  });

  // Sayfa saatlik üretilir; fiyat izni geri alındıysa ya da daha yeni fiyat girildiyse hemen yansıt
  var fb = document.getElementById("kpFiyatBlok");
  if (!fb) return;
  var TR2 = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var TR0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
  fetch(U + "/rest/v1/yayin_fiyatlar?select=*&isletme_id=eq." + encodeURIComponent(id), { headers: { apikey: C.key } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (r) {
      if (!r) return;
      var u = document.getElementById("kpEski"), tb = fb.querySelector("table");
      if (!r.length) {
        if (tb) tb.remove();
        u.hidden = false; u.textContent = "Bu işletmenin fiyatları şu an yayında değil. Güncel fiyat için işletmeyi arayabilirsin.";
        return;
      }
      var f = r[0];
      if (!tb || Date.parse(f.guncelleme) <= Date.parse(fb.getAttribute("data-guncelleme"))) return;
      ["gram", "ceyrek", "yarim", "tam"].forEach(function (k) {
        var tr = tb.querySelector('tr[data-tur="' + k + '"]'); if (!tr) return;
        var a = f[k + "_alis"], s = f[k + "_satis"], F = k === "gram" ? TR2 : TR0;
        if (a === null || s === null) { tr.hidden = true; return; }
        tr.hidden = false;
        tr.querySelector("[data-a]").textContent = "₺" + F.format(a);
        tr.querySelector("[data-s]").textContent = "₺" + F.format(s);
      });
      fb.setAttribute("data-guncelleme", f.guncelleme);
      var z = document.getElementById("kpFiyatZaman");
      if (z) z.textContent = new Date(f.guncelleme).toLocaleString("tr-TR", { timeZone: "Europe/Istanbul", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
      if (f.eski) { fb.classList.add("eski"); u.hidden = false; u.textContent = "Dikkat: bu fiyatlar 24 saatten eski; şu anki fiyat farklı olabilir."; }
      else { fb.classList.remove("eski"); u.hidden = true; }
    }).catch(function () {});
})();
