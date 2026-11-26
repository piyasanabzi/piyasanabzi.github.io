import os,glob
__file__=os.path.abspath(__file__) if "__file__" in dir() else os.path.abspath("content.py")
HERE=os.path.dirname(__file__)
exec(open(os.path.join(HERE,"build.py")).read())
K=0.9166
def g(x): return f"{x:.3f}".replace(".",",")
def h(x): return f"{x*K:.2f}".replace(".",",")
ARTS[:]=[
("ceyrek-altin-kac-gram","Çeyrek altın kaç gram? Yarım, tam ve Ata altın ağırlıkları","Çeyrek, yarım, tam, ikibuçukluk ve beşlik altının Darphane ağırlıkları, ziynet ve sikke farkı ve içindeki saf altın miktarı.","2026-11-20"),
("gram-altin-nasil-hesaplanir","Gram altın fiyatı nasıl hesaplanır?","Gram altın fiyatının ons altın ve dolar kurundan nasıl hesaplandığı, 22 ayar ve çeyrek altın için örnek hesaplar.","2026-11-20"),
("22-ayar-24-ayar-farki","22 ayar ve 24 ayar altın farkı nedir?","Ayar ve milyem nedir, 24, 22, 18 ve 14 ayar altında ne kadar saf altın bulunur, hangisi ne için kullanılır?","2026-11-20"),
("gram-altin-mi-ceyrek-altin-mi","Gram altın mı, çeyrek altın mı?","Gram altın ile çeyrek altını işçilik, alış-satış farkı, bozdurma kolaylığı ve kullanım amacı açısından karşılaştırıyoruz.","2026-11-20"),
("altin-alirken-dikkat-edilmesi-gerekenler","Altın alırken nelere dikkat edilmeli?","Fiziki altın alırken fatura, damga, ayar, alış-satış farkı, işçilik ve saklama konusunda bilmen gereken temel noktalar.","2026-11-20"),
]
coins=[("Çeyrek",1.754,1.804),("Yarım",3.508,3.608),("Tam (birlik)",7.016,7.216),("İkibuçukluk",17.54,18.04),("Beşlik",35.08,36.08)]
rows="".join(f"<tr><td>{n}</td><td>{g(z)} g</td><td>{g(s)} g</td></tr>" for n,z,s in coins)
rows2="".join(f"<tr><td>{n}</td><td>≈ {h(z)} g</td><td>≈ {h(s)} g</td></tr>" for n,z,s in coins)
A={}
A["ceyrek-altin-kac-gram"]=f"""
<p><b>Kısa cevap:</b> Darphane'nin bastığı çeyrek ziynet altın <b>1,754 gram</b>, çeyrek sikke (Ata) altın ise <b>1,804 gram</b> ağırlığındadır. Her ikisi de <b>22 ayardır</b>.</p>
<p>Türkiye'de cumhuriyet altınlarını yalnızca Darphane basar. Bu altınlar <b>ziynet</b> ve <b>sikke</b> olmak üzere iki grupta, beşer çeşit olarak üretilir: çeyrek, yarım, birlik (tam), ikibuçukluk ve beşlik. Yani toplam 10 farklı çap ve ağırlık vardır.</p>
<h2>Cumhuriyet altınlarının ağırlıkları</h2>
<table><tr><th>Çeşit</th><th>Ziynet</th><th>Sikke (Ata)</th></tr>{rows}</table>
<p class="note">Kaynak: Hazine ve Maliye Bakanlığı Darphane ve Damga Matbaası Genel Müdürlüğü, "Sorularla Cumhuriyet Altını".</p>
<h2>Ziynet ile sikke arasındaki fark</h2>
<p>Ziynet altınlar daha ince basılır ve genellikle takı olarak kullanılır; düğün, nişan ve doğum hediyelerinde takılan çeyrekler bu gruptandır. Sikke altınlar biraz daha ağırdır ve üzerlerinde Atatürk kabartması bulunur. Halk arasında <b>"Ata lira"</b> denilen altın, 7,216 gramlık birlik sikke altındır.</p>
<h2>Çeyrek altının içinde ne kadar saf altın var?</h2>
<p>22 ayar, altının yaklaşık %91,66'sının saf altın olduğu anlamına gelir (milyem olarak 916). Bu durumda her altının içindeki saf (24 ayar) altın miktarı yaklaşık olarak şöyledir:</p>
<table><tr><th>Çeşit</th><th>Ziynet</th><th>Sikke (Ata)</th></tr>{rows2}</table>
<p>Örneğin bir çeyrek ziynet altında yaklaşık 1,61 gram saf altın bulunur. Bu yüzden çeyrek altının fiyatı kabaca "gram altın fiyatı × 1,61" civarındadır. Kuyumcuda bunun üzerine bir miktar işçilik ve kâr payı eklenir.</p>
<h2>Eski tarihli ve yeni tarihli çeyrek farklı mı?</h2>
<p>Darphane'ye göre cumhuriyet altınlarının ayarı ve ağırlığı basım yılına göre değişmez. Piyasada "eski" ve "yeni" çeyrek için farklı fiyat görülebilir; bu fark altının kendisinden değil, kuyumcuların alım-satım tercihlerinden kaynaklanır.</p>
{CTA}
<p class="note">Bu yazı genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.</p>
"""
A["gram-altin-nasil-hesaplanir"]="""
<p><b>Kısa cevap:</b> Gram altın fiyatı, <b>ons altının dolar fiyatı × dolar/TL kuru ÷ 31,1035</b> formülüyle hesaplanır. Çünkü 1 ons altın 31,1035 gramdır.</p>
<h2>Formül</h2>
<div class="box"><b>Gram altın (TL) = Ons altın ($) × Dolar kuru (TL) ÷ 31,1035</b></div>
<p>Uluslararası piyasada altın, ons başına dolar olarak fiyatlanır. Türkiye'de ise alışveriş gram ve TL üzerinden yapılır. Bu yüzden gram altın iki şeye bağlıdır: dünyadaki ons fiyatına ve dolar kuruna. Ons sabit kalsa bile dolar yükselirse gram altın da yükselir.</p>
<h2>Örnek hesap</h2>
<p>Hesabı anlatmak için yuvarlak sayılar kullanalım (bunlar güncel fiyat değildir):</p>
<ul><li>Ons altın: 4.000 $</li><li>Dolar kuru: 50 TL</li></ul>
<p>4.000 × 50 = 200.000 TL (1 onsun TL fiyatı)<br>200.000 ÷ 31,1035 ≈ <b>6.430 TL</b> (1 gram 24 ayar altın)</p>
<h2>22 ayar ve çeyrek altın hesabı</h2>
<p>22 ayar altının yaklaşık %91,66'sı saf altındır. Bu yüzden:</p>
<ul><li><b>1 gram 22 ayar</b> ≈ gram altın × 0,9166 → örnekte ≈ 5.894 TL</li>
<li><b>Çeyrek ziynet (1,754 g)</b> ≈ gram altın × 1,754 × 0,9166 → örnekte ≈ 10.338 TL</li>
<li><b>14 ayar (585 milyem)</b> ≈ gram altın × 0,585</li></ul>
<h2>Kuyumcudaki fiyat neden farklı?</h2>
<p>Bu formül altının "ham" değerini verir. Kuyumcularda iki ek fark görürsün:</p>
<ul><li><b>Alış-satış farkı (makas):</b> Kuyumcunun senden alırken verdiği fiyat ile sana satarken istediği fiyat farklıdır.</li>
<li><b>İşçilik:</b> Bilezik, kolye gibi takılarda ve bazen sarrafiye altınlarda üretim maliyeti fiyata eklenir.</li></ul>
<p>Piyasa Nabzı'nda gram, çeyrek, yarım ve tam altın için piyasadaki <b>alış ve satış</b> fiyatlarını ayrı ayrı görebilirsin. Satış fiyatı ile bu formülle bulunan saf altın değeri arasındaki fark, sarrafiye işçiliği ve kuyumcunun payından kaynaklanır.</p>
""" + CTA + """<p class="note">Bu yazı genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.</p>"""
A["22-ayar-24-ayar-farki"]="""
<p><b>Kısa cevap:</b> 24 ayar altın neredeyse saftır (en az %99,5 altın). 22 ayar altının ise yaklaşık %91,6'sı altın, geri kalanı onu sertleştiren başka metallerdir.</p>
<h2>Ayar ve milyem ne demek?</h2>
<p><b>Ayar</b>, altının 24 parçasından kaçının saf altın olduğunu gösterir. 22 ayar, 24 parçanın 22'sinin altın olduğu anlamına gelir. <b>Milyem</b> ise aynı şeyi binde olarak ifade eder: 22 ayar = 916 milyem. Altının üzerindeki damgada genellikle milyem değeri yazar.</p>
<table><tr><th>Ayar</th><th>Milyem (damga)</th><th>Saf altın oranı</th><th>Yaygın kullanım</th></tr>
<tr><td>24 ayar</td><td>995 / 999,9</td><td>%99,5 – %99,99</td><td>Gram altın, külçe</td></tr>
<tr><td>22 ayar</td><td>916</td><td>≈ %91,6</td><td>Bilezik, çeyrek/yarım/tam</td></tr>
<tr><td>18 ayar</td><td>750</td><td>%75</td><td>Pırlanta ve mücevher</td></tr>
<tr><td>14 ayar</td><td>585</td><td>%58,5</td><td>Kolye, yüzük, küpe</td></tr>
<tr><td>8 ayar</td><td>333</td><td>≈ %33,3</td><td>Ucuz takılar</td></tr></table>
<h2>Hangisi ne için tercih edilir?</h2>
<p><b>24 ayar</b> çok yumuşak olduğu için takıya pek uygun değildir; daha çok birikim amaçlı gram ve külçe altın olarak satılır. <b>22 ayar</b> hem değerini korur hem de bilezik olarak takılabilecek kadar sağlamdır; Darphane'nin bastığı tüm cumhuriyet altınları da 22 ayardır. <b>14 ve 18 ayar</b> daha dayanıklıdır, ince işçilikli takılarda kullanılır ama içindeki altın oranı düşüktür.</p>
<h2>Fiyat farkı nasıl hesaplanır?</h2>
<p>Bir ayardaki altının değeri kabaca <b>gram altın fiyatı × milyem ÷ 1000</b> ile bulunur. Örneğin gram altın 6.000 TL ise 22 ayarın gramı ≈ 5.496 TL, 14 ayarın gramı ≈ 3.510 TL eder (işçilik hariç).</p>
<p>Ayrıntılı hesap için <a href="/rehber/gram-altin-nasil-hesaplanir.html">gram altın nasıl hesaplanır</a> yazımıza bakabilirsin.</p>
""" + CTA + """<p class="note">Bu yazı genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.</p>"""
A["gram-altin-mi-ceyrek-altin-mi"]="""
<p>Altın biriktirmek isteyenlerin en sık sorduğu sorulardan biri bu. Tek bir doğru cevap yok; ikisinin de farklı avantajları var. Aşağıda temel farkları özetledik.</p>
<table><tr><th></th><th>Gram altın</th><th>Çeyrek altın</th></tr>
<tr><td>Ayar</td><td>24 ayar (995 / 999,9)</td><td>22 ayar (916)</td></tr>
<tr><td>Ağırlık</td><td>1 g, 2,5 g, 5 g, 10 g…</td><td>1,754 g (ziynet)</td></tr>
<tr><td>İşçilik / ek maliyet</td><td>Genelde düşük</td><td>Genelde daha yüksek</td></tr>
<tr><td>Bozdurma</td><td>Kolay</td><td>Çok kolay, her kuyumcu alır</td></tr>
<tr><td>Hediye</td><td>Daha az geleneksel</td><td>Düğün, doğum vb. için klasik</td></tr></table>
<h2>Gram altının avantajları</h2>
<p>Gram altın 24 ayar olduğu için fiyatı doğrudan ons altına ve dolara bağlıdır, bu yüzden takibi kolaydır. Ambalajlı ve sertifikalı satılan gram altınlarda alış-satış farkı genelde çeyreğe göre daha düşüktür. Sadece birikim amacıyla alınıyorsa, aynı paraya daha fazla saf altın sahibi olmak mümkün olabilir.</p>
<h2>Çeyrek altının avantajları</h2>
<p>Çeyrek altın Türkiye'de en çok tanınan altındır; neredeyse her kuyumcu kolayca alıp satar. Düğün, nişan ve doğum gibi günlerde hediye olarak verilmeye uygundur. Darphane güvencesiyle basıldığı için ağırlığı ve ayarı standarttır.</p>
<h2>Karşılaştırırken nelere bakmalı?</h2>
<p>En doğru karşılaştırma, <b>1 gram saf altın başına ödediğin parayı</b> hesaplamaktır. Çeyrek altının içinde yaklaşık 1,61 gram saf altın vardır. Kuyumcunun çeyrek satış fiyatını 1,61'e bölüp gram altın satış fiyatıyla karşılaştırırsan hangisinin o gün daha ucuza geldiğini görürsün. Satarken de aynı hesabı alış fiyatları için yapmak gerekir.</p>
""" + CTA + """<p class="note">Bu yazı genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir. Karar vermeden önce kendi durumunu değerlendirmeni öneririz.</p>"""
A["altin-alirken-dikkat-edilmesi-gerekenler"]="""
<p>Fiziki altın alırken birkaç basit kontrol, hem fazla para ödemeni hem de sahte ürünle karşılaşmanı önleyebilir. İşte dikkat etmen gereken temel noktalar:</p>
<h2>1. Güvenilir bir yerden al ve fatura iste</h2>
<p>Altını bilinen bir kuyumcudan veya kurumdan almak ve mutlaka <b>fatura</b> istemek en önemli adımdır. Faturada ürünün cinsi, ayarı, gramı ve fiyatı yazmalıdır. İleride satarken ya da bir sorun yaşadığında bu belge işine yarar.</p>
<h2>2. Ayarı ve damgayı kontrol et</h2>
<p>Altının üzerinde ayarını gösteren damga bulunur: 22 ayar için 916, 14 ayar için 585 gibi. Gram altınlar genellikle üzerinde gramı, ayarı ve seri numarası yazan sertifikalı bir ambalajla satılır. Ambalajı açılmamış gram altın, satarken daha kolay kabul görür.</p>
<h2>3. Alış ve satış fiyatı arasındaki farka bak</h2>
<p>Kuyumcunun satış fiyatı ile alış fiyatı arasında her zaman bir fark vardır. Altını kısa süre içinde geri satarsan bu fark yüzünden zarar edebilirsin. Farklı yerlerdeki makası karşılaştırmak faydalıdır.</p>
<h2>4. İşçilik ücretini sor</h2>
<p>Bilezik, kolye gibi takılarda fiyata işçilik eklenir ve bu kısım satarken genellikle geri alınmaz. Sadece birikim amaçlıyorsan, işçiliği düşük ürünler (gram altın, sarrafiye) daha mantıklı olabilir.</p>
<h2>5. Tartıyı ve gramı kontrol et</h2>
<p>Özellikle takı alırken ürünün senin önünde tartılmasını iste. Cumhuriyet altınlarının standart ağırlıklarını <a href="/rehber/ceyrek-altin-kac-gram.html">çeyrek altın kaç gram</a> yazımızda bulabilirsin.</p>
<h2>6. Piyasa fiyatını önceden öğren</h2>
<p>Kuyumcuya gitmeden önce gram ve çeyrek altının o anki fiyatına bakmak, sana teklif edilen fiyatın makul olup olmadığını anlamanı sağlar.</p>
<h2>7. Saklamayı düşün</h2>
<p>Evde saklanan altın hırsızlık ve kaybolma riski taşır. Tutarı yüksekse güvenli saklama seçeneklerini araştırmak iyi olur.</p>
""" + CTA + """<p class="note">Bu yazı genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir.</p>"""
for _f in sorted(glob.glob(os.path.join(HERE,"yazilar","*.py"))): exec(open(_f).read())
exec(open(os.path.join(HERE,"gorseller.py")).read())
LM={SITE+"/":max(a[3] for a in ARTS)}
urls=[SITE+"/"]
for s,t,d,dt in ARTS:
    u=page(f"rehber/{s}.html",t,d,gorsel_ekle(s,A[s])+more(s),crumb='<a href="/rehber/">Rehberler</a>',date=dt); urls.append(u); LM[u]=dt
lst="".join(f'<a href="/rehber/{s}.html">{t}<div class="note" style="font-weight:400;margin-top:4px">{d}</div></a>' for s,t,d,_ in ARTS[::-1])
urls.append(page("rehber/index.html","Altın ve piyasa rehberleri","Çeyrek altın kaç gram, gram altın nasıl hesaplanır, ayar farkları ve altın alırken dikkat edilmesi gerekenler.",
 '<p>Altın ve piyasalarla ilgili sık sorulan soruları sade bir dille anlattığımız yazılar:</p><div class="more">'+lst+'</div>',crumb="Rehberler",article=False))
urls.append(page("hakkimizda.html","Hakkımızda","Piyasa Nabzı nedir, fiyatlar nereden gelir ve nasıl hesaplanır?","""
<p><b>Piyasa Nabzı</b>, altın, gümüş, döviz, petrol ve bitcoin fiyatlarını tek sayfada, anlık olarak takip edebilmen için hazırlanmış ücretsiz bir sitedir.</p>
<h2>Neler sunuyoruz?</h2>
<ul><li>Gram, çeyrek, yarım, tam ve Cumhuriyet altını, ons altın ve gümüş fiyatları</li>
<li>Dolar, euro ve euro/dolar kurları</li><li>Brent ve WTI petrol, bitcoin fiyatları</li>
<li>Son 24 saat ve 7 günlük grafikler, altın hesaplayıcı</li>
<li><a href="/gecmis-yatirim.html">Geçmiş yatırım hesaplayıcısı</a>: geçmişte altın, dolar, euro ya da bitcoin alsaydın bugün ne olurdu?</li>
<li><a href="/kuyumcu-fiyat-hesaplama.html">Kuyumcu fiyatı hesaplama</a>: kuyumcunun fiyatındaki işçilik ve farkı gör</li>
<li>Seçtiğin fiyat hedefe ulaşınca haber veren fiyat alarmı</li>
<li>Giriş yaparak varlıklarını ve borçlarını ekleyip kâr/zarar durumunu görebileceğin bir takip bölümü</li></ul>
<h2>Fiyatlar nereden geliyor?</h2>
<p>Gram, çeyrek, yarım, tam ve Cumhuriyet altını ile gümüşün piyasadaki <b>alış ve satış</b> fiyatları ile dolar ve euro kuru Kapalıçarşı'dan, Harem Altın'ın canlı fiyat yayını (haremaltin.com) üzerinden anlık alınır; bu yayına ulaşılamazsa finans.truncgil.com kullanılır. Ons altın xaus.com, döviz ve bitcoin Binance, petrol fiyatları OilPriceAPI üzerinden gelir. Piyasa verisi geçici olarak alınamazsa çeyrek, yarım ve tam altın değerleri Darphane'nin açıkladığı ağırlık ve ayar bilgileriyle hesaplanır ve sitede "tahmini" olarak işaretlenir.</p>
<h2>Önemli not</h2>
<p>Sitedeki fiyatlar bilgilendirme amaçlıdır ve kuyumcu ya da bankalardaki fiyatlardan farklı olabilir. Hiçbir içerik yatırım tavsiyesi değildir. Alım-satım kararlarını kendi değerlendirmenle vermelisin.</p>
<p>Ayrıca altınla ilgili merak edilen konuları anlattığımız <a href="/rehber/">rehberlerimize</a> göz atabilirsin.</p>""",article=False))
urls.append(page("gizlilik.html","Gizlilik Politikası","Piyasa Nabzı'nın hangi verileri nasıl işlediği, çerezler ve üçüncü taraf hizmetler hakkında bilgi.","""
<p class="note">Son güncelleme: 24 Kasım 2026</p>
<p>Bu sayfa, <b>piyasanabzi.site</b> adresindeki Piyasa Nabzı sitesini kullandığında hangi bilgilerin nasıl işlendiğini açıklar.</p>
<h2>Hesap ve varlık bilgileri</h2>
<p>Sitede oluşturduğun hesap (kullanıcı adı ve şifrenin tek yönlü şifrelenmiş hali) ve eklediğin varlık/borç kayıtları <b>yalnızca kendi cihazının tarayıcısında</b> (localStorage) saklanır. Bu bilgiler bize ya da herhangi bir sunucuya gönderilmez; biz bu bilgileri göremeyiz. Tarayıcı verilerini sildiğinde bu kayıtlar da silinir ve başka bir cihazdan erişilemez.</p>
<h2>Fiyat verileri ve üçüncü taraf hizmetler</h2>
<p>Güncel fiyatları göstermek için tarayıcın doğrudan şu hizmetlere bağlanır: haremaltin.com ve finans.truncgil.com (piyasa alış-satış fiyatları), xaus.com (ons altın ve gümüş), Binance (döviz ve bitcoin) ve OilPriceAPI (petrol). Bu bağlantılar sırasında, internetin olağan işleyişi gereği IP adresin ve tarayıcı bilgilerin bu hizmetler tarafından görülebilir. Site, GitHub Pages üzerinde barındırılmaktadır; GitHub da teknik kayıt amacıyla benzer bilgileri işleyebilir.</p>
<h2>Çerezler ve reklamlar</h2>
<p>Sitede Google AdSense gibi üçüncü taraf reklam hizmetleri kullanılabilir. Google dahil üçüncü taraf sağlayıcılar, bu siteye ve diğer sitelere yaptığın önceki ziyaretlere dayalı reklamlar göstermek için çerezler kullanır. Google'ın reklam çerezlerini kullanması, Google ve iş ortaklarının sana bu siteye ve/veya internetteki diğer sitelere yaptığın ziyaretlere dayalı reklamlar sunmasını sağlar.</p>
<p>Kişiselleştirilmiş reklamları <a href="https://adssettings.google.com" rel="nofollow">Google Reklam Ayarları</a> sayfasından kapatabilirsin. Üçüncü taraf sağlayıcıların kişiselleştirilmiş reklam çerezlerini <a href="https://www.aboutads.info/choices" rel="nofollow">aboutads.info</a> adresinden de devre dışı bırakabilirsin. Google'ın verileri nasıl kullandığı hakkında bilgi için <a href="https://policies.google.com/technologies/partner-sites" rel="nofollow">bu sayfaya</a> bakabilirsin.</p>
<h2>Ziyaret istatistikleri</h2>
<p>Sitenin kaç kişi tarafından ziyaret edildiğini ve hangi sayfaların okunduğunu anlamak için <b>Google Analytics</b> kullanılmaktadır. Google Analytics çerezler aracılığıyla ziyaret süresi, görüntülenen sayfalar, yaklaşık konum (şehir/ülke), cihaz ve tarayıcı türü gibi bilgileri toplar. Bu bilgiler bize yalnızca toplu istatistik olarak gösterilir; adın, telefon numaran veya sitede kaydettiğin varlık bilgilerin Google Analytics'e gönderilmez. Google Analytics'in veri toplamasını <a href="https://tools.google.com/dlpage/gaoptout" rel="nofollow">Google Analytics Devre Dışı Bırakma Eklentisi</a> ile engelleyebilirsin. Ayrıca sitenin arama sonuçlarındaki performansını izlemek için Google Search Console kullanılmaktadır.</p>
<h2>Çocukların gizliliği</h2>
<p>Site 18 yaş altındaki kişilere yönelik değildir ve bilerek çocuklardan bilgi toplamaz.</p>
<h2>İletişim</h2>
<p>Bu politikayla ilgili sorularını <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a> adresine iletebilirsin.</p>
<h2>Değişiklikler</h2>
<p>Bu politika gerektiğinde güncellenebilir. Güncel hali her zaman bu sayfada yer alır.</p>""",article=False))
urls.append(page("iletisim.html","İletişim","Piyasa Nabzı ile iletişime geç: soru, öneri ve hata bildirimleri için e-posta adresimiz.","""
<p>Soruların, önerilerin ya da sitede gördüğün bir hata için bize e-posta gönderebilirsin:</p>
<div class="box gold" style="font-size:18px"><b>E-posta:</b> <a href="mailto:piyasanabzi.iletisim@gmail.com">piyasanabzi.iletisim@gmail.com</a></div>
<p>Mesajlarını genellikle birkaç gün içinde yanıtlamaya çalışıyoruz.</p>
<h2>Bize ne yazabilirsin?</h2>
<ul><li>Fiyatlarda gördüğün bir hata veya gecikme</li><li>Sitede görmek istediğin yeni bir özellik</li><li>Rehber yazılarıyla ilgili soru ve öneriler</li><li>Reklam ve iş birliği talepleri</li></ul>
<p class="note">Not: Kişisel yatırım tavsiyesi veremiyoruz. Hesabın ve varlık kayıtların yalnızca kendi cihazında saklandığı için, unutulan şifreleri sıfırlayamıyoruz.</p>""",article=False))
urls[1:1]=[SITE+"/gecmis-yatirim.html",SITE+"/kuyumcu-fiyat-hesaplama.html"]  # elle yazılmış sayfalar (gecmis verisi: _kaynak/gecmis_veri.py)
exec(open(os.path.join(HERE,"takvim.py")).read())  # ekonomi-takvimi.html + takvim.js
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f"  <url><loc>{u}</loc><lastmod>{LM.get(u,TODAY)}</lastmod></url>\n" for u in urls)+"</urlset>\n"
open(ROOT+"/sitemap.xml","w").write(sm)
print("\n".join(urls))

# --- ana sayfadaki rehber listesi (son 8 yazı) ---
import re as _re
def _short(t):
    i=[(t.index(ch),ch) for ch in "?:" if ch in t]
    if not i: return t
    k,ch=min(i); return t[:k+(1 if ch=="?" else 0)]
_links="\n".join(f'    <a href="/rehber/{a[0]}.html">{_short(a[1])}</a>' for a in ARTS[::-1][:8])+'\n    <a href="/rehber/" style="color:var(--gold)">Tüm rehberler →</a>'
_p=os.path.join(ROOT,"index.html"); _s=open(_p).read()
_s2=_re.sub(r'(<h2 id="rehberler">Rehberler</h2>\s*<div class="guides">).*?(\n  </div>)',lambda m:m.group(1)+"\n"+_links+m.group(2),_s,count=1,flags=_re.S)
assert _s2!=_s or _links in _s
open(_p,"w").write(_s2)
print(len(ARTS),"yazi;",len(urls),"url")

# --- üst menü (tüm sayfalar) ---
exec(open(os.path.join(HERE,"nav.py")).read().split('if __name__ == "__main__":')[0])
print("menü:", uygula(ROOT), "sayfa")
