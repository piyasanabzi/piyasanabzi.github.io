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
