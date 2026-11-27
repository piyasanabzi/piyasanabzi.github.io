# kuyumcu-pazari/iller.json -> supabase/migrations/20261127000200_il_ilce.sql
import json, os
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(K, "kuyumcu-pazari", "iller.json"), encoding="utf-8"))
q = lambda x: "'" + x.replace("'", "''") + "'"
rows = [f"({q(i['slug'])},{q(i['ad'])},{q(z['slug'])},{q(z['ad'])})" for i in d["iller"] for z in i["ilceler"]]
out = ("-- 81 il / 973 ilçe (kaynak: kuyumcu-pazari/iller.json; supabase/il_ilce_uret.py ile üretildi)\n"
       "insert into public.ilceler (il_slug, il, ilce_slug, ilce) values\n" + ",\n".join(rows) + "\non conflict do nothing;\n")
open(os.path.join(K, "supabase", "migrations", "20261127000200_il_ilce.sql"), "w", encoding="utf-8").write(out)
print(len(rows), "ilçe")
