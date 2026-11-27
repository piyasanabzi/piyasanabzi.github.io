-- Piyasa Nabzı · Kuyumcu Yönetim Sistemi · veritabanı şeması
-- Bu dosya Supabase SQL Editor'da bir kez çalıştırılır (ya da `supabase db push`).
-- Temel ilke: tarayıcıya hiçbir şeye güvenilmez. Her kural veritabanında (RLS, sütun yetkisi,
-- tetikleyici, kısıt) uygulanır. Herkese açık okuma yalnızca yayin_* görünümlerinden yapılır.

begin;

-- ───────────────────────── Ortak yardımcılar ─────────────────────────
create table public.yoneticiler (
  user_id   uuid primary key references auth.users(id) on delete cascade,
  eklendi   timestamptz not null default now()
);
comment on table public.yoneticiler is 'Site sahibi/yönetici hesapları. Yalnızca SQL Editor''dan eklenir.';

-- Yönetici: yoneticiler tablosunda ve iki adımlı doğrulama (TOTP) ile giriş yapmış (aal2) olmalı.
create function public.yonetici_mi() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.yoneticiler y where y.user_id = (select auth.uid()))
     and coalesce((select auth.jwt()) ->> 'aal', '') = 'aal2'
$$;

create table public.denetim_kaydi (
  id        uuid primary key default gen_random_uuid(),
  zaman     timestamptz not null default now(),
  kullanici uuid,
  islem     text not null,
  tablo     text not null,
  kayit_id  text,
  ayrinti   jsonb not null default '{}'::jsonb
);
create index on public.denetim_kaydi (zaman desc);

create function public._kaydet(p_islem text, p_tablo text, p_kayit text, p_ayrinti jsonb default '{}'::jsonb)
returns void language sql security definer set search_path = '' as $$
  insert into public.denetim_kaydi (kullanici, islem, tablo, kayit_id, ayrinti)
  values ((select auth.uid()), p_islem, p_tablo, p_kayit, coalesce(p_ayrinti, '{}'::jsonb))
$$;

create function public.saatler_gecerli(s jsonb) returns boolean
language sql immutable set search_path = '' as $$
  select jsonb_typeof(s) = 'object'
    and (select count(*) from jsonb_object_keys(s)) = 7
    and (select bool_and(k in ('pzt','sal','car','per','cum','cmt','paz')) from jsonb_object_keys(s) k)
    and (select bool_and(jsonb_typeof(v) = 'string' and (
          v #>> '{}' = 'kapali'
          or (v #>> '{}' ~ '^([01][0-9]|2[0-3]):[0-5][0-9]-([01][0-9]|2[0-3]):[0-5][0-9]$'
              and substr(v #>> '{}', 1, 5) < substr(v #>> '{}', 7, 5))))
         from jsonb_each(s) e(k, v))
$$;

-- ───────────────────────── Sabit tablolar ─────────────────────────
create table public.ilceler (
  il_slug   text not null,
  il        text not null,
  ilce_slug text not null,
  ilce      text not null,
  primary key (il_slug, ilce_slug)
);

create table public.paketler (
  kod            text primary key check (kod ~ '^[a-z0-9_]{2,30}$'),
  ad             text not null check (length(btrim(ad)) between 2 and 40),
  satista        boolean not null default false,
  foto_limit     int  not null check (foto_limit between 0 and 50),
  fiyat_yayini   boolean not null default true,
  kampanya_limit int  not null default 0 check (kampanya_limit between 0 and 20),
  istatistik     boolean not null default true,
  rozet          text check (rozet is null or length(rozet) between 2 and 30),
  one_cikan      boolean not null default false,
  aylik_ucret_tl numeric(10,2) check (aylik_ucret_tl is null or aylik_ucret_tl >= 0),
  guncellendi    timestamptz not null default now()
);
comment on column public.paketler.aylik_ucret_tl is 'Henüz ödeme sistemi yok; yalnızca bilgi amaçlı. Boş = karar verilmedi.';

insert into public.paketler (kod, ad, satista, foto_limit, fiyat_yayini, kampanya_limit, istatistik, rozet, one_cikan) values
  ('ucretsiz',    'Ücretsiz',    true,  3,  true, 1, true, null,          false),
  ('profesyonel', 'Profesyonel', false, 10, true, 3, true, 'Profesyonel', false),
  ('premium',     'Premium',     false, 20, true, 5, true, 'Premium',     true);

-- ───────────────────────── İşletmeler ─────────────────────────
create type public.isletme_durum as enum
  ('taslak', 'basvuru', 'inceleniyor', 'eksik_bilgi', 'onayli', 'reddedildi', 'askida');

create table public.isletmeler (
  id            uuid primary key default gen_random_uuid(),
  sahip_id      uuid not null unique default auth.uid() references auth.users(id) on delete restrict,
  slug          text unique check (slug is null or (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and length(slug) between 3 and 90)),
  ad            text not null check (length(btrim(ad)) between 2 and 120),
  yetkili_ad    text not null check (length(btrim(yetkili_ad)) between 2 and 120),
  il            text not null,
  ilce          text not null,
  adres         text not null check (length(btrim(adres)) between 5 and 300),
  telefon       text not null check (telefon ~ '^\+90[0-9]{10}$'),
  whatsapp      text check (whatsapp is null or whatsapp ~ '^\+90[0-9]{10}$'),
  eposta        text check (eposta is null or eposta ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  aciklama      text check (aciklama is null or length(aciklama) <= 1000),
  saatler       jsonb not null check (public.saatler_gecerli(saatler)),
  durum         public.isletme_durum not null default 'taslak',
  durum_notu    text check (durum_notu is null or length(durum_notu) <= 1000),
  paket         text not null default 'ucretsiz' references public.paketler(kod),
  bekleyen_degisiklik jsonb,
  silme_talebi  timestamptz,
  basvuru_at    timestamptz,
  dogrulandi_at timestamptz,
  dogrulayan    uuid,
  olusturuldu   timestamptz not null default now(),
  guncellendi   timestamptz not null default now(),
  foreign key (il, ilce) references public.ilceler (il_slug, ilce_slug)
);
create index on public.isletmeler (durum);
create index on public.isletmeler (il, ilce);

-- Kullanıcının kendi işletmesi (RLS içinde özyinelemeyi önlemek için security definer)
create function public.benim_isletmem() returns uuid
language sql stable security definer set search_path = '' as $$
  select id from public.isletmeler where sahip_id = (select auth.uid())
$$;
create function public.onayli_isletmem() returns uuid
language sql stable security definer set search_path = '' as $$
  select id from public.isletmeler where sahip_id = (select auth.uid()) and durum = 'onayli'
$$;

-- Onaydan sonra kamuya açık alanlar değişirse doğrudan yazılmaz; yönetici onayına bekletilir.
create function public._isletme_guncelle() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
  kritik text[] := array['ad','il','ilce','adres','telefon','whatsapp','aciklama'];
  k text; yeni jsonb := to_jsonb(new); eski jsonb := to_jsonb(old); bekleyen jsonb := coalesce(old.bekleyen_degisiklik, '{}'::jsonb);
  degisti boolean := false;
begin
  new.guncellendi := now();
  if public.yonetici_mi() or current_setting('pn.yonetici_islem', true) = '1' then
    return new;
  end if;
  if old.durum = 'inceleniyor' then
    foreach k in array kritik loop
      if (yeni -> k) is distinct from (eski -> k) then
        raise exception 'Başvuru incelenirken işletme bilgileri değiştirilemez' using errcode = 'P0001';
      end if;
    end loop;
  end if;
  if old.durum in ('onayli', 'askida') then
    foreach k in array kritik loop
      if (yeni -> k) is distinct from (eski -> k) then
        bekleyen := bekleyen || jsonb_build_object(k, yeni -> k);
        degisti := true;
      end if;
    end loop;
    if degisti then
      new := jsonb_populate_record(new, (eski - 'saatler' - 'eposta' - 'yetkili_ad' - 'guncellendi'));
      new.bekleyen_degisiklik := bekleyen;
      new.guncellendi := now();
      perform public._kaydet('degisiklik_onaya_gonderildi', 'isletmeler', old.id::text, bekleyen);
    end if;
  end if;
  return new;
end $$;
create trigger isletme_guncelle before update on public.isletmeler
  for each row execute function public._isletme_guncelle();

-- ───────────────────────── Doğrulama, onaylar, izinler ─────────────────────────
create table public.dogrulamalar (
  id           uuid primary key default gen_random_uuid(),
  isletme_id   uuid not null references public.isletmeler(id) on delete cascade,
  yontem       text not null check (yontem in ('vergi_levhasi','esnaf_sicil','oda_kaydi','telefon','yerinde_goruntulu','adres_ziyaret')),
  notlar       text check (notlar is null or length(notlar) <= 500),
  kontrol_eden uuid not null,
  zaman        timestamptz not null default now(),
  unique (isletme_id, yontem)
);
comment on table public.dogrulamalar is 'Belge kopyası SAKLANMAZ; yalnızca yöntem, tarih ve kısa not.';

create table public.onaylar (
  id      uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  tur     text not null check (tur in ('aydinlatma', 'beyan', 'fiyat_izni', 'fiyat_izni_geri')),
  surum   text not null check (length(surum) between 3 and 60),
  zaman   timestamptz not null default now()
);

create table public.fiyat_izinleri (
  id          uuid primary key default gen_random_uuid(),
  isletme_id  uuid not null references public.isletmeler(id) on delete cascade,
  metin_surumu text not null,
  verildi     timestamptz not null default now(),
  geri_alindi timestamptz
);
create unique index fiyat_izni_tek_aktif on public.fiyat_izinleri (isletme_id) where geri_alindi is null;

create function public.fiyat_izni_aktif(p_isletme uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.fiyat_izinleri where isletme_id = p_isletme and geri_alindi is null)
$$;

-- ───────────────────────── Fiyatlar ─────────────────────────
create function public.fiyat_cifti(a numeric, s numeric) returns boolean
language sql immutable set search_path = '' as $$
  select (a is null and s is null) or (a > 0 and s >= a and s <= a * 1.25)
$$;

create table public.fiyatlar (
  id           uuid primary key default gen_random_uuid(),
  isletme_id   uuid not null references public.isletmeler(id) on delete cascade,
  gram_alis    numeric(12,2), gram_satis   numeric(12,2),
  ceyrek_alis  numeric(12,2), ceyrek_satis numeric(12,2),
  yarim_alis   numeric(12,2), yarim_satis  numeric(12,2),
  tam_alis     numeric(12,2), tam_satis    numeric(12,2),
  guncelleme   timestamptz not null default now(),
  giren        uuid default auth.uid(),
  durum        text not null default 'yayinda' check (durum in ('yayinda', 'gizlendi')),
  gizleme_nedeni text check (gizleme_nedeni is null or length(gizleme_nedeni) <= 300),
  check (public.fiyat_cifti(gram_alis, gram_satis) and public.fiyat_cifti(ceyrek_alis, ceyrek_satis)
     and public.fiyat_cifti(yarim_alis, yarim_satis) and public.fiyat_cifti(tam_alis, tam_satis)),
  check (gram_satis is not null),
  check (gram_satis between 500 and 100000)
);
create index on public.fiyatlar (isletme_id, guncelleme desc);
create index on public.fiyatlar (guncelleme desc);

create function public._fiyat_ekle() returns trigger
language plpgsql security definer set search_path = '' as $$
declare son timestamptz; gunluk int;
begin
  if not public.fiyat_girebilir(new.isletme_id) then
    raise exception 'Bu işletme için fiyat girme izniniz yok (onaylı işletme ve aktif fiyat izni gerekli)' using errcode = '42501';
  end if;
  -- zaman, giren ve durum istemciden alınmaz
  new.guncelleme := now(); new.giren := auth.uid(); new.durum := 'yayinda'; new.gizleme_nedeni := null;
  select max(guncelleme), count(*) filter (where guncelleme > now() - interval '1 day')
    into son, gunluk from public.fiyatlar where isletme_id = new.isletme_id;
  if son is not null and son > now() - interval '60 seconds' then
    raise exception 'Fiyat en fazla dakikada bir güncellenebilir' using errcode = 'P0001';
  end if;
  if gunluk >= 200 then
    raise exception 'Günlük fiyat güncelleme sınırı (200) doldu' using errcode = 'P0001';
  end if;
  -- yazım hatalarını yakalayan oran kontrolleri (çeyrek ≈ 1,6 gram; yarım = 2 çeyrek; tam = 4 çeyrek)
  if new.ceyrek_satis is not null and not (new.ceyrek_satis / new.gram_satis between 1.4 and 1.9) then
    raise exception 'Çeyrek / gram oranı olağan dışı; lütfen fiyatları kontrol edin' using errcode = 'P0001';
  end if;
  if new.yarim_satis is not null and new.ceyrek_satis is not null and not (new.yarim_satis / new.ceyrek_satis between 1.85 and 2.15) then
    raise exception 'Yarım / çeyrek oranı olağan dışı; lütfen fiyatları kontrol edin' using errcode = 'P0001';
  end if;
  if new.tam_satis is not null and new.ceyrek_satis is not null and not (new.tam_satis / new.ceyrek_satis between 3.7 and 4.3) then
    raise exception 'Tam / çeyrek oranı olağan dışı; lütfen fiyatları kontrol edin' using errcode = 'P0001';
  end if;
  return new;
end $$;
create trigger fiyat_ekle before insert on public.fiyatlar
  for each row execute function public._fiyat_ekle();

create function public.fiyat_girebilir(p_isletme uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.isletmeler i join public.paketler p on p.kod = i.paket
    where i.id = p_isletme and i.sahip_id = (select auth.uid()) and i.durum = 'onayli' and p.fiyat_yayini
  ) and public.fiyat_izni_aktif(p_isletme)
$$;

-- ───────────────────────── Fotoğraflar ─────────────────────────
create table public.fotograflar (
  id          uuid primary key default gen_random_uuid(),
  isletme_id  uuid not null references public.isletmeler(id) on delete cascade,
  yol         text not null unique,
  tur         text not null check (tur in ('magaza', 'urun')),
  aciklama    text not null check (length(btrim(aciklama)) between 3 and 150),
  sira        int not null default 0 check (sira between 0 and 100),
  durum       text not null default 'bekliyor' check (durum in ('bekliyor', 'onayli', 'reddedildi')),
  olusturuldu timestamptz not null default now(),
  check (yol ~ '^[0-9a-f-]{36}/[a-z0-9_-]{1,60}\.(jpg|jpeg|png|webp)$')
);

create function public.foto_yukleyebilir(p_klasor text) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.isletmeler i join public.paketler p on p.kod = i.paket
    where i.sahip_id = (select auth.uid()) and i.durum = 'onayli' and i.id::text = p_klasor
      and (select count(*) from storage.objects o
           where o.bucket_id = 'isletme-fotolari' and (storage.foldername(o.name))[1] = p_klasor) < p.foto_limit
  )
$$;

create function public._foto_ekle() returns trigger
language plpgsql security definer set search_path = '' as $$
declare lim int; adet int;
begin
  new.durum := 'bekliyor';
  if split_part(new.yol, '/', 1) <> new.isletme_id::text then
    raise exception 'Fotoğraf yolu işletme klasöründe olmalı' using errcode = 'P0001';
  end if;
  select p.foto_limit into lim from public.isletmeler i join public.paketler p on p.kod = i.paket where i.id = new.isletme_id;
  select count(*) into adet from public.fotograflar where isletme_id = new.isletme_id and durum <> 'reddedildi';
  if adet >= lim then
    raise exception 'Paketinizin fotoğraf sınırı (%) doldu', lim using errcode = 'P0001';
  end if;
  return new;
end $$;
create trigger foto_ekle before insert on public.fotograflar
  for each row execute function public._foto_ekle();

-- ───────────────────────── Kampanyalar ─────────────────────────
create table public.kampanyalar (
  id          uuid primary key default gen_random_uuid(),
  isletme_id  uuid not null references public.isletmeler(id) on delete cascade,
  baslik      text not null check (length(btrim(baslik)) between 3 and 80),
  aciklama    text not null check (length(btrim(aciklama)) between 3 and 500),
  baslangic   date not null,
  bitis       date not null,
  durum       text not null default 'bekliyor' check (durum in ('bekliyor', 'yayinda', 'reddedildi', 'gizlendi')),
  yonetici_notu text,
  olusturuldu timestamptz not null default now(),
  check (bitis >= baslangic and bitis - baslangic <= 60)
);

create function public._kampanya() returns trigger
language plpgsql security definer set search_path = '' as $$
declare lim int; adet int;
begin
  if public.yonetici_mi() or current_setting('pn.yonetici_islem', true) = '1' then return new; end if;
  -- işletmenin her eklemesi/düzenlemesi yeniden yönetici onayına düşer
  new.durum := 'bekliyor'; new.yonetici_notu := null;
  if tg_op = 'INSERT' then
    if new.bitis < current_date then raise exception 'Bitiş tarihi geçmiş olamaz' using errcode = 'P0001'; end if;
    select p.kampanya_limit into lim from public.isletmeler i join public.paketler p on p.kod = i.paket where i.id = new.isletme_id;
    select count(*) into adet from public.kampanyalar
      where isletme_id = new.isletme_id and bitis >= current_date and durum in ('bekliyor', 'yayinda');
    if adet >= lim then
      raise exception 'Paketinizin aktif kampanya sınırı (%) doldu', lim using errcode = 'P0001';
    end if;
  end if;
  return new;
end $$;
create trigger kampanya before insert or update on public.kampanyalar
  for each row execute function public._kampanya();

-- ───────────────────────── İstatistik ─────────────────────────
create table public.etkinlik_gunluk (
  isletme_id uuid not null references public.isletmeler(id) on delete cascade,
  gun        date not null default current_date,
  tur        text not null check (tur in ('profil', 'ara', 'whatsapp', 'yol_tarifi')),
  adet       int not null default 0,
  primary key (isletme_id, gun, tur)
);

-- Herkese açık sayaç: yalnızca onaylı işletme için, tek seferde +1. Kişisel veri (IP vb.) tutulmaz.
create function public.etkinlik_kaydet(p_isletme uuid, p_tur text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_tur not in ('profil', 'ara', 'whatsapp', 'yol_tarifi') then return; end if;
  if not exists (select 1 from public.isletmeler where id = p_isletme and durum = 'onayli') then return; end if;
  insert into public.etkinlik_gunluk as e (isletme_id, gun, tur, adet) values (p_isletme, current_date, p_tur, 1)
  on conflict (isletme_id, gun, tur) do update set adet = least(e.adet + 1, 1000000);
end $$;

-- ───────────────────────── İşletme sahibi işlemleri (RPC) ─────────────────────────
create function public.basvuru_gonder(p_aydinlatma_surumu text, p_beyan boolean) returns void
language plpgsql security definer set search_path = '' as $$
declare i public.isletmeler;
begin
  select * into i from public.isletmeler where sahip_id = (select auth.uid());
  if i.id is null then raise exception 'Önce işletme bilgilerini kaydedin' using errcode = 'P0001'; end if;
  if i.durum not in ('taslak', 'eksik_bilgi') then raise exception 'Başvuru zaten gönderildi' using errcode = 'P0001'; end if;
  if p_beyan is not true or coalesce(length(p_aydinlatma_surumu), 0) < 3 then
    raise exception 'Aydınlatma metni ve beyan onayı gerekli' using errcode = 'P0001';
  end if;
  insert into public.onaylar (user_id, tur, surum) values
    ((select auth.uid()), 'aydinlatma', p_aydinlatma_surumu), ((select auth.uid()), 'beyan', p_aydinlatma_surumu);
  perform set_config('pn.yonetici_islem', '1', true);
  update public.isletmeler set durum = 'basvuru', basvuru_at = now() where id = i.id;
  perform public._kaydet('basvuru_gonderildi', 'isletmeler', i.id::text);
end $$;

create function public.fiyat_izni_ver(p_metin_surumu text) returns void
language plpgsql security definer set search_path = '' as $$
declare v uuid := public.onayli_isletmem();
begin
  if v is null then raise exception 'Fiyat izni yalnızca onaylı işletme için verilebilir' using errcode = 'P0001'; end if;
  if coalesce(length(p_metin_surumu), 0) < 3 then raise exception 'İzin metni sürümü gerekli' using errcode = 'P0001'; end if;
  if public.fiyat_izni_aktif(v) then return; end if;
  insert into public.fiyat_izinleri (isletme_id, metin_surumu) values (v, p_metin_surumu);
  insert into public.onaylar (user_id, tur, surum) values ((select auth.uid()), 'fiyat_izni', p_metin_surumu);
  perform public._kaydet('fiyat_izni_verildi', 'isletmeler', v::text, jsonb_build_object('surum', p_metin_surumu));
end $$;

create function public.fiyat_izni_geri_al() returns void
language plpgsql security definer set search_path = '' as $$
declare v uuid := public.benim_isletmem();
begin
  if v is null then return; end if;
  update public.fiyat_izinleri set geri_alindi = now() where isletme_id = v and geri_alindi is null;
  insert into public.onaylar (user_id, tur, surum) values ((select auth.uid()), 'fiyat_izni_geri', 'geri-alma');
  perform public._kaydet('fiyat_izni_geri_alindi', 'isletmeler', v::text);
end $$;

create function public.silme_talep_et() returns void
language plpgsql security definer set search_path = '' as $$
declare v uuid := public.benim_isletmem();
begin
  if v is null then raise exception 'Kayıtlı işletme yok' using errcode = 'P0001'; end if;
  perform set_config('pn.yonetici_islem', '1', true);
  -- talep anında işletme yayından kalkar; silme işlemini yönetici yapar (KVKK m.7, en geç 30 gün)
  update public.isletmeler set silme_talebi = now(),
    durum = case when durum = 'onayli' then 'askida'::public.isletme_durum else durum end,
    durum_notu = case when durum = 'onayli' then 'Silme talebi nedeniyle yayından kaldırıldı' else durum_notu end
  where id = v;
  perform public._kaydet('silme_talebi', 'isletmeler', v::text);
end $$;

create function public.hesap_durumu() returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'giris', (select auth.uid()) is not null,
    'yonetici_hesabi', exists (select 1 from public.yoneticiler where user_id = (select auth.uid())),
    'aal', coalesce((select auth.jwt()) ->> 'aal', ''),
    'yonetici', public.yonetici_mi())
$$;

-- ───────────────────────── Yönetici işlemleri (RPC) ─────────────────────────
create function public._yonetici_sart() returns void
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.yonetici_mi() then
    raise exception 'Bu işlem için yönetici girişi ve iki adımlı doğrulama gerekli' using errcode = '42501';
  end if;
end $$;

create function public._slug(p text) returns text
language sql immutable set search_path = '' as $$
  select trim(both '-' from regexp_replace(lower(translate(p, 'ÇĞİIÖŞÜçğıöşüÂâÎîÛû', 'CGIIOSUcgiosuaaiiuu')), '[^a-z0-9]+', '-', 'g'))
$$;

create function public.yonetici_durum_degistir(p_id uuid, p_durum public.isletme_durum, p_not text default null) returns void
language plpgsql security definer set search_path = '' as $$
declare eski public.isletme_durum;
begin
  perform public._yonetici_sart();
  select durum into eski from public.isletmeler where id = p_id for update;
  if eski is null then raise exception 'İşletme bulunamadı' using errcode = 'P0001'; end if;
  if p_durum = 'onayli' then raise exception 'Onay için yonetici_onayla kullanılır' using errcode = 'P0001'; end if;
  if p_durum in ('reddedildi', 'eksik_bilgi', 'askida') and coalesce(length(btrim(p_not)), 0) < 3 then
    raise exception 'Bu karar için işletmeye gösterilecek bir açıklama yazın' using errcode = 'P0001';
  end if;
  if p_durum = 'askida' and eski <> 'onayli' then raise exception 'Yalnızca onaylı işletme askıya alınabilir' using errcode = 'P0001'; end if;
  perform set_config('pn.yonetici_islem', '1', true);
  update public.isletmeler set durum = p_durum, durum_notu = p_not where id = p_id;
  perform public._kaydet('durum_' || p_durum::text, 'isletmeler', p_id::text, jsonb_build_object('eski', eski, 'not', p_not));
end $$;

create function public.yonetici_dogrulama_ekle(p_id uuid, p_yontem text, p_not text default null) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  insert into public.dogrulamalar (isletme_id, yontem, notlar, kontrol_eden) values (p_id, p_yontem, p_not, (select auth.uid()))
  on conflict (isletme_id, yontem) do update set notlar = excluded.notlar, kontrol_eden = excluded.kontrol_eden, zaman = now();
  perform public._kaydet('dogrulama_eklendi', 'isletmeler', p_id::text, jsonb_build_object('yontem', p_yontem));
end $$;

create function public.yonetici_dogrulama_sil(p_id uuid, p_yontem text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  if exists (select 1 from public.isletmeler where id = p_id and durum = 'onayli')
     and (select count(*) from public.dogrulamalar where isletme_id = p_id and yontem <> p_yontem) < 2 then
    raise exception 'Onaylı işletmede en az iki doğrulama kalmalı; önce askıya alın' using errcode = 'P0001';
  end if;
  delete from public.dogrulamalar where isletme_id = p_id and yontem = p_yontem;
  perform public._kaydet('dogrulama_silindi', 'isletmeler', p_id::text, jsonb_build_object('yontem', p_yontem));
end $$;

create function public.yonetici_onayla(p_id uuid) returns text
language plpgsql security definer set search_path = '' as $$
declare i public.isletmeler; n int; s text; aday text; k int := 1; pk public.paketler;
begin
  perform public._yonetici_sart();
  select * into i from public.isletmeler where id = p_id for update;
  if i.id is null then raise exception 'İşletme bulunamadı' using errcode = 'P0001'; end if;
  if i.durum not in ('basvuru', 'inceleniyor', 'eksik_bilgi', 'askida') then
    raise exception 'Bu durumdaki işletme onaylanamaz: %', i.durum using errcode = 'P0001';
  end if;
  select count(*) into n from public.dogrulamalar where isletme_id = p_id;
  if n < 2 then raise exception 'Onay için en az iki doğrulama yöntemi gerekli (şu an %)', n using errcode = 'P0001'; end if;
  select * into pk from public.paketler where kod = i.paket;
  if not pk.satista then raise exception 'İşletmenin paketi satışta değil' using errcode = 'P0001'; end if;
  s := i.slug;
  if s is null then
    aday := left(public._slug(i.ad || ' ' || i.ilce), 80);
    if length(aday) < 3 then aday := 'kuyumcu-' || i.ilce; end if;
    s := aday;
    while exists (select 1 from public.isletmeler where slug = s) loop k := k + 1; s := aday || '-' || k; end loop;
  end if;
  perform set_config('pn.yonetici_islem', '1', true);
  update public.isletmeler set durum = 'onayli', durum_notu = null, slug = s,
    dogrulandi_at = coalesce(dogrulandi_at, now()), dogrulayan = (select auth.uid()) where id = p_id;
  perform public._kaydet('onaylandi', 'isletmeler', p_id::text, jsonb_build_object('slug', s, 'eski', i.durum));
  return s;
end $$;

create function public.yonetici_degisiklik_karar(p_id uuid, p_onay boolean) returns void
language plpgsql security definer set search_path = '' as $$
declare b jsonb;
begin
  perform public._yonetici_sart();
  select bekleyen_degisiklik into b from public.isletmeler where id = p_id for update;
  if b is null then return; end if;
  perform set_config('pn.yonetici_islem', '1', true);
  if p_onay then
    update public.isletmeler i set
      ad = coalesce(b->>'ad', i.ad), il = coalesce(b->>'il', i.il), ilce = coalesce(b->>'ilce', i.ilce),
      adres = coalesce(b->>'adres', i.adres), telefon = coalesce(b->>'telefon', i.telefon),
      whatsapp = case when b ? 'whatsapp' then b->>'whatsapp' else i.whatsapp end,
      aciklama = case when b ? 'aciklama' then b->>'aciklama' else i.aciklama end,
      bekleyen_degisiklik = null
    where id = p_id;
  else
    update public.isletmeler set bekleyen_degisiklik = null where id = p_id;
  end if;
  perform public._kaydet(case when p_onay then 'degisiklik_onaylandi' else 'degisiklik_reddedildi' end, 'isletmeler', p_id::text, b);
end $$;

create function public.yonetici_foto_karar(p_foto uuid, p_durum text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  if p_durum not in ('onayli', 'reddedildi') then raise exception 'Geçersiz karar' using errcode = 'P0001'; end if;
  update public.fotograflar set durum = p_durum where id = p_foto;
  perform public._kaydet('foto_' || p_durum, 'fotograflar', p_foto::text);
end $$;

create function public.yonetici_fiyat_gizle(p_fiyat uuid, p_neden text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  if coalesce(length(btrim(p_neden)), 0) < 3 then raise exception 'Gizleme nedeni yazın' using errcode = 'P0001'; end if;
  update public.fiyatlar set durum = 'gizlendi', gizleme_nedeni = p_neden where id = p_fiyat;
  perform public._kaydet('fiyat_gizlendi', 'fiyatlar', p_fiyat::text, jsonb_build_object('neden', p_neden));
end $$;

create function public.yonetici_kampanya_karar(p_id uuid, p_durum text, p_not text default null) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  if p_durum not in ('yayinda', 'reddedildi', 'gizlendi') then raise exception 'Geçersiz karar' using errcode = 'P0001'; end if;
  perform set_config('pn.yonetici_islem', '1', true);
  update public.kampanyalar set durum = p_durum, yonetici_notu = p_not where id = p_id;
  perform public._kaydet('kampanya_' || p_durum, 'kampanyalar', p_id::text, jsonb_build_object('not', p_not));
end $$;

create function public.yonetici_paket_kaydet(p_kod text, p_ad text, p_satista boolean, p_foto_limit int,
  p_fiyat_yayini boolean, p_kampanya_limit int, p_istatistik boolean, p_rozet text, p_one_cikan boolean, p_aylik_ucret_tl numeric)
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  insert into public.paketler as p (kod, ad, satista, foto_limit, fiyat_yayini, kampanya_limit, istatistik, rozet, one_cikan, aylik_ucret_tl)
  values (p_kod, p_ad, p_satista, p_foto_limit, p_fiyat_yayini, p_kampanya_limit, p_istatistik, nullif(btrim(p_rozet), ''), p_one_cikan, p_aylik_ucret_tl)
  on conflict (kod) do update set ad = excluded.ad, satista = excluded.satista, foto_limit = excluded.foto_limit,
    fiyat_yayini = excluded.fiyat_yayini, kampanya_limit = excluded.kampanya_limit, istatistik = excluded.istatistik,
    rozet = excluded.rozet, one_cikan = excluded.one_cikan, aylik_ucret_tl = excluded.aylik_ucret_tl, guncellendi = now();
  perform public._kaydet('paket_kaydedildi', 'paketler', p_kod);
end $$;

create function public.yonetici_paket_ata(p_id uuid, p_kod text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  if not exists (select 1 from public.paketler where kod = p_kod and satista) then
    raise exception 'Satışta olmayan paket atanamaz' using errcode = 'P0001';
  end if;
  perform set_config('pn.yonetici_islem', '1', true);
  update public.isletmeler set paket = p_kod where id = p_id;
  perform public._kaydet('paket_atandi', 'isletmeler', p_id::text, jsonb_build_object('paket', p_kod));
end $$;

create function public.yonetici_isletme_sil(p_id uuid) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  delete from public.isletmeler where id = p_id;
  perform public._kaydet('isletme_silindi', 'isletmeler', p_id::text);
end $$;

create function public.yonetici_istatistik() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  perform public._yonetici_sart();
  return jsonb_build_object(
    'durumlar', (select coalesce(jsonb_object_agg(durum, n), '{}'::jsonb) from (select durum, count(*) n from public.isletmeler group by durum) x),
    'bekleyen_foto', (select count(*) from public.fotograflar where durum = 'bekliyor'),
    'bekleyen_kampanya', (select count(*) from public.kampanyalar where durum = 'bekliyor'),
    'bekleyen_degisiklik', (select count(*) from public.isletmeler where bekleyen_degisiklik is not null),
    'silme_talebi', (select count(*) from public.isletmeler where silme_talebi is not null),
    'fiyat_24s', (select count(*) from public.fiyatlar where guncelleme > now() - interval '1 day'),
    'etkinlik_30g', (select coalesce(jsonb_object_agg(tur, n), '{}'::jsonb) from
       (select tur, sum(adet) n from public.etkinlik_gunluk where gun > current_date - 30 group by tur) x),
    'il_dagilimi', (select coalesce(jsonb_object_agg(il, n), '{}'::jsonb) from
       (select il, count(*) n from public.isletmeler where durum = 'onayli' group by il) x)
  );
end $$;

-- ───────────────────────── Herkese açık görünümler ─────────────────────────
-- Not: Bu görünümler bilerek görünüm sahibinin yetkisiyle çalışır (security_invoker kapalı):
-- ana tablolara anonim erişim yoktur; dışarıya yalnızca aşağıdaki sütunlar ve satırlar açılır.
create view public.yayin_isletmeler as
  select i.id, i.slug, i.ad, i.il, i.ilce, i.adres, i.telefon, i.whatsapp, i.aciklama, i.saatler,
         i.paket, p.rozet, p.one_cikan, i.dogrulandi_at,
         (select coalesce(array_agg(d.yontem order by d.yontem), '{}') from public.dogrulamalar d where d.isletme_id = i.id) as dogrulama_yontemleri,
         (public.fiyat_izni_aktif(i.id) and p.fiyat_yayini) as fiyat_izni,
         (select min(f.verildi) from public.fiyat_izinleri f where f.isletme_id = i.id and f.geri_alindi is null) as fiyat_izni_tarihi,
         i.guncellendi
  from public.isletmeler i join public.paketler p on p.kod = i.paket
  where i.durum = 'onayli' and p.satista and i.slug is not null;

create view public.yayin_fiyatlar as
  select distinct on (f.isletme_id) f.isletme_id, f.gram_alis, f.gram_satis, f.ceyrek_alis, f.ceyrek_satis,
         f.yarim_alis, f.yarim_satis, f.tam_alis, f.tam_satis, f.guncelleme,
         (f.guncelleme < now() - interval '24 hours') as eski
  from public.fiyatlar f join public.yayin_isletmeler y on y.id = f.isletme_id
  where f.durum = 'yayinda' and y.fiyat_izni and f.guncelleme > now() - interval '7 days'
  order by f.isletme_id, f.guncelleme desc;

create view public.yayin_fotograflar as
  select f.id, f.isletme_id, f.yol, f.tur, f.aciklama, f.sira
  from public.fotograflar f join public.yayin_isletmeler y on y.id = f.isletme_id
  where f.durum = 'onayli';

create view public.yayin_kampanyalar as
  select k.id, k.isletme_id, k.baslik, k.aciklama, k.baslangic, k.bitis
  from public.kampanyalar k join public.yayin_isletmeler y on y.id = k.isletme_id
  where k.durum = 'yayinda' and current_date between k.baslangic and k.bitis;

-- ───────────────────────── RLS ─────────────────────────
alter table public.yoneticiler     enable row level security;
alter table public.denetim_kaydi   enable row level security;
alter table public.ilceler         enable row level security;
alter table public.paketler        enable row level security;
alter table public.isletmeler      enable row level security;
alter table public.dogrulamalar    enable row level security;
alter table public.onaylar         enable row level security;
alter table public.fiyat_izinleri  enable row level security;
alter table public.fiyatlar        enable row level security;
alter table public.fotograflar     enable row level security;
alter table public.kampanyalar     enable row level security;
alter table public.etkinlik_gunluk enable row level security;

create policy "herkes okur" on public.ilceler for select to anon, authenticated using (true);
create policy "herkes okur" on public.paketler for select to anon, authenticated using (true);
create policy "yonetici okur" on public.yoneticiler for select to authenticated using (public.yonetici_mi());
create policy "yonetici okur" on public.denetim_kaydi for select to authenticated using (public.yonetici_mi());

create policy "sahip veya yonetici okur" on public.isletmeler for select to authenticated
  using (sahip_id = (select auth.uid()) or public.yonetici_mi());
create policy "sahip ekler" on public.isletmeler for insert to authenticated
  with check (sahip_id = (select auth.uid()) and durum = 'taslak');
create policy "sahip gunceller" on public.isletmeler for update to authenticated
  using (sahip_id = (select auth.uid())) with check (sahip_id = (select auth.uid()));
create policy "sahip taslagi siler" on public.isletmeler for delete to authenticated
  using (sahip_id = (select auth.uid()) and durum in ('taslak', 'reddedildi'));

create policy "sahip veya yonetici okur" on public.dogrulamalar for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());
create policy "kendi onaylari" on public.onaylar for select to authenticated
  using (user_id = (select auth.uid()) or public.yonetici_mi());
create policy "sahip veya yonetici okur" on public.fiyat_izinleri for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());

create policy "sahip veya yonetici okur" on public.fiyatlar for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());
create policy "izinli sahip ekler" on public.fiyatlar for insert to authenticated
  with check (public.fiyat_girebilir(isletme_id));

create policy "sahip veya yonetici okur" on public.fotograflar for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());
create policy "onayli sahip ekler" on public.fotograflar for insert to authenticated
  with check (isletme_id = public.onayli_isletmem());
create policy "sahip gunceller" on public.fotograflar for update to authenticated
  using (isletme_id = public.benim_isletmem()) with check (isletme_id = public.benim_isletmem());
create policy "sahip siler" on public.fotograflar for delete to authenticated
  using (isletme_id = public.benim_isletmem());

create policy "sahip veya yonetici okur" on public.kampanyalar for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());
create policy "onayli sahip ekler" on public.kampanyalar for insert to authenticated
  with check (isletme_id = public.onayli_isletmem());
create policy "sahip gunceller" on public.kampanyalar for update to authenticated
  using (isletme_id = public.benim_isletmem()) with check (isletme_id = public.benim_isletmem());
create policy "sahip siler" on public.kampanyalar for delete to authenticated
  using (isletme_id = public.benim_isletmem());

create policy "sahip veya yonetici okur" on public.etkinlik_gunluk for select to authenticated
  using (isletme_id = public.benim_isletmem() or public.yonetici_mi());

-- ───────────────────────── Yetkiler (en az yetki) ─────────────────────────
revoke all on all tables in schema public from anon, authenticated;
revoke execute on all functions in schema public from public, anon, authenticated;

grant select on public.ilceler, public.paketler to anon, authenticated;
grant select on public.yayin_isletmeler, public.yayin_fiyatlar, public.yayin_fotograflar, public.yayin_kampanyalar to anon, authenticated;

grant select, delete on public.isletmeler to authenticated;
grant insert (ad, yetkili_ad, il, ilce, adres, telefon, whatsapp, eposta, aciklama, saatler) on public.isletmeler to authenticated;
grant update (ad, yetkili_ad, il, ilce, adres, telefon, whatsapp, eposta, aciklama, saatler) on public.isletmeler to authenticated;
grant select on public.dogrulamalar, public.onaylar, public.fiyat_izinleri, public.etkinlik_gunluk,
  public.yoneticiler, public.denetim_kaydi to authenticated;
grant select on public.fiyatlar to authenticated;
grant insert (isletme_id, gram_alis, gram_satis, ceyrek_alis, ceyrek_satis, yarim_alis, yarim_satis, tam_alis, tam_satis) on public.fiyatlar to authenticated;
grant select, delete on public.fotograflar to authenticated;
grant insert (isletme_id, yol, tur, aciklama, sira) on public.fotograflar to authenticated;
grant update (sira) on public.fotograflar to authenticated;
grant select, delete on public.kampanyalar to authenticated;
grant insert (isletme_id, baslik, aciklama, baslangic, bitis) on public.kampanyalar to authenticated;
grant update (baslik, aciklama, baslangic, bitis) on public.kampanyalar to authenticated;

-- RLS içinde kullanılan yardımcılar
grant execute on function public.yonetici_mi(), public.benim_isletmem(), public.onayli_isletmem(),
  public.fiyat_izni_aktif(uuid), public.fiyat_girebilir(uuid), public.foto_yukleyebilir(text),
  public.saatler_gecerli(jsonb), public.fiyat_cifti(numeric, numeric) to authenticated;
grant execute on function public.etkinlik_kaydet(uuid, text) to anon, authenticated;
-- yayin_* görünümleri bu fonksiyonu çağırır; görünümü okuyan rolün çalıştırma yetkisi gerekir
grant execute on function public.fiyat_izni_aktif(uuid) to anon;
grant execute on function public.hesap_durumu() to authenticated;
grant execute on function public.basvuru_gonder(text, boolean), public.fiyat_izni_ver(text),
  public.fiyat_izni_geri_al(), public.silme_talep_et() to authenticated;
grant execute on function public.yonetici_durum_degistir(uuid, public.isletme_durum, text),
  public.yonetici_dogrulama_ekle(uuid, text, text), public.yonetici_dogrulama_sil(uuid, text),
  public.yonetici_onayla(uuid), public.yonetici_degisiklik_karar(uuid, boolean),
  public.yonetici_foto_karar(uuid, text), public.yonetici_fiyat_gizle(uuid, text),
  public.yonetici_kampanya_karar(uuid, text, text),
  public.yonetici_paket_kaydet(text, text, boolean, int, boolean, int, boolean, text, boolean, numeric),
  public.yonetici_paket_ata(uuid, text), public.yonetici_isletme_sil(uuid), public.yonetici_istatistik() to authenticated;

-- ───────────────────────── Fotoğraf deposu ─────────────────────────
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('isletme-fotolari', 'isletme-fotolari', true, 2097152, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

create policy "kp foto yukle" on storage.objects for insert to authenticated
  with check (bucket_id = 'isletme-fotolari' and public.foto_yukleyebilir((storage.foldername(name))[1]));
create policy "kp foto oku" on storage.objects for select to authenticated
  using (bucket_id = 'isletme-fotolari' and ((storage.foldername(name))[1] = public.benim_isletmem()::text or public.yonetici_mi()));
create policy "kp foto sil" on storage.objects for delete to authenticated
  using (bucket_id = 'isletme-fotolari' and ((storage.foldername(name))[1] = public.benim_isletmem()::text or public.yonetici_mi()));

commit;
