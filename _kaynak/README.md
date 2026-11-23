# Piyasa Nabzı sayfa üreticisi

Rehber yazıları, Hakkımızda/Gizlilik/İletişim sayfaları, `rehber/index.html`, `sitemap.xml`
ve ana sayfadaki "Rehberler" listesi bu klasördeki betikle üretilir.

## Yeni yazı eklemek
1. `yazilar/` içine sıradaki numarayla yeni bir dosya ekle (ör. `03-konu.py`).
   Örnek için `yazilar/02-bilezik-bitcoin-parite.py` dosyasına bak:
   - `ARTS += [("slug","Başlık","Açıklama (meta description)","YYYY-AA-GG")]`
   - `A["slug"]="""<p>...</p>...""" + CTA + """<p class="note">... yatırım tavsiyesi değildir.</p>"""`
2. Depo kökünde çalıştır: `python3 _kaynak/content.py`
3. Mevcut slug'ları ve sayfa adreslerini asla değiştirme (Google sıralaması bozulur).
4. `index.html` içindeki canlı fiyat kodunu bu betik değiştirmez; yalnızca "Rehberler" listesini günceller.

## Geçmiş yatırım hesaplayıcısı (`gecmis-yatirim.html`)
Sayfa elle yazılmıştır; içindeki aylık geçmiş veri (`/*VERI*/ ... /*VERI_SON*/`) betikle güncellenir.
Ayda bir, depo kökünde çalıştır: `python3 _kaynak/gecmis_veri.py` (yeni biten ayı ekler).

## Piyasa gündemi
- **Haber başlıkları:** `.github/workflows/haberler.yml` her 30 dakikada `_kaynak/haberler.py`'yi çalıştırır ve sonucu `veri` dalına `haberler.json` olarak yazar. Ana sayfa bu dosyayı raw.githubusercontent.com'dan okur. Yalnızca başlık, kaynak, saat ve bağlantı saklanır.
- **Ekonomi takvimi:** tarihler `_kaynak/takvim.py` içindedir; `content.py` çalışınca `takvim.js` ve `ekonomi-takvimi.html` üretilir. Liste en geç Haziran 2027'de yeni tarihlerle güncellenmeli.

## Menü ve görseller
- `nav.py`: Tüm sayfalarda `</header>` sonrasına üst menü ekler (`<!--nav-->` blokları). Menü öğeleri `MENU` listesinde.
- `gorseller.py`: Her rehber için `rehber/img/<slug>.svg` görselini çizer ve yazının ilk paragrafından sonra ekler. Yeni yazıya görsel eklemek için `_g(...)` satırı ekle.
