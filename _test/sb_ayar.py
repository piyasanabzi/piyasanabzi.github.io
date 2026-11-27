# Yerel test için supabase/config.toml ayarları (yalnızca test dalında)
import re, sys
p = sys.argv[1]; s = open(p).read()
def bolum(ad, anahtar, deger):
    global s
    m = re.search(r"(?ms)^\[" + re.escape(ad) + r"\]\n(.*?)(?=^\[|\Z)", s)
    if not m: s += f"\n[{ad}]\n{anahtar} = {deger}\n"; return
    govde = m.group(1)
    if re.search(rf"(?m)^#?\s*{anahtar}\s*=.*$", govde): govde = re.sub(rf"(?m)^#?\s*{anahtar}\s*=.*$", f"{anahtar} = {deger}", govde, count=1)
    else: govde = f"{anahtar} = {deger}\n" + govde
    s = s[:m.start(1)] + govde + s[m.end(1):]
bolum("auth", "site_url", '"http://127.0.0.1:8765"')
bolum("auth", "additional_redirect_urls", '["http://127.0.0.1:8765/**"]')
bolum("auth.rate_limit", "email_sent", "1000")
bolum("auth.rate_limit", "token_verifications", "1000")
bolum("auth.email", "enable_confirmations", "true")
bolum("auth.email", "max_frequency", '"1s"')
bolum("auth.mfa.totp", "enroll_enabled", "true")
bolum("auth.mfa.totp", "verify_enabled", "true")
for t in ("magic_link", "confirmation"):
    bolum(f"auth.email.template.{t}", "subject", '"Piyasa Nabzı giriş kodu"')
    bolum(f"auth.email.template.{t}", "content_path", '"./supabase/templates/giris-kodu.html"')
open(p, "w").write(s)
print(re.sub(r"(?m)^\s*#.*\n", "", s)[:3000])
