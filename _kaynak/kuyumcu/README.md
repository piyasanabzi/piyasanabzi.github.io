# Kuyumcu Pazarı veri biçimi

`isletmeler.json` içindeki her işletme, build sırasında (`python3 _kaynak/content.py`) doğrulanır.
Kurallara uymayan kayıt varsa build **hata verir ve hiçbir sayfa yazılmaz**.

Yalnızca şu koşulları sağlayan işletme yayınlanır:
- `yayinda: true`
- `dogrulama.durum == "dogrulandi"` (tarih ve en az iki doğrulama yöntemi ile)
- `paket` var olan ve `satista: true` olan bir paket

Fiyatlar yalnızca `fiyat_izni.verildi == true`, paket `fiyat_yayini: true` ve `fiyatlar.guncelleme` geçerli ise gösterilir.
Sayfada fiyat 24 saatten eskiyse uyarı, 7 günden eskiyse fiyat gizlenir.

```json
{
  "id": "kp-0001",
  "slug": "isletme-adi",
  "ad": "İşletme Adı",
  "il": "istanbul",                       // iller.json slug
  "ilce": "fatih",                        // iller.json ilçe slug
  "adres": "Açık adres",
  "telefon": "+902120000000",             // + ile başlayan uluslararası biçim
  "whatsapp": "+905000000000",            // isteğe bağlı
  "saatler": {"pzt": "09:00-19:00", "sal": "...", "car": "...", "per": "...", "cum": "...", "cmt": "...", "paz": "kapali"},
  "fotograflar": [{"dosya": "kuyumcu-pazari/foto/isletme-adi/1.jpg", "alt": "Vitrin"}],
  "dogrulama": {"durum": "dogrulandi", "tarih": "2026-12-01", "yontemler": ["vergi_levhasi", "telefon"]},
  "fiyat_izni": {"verildi": true, "tarih": "2026-12-01"},
  "fiyatlar": {"guncelleme": "2026-12-01T14:05:00+03:00",
               "gram": {"alis": 0, "satis": 0}, "ceyrek": {"alis": 0, "satis": 0},
               "yarim": {"alis": 0, "satis": 0}, "tam": {"alis": 0, "satis": 0}},
  "paket": "ucretsiz",
  "yayinda": true
}
```
Doğrulama yöntemleri: `vergi_levhasi`, `esnaf_sicil`, `oda_kaydi`, `telefon`, `yerinde_goruntulu`, `adres_ziyaret`.
