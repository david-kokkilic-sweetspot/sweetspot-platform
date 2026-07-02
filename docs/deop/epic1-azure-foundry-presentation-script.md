# Epic 1 — AI Altyapısı & Azure AI Foundry Entegrasyonu
## Sunum Scripti

---

## 1. Giriş — Ne İnşa Ettik

> "Epic 1'de Sweetspot için production-grade bir AI altyapısı inşa ettik — platformdaki mevcut ve gelecekteki tüm AI özelliklerinin üzerinden geçtiği eksiksiz bir AI temel katmanı. Azure AI Foundry bizim launch provider'ımız. Mimariyi birlikte inceleyelim."

---

## 2. Mimari Genel Bakış — Provider-Agnostik Pipeline

> "Temel tasarım prensibi **provider-agnostik orkestrasyon**. Tek bir `IAiClient` kontratı inşa ettik — platformdaki her AI çağrısı bu tek arayüzden geçiyor. Arkasında, herhangi bir provider'a dokunulmadan önce cross-cutting concern'leri yöneten katmanlı bir pipeline bulunuyor."

**Pipeline aşamaları (sırasıyla):**

1. **Tenant İzolasyonu** — `ITenantAiClient`, HTTP request'ten `AccountId` + `UserId`'yi otomatik olarak inject eder. Hiçbir feature kodu tenant kimliğiyle uğraşmaz.
2. **Model Çözümleme** — `AiModelResolver`, mantıksal model sınıflarını (Sonnet, Haiku, Opus) config üzerinden somut deployment isimlerine map eder.
3. **Harcama Limiti Kontrolü** — `DailyAiSpendCapEnforcer`, hesabın bugünkü `ai_usage` maliyetini sorgular. Günlük bütçe aşılmışsa, çağrı herhangi bir token tüketilmeden **önce** bloklanır. Hesap bazında override desteklenir.
4. **İçerik Filtreleme (Giriş)** — `ConfigurableAiContentFilter`, PII (e-posta, telefon, SSN, kredi kartı, IP) ve operatör tanımlı yasaklı terimleri tarar. Feature bazında eşik değerleri. Reddet veya maskeleme aksiyonları.
5. **Provider Çağrısı** — Asıl Azure Foundry (veya Anthropic legacy) transport burada devreye girer.
6. **Backoff ile Yeniden Deneme** — Polly v8 üstel backoff + jitter. Geçici vs kalıcı hata sınıflandırması. Ayarlanabilir retry bütçesi.
7. **İçerik Filtreleme (Çıkış)** — Aynı filtre motoru yanıt üzerinde çalışır.
8. **Çıktı Doğrulama** — FluentValidation ile şema tabanlı doğrulama. Model uyumsuz bir yanıt döndürürse, **düzeltici yeniden-prompt döngüsü** reddedilen çıktıyı otomatik olarak tekrar oynatır ve modelden düzeltmesini ister (N denemeye kadar).
9. **Fallback** — Tüm yeniden denemeler başarısız olursa, feature bazında şablon fallback'ler düşük kaliteli ama işlevsel yanıtlar döndürebilir.
10. **Kullanım Loglama** — Her çağrı (başarılı, başarısız, fallback, harcama limiti bloğu) tam denetim izi ile `ssp.ai_usage` tablosuna yazılır.

> "Bu pipeline, arkasında hangi provider olursa olsun aynı şekilde çalışıyor. Anthropic'ten Azure Foundry'ye geçiş, hiçbir feature kodunda değişiklik gerektirmedi."

---

## 3. Azure AI Foundry — Nasıl Entegre Ettik

> "Azure AI Foundry, birinci sınıf bir provider adapter olarak entegre edildi. İşte tam olarak nasıl çalışıyor."

### Transport Katmanı

- **Chat Completions:** `AzureFoundryChatCompletionsTransport` — `POST {BaseUrl}/chat/completions` endpoint'ine `api-key` header kimlik doğrulaması ile çağrı yapan typed `HttpClient`.
- **Embeddings:** `AzureFoundryEmbeddingsTransport` — `POST {BaseUrl}/embeddings` endpoint'ine `api-key` header kimlik doğrulaması ile çağrı yapan typed `HttpClient`.

### Chat Client — `AzureFoundryAiClient`

- Provider-nötr `AiGenerateRequest`'imizi Azure Foundry chat-completions wire formatına çevirir.
- Sistem talimatlarını `system` role mesajına map eder.
- Çözümlenen model ID'sini **Foundry deployment adı** olarak kullanır (ör. `foundry-sonnet-deployment`, `foundry-haiku-deployment`, `foundry-opus-deployment`).
- Yanıtı geri map eder: içerik, model, token kullanımı (input/output), durma nedeni, trace ID.
- Tüm retry, doğrulama, içerik filtreleme, maliyet hesaplama, harcama limitleri ve kullanım loglama `AiClientBase`'den miras alınır — Foundry adapter'ı sadece transport'u yönetir.

### Embeddings Client — `AzureFoundryEmbeddingClient`

- `IEmbeddingClient.EmbedBatchAsync`'i implemente eder.
- Girdiyi `Ai:Embeddings:BatchSize` (varsayılan 96) ile batch'ler.
- Provider'ın `index` alanı üzerinden çağrı sırasını korur.
- `text-embedding-3-large` ile 3072 boyut olarak yapılandırılmıştır.
- Bilgi tabanı parçalama ve benzerlik arama pipeline'ını besler.

### Provider Seçimi (DI Tabanlı)

```
Config: Ai:Provider = "azure-foundry"  →  AzureFoundryAiClient
Config: Ai:Provider = "anthropic"      →  AnthropicAiClient (legacy)
```

> "Kod varsayılanı `azure-foundry`. Anthropic, `[Obsolete]` olarak işaretlenmiş legacy adapter olarak kalıyor — devir teslim sürekliliği için duruyor ve Foundry üretim trafiğinin %100'ünü 30+ gün sürdürülebilir şekilde taşıdığında kaldırılacak."

### Yapılandırma

```json
{
  "Ai": {
    "Provider": "azure-foundry",
    "BaseUrl": "<Foundry endpoint>",
    "ApiKey": "<Key Vault'tan>",
    "Models": {
      "Sonnet": "foundry-sonnet-deployment",
      "Haiku": "foundry-haiku-deployment",
      "Opus": "foundry-opus-deployment"
    },
    "Embeddings": {
      "Provider": "azure-foundry",
      "ModelDeployment": "foundry-text-embedding-3-large",
      "Dimensions": 3072,
      "BatchSize": 96
    },
    "CostTable": {
      "foundry-sonnet-deployment": { "InputPer1k": 0.003, "OutputPer1k": 0.015 },
      "foundry-haiku-deployment": { "InputPer1k": 0.00025, "OutputPer1k": 0.00125 },
      "foundry-opus-deployment": { "InputPer1k": 0.015, "OutputPer1k": 0.075 }
    }
  }
}
```

---

## 4. Context Substrate — 9 Launch Context Block'u

> "Sweetspot'taki her AI özelliği aynı context block'lardan compose ediliyor. 'AI-first' iddiasını mimari düzeyde gerçek kılan şey bu — bağımsız AI çağrıları koleksiyonu değil, composable bir substrate."

| Block | Kaynak | Ne Sağlıyor |
|-------|--------|-------------|
| **Brand** | `brand_settings` | Ses tonu açıklaması, ton etiketleri, değerler, tek satırlık slogan (tonal). Renkler, fontlar, logolar (sadece renderer — asla prompt'larda değil) |
| **Org** | `Account` | Organizasyon adı, sektör, adres, saat dilimi, dil/bölge, web sitesi |
| **Industry** | `industry_template_configs` | Görüntüleme adı, alan kelime dağarcığı, tekrarlayan değer etiketleri |
| **Profile** | `organisation_profile` + `voice_samples` | Hedef kitle açıklaması, kademe isimleri, program kelime dağarcığı, terminoloji, 5'e kadar ses örnekleri |
| **Knowledge** | `kb_documents` + `kb_chunks` | Müşteri yükleme belgeleri, Foundry embeddings ile parçalanmış ve gömülmüş, pgvector benzerlik araması |
| **Field Semantics** | `contact_field_definitions` | 8 semantik etiket (kimlik, etkileşim, finansal vb.) AI'ın CRM alanları hakkında akıl yürütebilmesi için |
| **Event** | Etkinlik verileri | Etkinlik pazarlaması özellikleri için etkinliğe özgü context |
| **Brief** | Kampanya brief verileri | İçerik üretimi için kampanya brief context'i |
| **Contact Fields** | Contact field tanımları | Kullanılabilir merge tag'ler ve anlamları |

> "Her block aynı kontratı takip ediyor: `IContextBlock<TContext>` ve `LoadBlockContextAsync`. Zarif bozulma (graceful degradation) zorunlu — eksik veya seyrek veri kaynağı boş bir stub döndürür, asla AI çağrısını çökertmez. `Exists` bayrağı ve `ToPromptString()` metodu, feature builder'ların block bazında dallanma yapmadan block'ları compose etmesini sağlıyor."

---

## 5. Kullanım Loglama ve Maliyet Kontrolü

> "Her AI çağrısı — başarılı, başarısız, fallback veya harcama limiti bloğu — `ssp.ai_usage` tablosunda tam olarak bir satır üretiyor."

### Neler Loglanıyor

| Kolon | Amaç |
|-------|------|
| `account_id` | Çok kiracılı izolasyon, GDPR kademeli silme |
| `user_id` | Kullanıcı bazında atıf (sistem çağrıları için nullable) |
| `feature` | Hangi AI özelliğinin çağrıyı yaptığı |
| `model` | Somut deployment adı |
| `input_tokens` / `output_tokens` | Token tüketimi |
| `cost_usd` | Provider bazında fiyatlandırma tablolarından hesaplanan maliyet |
| `latency_ms` | Uçtan uca yanıt süresi |
| `success` | Çağrının başarılı olup olmadığı |
| `prompt_hash` / `output_hash` | Tekilleştirme ve denetim için SHA-256 |
| `consent_status` | GDPR onay durumu |
| `data_residency_region` | Veri yerleşimi uyumluluğu |
| `trace_id` | Dağıtık izleme bağlantısı |
| `content_filter_outcome` | JSONB — PII kategorileri, yasaklı terimler, alınan aksiyonlar (AI Act §13.7 açıklanabilirlik) |

### Harcama Limiti

- Provider öncesi günlük harcama limiti (hesap bazında).
- `Account.DailyAiSpendCapUsd` ile hesap bazında override.
- Bloklanan çağrılar yine de `success=false` ve sıfır maliyet ile loglanır — tamamen denetlenebilir.
- DB okuma hatası = açık kalarak devam (bir DB sorunu yüzünden tüm organizasyonun AI'ını asla bloklama).

---

## 6. İçerik Filtreleme ve Uyumluluk

> "İçerik filtreleme, ilk günden AB AI Yasası ve GDPR uyumluluğu için inşa edildi."

- **PII Tespiti:** E-posta, telefon, SSN, kredi kartı, IPv4 — sabit `[PII:<tür>]` maskeleme yer tutucuları ile.
- **Yasaklı Terimler:** Operatör tarafından yapılandırılabilir, regex-güvenli, büyük/küçük harf duyarsız, kelime sınırlı, şiddet sınıflandırmalı (düşük/orta/yüksek).
- **Feature Bazında Eşik Değerleri:** Her feature giriş/çıkış PII ve yasaklı terim aksiyonlarını bağımsız olarak kontrol eder.
- **Sızdırmadan Denetlenebilir:** İçerik filtresi sonuçları JSONB olarak kalıcılaştırılır (yalnızca kategoriler ve sayılar — eşleşen alt diziler asla).

---

## 7. Kanıt Noktaları — Substrate Üzerinde Çalışan Özellikler

### E-posta Üretimi (Task 1.5.1)

> "İlk gerçek feature migrasyonu. Orbit prototipinin e-posta üretimini yeni mimariye taşıdık — TypeScript prototipiyle **bayt-bazında aynı çıktı**, yan yana fixture testleriyle doğrulanmış."

- `EmailGeneratePromptBuilder`, Brand → Org → Industry context block'larını bir sistem prompt'una compose eder.
- `EmailGenerateOutput` şeması (konu, önizleme metni, html içerik) FluentValidation ile.
- Uyumsuz yanıtlarda düzeltici yeniden-prompt döngüsü otomatik olarak devreye girer.

### Form Üretimi (Task 1.9)

- Substrate üzerinden bağlanan ikinci özellik.
- Aynı pipeline, aynı context block'lar, aynı uyumluluk kontrolleri.

---

## 8. Bilgi Tabanı ve Embeddings Pipeline'ı

> "Bilgi tabanı pipeline'ı Azure Foundry'nin embeddings API'sini uçtan uca kullanıyor."

- Müşteri belge yükler → `kb_documents` tablosunda saklanır (durum: pending → processing → ready/failed).
- Belgeler `kb_chunks` parçalarına ayrılır.
- Her parça **Azure Foundry `text-embedding-3-large`** (3072 boyut) ile embed edilir.
- Embedding'ler PostgreSQL'de `pgvector` uzantısı ile saklanır (`vector(3072)` kolonu).
- Benzerlik araması, müşteri bilgisine dayalı bağlam-farkındalıklı AI yanıtları sağlar.

---

## 9. Test Kapsamı ve Kalite

> "Epic 1, pipeline'ın her katmanını kapsayan 280+ AI birim testiyle teslim ediliyor."

- Provider adapter mapping'i (istek/yanıt wire formatı).
- Retry sınıflandırması (geçici vs kalıcı).
- İçerik filtresi pattern'leri (PII, yasaklı terimler, şiddet eşikleri).
- Çıktı doğrulama (şema zorlama, düzeltici yeniden-prompt döngüsü).
- Harcama limiti zorlama (günlük limitler, hesap bazında override'lar).
- Context block kontratları (zarif bozulma, boş stub'lar, iptal).
- Kullanım loglama (her kod yolu tam olarak bir denetim satırı yazar).
- Yan yana provider hazırlık testleri (Anthropic ↔ Foundry deterministik stub'larla).

---

## 10. Özet — Temel Çıkarımlar

| Boyut | Ne Teslim Ettik |
|-------|-----------------|
| **Provider** | Azure AI Foundry launch provider olarak (chat + embeddings) |
| **Mimari** | 10 aşamalı orkestrasyonlu provider-agnostik `IAiClient` pipeline'ı |
| **Context** | Her AI özelliğini besleyen 9 composable context block |
| **Uyumluluk** | PII/yasaklı terim filtreleme, AB AI Yasası açıklanabilirliği, GDPR kademeli silme, veri yerleşimi |
| **Maliyet Kontrolü** | Hesap bazında günlük harcama limitleri, çağrı bazında maliyet loglama, provider fiyatlandırma tabloları |
| **Kalite** | 280+ birim test, prototiple bayt-bazında aynılık |
| **Embeddings** | Bilgi tabanı araması için pgvector üzerinden Foundry text-embedding-3-large |
| **Çok Kiracılılık** | Mimari zorlama — `AccountId` AI sınırında inject edilir, asla opsiyonel değil |

> "Bu bir API üzerine ince bir sarmalayıcı değil. Bu, ilk günden uyumluluk, maliyet kontrolü ve provider esnekliği içerecek şekilde tasarlanmış, çok kiracılı SaaS için production-grade bir AI substrate — ve Azure AI Foundry bunu güçlendiriyor."

---
