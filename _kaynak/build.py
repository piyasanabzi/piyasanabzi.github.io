import os, html, datetime
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE="https://piyasanabzi.site"
TODAY="2026-11-20"
CSS="""
:root{--bg:#0b111c;--card:#121b2b;--ink:#eef2f8;--muted:#8e9bb3;--line:#1f2b40;--gold:#f2c14e;--blue:#60a5fa}
@media (prefers-color-scheme: light){:root{--bg:#f3f5f9;--card:#fff;--ink:#0f1a2b;--muted:#66748c;--line:#e3e8f0;--gold:#b7861b;--blue:#2563eb}}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;justify-content:space-between;height:60px;gap:10px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:19px;color:var(--ink);text-decoration:none}
.brand svg{width:34px;height:34px}
.btn{font-size:13px;font-weight:700;color:var(--ink);text-decoration:none;border:1px solid var(--line);background:var(--card);padding:8px 12px;border-radius:12px}
.crumb{font-size:13px;color:var(--muted);margin:18px 0 0}.crumb a{color:var(--muted)}
h1{font-size:clamp(24px,5vw,32px);margin:10px 0 8px;letter-spacing:-.02em;font-weight:800;line-height:1.2}
.meta{color:var(--muted);font-size:13px;margin-bottom:18px}
article{font-size:16.5px;line-height:1.7}
article h2{font-size:20px;margin:28px 0 8px;letter-spacing:-.01em}
article a{color:var(--blue)}
table{width:100%;border-collapse:collapse;margin:12px 0;background:var(--card);border-radius:14px;overflow:hidden;font-size:15px}
th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;font-variant-numeric:tabular-nums}
th{color:var(--muted);font-size:13px}
@media (max-width:480px){table{font-size:13.5px}th,td{padding:8px 7px;overflow-wrap:anywhere}th{font-size:12px}}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:18px 0}
.box.gold{border-color:color-mix(in srgb,var(--gold) 50%,var(--line))}
.cta{display:inline-block;background:var(--gold);color:#1a1200;font-weight:800;padding:12px 16px;border-radius:14px;text-decoration:none;margin:6px 0}
.more{display:grid;gap:8px;margin:10px 0 24px}.more a{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;color:var(--ink);text-decoration:none;font-weight:700}
.note{font-size:13px;color:var(--muted)}
footer{border-top:1px solid var(--line);margin-top:30px;padding:18px 0 40px;font-size:13px;color:var(--muted)}
footer a{color:var(--muted);margin-right:14px;display:inline-block;margin-bottom:6px}
"""
LOGO='<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#0e1726"/><path d="M10 40 L22 30 L32 36 L46 20 L54 24" fill="none" stroke="#f2c14e" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
FOOT='''<footer><div class="wrap">
<a href="/">Canlı fiyatlar</a><a href="/rehber/">Rehberler</a><a href="/ekonomi-takvimi.html">Ekonomi takvimi</a><a href="/hakkimizda.html">Hakkımızda</a><a href="/gizlilik.html">Gizlilik Politikası</a><a href="/iletisim.html">İletişim</a>
<div style="margin-top:8px">Bu sitedeki bilgiler genel bilgilendirme amaçlıdır, yatırım tavsiyesi değildir. © Piyasa Nabzı</div></div></footer>'''
ARTS=[]
def page(path,title,desc,body,crumb=None,article=True,date=TODAY):
    url=SITE+"/"+path.replace("index.html","")
    cr=""
    if crumb: cr='<div class="crumb"><a href="/">Ana sayfa</a> › '+crumb+'</div>'
    ld=""
    if article:
        ld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":%s,"datePublished":"%s","dateModified":"%s","author":{"@type":"Organization","name":"Piyasa Nabzı"},"publisher":{"@type":"Organization","name":"Piyasa Nabzı"},"mainEntityOfPage":"%s"}</script>'%(json_s(title),date,date,url)
    meta=f'<div class="meta">Piyasa Nabzı · Güncelleme: {fmt(date)}</div>' if article else ""
    h=f'''<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Piyasa Nabzı</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:site_name" content="Piyasa Nabzı">
<meta name="theme-color" content="#0b111c">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230e1726'/%3E%3Cpath d='M10 40 L22 30 L32 36 L46 20 L54 24' fill='none' stroke='%23f2c14e' stroke-width='6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>{CSS}</style>{ld}
<script async src="https://www.googletagmanager.com/gtag/js?id=G-M419M3965F"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","G-M419M3965F");gtag("config","G-LP1EQD8PHJ");</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4295900331301338" crossorigin="anonymous"></script>
</head><body>
<header><div class="wrap bar"><a class="brand" href="/">{LOGO}Piyasa Nabzı</a><a class="btn" href="/">Canlı fiyatlar</a></div></header>
<main class="wrap">{cr}<h1>{html.escape(title)}</h1>{meta}<article>{body}</article></main>
{FOOT}</body></html>'''
    p=os.path.join(ROOT,path); os.makedirs(os.path.dirname(p),exist_ok=True)
    open(p,"w").write(h)
    return url
def json_s(s):
    import json; return json.dumps(s,ensure_ascii=False)
def fmt(d):
    y,m,g=d.split("-"); ay=["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    return f"{int(g)} {ay[int(m)-1]} {y}"
CTA='<div class="box gold"><b>Güncel fiyatlar:</b> Gram, çeyrek, yarım ve tam altının anlık fiyatlarını ana sayfada saniye saniye takip edebilirsin.<br><a class="cta" href="/">Canlı altın fiyatlarına git →</a></div>'
def more(skip):
    return '<h2>Diğer rehberler</h2><div class="more">'+"".join(f'<a href="/rehber/{a[0]}.html">{a[1]}</a>' for a in ARTS[::-1] if a[0]!=skip)+'</div>'
