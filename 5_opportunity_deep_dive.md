# 5 Opportunity Candidates — Market Deep Dive

**Tarih:** 2026-09-02
**Hedef:** 5 Adayı 3'e İndirmek İçin Pazar Gerçekleri.

---

## 1. Missed Call AI Receptionist (Eski #12)
**1. GERÇEK MÜŞTERİ SİNYALİ:** KOBİ'ler (tesisatçı, dişçi vb.) kaçan çağrı başına fırsat maliyetini hesaplayabiliyor. "Missed-call text-back" (cevapsız çağrıya otomatik SMS) özelliği için ödeme yapılıyor.
**2. GÜNCEL RAKİPLER:** 
- *Smith.ai / Ruby:* (Managed, insan destekli) $250+/ay.
- *Goodcall / Synthflow / BlandAI altyapılı ajanslar:* $50 - $200/ay.
**3. BAŞARISIZ/TERK EDİLMİŞ ÖRNEK:** "AI Voice" (sesli bot) projelerinin %65-95'i (özellikle SMB'lerde) ilk 60 günde iptal ediliyor. Neden: Botun karmaşık konuşmalarda halüsinasyon görmesi ve CRM'e (ServiceTitan vb.) entegre olamaması müşteriyi kızdırıyor.
**4. CUSTOMER ACQUISITION:** Yerel işletmelere doğrudan soğuk arama (cold call) veya "Google İşletmem" üzerinden kaçan çağrı simülasyonu gönderimi.
**5. DIFFERENTIATION:** Sesli AI (ki bu sık çöküyor) yerine **sadece SMS ile "Randevu ayarlayalım mı?" diyen "Text-back"** odaklı, çok daha hatasız bir sistem kurmak.
**6. 7-DAY MVP:** Sadece Twilio + basit bir webhook. Çağrı düştüğünde Twilio API ile müşteriye "Şu an meşgulüm, size nasıl yardımcı olabilirim?" SMS'i atılır. AI bile gerekmeyebilir.
**7. FIRST MONEY:** Bölgesel bir tesisatçıya "Kaçan müşteri başına 10$" veya sabit "50$/ay" modeli.
**HÜKÜM:** **KEEP** (Ama Sesli AI değil, Text-back otomasyonu olarak).

---

## 2. Codebase Technical Debt Audit Service (Eski #14)
**1. GERÇEK MÜŞTERİ SİNYALİ:** M&A (Birleşme & Satın Alma) ve Due Diligence süreçlerinde yatırımcılar kodu denetletmek için her zaman bütçe ayırır.
**2. GÜNCEL RAKİPLER:** 
- *Danışmanlık Şirketleri (Boutique due diligence):* Kapsama göre $10K - $30K arası.
- *Otomatik Araçlar:* Code Climate, SonarQube (fakat bunlar yönetici özeti sunmaz).
**3. BAŞARISIZ/TERK EDİLMİŞ ÖRNEK:** Sadece "Linting/Statik kod analizi" hatalarını PDF'e basıp 1000$ isteyen servisler yatırımcılar tarafından reddediliyor çünkü "iş riski" (business risk) sunmuyorlar.
**4. CUSTOMER ACQUISITION:** LinkedIn'de yatırım (Seed/Series A) arayan startupların CTO'larına veya küçük PE (Private Equity) şirketlerine ulaşmak.
**5. DIFFERENTIATION:** Çıktıyı yazılımcıya değil, "Yatırımcıya/CEO'ya" yönelik (Örn: "Bu kod tabanının bakım maliyeti aylık +$5000 ekstra yük getirir") finansal/risk dilinde veren AI destekli bir rapor.
**6. 7-DAY MVP:** Sadece bir Landing Page. Bize GitHub repo erişimi verin, 48 saat içinde manuel + LLM destekli "Tech Debt Executive Report" verelim. Fiyat: $499.
**7. FIRST MONEY:** Stripe linki ile tek seferlik rapor satışı.
**HÜKÜM:** **KEEP** (Satış döngüsü uzun olabilir ama tek satış yüksek marjlı).

---

## 3. Invoice → ERP / WhatsApp Automation (Eski #11)
**1. GERÇEK MÜŞTERİ SİNYALİ:** Taşeron, nakliye ve küçük inşaat firmalarının sahadaki şoförleri/elemanları faturaları buruşturup getiriyor. Veri girişi personeline maaş ödeniyor.
**2. GÜNCEL RAKİPLER:** 
- *Tipalti / Stampli:* Enterprise çözümler (Çok pahalı ve WhatsApp destekleri zayıf).
- *V7 Go / Rossum:* IDP (Intelligent Document Processing) SaaS'ları (Genelde aylık $1000+).
**3. BAŞARISIZ/TERK EDİLMİŞ ÖRNEK:** OCR kullanan klasik sistemler başarısız oluyor. Şirketler "el yazısı/buruşuk fiş" okunamadığı için insan müdahalesine dönüyor ve ROI kayboluyor.
**4. CUSTOMER ACQUISITION:** Bölgesel nakliye veya inşaat firmalarına (Örn. Kocaeli/Gebze sanayisi) kapıdan satış veya doğrudan WhatsApp üzerinden demosu atılarak.
**5. DIFFERENTIATION:** Şirket personeline yeni bir "App" indirtmemek. Sadece "WhatsApp'tan fişin fotoğrafını at" demek. Arkada Vision LLM'leri ile veriyi ayıklamak.
**6. 7-DAY MVP:** WhatsApp Business API -> Make.com -> OpenAI Vision -> Google Sheets (ERP öncesi Excel kanıtı).
**7. FIRST MONEY:** "Ayda 100 fiş işleme: $99/ay" kurulum bedeliyle lokal bir işletmeye doğrudan elden/havale ile satış.
**HÜKÜM:** **KEEP** (Lokal piyasada en hızlı paraya dönüşebilecek model).

---

## 4. AI Content Repurposing Service for B2B Execs (Eski #13)
**1. GERÇEK MÜŞTERİ SİNYALİ:** B2B yöneticileri (Founder/CEO) LinkedIn'de aktif olmak zorunda olduklarını biliyor ama vakitleri yok. Ghostwriting için bütçe ayırıyorlar.
**2. GÜNCEL RAKİPLER:** 
- *Freelance Ghostwriters / Butik Ajanslar:* $1500 - $5000/ay.
- *Otomatik Araçlar (OpusClip, Distribution AI vb.):* $20 - $110/ay.
**3. BAŞARISIZ/TERK EDİLMİŞ ÖRNEK:** "AI ile ayda 100 post at" diyen düşük kaliteli (AI slop) servisler terk ediliyor çünkü etkileşim (pipeline/lead) getirmiyor, sadece şirketin itibarını zedeliyor.
**4. CUSTOMER ACQUISITION:** LinkedIn üzerinden "Cold DM" atarak onlara özel, eski bir podcastlerinden üretilmiş 1 adet bedava yüksek kaliteli post hediye etmek.
**5. DIFFERENTIATION:** Prompt engineering'i satmak değil; "Haftada 1 saat ses kaydı verin, biz onu LLM + İnsan editörle markanıza dönüştürelim" (Productized Service) demek.
**6. 7-DAY MVP:** Landing page. "Sadece 3 müşteri alıyoruz." Arkada Claude/Gemini kullanarak manuel iş akışı (SaaS yok).
**7. FIRST MONEY:** Bir CEO'ya "İlk ay $500 deneme" paketi kesmek.
**HÜKÜM:** **WEAKEN** (Rekabet çok yüksek ve hizmet/insan eforu (editing) 7 gün MVP sonrası çok yorucu olabilir. SaaS veya otomasyon ölçeklenebilirliği düşük).

---

## 5. Agent Workflow / Automation Templates (Eski #6)
**1. GERÇEK MÜŞTERİ SİNYALİ:** İnsanlar ChatGPT kullanmayı öğrendi ama bunu iş akışına (Zapier/Make) bağlamayı bilmiyor ve vakit kaybediyor.
**2. GÜNCEL RAKİPLER:** 
- *Neura Market / No-Code Marketplace:* Premium blueprint satan platformlar.
- *Gumroad Creators:* Şablon bundle'larını $20 - $150'a satan indie hacker'lar.
- *Zapier/Make Native:* Ücretsiz (fakat jenerik) şablonlar.
**3. BAŞARISIZ/TERK EDİLMİŞ ÖRNEK:** Basit "Twitter to Slack" gibi şablonları satmaya çalışanlar başarısız oluyor çünkü native araçlar bunu bedava veriyor.
**4. CUSTOMER ACQUISITION:** YouTube veya Twitter'da eğitici bir video çekip "Bu sistemi (örn: otomatik lead kalifikasyonu) kendiniz kurmak isterseniz link aşağıda" diyerek satmak.
**5. DIFFERENTIATION:** Teknik şablon satmak yerine "İş Sonucu" satmak. Örneğin "Make.com Template" yerine "Small Business Lead Triage System" adıyla paketlemek.
**6. 7-DAY MVP:** Çalışan, 5 adımlı karmaşık ve değerli bir Make.com workflow'unu dışa aktarıp (export) Gumroad'a $49'a koymak ve Twitter'da flood yazmak.
**7. FIRST MONEY:** Gumroad (Dijital ürün indirimi).
**HÜKÜM:** **KEEP** (Yapması en hızlı, maliyeti sıfır. Ancak organik izleyici/trafik bulmak satışın kilidi).
