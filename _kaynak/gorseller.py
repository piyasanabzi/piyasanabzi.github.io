# Rehber yazıları için kendi çizdiğimiz SVG görseller (telifsiz). content.py tarafından exec edilir.
# Her görsel rehber/img/<slug>.svg olarak yazılır ve yazının ilk paragrafından sonra <figure> ile eklenir.
import os as _os
_IMG = _os.path.join(ROOT, "rehber", "img"); _os.makedirs(_IMG, exist_ok=True)
_W, _H = 600, 360
_BG, _CARD, _LINE, _INK, _MUT, _GOLD, _RED, _GRN, _BLUE = "#0e1626", "#16213a", "#26344f", "#eef2f8", "#93a1ba", "#f2c14e", "#ef4444", "#22c55e", "#60a5fa"
_F = 'font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"'

def _esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def _t(x, y, s, size=20, fill=_INK, w=600, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" {_F}>{_esc(s)}</text>'
def _svg(title, body, alt):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_W} {_H}" role="img" aria-label="{_esc(alt)}">'
            f'<rect x="1" y="1" width="{_W-2}" height="{_H-2}" rx="22" fill="{_BG}" stroke="{_LINE}" stroke-width="2"/>'
            + _t(26, 48, title, 25, _GOLD, 800) + body +
            _t(_W - 24, _H - 16, "piyasanabzi.site", 13, _MUT, 600, "end") + "</svg>")
def _num(v, d=0): return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _hbars(rows, maxv, color=_GOLD, x0=148, top=78, gap=52, bw=410):
    b = ""
    for i, (lab, v, txt) in enumerate(rows):
        y = top + i * gap; w = max(8, bw * v / maxv); inside = w > 130
        b += _t(x0 - 12, y + 26, lab, 21, _INK, 700, "end")
        b += f'<rect x="{x0}" y="{y}" width="{bw}" height="38" rx="10" fill="{_CARD}"/>'
        b += f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="38" rx="10" fill="{color}"/>'
        b += _t(x0 + w - 12 if inside else x0 + w + 10, y + 26, txt, 20, "#1a1200" if inside else _INK, 800, "end" if inside else "start")
    return b

def _box(x, y, w, h, title, lines, accent=_GOLD):
    b = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>'
    b += _t(x + 20, y + 44, title, 26, accent, 800)
    for i, l in enumerate(lines):
        b += f'<circle cx="{x+26}" cy="{y+87+i*48}" r="4" fill="{accent}"/>' + _t(x + 40, y + 94 + i * 48, l, 20, _INK, 600)
    return b

def _compare(a, b_, acc2=_GOLD):
    return _box(16, 72, 276, 256, a[0], a[1]) + _box(308, 72, 276, 256, b_[0], b_[1], acc2)

def _formula(boxes, ops, result):
    bw = 150; gap = 40; total = len(boxes) * bw + (len(boxes) - 1) * gap; x = (_W - total) / 2; y = 92; b = ""
    for i, (lab, val) in enumerate(boxes):
        b += f'<rect x="{x:.0f}" y="{y}" width="{bw}" height="112" rx="18" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>'
        b += _t(x + bw / 2, y + 44, lab, 20, _MUT, 700, "middle") + _t(x + bw / 2, y + 86, val, 26, _INK, 800, "middle")
        if i < len(boxes) - 1: b += _t(x + bw + gap / 2, y + 68, ops[i], 32, _GOLD, 800, "middle")
        x += bw + gap
    b += f'<rect x="{(_W-380)/2:.0f}" y="236" width="380" height="74" rx="18" fill="{_GOLD}"/>' + _t(_W / 2, 283, result, 28, "#1a1200", 800, "middle")
    return b

def _check(items):
    b = ""
    for i, a in enumerate(items):
        col, row = i % 2, i // 2; x = 16 + col * 292; y = 72 + row * 88
        b += f'<rect x="{x}" y="{y}" width="276" height="74" rx="16" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>'
        b += f'<circle cx="{x+38}" cy="{y+37}" r="19" fill="{_GOLD}"/><path d="M{x+29} {y+38} l6 6 l13 -14" fill="none" stroke="#1a1200" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        b += _t(x + 70, y + 45, a, 22, _INK, 800)
    return b

GORSEL = {}
def _g(slug, title, body, alt, cap):
    open(_os.path.join(_IMG, slug + ".svg"), "w", encoding="utf-8").write(_svg(title, body, alt))
    GORSEL[slug] = (alt, cap)

_g("ceyrek-altin-kac-gram", "Ziynet altınların ağırlığı",
   _hbars([("Çeyrek", 1.754, "1,754 g"), ("Yarım", 3.508, "3,508 g"), ("Tam", 7.016, "7,016 g"), ("İkibuçuk", 17.54, "17,54 g"), ("Beşlik", 35.08, "35,08 g")], 35.08),
   "Çeyrek, yarım, tam, ikibuçukluk ve beşlik ziynet altın ağırlıklarını gösteren çubuk grafik",
   "Darphane ziynet altın ağırlıkları. Hepsi 22 ayardır; sikke (Ata) altınlar biraz daha ağırdır.")
_g("22-ayar-24-ayar-farki", "Ayarlara göre saf altın oranı",
   _hbars([("24 ayar", 99.9, "%99,9"), ("22 ayar", 91.6, "%91,6"), ("18 ayar", 75, "%75"), ("14 ayar", 58.5, "%58,5"), ("8 ayar", 33.3, "%33,3")], 100),
   "24, 22, 18, 14 ve 8 ayar altındaki saf altın oranlarını gösteren grafik", "Ayar yükseldikçe altındaki saf altın oranı artar.")
_g("gram-altin-nasil-hesaplanir", "Gram altın formülü",
   _formula([("Ons altın", "$"), ("Dolar", "₺"), ("1 ons", "31,1035 g")], ["×", "÷"], "= Gram altın (₺)"),
   "Gram altın formülü: ons altın çarpı dolar kuru bölü 31,1035", "Gram altın = ons altın ($) × dolar kuru ÷ 31,1035. Ons ile dolar birlikte etkiler.")
_g("ons-altin-nedir", "1 ons kaç gram?",
   f'<circle cx="150" cy="200" r="96" fill="{_GOLD}"/>' + _t(150, 200, "1 ons", 38, "#1a1200", 800, "middle") + _t(150, 236, "troy ons", 20, "#1a1200", 700, "middle")
   + _t(290, 214, "=", 54, _INK, 800, "middle")
   + f'<rect x="340" y="124" width="236" height="152" rx="20" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>' + _t(458, 204, "31,1035", 44, _INK, 800, "middle") + _t(458, 246, "gram", 24, _MUT, 700, "middle"),
   "1 troy ons altının 31,1035 grama eşit olduğunu gösteren görsel", "Dünya piyasalarında altın, ons başına dolar olarak fiyatlanır.")
_g("gram-altin-mi-ceyrek-altin-mi", "Gram altın ve çeyrek altın",
   _compare(("Gram altın", ["24 ayar", "1, 5, 10 gram…", "Düşük işçilik", "Ons ve dolara bağlı"]), ("Çeyrek altın", ["22 ayar (916)", "1,754 gram", "≈1,61 g saf altın", "Hediye için klasik"])),
   "Gram altın ile çeyrek altının özelliklerini karşılaştıran iki kart", "Karşılaştırırken 1 gram saf altın başına ödediğin fiyata bak.")
_g("altin-alirken-dikkat-edilmesi-gerekenler", "Altın alırken kontrol listesi",
   _check(["Fatura al", "Damgaya bak", "Önünde tarttır", "Makası sor", "İşçiliği sor", "Fiyatı önceden bil"]),
   "Altın alırken kontrol edilmesi gereken altı madde", "Fatura, ayar damgası, tartı, alış-satış farkı, işçilik ve güncel fiyat.")
_lines = "".join(f'<line x1="300" y1="205" x2="{x}" y2="{y}" stroke="{_LINE}" stroke-width="3"/>' for x, y in [(110, 110), (490, 110), (110, 290), (490, 290)])
_g("dolar-kuru-neden-yukselir", "Dolar kurunu etkileyenler",
   _lines + f'<circle cx="300" cy="205" r="68" fill="{_GOLD}"/>' + _t(300, 200, "Dolar", 26, "#1a1200", 800, "middle") + _t(300, 230, "/ TL", 22, "#1a1200", 800, "middle")
   + "".join(f'<rect x="{x-95}" y="{y-27}" width="190" height="54" rx="16" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>' + _t(x, y + 8, s_, 21, _INK, 800, "middle") for x, y, s_ in [(110, 110, "Enflasyon"), (490, 110, "Faiz"), (110, 290, "Döviz talebi"), (490, 290, "Güven")]),
   "Dolar kurunu etkileyen temel etkenleri gösteren şema", "Enflasyon farkı, faiz, döviz talebi, güven ve küresel gelişmeler kuru birlikte etkiler.")
_g("gumus-nedir-gram-gumus", "Gram gümüş formülü",
   _formula([("Ons gümüş", "$"), ("Dolar", "₺"), ("1 ons", "31,1035 g")], ["×", "÷"], "= Gram gümüş (₺)"),
   "Gram gümüş formülü: ons gümüş çarpı dolar kuru bölü 31,1035", "Yatırımlık gümüş genelde 999, takı gümüşü genelde 925 ayardır.")
_g("bilezik-alirken-iscilik", "Bilezik fiyatı nasıl oluşur?",
   f'<rect x="24" y="96" width="420" height="96" rx="18" fill="{_GOLD}"/>' + _t(234, 140, "Altının değeri", 26, "#1a1200", 800, "middle") + _t(234, 172, "gram × 22 ayar fiyatı", 19, "#1a1200", 700, "middle")
   + _t(462, 154, "+", 34, _INK, 800, "middle")
   + f'<rect x="480" y="96" width="96" height="96" rx="18" fill="{_BLUE}"/>' + _t(528, 152, "İşçilik", 19, "#06122a", 800, "middle")
   + _t(24, 250, "Satarken genelde sadece", 23, _INK, 700) + _t(24, 284, "altının değeri ödenir.", 23, _INK, 700),
   "Bilezik fiyatının altın değeri ve işçilikten oluştuğunu gösteren görsel", "Bilezik fiyatı = altının değeri + işçilik. İşçilik oranı bilezik türüne göre değişir.")
_rw = [("2009", 50, "50"), ("2012", 25, "25"), ("2016", 12.5, "12,5"), ("2020", 6.25, "6,25"), ("2024", 3.125, "3,125")]
_g("bitcoin-nedir", "Bitcoin blok ödülü (halving)",
   "".join(f'<rect x="{40+i*110}" y="{300-v*4:.0f}" width="76" height="{v*4:.0f}" rx="10" fill="{_GOLD}"/>' + _t(78 + i * 110, 290 - v * 4, t_, 21, _INK, 800, "middle") + _t(78 + i * 110, 330, y, 19, _MUT, 700, "middle") for i, (y, v, t_) in enumerate(_rw)),
   "2009'dan 2024'e bitcoin blok ödülünün 50'den 3,125'e inişini gösteren grafik", "Her blokta üretilen yeni bitcoin yaklaşık 4 yılda bir yarıya iner; toplam arz en fazla 21 milyondur.")
_g("euro-dolar-paritesi-nedir", "Euro kuru nasıl oluşur?",
   _formula([("EUR/USD", "parite"), ("USD/TL", "dolar")], ["×"], "= Euro/TL"),
   "Euro kurunun euro/dolar paritesi ile dolar kurunun çarpımı olduğunu gösteren formül", "Örnek: parite 1,15 ve dolar 50 ₺ ise euro ≈ 57,50 ₺ (yuvarlak sayılar).")
_g("altin-hesabi-mi-fiziki-altin-mi", "Altın hesabı ve fiziki altın",
   _compare(("Altın hesabı", ["Anında al-sat", "Saklama derdi yok", "TMSF güvencesi", "Kambiyo vergisi"]), ("Fiziki altın", ["Elinde tutarsın", "Hediye ve takı", "Saklama riski", "Takıda işçilik"])),
   "Bankadaki altın hesabı ile fiziki altını karşılaştıran iki kart", "TMSF güvencesi limitlidir; alışta kambiyo vergisi kesilebilir.")
_g("enflasyon-nedir", "Enflasyon alım gücünü düşürür",
   f'<rect x="40" y="86" width="210" height="220" rx="18" fill="{_GOLD}"/>' + _t(145, 150, "Bugün", 24, "#1a1200", 700, "middle") + _t(145, 202, "1.000 ₺", 38, "#1a1200", 800, "middle") + _t(145, 246, "1 sepet", 24, "#1a1200", 700, "middle")
   + _t(300, 208, "→", 46, _INK, 800, "middle")
   + f'<rect x="350" y="86" width="210" height="220" rx="18" fill="{_CARD}" stroke="{_LINE}" stroke-width="2"/>'
   + f'<rect x="350" y="{86+220*0.23:.0f}" width="210" height="{220*0.77:.0f}" rx="18" fill="{_RED}"/>'
   + _t(455, 124, "1 yıl sonra", 21, _MUT, 700, "middle") + _t(455, 214, "≈ 0,77", 38, _INK, 800, "middle") + _t(455, 256, "sepet", 24, _INK, 700, "middle"),
   "Yüzde 30 enflasyonda 1000 liranın bir yıl sonra yaklaşık 0,77 sepet alabildiğini gösteren görsel", "Örnek: yıllık %30 enflasyonda bekleyen 1.000 ₺'nin alım gücü yaklaşık %23 azalır.")
_g("brent-ve-wti-petrol-farki", "Brent ve WTI",
   _compare(("Brent", ["Kuzey Denizi", "Avrupa, Türkiye", "Deniz yoluyla", "Genelde pahalı"]), ("WTI", ["ABD, Oklahoma", "ABD piyasası", "Hafif, tatlı", "Genelde ucuz"]), _BLUE),
   "Brent ve WTI petrolünü karşılaştıran iki kart", "Dünyadaki iki ana petrol fiyat referansı. İkisi genelde birlikte hareket eder.")

def gorsel_ekle(slug, html):
    if slug not in GORSEL: return html
    alt, cap = GORSEL[slug]
    fig = (f'<figure class="gorsel"><img src="/rehber/img/{slug}.svg" alt="{_esc(alt)}" width="{_W}" height="{_H}" loading="lazy" decoding="async">'
           f'<figcaption>{_esc(cap)}</figcaption></figure>')
    i = html.find("</p>")
    return html[:i + 4] + fig + html[i + 4:] if i >= 0 else fig + html
