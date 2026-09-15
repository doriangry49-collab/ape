# Validation Sprint V1 — H1 Validation Plan

**Tarih:** 2026-09-01  
**Tür:** Human-led Validation Plan — Sıfır Kod / Sıfır Mimari Değişikliği  
**Governance Zinciri:** G3b → P1.1–P1.8 → Bu belge  
**Temel Soru:** *H1 gerçek dünyada doğrulanabilir bir ürün fırsatı mı?*

---

## 0. Metodolojik İlke

> **Bu plan H1'i kanıtlamaya değil, yanlışlamaya çalışır.**

Mevcut P1 evidence'ı (4 observation, 2 sinyal, 0 doğrulanmış WTP) bir fırsat *olabileceğini* gösteriyor. Olduğunu kanıtlamıyor.

Validation'ın görevi:

```text
H1'i yanlışlamak için minimum maliyetli, maksimum bilgi içerikli
kanıtlar toplamak. Yanlışlanamıyorsa ve pozitif sinyal yeterliyse:
H1 → validated → next investment.
```

Sıralama kasıtlı: **önce en kolay yanlışlanabilir önermeler.**

---

## 1. Hypothesis

**H1 Primary:**

> *"Edge-first, offline-capable, resource-efficient log collection and buffering agent için gerçek kullanıcı problemi ve ödeme isteği mevcut."*

**H1 Decomposition:**

| ID | Alt Hipotez | Kritiklik | Mevcut Kanıt |
|:---|:---|:---:|:---|
| H1a | Edge log infrastructure problemi sık yaşanıyor | 🔴 | ev_p1_001, ev_p1_002 (2 gözlem) |
| H1b | Problem yeterince pahalı/acılı (switching motivasyonu var) | 🔴 | ev_p1_002 (maliyet sinyal; miktar bilinmiyor) |
| H1c | Offline/store-and-forward gerçek bir tasarım kısıtı | 🟠 | ev_p1_004 (1 gözlem) |
| H1d | Resource footprint kritik satın alma kriteri (hard requirement) | 🟠 | ev_p1_001 (1 gözlem) |
| H1e | Mevcut çözümler (Datadog/Loki) bu bağlamda yeterince kötü | 🟠 | ev_p1_001, ev_p1_002 |
| H1f | Kullanıcılar H1 çözümü için ödeme yapar (WTP > 0) | 🔴 | **Hiç yok** |

**Karar ağırlıkları:**
- H1a ❌ VEYA H1f ❌ VEYA H1b ❌ → **H1 REJECT / REFORMULATE** (devam anlamsız)
- H1a ✅ + H1b ✅ + H1f ✅ + H1c/H1d/H1e'den ≥ 2 ✅ → **H1 VALIDATED**
- Karma sinyal → **H1 CONDITIONAL** (hipotezi daralt veya yeniden yaz)

---

## 2. Falsification Criteria (Yanlışlama Koşulları)

H1'in reddedileceği gözlem örnekleri:

```text
H1a FAIL:
  Hedef kullanıcıların çoğunluğu log altyapısını
  düşük öncelikli veya nadiren sorunlu olarak rapor ediyor.

H1b FAIL:
  Kullanıcılar mevcut çözümle "idare edilebilir" diyor;
  aktif arayış veya bütçe tahsisi yok.

H1c FAIL:
  Kullanıcılar reliable connectivity'e sahip;
  offline-first gereksinimleri raporlamıyor.

H1d FAIL:
  Kaynak kısıtı bir problem değil; kullanıcılar
  yeterince güçlü donanım kullanıyor.

H1e FAIL:
  Loki/Fluentbit veya benzer stack yeterince iyi;
  kullanıcılar alternatif aramıyor.

H1f FAIL:
  Kullanıcılar yalnızca ücretsiz/OSS çözüm kullanıyor;
  budget yoksa veya WTP < yapılabilir fiyat eşiği.
```

---

## 3. Evidence Requirements Per Sub-Hypothesis

Her alt hipotezin doğrulanması için gereken **minimum kanıt eşiği ve kaynağı:**

### H1a — Problem Frequency

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 5 bağımsız rapor (farklı organizasyonlardan) |
| Kabul edilebilir kaynak türleri | Müşteri interview, GitHub Issues/Discussions, forum thread, Stack Overflow |
| Mevcut durum | ev_p1_001 + ev_p1_002 = 2 sinyal (YETERSİZ) |
| Eksik | 3+ ek bağımsız gözlem |
| Contradictory evidence kuralı | 2+ "problem yok" raporu → H1a CONDITIONAL |

### H1b — Problem Severity / Switching Motivation

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 3 interview'da açık "bütçe harcıyorum / harcardım" ifadesi VEYA kanıtlanmış churn/maliyet rakamı |
| Mevcut durum | ev_p1_002: "expensive cloud bills" — miktar/bütçe yok (YETERSİZ) |
| Eksik | Datadog/Honeycomb maliyet verisi + interview doğrulaması |
| Contradictory evidence | "Maliyeti önemsemiyoruz" → H1b CONDITIONAL |

### H1c — Offline/Store-and-Forward Requirement

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 2 bağımsız kullanım bağlamı raporu |
| Mevcut durum | ev_p1_004 = 1 sinyal (MARGINAL) |
| Eksik | 1+ ek bağımsız gözlem (interview veya forum) |
| Contradictory evidence | "Bağlantımız güvenilir" → H1c FAIL |

### H1d — Resource Footprint as Hard Requirement

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 2 kullanıcı "resource limit = blocker" olarak tanımlıyor |
| Mevcut durum | ev_p1_001 = 1 sinyal (MARGINAL) |
| Eksik | 1+ ek bağımsız gözlem |
| Contradictory evidence | "Donanımımız yeterli" → H1d FAIL |

### H1e — Existing Solutions Inadequate

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 2+ gözlem, spesifik failure mode ile |
| Mevcut durum | ev_p1_001 (Loki kaynak), ev_p1_002 (Datadog maliyet) = 2 sinyal (MARGINAL) |
| Eksik | Daha spesifik "Loki/Fluentbit bunu yapamıyor" örnekleri |
| Contradictory evidence | "Mevcut stack iyi çalışıyor" → H1e CONDITIONAL |

### H1f — Willingness to Pay (KRITIK — Mevcut Kanıt YOK)

| Gereksinim | Detay |
|:---|:---|
| Minimum kaynak | 3 interview'da açık WTP ifadesi VEYA karşılaştırmalı fiyat araştırması |
| Mevcut durum | **Sıfır kanıt** |
| Öncelik | 🔴 EN YÜKSEKPRİORİTE — negatif sonuç tüm hipotezi geçersiz kılar |
| Kabul eşiği | Potansiyel ödeme isteği > makul ürün fiyat eşiği (ör. $50–500/ay per gateway) |
| Contradictory evidence | "OSS only" veya "hiç para ödemeyiz" → H1f FAIL |

---

## 4. Validation Actions

**İlke:** Minimum maliyet — maksimum bilgi. Pahalı/yavaş eylemler sona.

### Sequence (Önce En Kolay Yanlışlanabilir)

```
PHASE 1 — Desk Research (APE-assisted, ~1 hafta)
   ├── V1.1  Competitor pricing research
   │         Datadog/Honeycomb edge K8s maliyet noktaları
   │         → H1b, H1e için temel veri
   │
   ├── V1.2  Extended community evidence
   │         GitHub Issues, HackerNews, Reddit'te
   │         H1a/H1c/H1d için 3+ ek gözlem arama
   │         → ev_p1_001..004'ü destekleme veya çürütme
   │
   └── V1.3  Source independence audit
             ev_p1_001..004'ün bağımsız mı yoksa aynı
             kaynak raporundan mı türediğini doğrulama

PHASE 2 — Customer Discovery (Human-led, ~2-3 hafta)
   ├── V2.1  5–10 interview: edge K8s operators
   │         → H1a, H1b, H1c, H1d, H1f
   │
   ├── V2.2  3–5 interview: industrial IoT/OT operators
   │         → H1c, H1d segment doğrulama
   │
   └── V2.3  2–3 interview: former Datadog/Honeycomb customers
             → H1e, H1f, competitive switching data

PHASE 3 — Technical Validation (Human + APE, ~1 hafta)
   └── V3.1  ARM64 prototype feasibility
             ev_p1_003 benchmark'ının gerçek
             production workload'ında tekrarlanabilirliği
             → H1d teknik temel
```

### APE'nin Rolü vs İnsan'ın Rolü

| Eylem | Kimin Görevi |
|:---|:---|
| Competitor pricing research (V1.1) | APE (search + collect + trace) |
| Community evidence search (V1.2) | APE (search + normalize + report) |
| Source independence audit (V1.3) | APE (cross-reference check) |
| Customer interviews (V2.1, V2.2, V2.3) | **İnsan** |
| WTP yorumlama | **İnsan** |
| Alt hipotez kararları (pass/fail) | **İnsan** |
| ARM64 prototype deployment (V3.1) | **İnsan** (APE benchmark analizi destekler) |
| H1 final hükmü | **İnsan** |

---

## 5. Decision Rules — Phase Gate

### Phase 1 Sonrası Gate

```
IF V1.1 shows Datadog/Honeycomb edge price < $100/gateway/month
   → H1b ekonomik argümanı zayıflıyor → Phase 2'de özellikle test et

IF V1.2 <3 yeni bağımsız gözlem bulundu
   → H1a kanıt temeli zayıf → Phase 2 öncelikli

IF V1.3 ev_p1_001..004 aynı kaynaktan türüyor
   → P1 evidence base temelden zayıf → H1'i askıya al
```

### Phase 2 Sonrası Gate (Kritik)

```
IF H1f FAIL (WTP yok veya çok düşük)
   → STOP. H1 REJECT. P1 kapatılır.

IF H1a + H1b + H1f PASS, H1c/H1d/H1e karma
   → H1 CONDITIONAL. Hipotezi daralt.

IF H1a + H1b + H1c + H1d + H1e + H1f PASS
   → H1 VALIDATED. Prototype fazına geç.
```

### Phase 3 Sonrası Gate

```
IF ARM64 prototype feasibility FAIL
   → H1 teknik temeli yeniden değerlendir.
   → ClickHouse/Vector CANDIDATE statüsünden çıkabilir.
```

---

## 6. Failure = Signal, Not Shame

```
H1 REJECT → Valuable outcome.
   Evidence says: this specific form is not a business.
   Next step: reformulate or pivot.

H1 CONDITIONAL → Valuable outcome.
   Evidence says: some sub-problems are real; others are not.
   Next step: narrow hypothesis.

H1 VALIDATED → Proceed with confidence backed by evidence.
```

P1 sürecinin metodolojisine uygun: **negatif kanıt da üretim çıktısıdır.**

---

## 7. Bağlam: Mevcut Kanıtın Yeterliliği

P1 evidence'ının Validation Sprint V1 başlangıcındaki yeterliliği:

| Alt Hipotez | Mevcut Kanıt | Validation Yeterliliği |
|:---|:---:|:---|
| H1a | 2 sinyal | ❌ Yetersiz (min: 5) |
| H1b | Kısmi | ❌ Yetersiz (miktar yok) |
| H1c | 1 sinyal | ❌ Marginal (min: 2) |
| H1d | 1 sinyal | ❌ Marginal (min: 2) |
| H1e | 2 sinyal | ❌ Marginal |
| H1f | **0 sinyal** | 🔴 **Kritik boşluk** |

Bu tablo validation fazının neden gerekli olduğunu kanıtlıyor.

---

## 8. İlk Görev

**V1.1 — Competitor Pricing Research (APE)**

APE'nin yapacağı:

```text
SEARCH: Datadog, Honeycomb, Elastic Cloud
       edge Kubernetes / IoT pricing

COLLECT: public pricing tiers, enterprise contract ranges,
        Reddit/HN maliyet şikayetleri

NORMALIZE: per-gateway / per-host / per-GB fiyatlandırma
          karşılaştırılabilir biçimde

REPORT:
  - Observed price range: X–Y $
  - Pricing model type
  - Edge-specific constraints
  - Source snapshots with provenance
```

**APE'nin yapmayacağı:**

```text
❌ Bu fiyatlardan "WTP bu kadar" sonucu çıkarmak
❌ H1b'yi otomatik olarak pass veya fail işaretlemek
❌ Yeni scorer veya evidence layer yazmak
❌ G3b, Scorer v1, datasets'e dokunmak
```

---

## 9. Governance

| Bileşen | Durum |
|:---|:---:|
| G3b artifacts | 🔒 UNCHANGED |
| Scorer v1 | 🔒 FROZEN |
| Datasets | 🔒 UNTOUCHED |
| P1.1–P1.8 artifacts | 🔒 FROZEN |
| Evidence ledger | APPEND-ONLY |

Validation Sprint V1 çıktıları ayrı `validation/` dizininde tutulur.
Mevcut hiçbir artifact değiştirilmez.

---

*Validation Sprint V1 — H1 Validation Plan — READ-ONLY governance document*  
*G3b: UNCHANGED · Scorer v1: FROZEN · Datasets: UNTOUCHED*
