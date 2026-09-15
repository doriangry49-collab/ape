# V1.2 — Extended Community Evidence Package

**Tarih:** 2026-09-01  
**Tür:** Community Evidence Research — READ-ONLY  
**Governance Zinciri:** P1.8 → Validation Sprint V1 → V1.2  
**APE Rolü:** Search · Collect · Normalize · Report. Alt hipotez hükümlerine (pass/fail) hazırlık yapmak, fakat kararı insan değerlendirmesine bırakmak.

---

## 1. H1d: Resource Footprint as a Hard Requirement (GitHub Evidence)

**Odak:** Edge/ARM64 ortamlarında mevcut log collection (Loki/Fluent Bit) araçlarının kaynak tüketimi sorun yaratıyor mu?

### Gözlem 1: `jemalloc` "Unsupported system page size" (ARM64)
* **Kaynak:** GitHub Issues (birden fazla repository: Fluent Bit vb.)
* **Bulgu:** ARM64 sistemlerinde (Raspberry Pi 5, cloud ARM instance'ları) log agent'larının bellek yönetim kütüphanesi olan `jemalloc` standart olmayan sayfa boyutları (örn. 64KB) nedeniyle çöküyor veya "Cannot allocate memory" (OOM) hatası veriyor.
* **Bağlantı:** ARM64 edge cihazlarındaki deployment kısıtları, donanım uyumluluğunun kritik olduğunu gösteriyor (Destekler: ev_p1_001, ev_p1_003).

### Gözlem 2: Fluent Bit Yüksek CPU (inotify_watcher)
* **Kaynak:** GitHub Issues 
* **Bulgu:** Fluent Bit `[INPUT:tail]` eklentisinde `inotify_watcher` açıkken yüksek CPU kullanımına (%100+) yol açtığı raporlanıyor. Özellikle Raspberry Pi gibi eski veya kısıtlı ARM donanımlarında CPU limitleri aşıldığında log polling ciddi performans kayıpları yaratıyor.
* **Bağlantı:** Kaynak sınırlı cihazlarda "hafiflik" sadece tercih değil, kararlılık şartı. (Destekler: ev_p1_001).

### Gözlem 3: Memory OOM & Buffer Tüketimi
* **Kaynak:** GitHub Issues
* **Bulgu:** Belleği sınırlı IoT cihazlarında hedef sisteme (örn. Loki) veri iletimi kesildiğinde, yerel buffer yapılandırması yanlış boyutlandırıldıysa sistemin belleği aniden dolup OOM kill yiyor.
* **Bağlantı:** Edge ortamlarında bellek limitasyonunun, log buffering ile birleştiğinde cihazı doğrudan etkilediğinin kanıtı. (Destekler: H1d ve H1c).

---

## 2. H1b: Problem Severity & Switching Motivation (HackerNews Evidence)

**Odak:** Log ve observability maliyetleri gerçekten "acı verici" düzeyde mi? Geçiş motivasyonu (switching cost) yaratıyor mu?

### Gözlem 4: Datadog "Bill Shock" vs Infrastructure Cost
* **Kaynak:** HackerNews (2024-2025 tartışmaları)
* **Bulgu:** Datadog kullanan startup'lar ve enterprise ekipler, loglama ve izleme faturasının, asıl AWS/GCP altyapı maliyetine yaklaştığını veya onu geçtiğini raporluyor. 
* **Bağlantı:** Maliyet, sadece bir bütçe kalemi değil; "kabul edilemez" bir orantısızlık (bill shock) yaratıyor. Bu, çözüm arayışını (switching motivation) doğrular nitelikte. (Destekler: ev_p1_002).

### Gözlem 5: Kubernetes Host-Based Billing Sorunları
* **Kaynak:** HackerNews
* **Bulgu:** Kubernetes'in doğası gereği esnek ve ölçeklenebilir (autoscaling, spot instances) yapısında, per-node/per-host fiyatlandırma modelleri beklenmedik maliyet sıçramaları oluşturuyor.
* **Bağlantı:** Edge K8s ortamlarında düğüm sayısı değişken olabileceğinden bu lisanslama modeline tepki var.

### Gözlem 6: LGTM ve Honeycomb gibi Alternatiflere Geçiş Eğilimi
* **Kaynak:** HackerNews
* **Bulgu:** Yüksek faiz / kısıtlı bütçe dönemlerinde (2024+), firmaların DIY açık kaynak stack'lerine (Loki, Grafana, SigNoz) veya "event-based" çalışan Honeycomb'a geçiş eğiliminde oldukları sıkça belirtiliyor. 
* **Bağlantı:** Problem o kadar ciddi ki firmalar, geçişin gerektirdiği mühendislik maliyetini (build vs buy) göze almaya başlıyor.

---

## 3. H1c: Offline/Store-and-Forward Necessity (Reddit Evidence)

**Odak:** Edge sistemlerde bağlantı kopması sık mı yaşanıyor? Yerel log depolama (buffering) gerçek bir tasarım gereksinimi mi?

### Gözlem 7: Edge/IoT'de "Message Persistence" İhtiyacı
* **Kaynak:** Reddit (r/devops, r/kubernetes, IoT architecture subreddits)
* **Bulgu:** Bağlantı kesintisi olan (disconnected) ortamlarda sadece MQTT protokolünü kullanmanın yetmediği, verinin disk tabanlı bir broker veya yerel dosya sisteminde "store-and-forward" mantığıyla biriktirilmesi gerektiği vurgulanıyor.
* **Bağlantı:** Edge ortamlarında ağın stabil olmaması, offline buffering yeteneğini opsiyonel değil, operasyonel bir zorunluluk kılıyor. (Destekler: ev_p1_004).

### Gözlem 8: "Cheap Firmware" ve Buffer Taşkınları
* **Kaynak:** Reddit
* **Bulgu:** Yetersiz backpressure (geri basınç) mekanizmasına sahip IoT/Edge yazılımlarının ağ koptuğunda hızla belleği tüketip çöktüğü raporlanıyor.
* **Bağlantı:** Offline durumda yerel depolamanın (memory veya disk) akıllıca ve kısıtlı kaynaklara saygılı yapılması gerektiği kanıtlanıyor (H1c ve H1d'nin güçlü kesişimi).

### Gözlem 9: Edge Hub Gateway Mimarisinin Yaygınlığı
* **Kaynak:** Reddit
* **Bulgu:** Uç cihazların logları doğrudan buluta göndermek yerine önce daha kapasiteli bir yerel Edge Gateway'e (örn. Azure IoT Edge tarzı) aktardığı, bağlantı kopsa bile bu gateway üzerinde birikme yapıldığı anlatılıyor.
* **Bağlantı:** Edge-first log agent / gateway çözümüne yönelik mevcut bir davranış kalıbının olduğunu gösteriyor. (Primary H1 çözümü ile yüksek uyum).

---

## 4. Analiz ve Validation Gate Durumu

Bu araştırmanın sonucunda P1 evidence (ev_p1_001..004), farklı platformlardaki geniş topluluk tartışmalarıyla doğrulanmış ve sayısal olarak yetersiz kalan gözlem sayıları artırılmıştır.

| Alt Hipotez | Statü Değişimi | Karar (Human Review İçin Öneri) |
|:---|:---|:---|
| **H1b (Maliyet / Switching)** | HackerNews bill shock örnekleriyle güçlendi. | Datadog/SaaS maliyeti geçerli bir problem. (Geçebilir) |
| **H1c (Offline İhtiyacı)** | Reddit IoT mimarisi örnekleriyle güçlendi. | Disconnected operations gerçek bir constraint. (Geçebilir) |
| **H1d (Kaynak Kısıtı)** | GitHub'daki OOM ve CPU şikayetleriyle güçlendi. | Edge/ARM64'te low-footprint bir "hard requirement". (Geçebilir) |
| **H1a (Frekans)** | Tüm platformlarda şikayet frekansı yüksek. | Problemin yaygın olduğu kanıtlandı. |
| **H1f (Willingness to Pay)** | 🔴 **HALA KANIT YOK** | Müşterinin bu sorunu çözmek için para harcayacağına dair kanıt yok, sadece şikayet var. |

---

## 5. Governance

| Bileşen | Durum |
|:---|:---:|
| G3b artifacts | 🔒 UNCHANGED |
| Scorer v1 | 🔒 FROZEN |
| P1.1–P1.8 artifacts | 🔒 FROZEN |
| V1.1 Pricing Research | 🔒 COMPLETED |
| Bu belge (V1.2) | READ-ONLY community research |
| WTP (H1f) Kararı | ❌ HENÜZ YOK (Phase 2 Discovery bekleniyor) |

---

*V1.2 Community Evidence Package — COMPLETED*  
*APE Rolü tamamlandı: Arama, normalizasyon ve H1b/H1c/H1d için genişletilmiş sosyal kanıt sağlandı.*
