# DIFFERENTIATION: AI-Native Relational Database Seeder vs. Snaplet Seed

> **Konumlandırma & Temel Fark:**
> `@snaplet/seed` (güncel fork: `supabase-community/seed`), veritabanı DDL şemasını inceleyip deterministik rastgele değerler (`copycat`/`faker`) atayan **Sentaktik/İlişkisel Veri Üretecidir**. Foreign Key (FK) ID eşleşmelerini çözer, ancak veri sütunlarının durum makinelerini (state machines) veya çapraz sütun mantıklarını otomatik "anlamaz".
> 
> **LLM-Native Relational Database Seeder** ise veritabanı şemasını **Anlamsal ve Mantıksal Durum Makinesi** olarak ele alır. Çapraz sütun durum bağımlılıklarını sıfır manuel kodlama ile otomatik çıkarır.

---

## 1. Snaplet Seed Yetenekleri ve Dokümantasyon Doğrulamaları

- **Foreign Key (FK) İlişkileri:**  
  - **Snaplet Durumu:** ✅ Destekliyor.  
  - **Kaynak/Dokümantasyon:** Snaplet Seed docs (`github.com/supabase-community/seed`): *"Seed automatically manages relational data and foreign key constraints using type-safe TypeScript methods."* (`seed.users((x) => x(3, { posts: (x) => x(2) }))`).
- **Tablo-İçi Çapraz Sütun Durum Mantığı (Cross-Column Logic):**  
  - **Snaplet Durumu:** ❌ Otomatik yapamıyor.  
  - **Kaynak/Dokümantasyon:** Snaplet Seed Refinements docs: *"To satisfy specific business rules or override generated values, you must pass custom TypeScript refinement objects."* (Geliştirici her sütun kısıtı için manuel TS `refinements` kodu yazmak zorundadır; motor sütunları primitif tiplerine göre bağımsız türetir).
- **`CHECK` Constraints & Matematiksel İnvaryantlar (`subtotal + tax = total`):**  
  - **Snaplet Durumu:** ❌ Otomatik yapamıyor.  
  - **Kaynak/Dokümantasyon:** Snaplet Seed dokümantasyonu & topluluk çözümleri: *"If seed struggles to generate data that satisfies a complex CHECK constraint, providing the data manually via the override method (refinements) is the standard workaround."*  
  - **İstisna / Teşhis:** *(Varsayım — doğrulanmadı / Hipotez: Manuel override yazılmadan rastgele `DECIMAL` türetildiğinde DB seviyesinde `CheckViolationError` alma riski yüksektir, ancak bu her özel kısıt için bağımsız test edilmelidir).*
- **JSONB Semantik Doğrulama:**  
  - **Snaplet Durumu:** ❌ Otomatik yapamıyor.  
  - **Kaynak/Dokümantasyon:** Snaplet varsayılan olarak primitif dummy nesneler doldurur. Şemaya özel JSONB validation için kullanıcıların `pg_jsonschema` veya manuel TS override yazması gerekir.

---

## 2. v0 MVP Kapsam Sınırı (Kapsam Daraltması)

Geçmişteki "her şeyi tek seferde yapalım" hatasına düşmemek ve 7 günlük hedefi korumak için, **v0 MVP kapsamı en güçlü ve en düşük riskli 2 temel özelliğe daraltılmıştır**:

### v0 Dahil (7-Günlük MVP Kapsamı):
1. **Çapraz-Sütun Mantıksal Bağımlılıkları (In-Table Cross-Column State Cohesion):**
   - **Senaryo:** `orders` tablosunda `status` (`ENUM: 'pending', 'processing', 'shipped', 'cancelled'`), `shipped_at` (`TIMESTAMP NULL`), `cancellation_reason` (`TEXT NULL`).
   - **Snaplet Ne Yapar (Y):** Sütun tiplerine göre bağımsız türetir. `status = 'pending'` iken `shipped_at` doldurabilir. Geliştiricinin TS'de `if/else` yazmasını bekler.
   - **Biz Ne Yaparız (Z):** LLM şemadan durum makinesini çıkarır. `status = 'shipped'` ise `shipped_at` doldurur, `cancellation_reason = NULL` bırakır. Manuel TS yazımı gerektirmez.
2. **Foreign Key (FK) İntrospection & Bütünlük:**
   - İlişkisel tabloların DDL şemasını parse edip ana-çocuk kayıtlarını tutarlı FK ID'leri ile bağlar.

### v1 Backlog (v0 Sonrasına Ertelenen Özellikler):
1. **`CHECK` Constraint Garantisi & Matematiksel İnvaryantlar (`subtotal + tax = total`):**
   - **Ertelenme Nedeni:** Single-shot LLM çıktısı deterministik değildir; veritabanı kısıtlarını %100 garanti etmek karmaşık bir *üret -> DB'de dene -> hata varsa retry/validate* döngüsü gerektirir. 7 günlük v0 kapsamını korumak için ertelenmiştir.
2. **JSONB Semantik Şema Doğrulaması:**
   - v1 sürümüne bırakılmıştır.

---

## 3. Özet Karşılaştırma Matrisi (v0 vs. Snaplet)

| Özellik / Senaryo | Snaplet Seed (Açık Kaynak) | LLM-Native Seeder (v0 MVP) | Durum / Kaynak |
|---|---|---|---|
| **Foreign Key (FK) Bütünlüğü** | ✅ Var | ✅ Var | Dokümantasyonla Doğrulandı |
| **Tablo-İçi Çapraz Sütun Mantığı** | ❌ Manuel TS `refinements` şart | ✅ Otomatik (v0 Odak Noktası) | Dokümantasyonla Doğrulandı |
| **DB `CHECK` Constraint Garantisi** | ❌ Manuel Override şart | ⏳ v1 Backlog (v0 Dışı) | Kapsam Daraltıldı (Retry Loop Gerektirir) |
| **JSONB Semantik Doğrulama** | ❌ Manuel Override şart | ⏳ v1 Backlog (v0 Dışı) | Kapsam Daraltıldı |
