# V1.1 — Competitor Pricing Evidence Package

**Tarih:** 2026-09-01  
**Tür:** Competitor Pricing Research — READ-ONLY  
**Governance Zinciri:** P1.8 → Validation Sprint V1 → V1.1  
**APE Rolü:** Search · Collect · Normalize · Provenance. H1f WTP hükmü vermemek.

---

## Metodoloji Notu

Her fiyat gözlemi için şu alanlar kayıt altına alınmıştır:

- `price_value` / `price_unit` / `currency`
- `source_type`: PRIMARY (vendor official) veya SECONDARY (analysis/community)
- `source_url` / `accessed`
- `what_included` / `what_excluded`
- `customer_segment`
- `confidence`: HIGH (primary, güncel) / MEDIUM (secondary) / LOW (eski veya tahmini)
- `edge_relevance`: Araştırma konusuyla doğrudan ilgisi

**Kurallar:**
- Birden fazla fiyat modeli zorla tek metriğe normalize edilmedi.
- `NOT_FOUND` açıkça işaretlendi.
- "Bu H1f'yi destekliyor" şeklinde sonuç çıkarılmadı.
- Lista fiyatı ile gerçek kullanım maliyeti ayrıştırıldı.

---

## Araştırılan Ürünler

1. Datadog — Log Management
2. Honeycomb — Observability Platform
3. Grafana Cloud — Loki (log ingestion)
4. New Relic — Data Ingest
5. OSS self-hosted stack (referans maliyet profili)

---

## 1. Datadog — Log Management

### Pricing Model: "Logging without Limits"

İki ayrı sayaç. Bunlar **toplanarak** gerçek fatura oluşur.

#### 1a. Log Ingestion (sayaç 1)

| Alan | Değer |
|:---|:---|
| `price_value` | $0.10 |
| `price_unit` | per GB ingested |
| `currency` | USD |
| `source_type` | SECONDARY (signoz.io, doit.com — primary page JS-rendered, fiyat çıkarılamadı) |
| `source_url` | https://signoz.io/blog/datadog-pricing/ ; https://doit.com/blog/datadog-log-management-pricing/ |
| `accessed` | 2026-09-01 |
| `what_included` | Parsing, enrichment, routing — tüm ingested log |
| `what_excluded` | Indexing (ayrı sayaç); retention > 15 gün |
| `customer_segment` | Tüm müşteriler; plan bağımsız |
| `confidence` | MEDIUM (secondary source; Datadog official page JS-rendered, ham değer alınamadı) |
| `edge_relevance` | Doğrudan. Edge gateway log hacmi bu fatura bileşenini etkiler. |

#### 1b. Log Indexing (sayaç 2 — searchability için)

| Alan | Değer |
|:---|:---|
| `price_value` | $1.06 – $2.50 |
| `price_unit` | per million log events (retention'a göre) |
| `currency` | USD |
| `source_type` | SECONDARY (signoz.io, doit.com) |
| `source_url` | https://signoz.io/blog/datadog-pricing/ |
| `accessed` | 2026-09-01 |
| `what_included` | Log arama, dashboard, alert |
| `what_excluded` | Archive (S3 vb.) yalnız indexing için geçerli değil |
| `customer_segment` | Indexing seçen müşteriler; opsiyonel |
| `confidence` | MEDIUM |
| `edge_relevance` | Orta. Edge gateway event hacmi Kubernetes'te hızla büyüyebilir. |

**Benchmark reference (secondary):** Community raporları 30–40% underestimate yaygın; Kubernetes'te "pod-per-agent misconfiguration" maliyet spike riski belgelenmiş. Kaynak: groundcover.com, openobserve.ai.

#### 1c. Gerçek Kubernetes Maliyeti — Toplam Fatura Yapısı

Datadog için Kubernetes ortamında ek bileşenler faturaya eklenir:

| Bileşen | Fiyatlandırma Yöntemi |
|:---|:---|
| Infrastructure Monitoring | Per-host, high-water mark |
| APM | Per-host |
| Log Ingestion | Per GB |
| Log Indexing | Per million events |
| Custom Metrics | Per metric |

**NOT:** "Per-host log cost" hesabı Kubernetes'te yanıltıcıdır (log hacmi host sayısıyla linear değil büyür). Bu nedenle "per gateway cost" estimate NOT_FOUND — edge-specific fiyatlandırma Datadog'da yoktur.

**"Datadog Whisperer" Gözlemi (community):** Büyük org'larda Datadog harcamasını optimize etmek için özel rol oluşturulduğu community'de raporlanmış. Kaynak: groundcover.com blog, 2024.

---

## 2. Honeycomb — Observability Platform

### Pricing Model: Events per Month

Honeycomb GB yerine olay (event) sayıyor.

#### 2a. Plan Tiers

| Alan | Free | Pro | Enterprise |
|:---|:---:|:---:|:---:|
| `price_value` | $0 | ~$130–150/month starting | Custom |
| `price_unit` | — | per month | — |
| `currency` | — | USD | — |
| `event_allowance` | 20M events/month | 100M–1.5B events/month | >1.5B/year |
| `source_type` | SECONDARY (monitoringcost.com, motadata.com; confirmed primary page accessible) |
| `source_url` | https://monitoringcost.com/honeycomb ; https://honeycomb.io/pricing |
| `accessed` | 2026-09-01 |
| `confidence` | MEDIUM-HIGH (secondary verified against primary page title) |
| `edge_relevance` | Orta. Edge Kubernetes cluster event hacmi kullanım senaryosuna bağlı. |

#### 2b. Event Definition

1 event = 1 structured record (1 log satırı, 1 trace span, 1 metrik data point).

**Edge bağlamı:** Edge gateway, ağ kesintisi ve log buffering senaryolarında olay gönderimi batch veya gecikmeli olabilir. Bu Honeycomb'un "per event" modelini nasıl etkiler: billing timestamp'i gateway'in gönderdiği an mı, origination timestamp mı — NOT_FOUND.

#### 2c. Edge / Self-Hosted Seçeneği

Honeycomb'da `Private Cloud` deployment opsiyonu var. Pricing: Custom / Enterprise tier. Kaynak: honeycomb.io/platform/private-cloud (tespit edildi, fiyat NOT_FOUND).

---

## 3. Grafana Cloud — Loki (Log Ingestion)

### Pricing Model: Per GB (Processing + Writing ayrı sayaçlar)

#### 3a. Fiyat Bileşenleri

| Bileşen | Rate |
|:---|:---:|
| Processing | $0.05/GB |
| Writing | $0.40/GB |
| **Effective Total** | **~$0.45/GB** |
| Extended Retention (>30 gün) | +$0.10/GB per 30-day increment |
| Query overage | $0.003/GB |
| Free tier | 50 GB/month; 14-gün retention |
| `source_type` | PRIMARY (grafana.com/pricing) |
| `source_url` | https://grafana.com/pricing/ |
| `accessed` | 2026-09-01 |
| `confidence` | HIGH |
| `edge_relevance` | Yüksek. Loki, P1 evidence'ında (ev_p1_001) mevcut stack olarak tespit edilmişti. |

#### 3b. Grafana Cloud vs Self-Hosted Loki

Self-hosted Loki: Ücretsiz OSS. Maliyet = operasyonel yük (engineering time, infrastructure).

**Önemli:** ev_p1_001, self-hosted Loki/Fluentbit'in **kaynak tüketimini** (CPU/bellek) sorun olarak raporluyor — lisans maliyetini değil. Bu ayrım önemlidir: Grafana Cloud pricing doğrudan bu sorunla ilgili değildir; OSS Loki kullanım maliyeti farklıdır.

---

## 4. New Relic — Data Ingest

### Pricing Model: Unified Per GB (tüm telemetri)

#### 4a. Data Ingest Rates

| Plan | Rate | Free Allowance |
|:---|:---:|:---:|
| Standard / Pro | $0.40/GB overage | 100 GB/month |
| Data Plus | $0.60/GB overage | 100 GB/month |
| `source_type` | PRIMARY (newrelic.com/pricing) |
| `source_url` | https://newrelic.com/pricing |
| `accessed` | 2026-09-01 |
| `confidence` | HIGH |
| `edge_relevance` | Orta. New Relic P1 evidence'ında geçmiyor; karşılaştırmalı referans. |

#### 4b. Kubernetes-Specific

No per-host/container fees — volume-only. Edge auto-scaling maliyet üretmez; yalnızca telemetri hacmi.

---

## 5. OSS Self-Hosted Stack — Referans Maliyet Profili

OSS alternatifleri: Grafana + Loki + Prometheus + Vector + ClickHouse

| Bileşen | Lisans Maliyeti | Operasyonel Maliyet |
|:---|:---:|:---:|
| Grafana OSS | $0 | — |
| Loki | $0 | Engineering overhead |
| Prometheus | $0 | — |
| Vector | $0 | — |
| ClickHouse OSS | $0 | — |
| **Toplam lisans** | **$0** | — |
| **Gerçek maliyet** | — | DevOps engineering time |

**Kaynak:** community consensus (Reddit, HackerNews), secondary.

**"Build vs Buy" notasyonu (community):**
> OSS stack can eliminate per-GB vendor bills but shifts cost to engineering time for maintenance, scaling, and operational overhead.

Kaynak: reddit.com/r/devops, 2024. NOT_FOUND: quantified engineering hours.

---

## 6. Normalized Comparison Table (Ham Fiyatlar)

**Uyarı:** Farklı fiyatlandırma modelleri. Doğrudan karşılaştırma kısıtlı; önce ham veri.

| Ürün | Fiyatlandırma Birimi | Temel Oran | Ücretsiz Tier | Model Türü |
|:---|:---|:---:|:---:|:---|
| Datadog Log Ingest | Per GB | $0.10/GB | Yok | Usage |
| Datadog Log Index | Per M events | $1.06–$2.50/M | Yok | Usage |
| Honeycomb Pro | Per month starting | ~$130/mo | 20M events | Tier |
| Grafana Cloud Loki | Per GB | ~$0.45/GB | 50 GB | Usage |
| New Relic | Per GB | $0.40/GB | 100 GB | Usage |
| OSS Stack | $0 | $0 | Unlimited | OpEx only |

**Uyarı notu:** Datadog'un ikili sayacı (ingestion + indexing) diğerleriyle karşılaştırılamaz; toplam fatura ikisinin toplamıdır.

---

## 7. Edge/Kubernetes Bağlamına Özel Gözlemler

| Gözlem | Kaynak | Güç |
|:---|:---|:---:|
| Datadog'da "per-host" hesabı Kubernetes'te yanıltıcı; log hacmi bağımsız büyüyor | doit.com, signoz.io | MODERATE |
| Kubernetes'te pod-per-agent misconfiguration → maliyet spike riski | openobserve.ai, signoz.io | MODERATE |
| Datadog faturasının 30–40% underestimate yaygın community raporu | groundcover.com | WEAK (single source) |
| "Datadog Whisperer" rolü büyük org'larda belgelenmiş | groundcover.com | WEAK (single source) |
| Telemetry pipeline (Cribl, OTel collector) maliyet yönetimi için yaygın kullanılıyor | dataintelo.com | MODERATE |
| OSS stack lisans $0 fakat operasyonel yük var | Reddit, HackerNews community consensus | MODERATE |

---

## 8. NOT_FOUND Listesi (Eksik Veri Envanteri)

| Aranan Veri | Neden Bulunamadı |
|:---|:---|
| Datadog edge/IoT özel fiyatlandırma | Böyle bir segment yoktur; tüm deploymentlar aynı model |
| Honeycomb per-event edge batch billing | Private Cloud fiyatı custom/enterprise |
| Gerçek müşteri Datadog aylık fatura (edge K8s) | Gizli / contract |
| Honeycomb actual contract size (enterprise edge) | Gizli |
| Self-hosted OSS engineering hours per org | Quantified data not found |
| "Acceptable price point for edge log buffering agent" | WTP araştırması gerekiyor — H1f |

---

## 9. Implications (APE Yorumu — WTP Hükmü Değil)

Aşağıdaki ifadeler gözlemlenen fiyatlara dayalı teknik çıkarımlardır. WTP hükmü değildir.

1. **Datadog ve Honeycomb cloud modeller, düşük-kaynak edge gateway'ler için optimize edilmemiştir.** Edge-specific deployment seçeneği veya fiyatlandırması yoktur.

2. **Grafana Cloud Loki $0.45/GB gerçek kullanım maliyeti**, ev_p1_001'deki "OSS Loki yüksek kaynak tüketiyor" sorununu ele almaz; OSS Loki ve Cloud Loki aynı ürünün farklı deployment modelleridir.

3. **OSS stack lisans maliyeti $0** — ancak kaynak tüketim (ev_p1_001) veya offline buffering (ev_p1_004) sorunlarını da otomatik çözmez.

4. **Community kayıtlarında maliyet şikayeti** var (Datadog bill shock, Honeycomb cost management). Bunlar H1b için sinyal üretir; WTP için kanıt değildir.

---

## 10. Governance

| Bileşen | Durum |
|:---|:---:|
| G3b artifacts | 🔒 UNCHANGED |
| Scorer v1 | 🔒 FROZEN |
| P1.1–P1.8 artifacts | 🔒 FROZEN |
| Bu belge | READ-ONLY research output |
| H1f WTP hükmü | ❌ APE tarafından verilmedi |

---

## 11. V1.2 İçin Önerilen Sonraki Araştırma

Bu belge V1.1'i tamamlar. V1.2 (Community Evidence) için:

1. GitHub Issues'ta "Loki edge ARM64 resource" araması → H1d için daha fazla gözlem
2. HackerNews "Datadog bill" + "kubernetes" araması → H1b için bağlamlı maliyet şikayeti
3. Reddit r/devops'ta "self-hosted observability" → H1e için sosyal kanıt

**V1.1 → V1.2 Geçiş Notu:** Bu package'ta birincil WTP kanıtı üretilmedi. H1f için customer interview hâlâ sıfır kanıta sahip. Bu P1.8'deki known unknowns listesiyle tutarlıdır.

---

*V1.1 Competitor Pricing Evidence Package — COMPLETED*  
*G3b: UNCHANGED · Scorer v1: FROZEN · Datasets: UNTOUCHED*  
*APE rolü bu belgede tamamlandı: Search · Collect · Normalize · Provenance*
