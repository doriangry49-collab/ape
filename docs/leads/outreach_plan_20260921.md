# 🎯 AI-DB-SEEDER — DETAYLI OUTREACH VE LEAD DEĞERLENDİRME PLANI (TASK-022)

**Tarih:** 21.09.2026  
**Hedef Ürün:** `ai-db-seeder` (Snaplet alternatifi, sıfır konfigürasyonlu ilişkisel veritabanı seed aracı)  
**Veri Kaynağı:** `docs/leads/leads_ai_db_seeder_20260921.json` (18 Doğrulanmış Lead)  
**Özet Dağılım:** **6 Yüksek Aciliyet (HIGH)**, **5 Orta Aciliyet (MEDIUM)**, **7 Düşük Aciliyet (LOW)**  

---

## 📌 STRATEJİK DEĞERLENDİRME & FIRSAT ANALİZİ
Snaplet'in Temmuz/Ağustos 2024'te kapanması (`shutdown`) ve bakımının durması, açık kaynak geliştirici ekosisteminde **3 kritik acil problem** doğurmuştur:
1. **Bozuk CI ve Güvenlik Açığı (Lead #1, #3):** `@snaplet/seed 0.98.0` paketinin bağımlılıkları `npm audit` denetimlerinde yüksek riskli güvenlik açığı veriyor. Aktif projeler bağımlılığı güncelleyemediği için CI boru hatları kırılıyor.
2. **Açıkta Kalan Prisma & Supabase Görevleri (Lead #2, #10):** Geliştiriciler repolarında açıkça 'Snaplet mi kullanalım yoksa elle SQL mi yazalım?' ikilemiyle bekliyor.
3. **Windows 11 Kurulum Sorunları (Lead #4):** `@snaplet/seed init` Windows ortamında çöküyor. `ai-db-seeder`'ın derlenmiş tek bir ikili dosya (standalone CLI) olarak sunulması bu geliştiricileri doğrudan kurtaracaktır.

---

## 🚨 1. BÖLÜM: YÜKSEK ACİLİYETLİ LEAD'LER (HIGH PRIORITY — DOĞRUDAN DÖNÜŞ VE PR TEKLİFİ)
Bu lead'ler şu anda doğrudan bozuk bağımlılık veya çözümsüz bir seed göreviyle uğraşan en sıcak hedeflerdir.

### Lead #1: [https://github.com/ONEARMY/community-platform/issues/4889](https://github.com/ONEARMY/community-platform/issues/4889)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [ONEARMY](https://github.com/ONEARMY) | Repo: [ONEARMY/community-platform](https://github.com/ONEARMY/community-platform)
- **Mevcut Sorun:** *"seed.ts depends on @snaplet/seed 0.98.0, unmaintained since 2024 and failing npm audit: `db:seed` runs `bunx @snaplet/seed sync && bunx tsx seed.ts` against @snaplet/seed 0.98.0, the package's last release (July 2024, no commits since August 2024), a"*
- **Bağlam & Teşhis:** ONEARMY community-platform projesinde `seed.ts` doğrudan `@snaplet/seed 0.98.0` kullanıyor ve unmaintained olduğu için npm audit güvenlik açığı veriyor. Build/CI blokajı var.
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Direct Drop-in Replacement for @snaplet/seed in seed.ts)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hey @ONEARMY — noticed your repo is blocked by the unmaintained `@snaplet/seed 0.98.0` failing npm audit in `seed.ts`. We built `ai-db-seeder` as an open-source, zero-dependency alternative that generates relational seed data without unmaintained runtime baggage. Would you be open to a quick PR migrating your seeding script to resolve the security audit?"*

### Lead #2: [https://github.com/ASVGay/the-rhapsodies/issues/917](https://github.com/ASVGay/the-rhapsodies/issues/917)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [ASVGay](https://github.com/ASVGay) | Repo: [ASVGay/the-rhapsodies](https://github.com/ASVGay/the-rhapsodies)
- **Mevcut Sorun:** *"Generate seed data using Snaplet: https://supabase.com/docs/guides/local-development/seeding-your-database#generating-seed-data  It would be nice to clean up some envs by doing this if possible"*
- **Bağlam & Teşhis:** The Rhapsodies reposu aktif olarak Supabase üzerinde Snaplet ile test verisi üretmek için açık bir görev (issue #917) açmış durumda.
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Supabase Database Seeding Replacement)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @ASVGay — saw your repository task (#917) exploring Snaplet for Supabase seed generation. Following Snaplet's shutdown, we're building `ai-db-seeder` to automatically infer relational foreign keys and populate local/staging databases. Happy to provide an early configuration tailored to your Supabase schema if helpful!"*

### Lead #3: [https://github.com/supabase-community/seed/issues/213](https://github.com/supabase-community/seed/issues/213)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [supabase-community](https://github.com/supabase-community) | Repo: [supabase-community/seed](https://github.com/supabase-community/seed)
- **Mevcut Sorun:** *"High severity npm audit vulnerabilities in v0.98.0 dependencies: # Bug report  ## Describe the bug  `@snaplet/seed` version 0.98.0 has transitive dependencies with known high-severity security vulnerabilities. Running `npm audit` reports vulnerabilit"*
- **Bağlam & Teşhis:** Supabase-community/seed reposunda `@snaplet/seed` transitive bağımlılıklarının yüksek riskli güvenlik açığı vermesi raporlandı (issue #213).
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Drop-in Replacement for npm audit vulnerable seed package)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hello @supabase-community — saw issue #213 regarding high-severity npm audit vulnerabilities in `@snaplet/seed 0.98.0`. We designed `ai-db-seeder` as a standalone, zero-dependency CLI precisely to eliminate these transitive node module vulnerabilities. We'd love to help benchmark or provide a clean alternative for the community."*

### Lead #4: [https://github.com/supabase-community/seed/issues/193](https://github.com/supabase-community/seed/issues/193)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [supabase-community](https://github.com/supabase-community) | Repo: [supabase-community/seed](https://github.com/supabase-community/seed)
- **Mevcut Sorun:** *"Cant run npx @snaplet/seed init on windows 11: I try to run `npx @snaplet/seed init` and got this error:  ``` Welcome to @snaplet/seed! Snaplet Seed populates your database with realistic, production-like mock data ✨ (node:1152) [DEP0040] Depreca"*
- **Bağlam & Teşhis:** Kullanıcı Windows 11 üzerinde `npx @snaplet/seed init` çalıştırırken Node deprecation ve çökme hatası alıyor.
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Cross-platform Standalone Executable)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @supabase-community — noticed the Windows 11 initialization crash reported in issue #193 for `@snaplet/seed`. `ai-db-seeder` runs as a compiled standalone binary with zero Node/npx environmental quirks on Windows. Happy to share a pre-built Windows executable to test if it unblocks local setup."*

### Lead #7: [https://github.com/webinstall/webi-installer-requests/issues/46](https://github.com/webinstall/webi-installer-requests/issues/46)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [webinstall](https://github.com/webinstall) | Repo: [webinstall/webi-installer-requests](https://github.com/webinstall/webi-installer-requests)
- **Mevcut Sorun:** *"Request for snaplet: It would be awesome being able to temporarily [install snaplet](https://docs.snaplet.dev/quickstart) using webi as it can provide for temporal database to test on CI environments"*
- **Bağlam & Teşhis:** Webi reposunda CI ortamlarında geçici veritabanı testleri için Snaplet kurulumu talep ediliyor.
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Fast CI Test Database Population)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @webinstall — saw request #46 for ephemeral testing database seeding in CI. Since Snaplet's discontinuation, `ai-db-seeder` provides single-binary, instant database seeding without Node dependencies, ideal for lightweight CI runners. Happy to submit a package definition if you're still interested!"*

### Lead #10: [https://github.com/edmondsoun/living-timeline/issues/2](https://github.com/edmondsoun/living-timeline/issues/2)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [edmondsoun](https://github.com/edmondsoun) | Repo: [edmondsoun/living-timeline](https://github.com/edmondsoun/living-timeline)
- **Mevcut Sorun:** *"Set up seed file for database: See Prisma docs here for options to set up a seed file: https://www.prisma.io/docs/orm/prisma-migrate/workflows/seeding  Questions: - Do we want to use Snaplet to auto-generate data? - If not, preference to write se"*
- **Bağlam & Teşhis:** Living-timeline projesinde Prisma seed dosyası oluşturulurken 'Snaplet kullanalım mı yoksa kendimiz mi yazalım?' sorusu sorulmuş.
- **Aciliyet:** 🔴 **HIGH**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Prisma Seed Alternative)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @edmondsoun — noticed your open question in issue #2 about using Snaplet vs writing manual Prisma seed fixtures. Since Snaplet is no longer actively maintained, `ai-db-seeder` offers automated, schema-aware seed generation that outputs directly compatible Prisma/SQL records. Happy to provide a quick sample for your schema!"*

---

## ⚡ 2. BÖLÜM: ORTA ACİLİYETLİ LEAD'LER (MEDIUM PRIORITY — ÖZELLİK TALEP EDENLER & TOPLULUK)
Drizzle ORM gibi popüler depolarda `seed.sql` veya CHECK constraint jeneratörü isteyenler ve Snaplet ekosistem liderleri.

### Lead #5: [https://github.com/drizzle-team/drizzle-orm/issues/4133](https://github.com/drizzle-team/drizzle-orm/issues/4133)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [drizzle-team](https://github.com/drizzle-team) | Repo: [drizzle-team/drizzle-orm](https://github.com/drizzle-team/drizzle-orm)
- **Mevcut Sorun:** *"[FEATURE]: Generate seed.sql file with Drizzle Seed (for Supabase etc): ### Feature hasn't been suggested before.  - [x] I have verified this feature I'm about to request hasn't been suggested before.  ### Describe the enhancement you want to request"*
- **Bağlam & Teşhis:** Drizzle ORM reposunda Supabase için `seed.sql` üretme özelliği talep eden 4133 numaralı açık feature request.
- **Aciliyet:** 🟡 **MEDIUM**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (SQL-First Seed Generation for ORMs)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hey @drizzle-team — saw feature request #4133 asking for automated `seed.sql` generation for Supabase. `ai-db-seeder` directly targets this gap by emitting pure, constraint-compliant `seed.sql` batches ready for direct migration execution. Would love to share our schema-to-SQL generation spec with the Drizzle community."*

### Lead #6: [https://github.com/drizzle-team/drizzle-orm/issues/5320](https://github.com/drizzle-team/drizzle-orm/issues/5320)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [drizzle-team](https://github.com/drizzle-team) | Repo: [drizzle-team/drizzle-orm](https://github.com/drizzle-team/drizzle-orm)
- **Mevcut Sorun:** *"[FEATURE]: drizzle-seed: Grouped column values with different generator configs: ### Feature hasn't been suggested before.  - [x] I have verified this feature I'm about to request hasn't been suggested before.  ### Describe the enhancement you want t"*
- **Bağlam & Teşhis:** Drizzle ORM reposunda kolonlar arası ilişkili jeneratör konfigürasyonu talep eden 5320 numaralı issue.
- **Aciliyet:** 🟡 **MEDIUM**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Multi-column Grouped Seed Generator)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @drizzle-team — regarding issue #5320 on grouped column generators: `ai-db-seeder` solves multi-column constraints and relational dependencies automatically using state-machine inference. We'd be glad to share how we handle cross-column coherence if you're exploring implementation patterns."*

### Lead #11: [https://github.com/Yash40000/forgetdm/issues/90](https://github.com/Yash40000/forgetdm/issues/90)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [Yash40000](https://github.com/Yash40000) | Repo: [Yash40000/forgetdm](https://github.com/Yash40000/forgetdm)
- **Mevcut Sorun:** *"[SYN-012] CHECK constraints and cross-column business rules: ## User story  As a ForgeTDM user or operator, I need **CHECK constraints and cross-column business rules** so that the product behavior is safe, predictable, and independently verifiable. "*
- **Bağlam & Teşhis:** ForgeTDM projesinde CHECK constraint ve iş kurallarına uygun sentetik test verisi üretimi isteniyor (issue #90).
- **Aciliyet:** 🟡 **MEDIUM**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Cross-column Business Rules & CHECK Constraints)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @Yash40000 — saw your user story in SYN-012 regarding cross-column CHECK constraints and business rules. Solving interdependent column constraints is the primary design focus of `ai-db-seeder`. Would love to collaborate or benchmark our constraint-satisfaction engine against your test cases."*

### Lead #17: [https://x.com/jianreis/status/1807707851340579155](https://x.com/jianreis/status/1807707851340579155)
- **Kaynak / Tip:** `twitter`
- **İletişim / Profil:** X/Twitter: [@jianreis](https://x.com/jianreis/status/1807707851340579155)
- **Mevcut Sorun:** *"Working at Snaplet has been the highlight of my career. Thanks to all the developers who used us, the team who built it, and the investors who backed us."*
- **Bağlam & Teşhis:** Eski Snaplet ekip üyesi Jian Reis'in Snaplet mirası üzerine paylaşımı. Ekosistem ve vizyon uyumu yüksek.
- **Aciliyet:** 🟡 **MEDIUM**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Snaplet Alum / Core Contributor Outreach)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @jianreis — immense respect for what the Snaplet team built! The developer experience you pioneered was phenomenal. We're building `ai-db-seeder` to keep the mission of zero-config, intelligent relational seeding alive in open-source. Would be honored to get your high-level feedback on our approach whenever you have a moment."*

### Lead #18: [https://x.com/mojitane](https://x.com/mojitane)
- **Kaynak / Tip:** `twitter`
- **İletişim / Profil:** X/Twitter: [@mojitane](https://x.com/mojitane)
- **Mevcut Sorun:** *"Snaplet is now Open Source: supabase.link/O2eQSWS Last month @_snaplet shut down. But that's not the end of the story. Some of the team joined @supabase."*
- **Bağlam & Teşhis:** Snaplet'in kapanması ve açık kaynağa geçişi hakkında duyuru yapan topluluk lideri (mojitane).
- **Aciliyet:** 🟡 **MEDIUM**
- **ai-db-seeder Çözüyor mu?:** ✅ YES (Supabase Community Ecosystem Champion)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @mojitane — loved your post on Snaplet's open-source transition! As the community looks for modern, maintained relational seeding solutions that integrate seamlessly with Supabase, we're building `ai-db-seeder`. Would love to connect and share a demo with the Supabase developer community."*

---

## ℹ️ 3. BÖLÜM: DÜŞÜK ACİLİYETLİ LEAD'LER (LOW PRIORITY — İZLEME VE RADAR)
Doğrudan Snaplet alternatifi aramayan ancak veritabanı testi ve mimari tartışması yürüten arka plan lead'leri.

### Lead #8: [https://github.com/irthomasthomas/undecidability/issues/693](https://github.com/irthomasthomas/undecidability/issues/693)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [irthomasthomas](https://github.com/irthomasthomas) | Repo: [irthomasthomas/undecidability](https://github.com/irthomasthomas/undecidability)
- **Mevcut Sorun:** *"https://supabase.com/blog/postgres-wasm: - [ ] [https://supabase.com/blog/postgres-wasm](https://supabase.com/blog/postgres-wasm)   # Title: [Postgres WASM by Snaplet and Supabase](https://supabase.com/blog/postgres-wasm)  **Description:** Postgres W"*
- **Bağlam & Teşhis:** Postgres-wasm ve Snaplet ilişkisi üzerine teknik referans kaydı.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Postgres WASM / Seeding Research)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @irthomasthomas — noticed your reference tracking around Postgres WASM and Snaplet. If your browser-based or local database workflows require fast, relational mock data generation, `ai-db-seeder` provides a modern constraint-based approach. Happy to exchange notes!"*

### Lead #9: [https://github.com/near/queryapi/issues/311](https://github.com/near/queryapi/issues/311)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [near](https://github.com/near) | Repo: [near/queryapi](https://github.com/near/queryapi)
- **Mevcut Sorun:** *"🔷 [Epic] WebBrowser-based database for debugging: ### Description Currently users can run indexers in debug mode in the browser for selected blocks, read the logs and inspect errors in the browser console. However, commands that interact with the da"*
- **Bağlam & Teşhis:** Near queryapi reposunda tarayıcı içi veritabanı hata ayıklama ve test verisi ihtiyacı tartışılıyor.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Database Debugging & In-browser State)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @near — saw your debugging infrastructure epic (#311). If test state seeding or deterministic mock data generation is needed for reproducible browser indexing, `ai-db-seeder` specializes in constraint-compliant database state population."*

### Lead #12: [https://github.com/zhaoanliu/job-tracker/issues/745](https://github.com/zhaoanliu/job-tracker/issues/745)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [zhaoanliu](https://github.com/zhaoanliu) | Repo: [zhaoanliu/job-tracker](https://github.com/zhaoanliu/job-tracker)
- **Mevcut Sorun:** *"Add retry and failure metrics to database reads and writes: ## Summary  Database access in the app has no resilience layer and no failure observability. Two related gaps:  1. **DB reads and writes have no retry** — a single transient failure (network"*
- **Bağlam & Teşhis:** Job-tracker reposunda veritabanı okuma/yazma hata senaryoları ve metrikleri tartışılıyor.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Database Reliability & Failure Testing)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @zhaoanliu — noticed your discussion in issue #745 around database resilience and failure metrics. If you need realistic, edge-case synthetic data to stress-test your retry layers, `ai-db-seeder` can generate pathological state combinations out of the box."*

### Lead #13: [https://github.com/teamleaderleo/fieldwork/issues/211](https://github.com/teamleaderleo/fieldwork/issues/211)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [teamleaderleo](https://github.com/teamleaderleo) | Repo: [teamleaderleo/fieldwork](https://github.com/teamleaderleo/fieldwork)
- **Mevcut Sorun:** *"[Lane] Scout foundational libraries, databases, and Linux systems: State: `ready`  Programme: #207   Owned path: `programmes/open-source-ecosystems/scouts/foundational-systems/`  ## In simple words  Map the quiet components that sit underneath many a"*
- **Bağlam & Teşhis:** Fieldwork projesinde altyapı kütüphaneleri ve veritabanı izciliği yürütülüyor.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Open Source Tooling Scout)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @teamleaderleo — saw your foundational tooling scout programme (#211). For your database tooling radar, `ai-db-seeder` is an open-source engine bridging the gap left by Snaplet for automated development database seeding."*

### Lead #14: [https://github.com/mcarlson94/parentpresents-web/issues/13](https://github.com/mcarlson94/parentpresents-web/issues/13)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [mcarlson94](https://github.com/mcarlson94) | Repo: [mcarlson94/parentpresents-web](https://github.com/mcarlson94/parentpresents-web)
- **Mevcut Sorun:** *"Record platform decisions: database engine, data access, and auth for /admin: ```yaml source: Backlog seeding, issue #11 related_post_slug: dependencies: [] started_at: 2026-09-15T10:01:14Z completed_at: result: ```  ## Goal  Produce a single platfor"*
- **Bağlam & Teşhis:** Parentpresents projesinde veritabanı ve erişim kararları backlog seeding başlığı altında toplanmış.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Database Engine & Data Access Decisions)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @mcarlson94 — saw your platform decision roadmap in issue #13 regarding database engine and data access setup. Once your database schema stabilizes, `ai-db-seeder` can automate your local test data generation without manual fixtures."*

### Lead #15: [https://github.com/schplitt/iso4/issues/82](https://github.com/schplitt/iso4/issues/82)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [schplitt](https://github.com/schplitt) | Repo: [schplitt/iso4](https://github.com/schplitt/iso4)
- **Mevcut Sorun:** *"design: SQLite support — per-prefix databases, multiple warm instances writing the same DB: Design issue — options and open decisions, no implementation. Direction stated 2026-08-10 and reaffirmed 2026-08-14: prefixes get SQLite databases, alongside "*
- **Bağlam & Teşhis:** SQLite çoklu instance desteği ve per-prefix mimarisi tartışması.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (SQLite Database Architecture)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @schplitt — saw your design discussion around per-prefix SQLite databases in issue #82. If you need automated population or constraint-checked state seeding across those SQLite instances, `ai-db-seeder` provides native SQLite seed generation."*

### Lead #16: [https://github.com/BoloDB/bolodb/issues/238](https://github.com/BoloDB/bolodb/issues/238)
- **Kaynak / Tip:** `github_issue`
- **İletişim / Profil:** GitHub: [BoloDB](https://github.com/BoloDB) | Repo: [BoloDB/bolodb](https://github.com/BoloDB/bolodb)
- **Mevcut Sorun:** *"Post-Query Data Filtering & Sorting: ## Problem Statement  Query results are displayed as static tables with no client-side filtering, sorting, or searching. Users must modify their SQL to change result ordering or filter rows, which is inefficient f"*
- **Bağlam & Teşhis:** BoloDB reposunda statik tablolar ve veri filtreleme tartışması.
- **Aciliyet:** ⚪ **LOW**
- **ai-db-seeder Çözüyor mu?:** ⚠️ PARTIAL (Post-Query Filtering & Analytics)
- **Önerilen Kişiselleştirilmiş Outreach Taslağı:**
  > *"Hi @BoloDB — saw your discussion in issue #238 regarding static table displays and filtering. If you need large, realistic relational datasets to benchmark query sorting and UI table rendering, `ai-db-seeder` generates scalable test volumes instantly."*

---

## 🛡️ OUTREACH PROTOKOLÜ VE ETİK KURALLAR
1. **Spam Kesinlikle Yasaktır:** Asla genel kopyala-yapıştır mesajlar atılmayacaktır. Her mesaj geliştiricinin paylaştığı issue numarasına, hata loguna veya mimari kararına doğrudan atıfta bulunacaktır.
2. **Değer Odaklı Yaklaşım ('Give Before You Ask'):** 'Ürünümüz çıktı hemen deneyin' yerine 'Projenizdeki güvenlik audit hatasını giderecek bir PR açabiliriz' veya 'Windows'ta çalışacak hazır konfigürasyonu paylaşabiliriz' şeklinde somut mühendislik yardımı teklif edilecektir.
3. **Onay Kilidi:** Hiçbir mesaj Claude Şef'in açık onayı olmadan GitHub veya X üzerinden gönderilmeyecektir.