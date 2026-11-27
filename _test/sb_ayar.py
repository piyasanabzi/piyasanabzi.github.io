# Yerel test için Supabase yapılandırması (yalnızca test dalında). config.jsonc (CLI 3.x) ya da config.toml.
import json, os, re, sys

d = sys.argv[1]
AYAR = [
    (("auth", "site_url"), "http://127.0.0.1:8765"),
    (("auth", "additional_redirect_urls"), ["http://127.0.0.1:8765/**"]),
    (("auth", "rate_limit", "email_sent"), 1000),
    (("auth", "rate_limit", "token_verifications"), 1000),
    (("auth", "email", "enable_confirmations"), True),
    (("auth", "email", "max_frequency"), "1s"),
    (("auth", "mfa", "totp", "enroll_enabled"), True),
    (("auth", "mfa", "totp", "verify_enabled"), True),
]
for t in ("magic_link", "confirmation"):
    AYAR.append((("auth", "email", "template", t, "subject"), "Piyasa Nabzı giriş kodu"))
    AYAR.append((("auth", "email", "template", t, "content_path"), "./supabase/templates/giris-kodu.html"))


def yorumsuz(s):
    o, i, n, ic = [], 0, len(s), False
    while i < n:
        c = s[i]
        if ic:
            o.append(c)
            if c == "\\": o.append(s[i + 1]); i += 1
            elif c == '"': ic = False
        elif c == '"': ic = True; o.append(c)
        elif s.startswith("//", i): i = s.find("\n", i); i = n if i < 0 else i; continue
        elif s.startswith("/*", i): i = s.find("*/", i) + 2; continue
        else: o.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(o))


j = os.path.join(d, "config.jsonc")
if os.path.exists(j):
    c = json.loads(yorumsuz(open(j).read()))
    for yol, v in AYAR:
        x = c
        for k in yol[:-1]: x = x.setdefault(k, {})
        x[yol[-1]] = v
    open(j, "w").write(json.dumps(c, indent=2, ensure_ascii=False))
    print(json.dumps(c.get("auth", {}), indent=1, ensure_ascii=False)[:4000])
else:
    p = os.path.join(d, "config.toml"); s = open(p).read()
    for yol, v in AYAR:
        b, k = ".".join(yol[:-1]), yol[-1]
        val = json.dumps(v, ensure_ascii=False) if not isinstance(v, bool) else str(v).lower()
        m = re.search(r"(?ms)^\[" + re.escape(b) + r"\]\n(.*?)(?=^\[|\Z)", s)
        if not m: s += f"\n[{b}]\n{k} = {val}\n"; continue
        g = m.group(1)
        g = re.sub(rf"(?m)^#?\s*{k}\s*=.*$", f"{k} = {val}", g, count=1) if re.search(rf"(?m)^#?\s*{k}\s*=", g) else f"{k} = {val}\n" + g
        s = s[:m.start(1)] + g + s[m.end(1):]
    open(p, "w").write(s)
    print(s[:3000])
