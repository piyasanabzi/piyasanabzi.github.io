"""Gerçek internet testi: geliştirme dalının kodu yerelde sunulur, veri kaynakları gerçek."""
import asyncio, json, re
from playwright.async_api import async_playwright
BASE="http://localhost:8765"
FAKE=["42,31","4.085,40","91.250","Önizleme"]
res=[]
def rec(n,ok,d=""): res.append((n,ok,d)); print(("GEÇTİ " if ok else "KALDI ")+n+(" — "+str(d)[:400] if d else ""),flush=True)
CARD="""(n)=>{ const c=[...document.querySelectorAll('.c')].find(e=>e.querySelector('.n span').textContent===n); if(!c) return null; return {p:c.querySelector('.p').textContent, ab:(c.querySelector('.ab')||{}).textContent||'', ch:c.querySelector('.ch').textContent, upd:c.querySelector('.upd').innerText.replace(/\\n/g,' | '), fb:c.classList.contains('fb'), eski:c.classList.contains('eski')}; }"""
BAN="(()=>{const b=document.getElementById('durum');return b.hidden?'':b.textContent})()"
NO_HAREM="(()=>{const RW=window.WebSocket; window.WebSocket=function(u,p){ if(String(u).includes('haremaltin')) throw new Error('engellendi'); return new RW(u,p); }; window.WebSocket.prototype=RW.prototype; Object.assign(window.WebSocket,RW);})();"
async def yeni(br,mobile=True,init=None):
    ctx=await br.new_context(viewport={"width":360,"height":740} if mobile else {"width":1200,"height":900},is_mobile=mobile,has_touch=mobile,locale="tr-TR",timezone_id="Europe/Istanbul",
        user_agent="Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36" if mobile else None)
    if init: await ctx.add_init_script(init)
    pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)[:200]))
    return ctx,pg,errs
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--autoplay-policy=no-user-gesture-required"])
        # 1) Normal (mobil, gerçek ağ)
        ctx,pg,errs=await yeni(br)
        await pg.goto(BASE+"/index.html"); await pg.wait_for_timeout(15000)
        for n in ["Gram altın","Çeyrek altın","Ons altın","Gram gümüş","Dolar","Euro","Sterlin","Japon yeni","Brent petrol","Bitcoin"]:
            c=await pg.evaluate(CARD,n); rec("Gerçek ağ / normal: "+n, c and c["p"]!="—", c)
        rec("Gerçek ağ / normal: uyarı şeridi", True, await pg.evaluate(BAN) or "(yok)")
        rec("Gerçek ağ / normal: canlı göstergesi", True, await pg.inner_text("#liveTxt"))
        rec("Gerçek ağ / normal: grafik", await pg.evaluate("document.querySelectorAll('#chart path').length")>=2, await pg.text_content("#cSrc"))
        t=await pg.inner_text("body"); rec("Gerçek ağ / normal: sahte değer yok", not [x for x in FAKE if x in t])
        rec("Gerçek ağ / normal: taşma yok", await pg.evaluate("document.documentElement.scrollWidth")<=360)
        rec("Gerçek ağ / normal: JS hatası yok", not errs, errs)
        await pg.screenshot(path="ss_normal.png")
        son=await pg.evaluate("(window.dispatchEvent(new Event('pagehide')), localStorage.getItem('pn-son'))")
        # 2) Aynı cihazda internet kesildi
        await ctx.set_offline(True); await pg.wait_for_timeout(2000)
        rec("Gerçek ağ / bağlantı kesildi: uyarı", "İnternet bağlantın yok" in await pg.evaluate(BAN), await pg.evaluate(BAN))
        rec("Gerçek ağ / bağlantı kesildi: gram", True, await pg.evaluate(CARD,"Gram altın"))
        await pg.reload(wait_until="domcontentloaded") if False else None
        await ctx.set_offline(False); await pg.wait_for_timeout(12000)
        rec("Gerçek ağ / bağlantı geri geldi: uyarı kalktı veya yedek etiketi", "İnternet" not in await pg.evaluate(BAN), await pg.evaluate(BAN) or "(yok)")
        await ctx.close()
        # 3) Tüm kaynaklar kapalı, önbellek var (aynı tarayıcı verisiyle)
        ctx,pg,errs=await yeni(br)
        await pg.goto(BASE+"/index.html"); await pg.evaluate("(s)=>localStorage.setItem('pn-son',s)",son)
        async def kes(route):
            if route.request.url.startswith(BASE): await route.continue_()
            else: await route.abort()
        await pg.route("**/*",kes); await ctx.add_init_script("(()=>{const RW=window.WebSocket; window.WebSocket=function(){ throw new Error('kapali'); };})();")
        await pg.reload(); await pg.wait_for_timeout(11000)
        g=await pg.evaluate(CARD,"Gram altın")
        rec("Gerçek ağ / kaynaklar kapalı + önbellek: son doğrulanmış", "Son doğrulanmış" in g["upd"] and g["eski"], g)
        rec("Gerçek ağ / kaynaklar kapalı + önbellek: uyarı", "son doğrulanmış" in await pg.evaluate(BAN), await pg.evaluate(BAN))
        rec("Gerçek ağ / kaynaklar kapalı: JS hatası yok", not errs, errs)
        await pg.screenshot(path="ss_onbellek.png"); await ctx.close()
        # 4) Harem engelli → yedek kaynak
        ctx,pg,errs=await yeni(br,init=NO_HAREM)
        await pg.goto(BASE+"/index.html"); await pg.wait_for_timeout(15000)
        g=await pg.evaluate(CARD,"Gram altın"); u=await pg.evaluate(CARD,"Dolar"); b=await pg.evaluate(BAN)
        rec("Gerçek ağ / Harem yok: gram yedek kaynak + turuncu", g and g["fb"] and "Harem" not in g["upd"], g)
        rec("Gerçek ağ / Harem yok: dolar yedek kaynak", u and u["fb"], u)
        rec("Gerçek ağ / Harem yok: uyarı şeridi", "Harem" in b, b)
        rec("Gerçek ağ / Harem yok: JS hatası yok", not errs, errs)
        await pg.screenshot(path="ss_harem_yok.png"); await ctx.close()
        # 5) Yavaş 3G (CDP ağ kısıtlaması: 400 ms gecikme, ~50 KB/s)
        ctx,pg,errs=await yeni(br)
        cdp=await ctx.new_cdp_session(pg)
        await cdp.send("Network.enable"); await cdp.send("Network.emulateNetworkConditions",{"offline":False,"latency":2000,"downloadThroughput":50*1024,"uploadThroughput":20*1024})
        await pg.goto(BASE+"/index.html",wait_until="domcontentloaded",timeout=120000)
        await pg.wait_for_timeout(7000)
        t=await pg.inner_text("body"); rec("Gerçek ağ / yavaş 3G: 7. sn sahte değer yok", not [x for x in FAKE if x in t], (await pg.evaluate(CARD,"Gram altın")))
        await pg.wait_for_timeout(40000)
        g=await pg.evaluate(CARD,"Gram altın")
        rec("Gerçek ağ / yavaş 3G: sonunda gerçek fiyat", g and g["p"]!="—", g)
        rec("Gerçek ağ / yavaş 3G: uyarı", True, await pg.evaluate(BAN) or "(yok)")
        rec("Gerçek ağ / yavaş 3G: grafik", await pg.evaluate("document.querySelectorAll('#chart path').length")>=2, await pg.text_content("#cSrc"))
        rec("Gerçek ağ / yavaş 3G: JS hatası yok", not errs, errs)
        await pg.screenshot(path="ss_yavas.png"); await ctx.close()
        # 6) Kuyumcu ve geçmiş yatırım (gerçek ağ)
        ctx,pg,errs=await yeni(br)
        await pg.goto(BASE+"/kuyumcu-fiyat-hesaplama.html"); await pg.wait_for_timeout(12000)
        rec("Gerçek ağ / kuyumcu sayfası", "Canlı" in await pg.inner_text("#live"), (await pg.inner_text("#live")).replace("\n"," | "))
        await pg.goto(BASE+"/gecmis-yatirim.html"); await pg.wait_for_timeout(8000)
        rec("Gerçek ağ / geçmiş yatırım kaynak notu", "canlı" in await pg.inner_text("#src"), await pg.inner_text("#src"))
        rec("Gerçek ağ / diğer sayfalar JS hatası yok", not errs, errs)
        await ctx.close(); await br.close()
    json.dump(res,open("sonuc.json","w"),ensure_ascii=False,indent=1)
    print("TOPLAM",len(res),"GEÇTİ",sum(1 for r in res if r[1]))
asyncio.run(main())
