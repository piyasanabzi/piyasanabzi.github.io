/* Kuyumcu Yönetim Sistemi bağlantı ayarı.
   url: Supabase proje adresi (https://xxxx.supabase.co)
   key: Supabase "Publishable key" (sb_publishable_...). Bu anahtar herkese açık olacak şekilde tasarlanmıştır;
        güvenlik veritabanındaki RLS kurallarıyla sağlanır.
   ASLA buraya "Secret key" (sb_secret_...) ya da "service_role" anahtarı yazmayın.
   İkisi de boşken paneller "henüz açılmadı" ekranı gösterir ve hiçbir veri gönderilmez. */
window.PN_SUPA = { url: "", key: "" };
