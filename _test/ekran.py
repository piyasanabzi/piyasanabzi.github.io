"""Gerçek verilerle telefon ekran görüntüleri; görüntüler günlüğe base64 olarak yazılır."""
import asyncio, base64
from playwright.async_api import async_playwright
BASE="http://localhost:8765"
UA="Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
NO_HAREM="(()=>{const RW=window.WebSocket; window.WebSocket=function(u,p){ if(String(u).includes('haremaltin')) throw new Error('engellendi'); return new RW(u,p); }; window.WebSocket.prototype=RW.prototype; Object.assign(window.WebSocket,RW);})();"
def dok(ad, data):
    b=base64.b64encode(data).decode()
    print(f"=====RESIM {ad} {len(b)}")
    for i in range(0,len(b),8000): print("B64:"+b[i:i+8000])
    print(f"=====BITTI {ad}")
async def foto(pg, ad, y=None, el=None):
    if el: await pg.locator(el).scroll_into_view_if_needed(); await pg.evaluate(f"window.scrollBy(0,-70)")
    elif y is not None: await pg.evaluate(f"window.scrollTo(0,{y})")
    await pg.wait_for_timeout(700)
    dok(ad, await pg.screenshot(type="jpeg", quality=72))
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await br.new_context(viewport={"width":412,"height":915},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme="dark",locale="tr-TR",timezone_id="Europe/Istanbul",user_agent=UA)
        pg=await ctx.new_page()
        async def r(route):
            u=route.request.url
            if any(x in u for x in ("googlesyndication","googletagmanager","google-analytics","doubleclick")): await route.abort()
            else: await route.continue_()
        await pg.route("**/*",r)
        await pg.goto(BASE+"/index.html"); await pg.wait_for_timeout(16000)
        await foto(pg,"1_ust",0)
        await foto(pg,"2_altin",el="#gGold")
        await pg.evaluate("document.getElementById('gGold').scrollIntoView(); window.scrollBy(0,560)"); await pg.wait_for_timeout(500); dok("3_altin_devam", await pg.screenshot(type="jpeg",quality=72))
        await foto(pg,"4_doviz",el="#gFx")
        await foto(pg,"5_grafik",el="#chart")
        son=await pg.evaluate("(window.dispatchEvent(new Event('pagehide')), localStorage.getItem('pn-son'))")
        await ctx.close()
        # Harem bağlantısı yokken (son alınan Kapalıçarşı fiyatı + alternatif kaynak)
        ctx=await br.new_context(viewport={"width":412,"height":915},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme="dark",locale="tr-TR",timezone_id="Europe/Istanbul",user_agent=UA)
        await ctx.add_init_script(NO_HAREM)
        pg=await ctx.new_page(); await pg.route("**/*",r)
        await pg.goto(BASE+"/index.html"); await pg.evaluate("(s)=>localStorage.setItem('pn-son',s)",son); await pg.reload(); await pg.wait_for_timeout(15000)
        await foto(pg,"6_harem_kesik",0)
        await foto(pg,"7_harem_kesik_kartlar",el="#gGold")
        await ctx.close(); await br.close()
asyncio.run(main())
