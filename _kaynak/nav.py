# Üst menü: tüm sayfalarda </header> sonrasına <!--nav-->...<!--/nav--> bloğu ekler/günceller.
# content.py sonunda çalışır; elle yazılmış sayfalara (index, gecmis-yatirim, kuyumcu...) da uygulanır.
import os, re, glob

MENU = [
    ("/", "Canlı fiyatlar"),
    ("/rehber/", "Rehberler"),
    ("/ekonomi-takvimi.html", "Ekonomi takvimi"),
    ("/kuyumcu-fiyat-hesaplama.html", "Kuyumcu hesabı"),
    ("/kuyumcu-pazari/", "Kuyumcu Pazarı"),
    ("/gecmis-yatirim.html", "Geçmiş yatırım"),
    ("/hakkimizda.html", "Hakkımızda"),
]
CSS = ("<style>.pn-nav{border-bottom:1px solid var(--line,#1f2b40);background:var(--bg,#0b111c)}"
       ".pn-nav .in{padding-top:8px;padding-bottom:8px;display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}"
       ".pn-nav .in::-webkit-scrollbar{display:none}"
       ".pn-nav a{flex:none;font:600 13.5px/1 Inter,system-ui,sans-serif;color:var(--muted,#8e9bb3);text-decoration:none;padding:9px 13px;border-radius:999px;border:1px solid var(--line,#1f2b40);background:var(--card,#121b2b);white-space:nowrap}"
       ".pn-nav a:hover{color:var(--ink,#eef2f8)}"
       ".pn-nav a[aria-current]{color:#1a1200;background:var(--gold,#f2c14e);border-color:var(--gold,#f2c14e)}"
       "@media (prefers-color-scheme: light){.pn-nav a[aria-current]{color:#fff}}</style>")


def _aktif(rel):
    rel = rel.replace(os.sep, "/")
    if rel == "index.html": return "/"
    if rel.startswith("rehber/"): return "/rehber/"
    if rel.startswith("kuyumcu-pazari/"): return "/kuyumcu-pazari/"
    return "/" + rel


def nav_html(rel):
    a = _aktif(rel)
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == a else ""}>{t}</a>' for h, t in MENU)
    return f'<!--nav-->{CSS}<nav class="pn-nav" aria-label="Site menüsü"><div class="wrap in">{links}</div></nav><!--/nav-->'


def uygula(root):
    n = 0
    for p in sorted(glob.glob(os.path.join(root, "*.html")) + glob.glob(os.path.join(root, "rehber", "*.html")) + glob.glob(os.path.join(root, "kuyumcu-pazari", "**", "*.html"), recursive=True)):
        rel = os.path.relpath(p, root)
        if os.path.basename(p).startswith("google"): continue
        s = open(p, encoding="utf-8").read()
        blok = nav_html(rel)
        if "<!--nav-->" in s:
            s2 = re.sub(r"<!--nav-->.*?<!--/nav-->", lambda m: blok, s, count=1, flags=re.S)
        elif "</header>" in s:
            s2 = s.replace("</header>", "</header>\n" + blok, 1)
        else:
            continue
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2); n += 1
    return n

if __name__ == "__main__":
    print(uygula(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sayfa güncellendi")
