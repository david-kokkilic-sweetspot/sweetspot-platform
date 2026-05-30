# Sweetspot

## AI mimari stratejisi

### Teknik inceleme için referans dokümanı

**Durum:** Taslak v2 — kişi alanı katman yapısı, yolculuk e-posta üretimi için `AIEmailModal` yeniden kullanımı, varlık bağlam bloğu ve hiper-kişiselleştirme kapsamı etrafındaki düzeltmeleri yansıtacak şekilde güncellendi. Veri mimarı ve partner mühendislik değerlendiricileriyle inceleme için. 

**Hedef kitle:** Kod tabanına yeni gelen mühendisler ve mimarlar. Önceden Sweetspot bağlamı bilinmediği varsayılır. Depodaki mevcut mimari ve geçiş spesifikasyon dokümanlarıyla birlikte okunur. 

**Kapsam:** AI mimarisi kararlarını, sistemin mevcut durumunu, hedef durumu, oraya ulaşmak için geçiş planını ve ileriye dönük altyapı ile uyumluluk gereksinimlerini kapsar. 

**Kapsam dışı:** Belirli prompt içeriği; UI tasarım spesifikasyonları; CRM adapter pattern (ayrı ele alınıyor); AI dışı altyapı konuları; fiyatlandırma ve paketleme. 

## 1. Yönetici özeti

Sweetspot, üyelik kuruluşları için AI-first, CRM-agnostic bir pazarlama otomasyonu ürünüdür. Ürün, HubSpot ve Mailchimp gibi araçlara karşı kendisini sektör bazında görüş sahibi bir çözüm olarak konumlandırır — genel amaçlı, yapılandırılabilir bir platform sunmak yerine belirli bir dikey sektör için pazarlama metodolojisini, kıyaslama verilerini ve en iyi uygulamaları kodlar. 

"AI-first" iddiası birbiriyle bağlantılı üç sütuna dayanır: sektör bazında kodlanmış bir metodoloji katmanı (iyi pazarlamanın nasıl göründüğü), kişi verilerini anlamsal olarak okunabilir kılan bir AI-ready katmanı (böylece AI alanların ne anlama geldiğini anlar) ve her AI özelliğini aynı marka, sektör, plan, hedef kitle ve metodoloji verisiyle besleyen bileşenlere ayrılabilir bir bağlam alt yapı katmanı. 

Bugün AI özellikleri farklı route'lar arasında bağımsız şekilde uygulanıyor — her biri marka ve sektör verisinin kendi dar dilimini okuyor, her biri kendi HTML oluşturma mantığını tekrar ediyor ve hiçbiri eldeki bağlamı mimarinin öngördüğü şekilde birleştirmiyor. Bu doküman, bu durumdan ürünün stratejik hedefinin gerektirdiği birleşik, bileşenlere ayrılabilir ve uyumluluğa hazır bir AI alt yapı katmanına giden yolu açıklar. 

Geçiş 10-15 haftaya yayılmıştır ve iki yakınsayan ürün hattının temelini oluşturur: (a) Insights'ın yalnızca raporlama değil aksiyon sürdürdüğü öneri odaklı komuta merkezi vizyonunu hayata geçirmek ve (b) sonunda SOC 2 Type 2, GDPR, EU AI Act dahil kurumsal uyumluluk ve güvenlik standartlarını karşılamak ve model sağlayıcısı olarak AI Foundry ile Azure'a altyapı geçişini desteklemek. 

#### Bu doküman neden var

**Üç neden:** 

Yeni teknik değerlendiriciler için başlangıç süreci bağlamı. Depodaki mevcut mimari ve geçiş spesifikasyon dokümanları, önceki kararların bilindiğini varsayıyor. Bu doküman, o önceki bağlamı tek bir yerde toplar. 

Veri katmanını etkileyen kararlar. Veri mimarının, kod sisteme inmeden önce şema etkilerini (yeni tablolar, genişletilmiş şemalar, RLS desenleri) görmesi gerekir. 

Mimari düzeyde savunulabilir bir "AI-first" iddiası. Teknik durum tespiti yapan partnerler ve müşteriler, bağımsız AI çağrılarından oluşan bir koleksiyon değil, tutarlı bir tasarım görmelidir. 

#### Doküman haritası

2-3. bölümler ürün ve stratejik bağlamı oluşturur. 4. bölüm mimari modelini açıklar. 5. bölüm mevcut durumu denetler. 6. bölüm hedef durumu açıklar. 7. bölüm geçiş planını ortaya koyar. 8-9. bölümler özellikle veri mimarisi ve uyumluluğu ele alır. 10. bölüm açık soruları, 11. bölüm ise sözlüğü içerir. 

## 2. Ürün bağlamı

### 2.1 Sweetspot nedir

Sweetspot, üyelik kuruluşları için bir pazarlama otomasyonu ürünüdür. Müşteri; kazanım, yenileme, etkileşim ve etkinlik programlamasından sorumlu, üyelik tabanlı bir kuruluştaki pazarlama lideridir (meslek birlikleri, ticaret kuruluşları, üye odaklı kâr amacı gütmeyenler, inanç temelli kuruluşlar vb.). Genellikle küçük bir ekibe sahiptir ve ya hiç resmi CRM kullanmaz ya da hafif bir CRM kullanır. Bugün bu işi e-tablolar, e-posta platformları, proje araçları ve varsa CRM'i arasında bölüştürerek yürütür. 

Sweetspot bu parçalı yığını; kazanım, yenileme, kopmuş kullanıcıları yeniden etkileşime alma, etkinlik ve konferans tanıtımı, bağışçı geliştirme, içerik programlama ve atıf ölçümünü kapsayan tek bir ürünle değiştirir. Bilerek satış pipeline yönetimi, anlaşma tahmini, hizmet ticketing, CMS veya genel RevOps workflow alanına genişlemez. Kullanıcı pazarlamacıdır; satış temsilcisi değildir. 

### 2.2 Neden "AI-first" gerçek bir iddia

Üç şey bir araya geldiğinde AI-first konumlandırması yalnızca pazarlama dili olmaktan çıkar ve savunulabilir hâle gelir: 

- **Dikey sektör başına metodoloji ve içerik.** Üyelik kuruluşları için (v1) Sweetspot, düzenlenmiş ve küratörlüğü yapılmış içerik olarak 5 pazarlama disiplini, 5 hedef türü, 13 program şablonu ve 8 alan semantiği `tags` etiketiyle gelir. Bu içerik AI tarafından üretilmez. AI, müşterileri bilinen ve görüş sahibi bir metodoloji boyunca yönlendirir; stratejiyi sıfırdan icat etmez. 

- **AI-ready katman (alan semantiği).** Kişi alanları, iş bağlamında ne anlama geldiklerine göre etiketlenir (`renewal_date` bir yenileme sinyalidir, `last_login_at` bir etkileşim sinyalidir, `lifecycle_stage` bir yolculuk göstergesidir). Bu katman olmadan AI, veritabanının etrafına sarılmış bir sohbet botudur; bununla birlikte ise yenilemeler, etkileşim ve yaşam döngüsü hakkında akıl yürütebilir. 

- **CRM-agnostic adapter.** CRM'i olmayan müşteriler Sweetspot'u kayıt sistemi olarak kullanabilir. CRM'i olan müşteriler ise hiçbir zaman değiştirilmeden adapter pattern üzerinden bağlanır. Bu da geçiş maliyetini ve benimseme sürtünmesini azaltır. 

### 2.3 Lansman profili

Lansman, 3-4 ay içinde yalnızca üyelik odaklıdır. B2B framework (Volaris growth playbook temelinde) IP teyidi beklediği için v2'ye sıraya alınmıştır. Kâr amacı gütmeyen ve wealth-management dikey sektörleri yalnızca mimari iskeletler olarak vardır. 

Bugün ön-üretim aşamasında. Aktif müşteri görüşmeleri ve demolar sürüyor ve lansman penceresi boyunca bir veya iki pilot müşteri ekiple yakın çalışacak, ancak henüz hiçbir müşteri hesabı provision edilmedi. Bu durum geçiş riskini etkiler: burada anlatılan temizlik çalışması sırasında şema ve kod değişikliklerinin canlı müşteri yapılandırmalarıyla geriye dönük uyumluluğu desteklemesi gerekmez. 

GitHub Enterprise, Azure üzerinde Postgres, Azure üzerinde barındırılan uygulama ve model sağlayıcısı olarak Azure AI Foundry'ye altyapı geçişi lansman sonrası (v2 veya sonrası) beklenmektedir. Bu dokümandaki mimari kararlar bu geçiş göz önünde bulundurularak alınmıştır; böylece geçiş gerçekleştiğinde tasarımın baştan yazılması gerekmez. 

### 2.4 Zaten AI-ready olanlar

Bu dokümanın anlattığı alt yapı katmanının birkaç parçası zaten kısmen inşa edilmiş durumda. Değerlendiricilerin her şeyin sıfırdan başlanan olmadığını varsaymaması için bunları burada özellikle belirtiyoruz: 

- **AI etiketlemeli varlık kütüphanesi.** Varlık yönetimi özelliği mevcut (`content_assets` table, klasör yapısı, arama). Görsel yüklemeleri `/api/content/analyse` tarafından otomatik analiz edilir ve AI tarafından üretilmiş açıklamalar ile `tags` verilir. Dolayısıyla varlık bağlam bloğu için altyapının büyük kısmı zaten hazır — eksik olan şey bunun diğer AI özelliklerine açılmasıdır. 

- **Kişi alanı katman yapısı.** Kişi alanları zaten kişiler ayarları UI'ında üç katmana ayrılıyor: 11 sistem alanı (evrensel, hardcoded), şablon alanları (sektör tarafından tohumlanmış, gizlenebilir ama silinemez) ve özel alanlar (tam CRUD ve CRM eşlemesiyle kullanıcı tarafından oluşturulur). Alan semantiği genişletme sütunları (`description`, `field_tags`, `ai_suggested_tags`) `contact_field_definitions` üzerinde mevcut ancak henüz hiçbir UI'da görünür değil. 

- **Pazarlama framework v1 (üyelik).** RLS'li 12 şema tablosu, 5 disiplin, 5 hedef türü, 13 program ve 8 etiket etiketi tohumlanmış durumda. Plan çalışma alanı UI'ı uçtan uca canlı (oluşturma, hedefler, programlar, performans). 

- **Marka rol atamaları.** 8 rollü sistem (heading, body, link, cta_bg, cta_text, canvas, callout_bg, divider) canlı durumda; `brand_settings`.`color_roles` JSONB sütunuyla çalışıyor. Rol farkındalığı olan e-posta üretimi `/api/email/generate` içinde çalışıyor. 

- **AI e-posta üretim modalı.** `AIEmailModal` component'i (şu anda e-posta gönderim detay sayfasında inline) yolculuk e-posta adımları için önemli ölçüde yeniden kullanılabilir. E-posta editörü dışından çağrılabilmesi için prop contract tarafında (`emailId` yerine `context` object) bir refactor gerekiyor — ancak UI, oluştur-incele-düzenle-onayla akışı ve inline contentEditable önizleme aynen taşınabiliyor. 

Bu dokümandaki geçiş, bunları yeniden inşa etmek yerine bu temeller üzerine kuruludur. 

## 3. Stratejik temel

AI mimarisi belirli bir ürün stratejisine hizmet eder. Mimariye neden bu şekilde biçim verildiğini anlamak için stratejiyi anlamak gerekir. 

### 3.1 Sektör temel katmandır

Her Sweetspot kuruluşu kayıt olurken bir sektör şablonuna bağlanır (bugün: membership, b2b, non_profit, wealth_management). Sektör, aşağı akışta birbirinden ayrı dört şeyi belirler: 

- **Kelime dağarcığı.** Üye mi, müşteri mi, danışan mı, bağışçı mı. "Renewal date" mi, "subscription end" mi, "contract end" mi. UI ve AI prompt'larında boyunca görünen sektöre özgü terminoloji. 

- **Metodoloji.** Strateji/plan çalışma alanını besleyen pazarlama framework'ü (disiplinler, hedef türleri, program şablonları, KPI'lar). Bu, AI tarafından üretilmeyen küratörlü içeriktir. 

- **Kıyaslama verileri.** Önerileri temellendirmek için Insights içinde kullanılan sektör kapsamlı karşılaştırma verileri — ortalama açılma oranları, ortalama üye kalış süresi, ortalama yenileme sıklığı gibi. 

- **Önerilen varsayılanlar.** Müşterinin çalışma alanını, dikey sektöründe neyin işe yaradığı bilgisine dayanarak önceden dolduran hedef türleri, sinyaller, hedef kitle biçimleri ve program önerileri. 

Sektör mimaride markanın aşağısında değil, markaya paraleldir. Marka kuruluşa özgü kimliktir (ses tonu, renkler, logo). Sektör ise sektöre göre şekillenmiş tavsiyedir. İkisi de AI bağlam katmanını besler ama hiçbiri diğerine sahip değildir. 

### 3.2 Pazarlama planı bir çeyreklik oyun kitabı olarak

Bir pazarlama planı, belirli bir dönem için (tipik olarak bir çeyrek) bir framework'ün müşteri tarafından somutlaştırılmasıdır. Plan şunları içerir: 

- **Goals** — hedef, başlangıç seviyesi, son tarih ve mevcut gidişatla birlikte taahhüt edilmiş sonuçlar (kazanım, yenileme artışı, etkinlik doluluğu, yeniden etkileşime alma vb.). 

- **Programmes** — bir hedef içindeki tutarlı yürütme birimleri. Bir program; hedef kitle tanımını, bir veya daha fazla taktiği (her biri bir yolculuk, campaign veya içerik brief'ine bağlı), bir takvimi, hedef KPI'larına yuvarlanan program düzeyi KPI'ları ve bir durumu (draft/active/paused/completed) bir araya getirir. Program, aktivasyon birimidir. 

- **Hedefe karşı performans** — plan sağlığı sinyallerinin kaynağı hâline gelen hesaplanmış gidişat. 

Dönem başına kuruluş başına tek aktif plan. Eski planlar, geriye dönük analiz ve bir sonraki planın tohumlanması için saklanır. Plan, oluşturulurken bir framework sürümüne sabitlenir; böylece framework güncellendiğinde canlı planlar geriye dönük olarak değişmez. 

Mimari açıdan önemli nokta şu: plan, diğer her şeyi organize eden "neden"dir. Aktif planı bilen AI çağrıları çıktılarında "Q3 acquisition hedefiniz" diyebilir. Plan bağlamı olmadan AI çıktısı geneldir. 

### 3.3 Insights komuta merkezi olarak, raporlama olarak değil

Insights yüzeyi veri kaynakları etrafında değil sonuçlar etrafında yeniden tasarlanıyor. Yeni IA şöyle: 

- **Today** — `/dashboard/insights` adresindeki komuta merkezi. Önceliklendirilmiş öneri akışı, mini takvim widget'ı, AI palette girdisi. Ürünün yeni giriş kapısı. 

- **Grow** — kazanım: lead'ler, prospects, funnel velocity, source attribution. 

- **Engage** — kanal performansı: email, web, events, agents. 

- **Retain** — risk altındaki üyeler, kopmuş kohort, geri kazanım, yenileme pipeline'ı. Üyelik şablonu çalışması esas olarak burada yer alır. 

- **Earn** — abonelik geliri, yenileme geliri, ARPU, LTV, segment bazında gelir. Bir dernek için şu anda üründe olmayan bir yönetim kurulu metriği. 

Kavramsal hamle, şu anda birbirine dolanmış üç şeyi ayırıp onları tek bir primitive içinde yeniden birleştirmektir:  

- **Insight** — bir olgu ("412 kopmuş üye, %23'ü hâlâ e-postaları açıyor") 

- **Recommendation** — ne yapılması gerektiği ("bir nurture journey ile onları yeniden etkileşime alın") 

- **Action** — bunu gerçekten yapmak (hedef kitle oluşturmak, yolculuk kurmak, kişileri kaydetmek, gönderime başlamak) 

Üçü de tek bir recommendation card üzerinde, önizle-ve-onayla akışıyla yaşar. Tek tıkla asla gönderim yapılmaz. Her commit, hedef kitle önizlemesini, yolculuk veya campaign şablonunu, öngörülen etkiyi gösterir ve bir audit trail kaydı yazar. 

Güven doğruluğu taviz verilemez bir konudur: kurala dayalı öneriler "Counted" olarak etiketlenir (412 kopmuş üyeyi saydık); AI tarafından üretilen öneriler "Suggested" olarak etiketlenir (Salı sabahı gönderimin açılmaları artıracağını düşünüyoruz). Bunları birbirine karıştırmak güveni aşındırır. 

### 3.4 Güven inşası ilerleyişi

Insights'ın gerçek bir komuta merkezine dönüşmesi — yani AI'ın planı yürüttüğü ve pazarlamacının yalnızca istisna durumunda devreye girdiği yapı — lansman hedefi değil, uzun vadeli bir hedeftir. AI'a güven kademeli olarak inşa edilmelidir. Her aşama bir sonrakini hak eder. Bunu atlamak, çoğu zaman geri kazanılamayacak şekilde güveni zedeler. 

| Aşama | AI ne yapar | Kullanıcı katılımı | İstenen güven düzeyi |
| --- | --- | --- | --- |
| Phase 1 (launch) | Kurala dayalı önerileri gösterir; önizleme tam hedef kitleyi ve içeriği gösterir | Her seferinde açık onay verir | Düşük — kullanıcı her şeyi kontrol eder |
| Phase 2 (launch) | Yolculuklar ve programlar için içerik üretir; öneri metni plan hedeflerine referans verir; CTA'lar bağlam farkındalığı taşır | İçerikte tek tıkla işlemi onaylar, hedef kitleyi yine önizler | Orta — içeriğe güvenir, hedef kitleyi doğrular |
| Phase 3 (post-launch) | Rutin aksiyonlar onay olmadan yürütülür — opt-in yapılmış, denetlenmiş, geri alınabilir. Yeni veya riskli aksiyonlar yine önizlenir | Audit log'u inceler, aksiyon türüne göre özerklik ayarlar | Yüksek — neyin rutin olduğuna dair muhakemeye güvenir |
| Phase 4 (future) | Plan, kullanıcının belirlediği özerklik sınırları içinde kendi kendine yürür. Kullanıcı istisna durumunda devreye girer | Onaylayan değil, istisna işleyicisi olur | En yüksek — Phase 2 ve 3 ile kazanılmış |

## 4. AI mimari modeli

Mimarinin temelinde dört fikir vardır. Her biri aşağıda açıklanmıştır. 

### 4.1 Bileşenlere ayrılabilir bağlam blokları

Her AI çağrısı, yeniden kullanılabilir bağlam bloklarından oluşan bir yığından prompt'unu oluşturur; her blok kurumsal anlayışın tek bir boyutunu kapsüller. Özellikler, hangi blokları birleştirdiklerine göre farklılaşır; blokların kendi çalışma biçimine göre değil. 

Bağlam bloğu; `org_id` (ve gerektiğinde özelliğe özgü argümanlar) alan ve prompt tüketimine uygun biçimlendirilmiş bir string fragment döndüren bir function'dır. Bloklar başka bloklara bağlı olabilir (hedef kitle, alan semantiğine bağlıdır). Veri kaynağı eksik veya seyrek olduğunda bloklar zarif biçimde bozulmalıdır — boş ya da minimal bir stub dönmeli, asla hata fırlatmamalıdır. Blokların yan etkisi olmamalıdır — yalnızca okuma ve biçimlendirme. 

Bugün tanımlı olan dokuz on blok şunlardır: 

| Blok | Kaynak | Sağladığı şey |
| --- | --- | --- |
| brand | `brand_settings` table + `color_roles` JSONB | Ses tonu, palet, logo, gönderici bilgisi, rol atamaları (heading/body/CTA/etc.) |
| org | organizations table | Kuruluş adı, türü, fiziksel adres, gizlilik URL'si |
| industry | industry_template_configs table | Dikey sektöre özgü ton, hedef kitle kelime dağarcığı, düzenleyici teamüller |
| methodology | marketing_disciplines, goal_types, programmes, tag_labels tables | Kuruluşun dikey sektörü için aktif framework içeriği (disiplinler, programlar, KPI'lar) |
| field-semantics | `contact_field_definitions` üzerindeki alan semantiği genişletmesi | Her kişi alanının iş bağlamında ne anlama geldiği — AI-ready temel |
| audience | audiences + audience_contacts + field-semantics | Alıcı `description` verisini anlamsal terimlerle sunar ("90 gün içinde yenilenecek aktif üyeler"). Phase 3+ hiper-kişiselleştirme için ayrıca alıcı bazında derinlik (`tags`, son etkinlik, yaşam döngüsü aşaması) sunar. |
| plan | marketing_plans + plan_goals + plan_programmes | Aktif plan, mevcut hedefler ve hedef değerleri, hedefe karşı performans |
| insights | Kuruluşlar arası agregatlardan hesaplanan kıyaslama verileri (mahremiyete saygılı) | Sektör kapsamlı kıyaslamalar ("X büyüklüğündeki üyelik kuruluşlarında ortalama açılma oranı Y'dir") |
| knowledge | Supabase içindeki KB tabloları (kuruluş bazlı ve küratörlü) | Prompt için vector search ile en ilgili Top-K chunk'lar. Kuruluş kapsamlı müşteri içeriği (stil rehberi, geçmiş campaign'ler, SSS, ürün sayfaları) ile Sweetspot'un küratörlü içeriği (en iyi uygulamalar, playbook'lar). |
| assets | `content_assets` table (mevcut altyapı, yüklemede AI ile etiketlenir) | `tags`, içerik türü ve anlamsal aramaya göre filtrelenebilen mevcut görsel, video, ses ve dosyalar. AI'ın üretilen çıktıda belirli varlıklara referans vermesini sağlar (ör. bir bülten bölümüne doğru görseli seçmek). |

Bu desenin sonuçları şunlardır: yeni bir bağlam bloğu aynı anda her özelliğe açılır. Marka sesindeki bir değişiklik tek bir düzenlemeyle her AI yüzeyine yayılır. Model geçişi tek bir dosyaya dokunur (istemci sarmalayıcı). Hedef kitle akıl yürütmesindeki bir hata dokuz kez değil, bir kez düzeltilir.

Bu, mevcut durumun tam tersidir; bugün her route kendi "bu kuruluşun tonu nedir" sürümünü inline olarak yazar ve bu inline sürümler zamanla birbirinden sapar. 

### 4.2 Varlık biçimi çerçevesi

Önceki planlamalardaki yaygın bir hata, tüm AI üretim route'larını tek bir "AI surfaces" kovasında toplamaktı. Aslında bunlar, her biri farklı gereksinimlere sahip üç kategoriye ayrılır: 

| Biçim | AI'ın ürettiği şey | Örnekler |
| --- | --- | --- |
| Markalı HTML içerik | Müşteriye dönük, markalı HTML e-postalar veya sayfalardaki metin | email-generate, journey email step content, form-agent confirmation, event-agent confirmation |
| Yapısal JSON | Editörün render ettiği şema veya graph verisi, marka etkisi hafif | forms-generate (form schema), journey-generate (steps and edges JSON) |
| Metadata | Kısa tanımlayıcılar ve açıklamalar | campaigns-generate (name, type, `description`) |

Tüm özelliklerde ortak taban çizgisi şudur: içerik taşıyan her özelliğin aynı çıktıyı üreten iki oluşturma yolu vardır — tamamen doldurulmuş, marka temalı, önizlenebilir ve test edilebilir bir artifact. Şablon seç = küratörlü bir başlangıç noktasından başla. AI seç = ne istediğini anlat, AI her şeyi doldursun. Her ikisi de marka + sektör bağlamından geçer. Her ikisi de oluşturulduktan sonra satır içinde düzenlenebilir. 

### 4.3 Agent tanımı: yalnızca gelen kutusu

Kod tabanında "Agent" şu anda aşırı yüklenmiş bir terim. Agent olarak adlandırılan üç şey farklı işler yapıyor: 

- **Bugünkü form-agent ve event-agent** — form gönderimi veya etkinlik kaydı sonrası onay e-postası gönderen, ardından kişiyi bir yolculuğa kaydeden tek çağrılık AI invocations. Multi-turn değiller. Stateful değiller. Yanlış isim takmış tek atımlık AI çağrıları. 

- **Chat agent** — gelen mesajlar için multi-turn konuşma işleyicisi. Durum, geçmiş, kararlar. Gerçek bir agent. 

- **Strategy agent (planned)** — Plan-Build-Launch-Learn döngüsü. Çok adımlı, araç kullanan, stateful. Gerçek bir agent. 

Hedef tanım şu: bir agent, çok adımlı, konuşma yürüten, karar veren bir varlıktır. Tek çağrılık e-posta göndericileri agent değildir — onlar handler veya generator'dır. 

Bunun ima ettiği mimari sadeleştirme şu: bugünkü form-agent ve event-agent, oluşturma mantığını (onay e-postası gönderme) çalışma zamanı mantığıyla (sonraki yanıtları işleme) tek bir trigger içinde ezip birleştiriyor. Temizlik bu ikisini ayırıyor: 

- **Creation** — yolculuğa taşınır. Yolculuğun ilk adımı, marka ve etkinlik bağlamıyla AI tarafından üretilen onay e-postasıdır. `.ics` attachment desteği de agent'e özgü bir özellik olarak değil, bir journey-email özelliği olarak burada yer alır. 

- **Runtime** — agent ile kalır. Agent, kayıt yaptıran kişiden gelen yanıtları çok turlu şekilde, orijinal kayıt bağlamıyla birlikte işler. 

Bunun neden daha temiz olduğu açık: giden e-postalar için tek bir kaynak noktası olur (journeys), agent'ler kelimenin ima ettiği şeye dönüşür (süreklilik gösteren, konuşma tabanlı), email-generate / form-agent / event-agent arasındaki HTML oluşturma tekrarları ortadan kalkar ve tek çağrılık özelliklerle çok adımlı agent'ler arasındaki ayrım nihayet mimari anlam kazanır. 

### 4.4 İlke olarak bağlam farkındalığıyla üretim

Bugün kullanıcı, AI e-posta üretirken CTA URL'lerini elle giriyor. Bu, eksik bağlam için bir geçici çözümdür. Doğru desen şu: AI, oluşturduğu e-postayı çevreleyen bağlamı bilir ve bu bilgiyi kullanır. 

Bilinen bir bağlamın içinde üretim yapan AI (etkinlik yolculuğu → etkinlik kayıt URL'sini kullan; form-followup yolculuğu → form'un redirect URL'sini kullan; recipe tabanlı programme → recipe'nin bilinen CTA'sını kullan): CTA önceden doldurulur ve kullanıcı isterse üzerine yazabilir. 

Çevresinde bilinen bir bağlam olmadan bağımsız üretim yapan AI (sıfırdan yazılan tek seferlik bir pazarlama e-postası): bugünkü gibi CTA ister ya da toggle ile atlar. 

Aynı ilke CTA'ların ötesine uzanır: etkinlik başlığına referans veren konu satırları, hedef kitlenin adını kullanan gövde metni, tetikleyici neden ile eşleşen açılış kancaları — hepsi aynı fikirden doğar. Birleşik email-content component'i sadece bir prompt almaz; çevresindeki context object'i de alır (hangi yolculuk, hangi etkinlik, hangi form, hangi hedef kitle, hangi plan hedefi). 

İşte "AI-first" hissini "her formun üzerinde bir AI butonu" hissinden ayıran şey budur. 

### 4.5 Birleşik email-content component'i

Mimari temizliğin kilit taşı. Birden fazla yüzeyden çağrılabilen tek bir içerik üretim deseni: 

- **Email editor** — bugünkü gibi bağımsız üretim. 

- **Journey editor** — "Bu e-posta adımı için içerik üret", yolculuğun çevresel bağlamı içeri akar. 

- **Recommendation action handlers** — Today sayfasındaki bir card bir yolculuğu commit ettiğinde, yolculuğun e-postaları bu component aracılığıyla doldurulur; recommendation bağlamı da içeri akar. 

Tek bir uygulama, üç tüketici. Güven inşası ilerleyişinin Phase 2'sini mümkün kılan da budur: müşteri bir recommendation card üzerinde "Build the campaign" dediği anda sistem bir hedef kitle oluşturur, bir yolculuk üretir, her e-posta adımını bu component üzerinden marka farkındalığı olan AI içeriğiyle doldurur, önizlemeyi açar ve onay bekler. O ânı akıllı kılan çalışma zamanı bu component'tir. 

#### Mevcut `AIEmailModal` yeniden kullanımı

Mevcut `AIEmailModal` component'i (≈300 satır, bugün e-posta gönderim detay sayfasında inline) ihtiyaç duyulan UI'ın büyük kısmını zaten sağlar: prompt girişi, AI-prompt önerileri, URL ve etiketli CTA toggle'ı, oluştur-incele-düzenle-onayla akışı, inline contentEditable önizleme. Taşınabilir durumdadır. Değişmesi gereken bağlılık noktası prop contract'tır: bugün bir `emailId` alır (`campaign_emails` satırına işaret eder) ve bunu `/api/email/generate`'e geçirir. Journey email step için ise tüketicide `campaign_emails` satırı yoktur — onun elinde bir journey step config vardır. 

Temiz refactor şudur: `emailId` yerine yapılandırılmış bir context object kullanmak: 

```typescript
type GenerationContext =
  | { kind: 'campaign_email'; emailId: string }
  | { kind: 'journey_step'; journeyStepId: string;
      journeyId: string; eventId?: string;
      recipeId?: string; audienceId?: string }
  | { kind: 'standalone' }
``` 

Modal, bağlamı birleşik bir backend route'una geçirir. Route, `kind` ve özelliğe özgü argümanlara göre uygun bağlam bloklarını yükler, prompt'u birleştirir, istemci sarmalayıcıyı çağırır ve sonucu döndürür. Modal da sonucu bugün yaptığı şekilde inceleme ve düzenleme için render eder. 

Bağlam farkındalığıyla CTA türetme bunun doğal bir uzantısıdır: `kind === 'journey_step'` ve `eventId` mevcut olduğunda modal, etkinliğin registration_url bilgisinden CTA URL'si önceden doldurulmuş olarak açılır; yanında da küçük bir not görünür ("Etkinlikten alındı — gerekirse düzenleyin"). Aynı şey `recipeId` ve `audienceId` için de geçerlidir. `standalone` için davranış bugünle aynıdır: kullanıcı CTA'yı sağlar ya da kapatır. 

### 4.6 Hiper-kişiselleştirme

Hiper-kişiselleştirme — bireysel alıcıya göre uyarlanmış e-postalar veya bültenler — birleşik email-content component'i ile varlık bloğunun üzerine kurulur. Mimari, bunu güven inşası ilerleyişinin aşamalarına eşlenen iki türe ayırır: 

| Tür | Anlamı |
| --- | --- |
| Segment düzeyinde (Phase 2, launch) | AI, hedef kitle segmentine göre uyarlanmış tek bir e-posta üretir. Aynı gönderim içinde farklı yaşam döngüsü aşamaları veya kıdem katmanları için farklı metin üretir. Varlıklar bağlama göre kütüphaneden AI tarafından önerilir. Pazarlamacı, gönderim öncesi önizlemede segment varyantlarını görür, commit eder veya düzenler. Bu, "AI-first" hissinin merge tag'lerden farklı olmasının temelidir. |
| Alıcı bazında (Phase 3+, post-launch) | AI, her alıcı için benzersiz içerik üretir. Konu satırı, gövde metni, varlık seçimi ve CTA bu belirli alıcıyı dikkate alır (yaşam döngüsü aşaması, yakın dönem etkileşim, etiket üyeliği, özel alan değerleri). Gönderim pipeline'ı tek bir render edilmiş şablondan değil, teslimat anında alıcı bazında birleştirme yapar. |

Hiper-kişiselleştirmeyi destekleyen mimari parçalar:

- **Audience block**, alıcı bazında derinlikle birlikte. Bugünkü hedef kitle tanımlayıcısı segment düzeyindedir ("90 gün içinde yenilenecek aktif üyeler"). Alıcı bazında üretim için bu blok, prompt içinde her alıcı için kişi düzeyinde alan değerlerini AI'a sunacak şekilde genişler.
- **Assets block.** AI'a mevcut varlık kütüphanesini sunar; böylece her alıcıya veya segmente uygun görsel, video ya da başka medyayı seçebilir.
- **Gönderim anında alıcı bazında üretim modu.** Phase 3+ için gereklidir. Gönderim pipeline'ı birleşik email-content component'ini tüm gönderim için bir kez değil, alıcı başına (veya segment grubu başına) çağırır.

⚠️ **Sınırlayıcı etken maliyettir**; alıcı bazında üretimde durum budur. 10.000 kişilik bir gönderimde alıcı başına benzersiz içerik üretmek 10.000 AI çağrısı demektir. Fiyatlandırma farkındalığı taşıyan desenler, Phase 3 yayına çıkmadan önce sisteme inmelidir:

- **Variant-based hybrid** — AI baştan N adet (ör. 8) varyant üretir; gönderim anındaki alıcı bazlı mantık, alan değerlerine göre her kişi için en iyi eşleşeni seçer. Liste boyutundan bağımsız olarak AI maliyetini sınırlar.
- **Per-section variants** — bültenler için AI her bölüm başına az sayıda varyant üretir; alıcıya kişiselleştirilmiş bir karışım gider. Tek şablondan daha ifade gücü yüksektir, tam alıcı bazlı üretimden ise çok daha ucuzdur.
- **Günlük ve gönderim başına sert üst sınırlar** — kuruluş başına günlük AI harcama limiti, gönderim başına varyant sayısı limiti, eşiklerde uyarı. İstemci sarmalayıcı bölümünde bunun zaten tavizsiz olduğu işaretlenmişti.

Lansman hedefi: Phase 2 segment düzeyinde hiper-kişiselleştirme; otomatik önerilen varlıklarla birlikte, birleşik email-content component'inin çağrıldığı her yerde kullanılabilir. Alıcı bazında hiper-kişiselleştirme ise lansman sonrasıdır ve maliyet kontrol desenlerinin hayata geçmesine bağlıdır.

## 5. Mevcut durum denetimi

Bugün AI yüzey alanında nelerin bulunduğuna dair kesin envanter. Temizlik çalışması işte buradan göç eder. 

### 5.1 Bugünkü AI üretim yüzeyleri

| Route | Varlık biçimi | Ne üretir |
| --- | --- | --- |
| `/api/email/generate` | Markalı HTML içerik | Marka + rol farkındalığı olan CTA ile tam HTML e-posta. `brand_settings` ile tamamen entegre. |
| `/api/agents/form/trigger` | Markalı HTML içerik | Form gönderiminde AI tarafından yazılmış onay e-postası. 4 marka alanını okur. |
| `/api/agents/event/trigger` | Markalı HTML içerik | `.ics` attachment ile AI tarafından yazılmış etkinlik onay e-postası. 4 marka alanını okur. |
| `/api/journey/generate` | Yapısal JSON | Journey steps + edges. Sadece sektör kelime dağarcığını okur. E-postalarda içerik yok. |
| `/api/forms/generate` | Yapısal JSON | Form schema. Sadece sektör kelime dağarcığını okur. Marka farkındalığı yok. |
| `/api/campaigns/generate` | Metadata | Campaign adı, türü, `description`. Marka farkındalığı yok. |
| `/api/journey/create-from-recipe` | Deterministic | Hardcoded recipe içeriğini marka rengi ekleyerek basar. AI çağrısı yok. |
| `/api/journey/create-from-event` | Deterministic | Etkinlik öncesi/sonrası yolculuk şablonlarını basar. AI çağrısı yok. |
| `/api/forms/create-from-template` | Deterministic | Bir şablonu form içine klonlar. AI çağrısı yok. |

Önceki geçiş spesifikasyonu, journey-generate, forms-generate ve campaigns-generate route'larını email-generate ile birlikte öncelikli geçiş hedefleri olarak gruplayordu. Bu birleştirme doğru değildir — bunlar farklı gereksinimlere sahip farklı varlık biçimleridir. 

### 5.2 Bugün yüzeyler arasında marka farkındalığı

Her route `brand_settings` içinden kendi dar dilimini okur. Paylaşılan bir soyutlama yoktur. Bu dar dilimler zamanla birbirinden sapar. 

| Route | Okunan marka alanları |
| --- | --- |
| `/api/email/generate` | Tam palet + ses tonu + `color_roles` (rol farkındalığı ✓) |
| `/api/agents/form/trigger` | primary_color, logo_url, brand_voice, body_font |
| `/api/agents/event/trigger` | primary_color, logo_url, brand_voice, body_font (ayrıca agent düzeyi gönderici override'ları) |
| `/api/journey/create-from-recipe` | primary_color, logo_url |
| `/api/journey/create-from-event` | primary_color, logo_url, body_font |
| `/api/forms/create-from-template` | primary_color, background_color, text_color, body_font |
| `/api/forms/generate` | Hiçbiri — sadece industry_template_configs okur |
| `/api/journey/generate` | Yok |
| `/api/campaigns/generate` | Yok |

### 5.3 Bugünkü `ai_usage` table

AI çağrıları `/lib/track-ai-usage.ts` içindeki bir helper üzerinden log'lanıyor. Şu anda yazılan sütunlar şunlar: 

- `org_id`
- feature (ör. "emails", "forms", "journeys", "campaigns") 

- input_tokens, output_tokens, total_tokens 

- cost_usd (`Sonnet 4` için hardcoded fiyatlandırma kullanılarak log anında hesaplanıyor: girdi $3/M, çıktı $15/M) 

Mimarinin öngördüğü fakat şu anda yazılmayan sütunlar: `user_id`, model, latency_ms, success, `error_message`, created_at. Paralel bir `usage_summaries` table'ı feature ve dönem bazında toplulaştırma yapar. 

Kapsama eksiktir — her AI çağrısı bu helper'dan geçmez. Temizlik, loglamayı opsiyonel olmayan bir pass-through hâline getirir. 

### 5.4 Neyin tekrarlandığı, neyin eksik olduğu

Kod tabanında görülen üç somut tekrar: 

- Markalı HTML e-posta üretimi en az üç kez uygulanmış: email-generate, form-agent trigger, event-agent trigger. Her birinin niyeti aynı ama HTML iskeleti biraz farklı. Zamanla ayrışıyorlar. 

- Marka yükleme kodu route başına ayrı uygulanmış. Her route, ihtiyaç duyduğu `brand_settings` alt kümesini bilir ve Supabase üzerinden doğrudan okur. 

- Anthropic SDK çağrısı her route içinde doğrudan yapılıyor. Retry, hata işleme, model seçimi veya loglama tutarlılığı için merkezi bir nokta yok. 

Tamamen eksik olan üç şey: 

- Bileşenlere ayrılabilir bir bağlam katmanı. Mimari dokümanda anlatılan `/lib/ai/context/` dizini yok. 

- Alan etiketleme UI'ı. Özel alanlarda alan semantiği genişletmesini doldurmak için gerekli. Bu olmadan özel alan semantiği seyrek veri döndürür. Sistem alanı ve şablon alanı semantiği içerik olarak tohumlanacağı için (UI gerekmeden) katman ilk günden itibaren kısmen canlı olur. 

- Öneri odaklı action handler'lar. Insights'tan yolculuk oluşturmaya giden "önizle-ve-onayla" akışı henüz yok. Today sayfası komuta merkezi tasarlandı ama henüz inşa edilmedi. 

### 5.5 Zaten kısmen yerinde olanlar

Temizlik sıfırdan başlamıyor. Geçişin dayandığı belirli parçalar şunlar: 

- **Kişi alanı katman yapısı.** Kişiler ayarları sayfası zaten üç katmanı uygular — sayfada hardcoded duran 11 sistem alanı, `is_template_field = true` olan `contact_field_definitions` içindeki şablon alanlar ve false olan özel alanlar. Alan etiketleme UI'ı bunun üstüne kurulur; icat edilecek yeni bir şey değildir. 

- **AI etiketlemeli varlık kütüphanesi.** Klasör desteği, `description`, `tags`, `ai_analysed`, `content_type` içeren `content_assets` table'ı mevcut. Görsel yüklemeleri, `description` ve `tags` alanlarını dolduran AI analizini tetikliyor. İsim, `description` veya `tags` ile arama çalışıyor. Eksik olan şey: bu veriyi varlık sayfası dışındaki AI özelliklerine açan assets context block. 

- **`AIEmailModal` component'i.** Bugün e-posta gönderim detay sayfasında inline (≈300 satır). Tüm oluştur-incele-düzenle-onayla UI akışını, inline contentEditable önizleme ile sağlar. `emailId` yerine yapılandırılmış bir context object kullanan prop contract değişikliğiyle diğer yüzeylere taşınabilir. Geçiş, yeni bir modal inşa etmek yerine doğrudan bunu kullanır. 

- **Pazarlama framework v1 (üyelik).** RLS'li 12 şema tablosu, tohumlanmış içerik, uçtan uca çalışan Plan çalışma alanı UI'ı. Methodology ve plan bağlam bloklarının ilk günden okuyacak verisi vardır. 

- **Marka rol atamaları.** Prod ortamında canlı. Email-generate zaten rol farkındalığı taşıyor. Brand context block bunu kullanır ve diğer özelliklere genişletir. 

## 6. Hedef durum

Temizlik, sistemi `/lib/ai/` altında her konu için tek bir doğruluk kaynağı bulunan, net katmanlara ayrılmış bir mimariye taşır. 

### 6.1 Kütüphane yapısı

Hedef dizin biçimi: 

```
/lib/ai/
  client.ts            — Wrapped AI SDK: logging, retries, model selection, validation, content filter
  index.ts             — Public entry point
  /prompts/            — Per-feature system prompts as files, not inline in routes
    email-generate.ts
    journey-content.ts
    form-generate.ts
    ...
  /context/            — Composable context blocks
    brand.ts, org.ts, industry.ts, methodology.ts,
    field-semantics.ts, audience.ts, plan.ts, insights.ts,
    knowledge.ts, assets.ts
  /knowledge/          — KB / RAG layer (vector search, embedding generation)
  /agents/             — Multi-step agent loops (chat, strategy, future inbound handlers)
  /schemas/            — zod schemas for structured AI outputs
  /usage/
    log.ts             — Writes to ai_usage after every call
    cost.ts            — Token-and-model → cost calculation
``` 

### 6.2 İstemci sarmalayıcı

Her AI çağrısı bu sarmalayıcıdan geçer. `/lib/ai/client.ts` dışındaki doğrudan `anthropic.messages.create` çağrıları kod incelemesinde kırmızı bayraktır. 

Sorumluluklar: 

- **Sağlayıcı soyutlaması** — generate({ feature, system, messages, model_class }) → { content, usage, metadata }. İçeride bugün Anthropic'e, geçiş sonrası Azure AI Foundry'ye, gerekirse başkalarına çevirir. Tek değişim noktasıdır. 

- **Loglama** — her çağrı `ai_usage` içine `org_id`, `user_id`, feature, model, input/output token sayıları, maliyet, latency, success/failure, içerik hash'i, consent status, data residency region ve trace ID ile yazılır. Tavizsiz kural: bu olmadan ne maliyet görünürlüğü ne de uyumluluk denetim izi vardır. 

- **Hata işleme** — geçici hatalar backoff ile retry edilir. Kalıcı hatalar özellik için uygun bir fallback ile zarif şekilde bozulur (AI tarafından üretilmiş içerik yerine şablon tabanlı içerik gibi). Hatalar görünür olmalı, asla yutulmamalıdır. 

- **Model seçimi** — feature bazında Sonnet ile Haiku arasında karar vermek için tek yer. Premium özellikler (strateji, karmaşık üretim) Sonnet kullanır; yüksek hacimli veya gecikmeye duyarlı özellikler (chat suggestions, classification) Haiku kullanır. 

- **Çıktı doğrulama** — bir özellik zod schema sağladığında sarmalayıcı bunu parse eder, doğrular ve hata durumunda düzeltici prompting ile retry eder. N (varsayılan 2) başarısızlıktan sonra typed error döner. 

- **İçerik filtreleme** — çıktılarda PII tespiti, yasaklı içerik kontrolleri, düzeltme/sansürleme loglaması. Sonradan eklemeye göre çok daha kolay olduğu için en baştan yerleşik olmalıdır. 

### 6.3 Bağlam bloğu contract'ları

Her blok şu imzaya sahip bir function export eder: 

```typescript
loadBlockContext(orgId: string, options?: BlockOptions): Promise<BlockContext>
``` 

Burada `BlockContext`, alan erişicileri ve bir `.toPromptString()` method'u olan yapılandırılmış bir object'tir; böylece tüketen route'lar ya bloğun tamamını bir prompt içine bırakabilir ya da ihtiyaç duydukları belirli alanları seçebilir. Bu, her tüketiciyi tek bir katı string formatına zorlamayı önler. 

Temsili özellikler için blok bileşimi: 

| Özellik | Birleştirdiği bloklar |
| --- | --- |
| email-generate | brand + org + industry + audience + plan + assets + (optional) knowledge |
| journey-content (her e-posta adımı için) | brand + org + industry + journey-context + audience + plan + assets |
| form-generate | brand + org + industry |
| chat agent | brand + org + industry + knowledge + conversation history |
| strategy agent | brand + org + industry + methodology + plan + insights + knowledge |
| insights-agent | org + industry + methodology + plan + insights + knowledge |
| recommendation action | yukarıdakilerin tümü + signal context + recommendation reasoning |

### 6.4 Birleşik email-content component'i

Markalı HTML e-posta gövdesi üretmesi gereken herhangi bir yüzeyden çağrılabilen bir function. Lansmanda üç tüketici vardır: email editor (bağımsız), journey editor (e-posta adımı başına), recommendation action handler. 

İmza, mevcut `AIEmailModal` içindeki prop contract refactor'ı ile uyumludur (bkz. Bölüm 4.5). Function, yapılandırılmış bir generation context ve kullanıcı tarafından verilen bir niyet alır; yapılandırılmış bir sonuç döndürür: 

```typescript
generateBrandedEmail({
  intent,         // user description of what the email should achieve
  context,        // GenerationContext: campaign_email | journey_step | standalone
  cta?,           // optional explicit override; otherwise derived from context
  structuralOptions?,
}): Promise<{
  subject, previewText, body_html,
  suggested_cta, derived_from_context
}>
``` 

Function içeride, `kind` değerine göre ilgili bağlam bloklarını birleştirir: her çağrı için brand ve org, gerektiğinde journey/event/recipe/audience bağlamı ve görsel isteniyorsa assets. İstemci sarmalayıcıyı çağırır, çıktıyı `EmailOutputSchema` ile doğrular ve tüketicinin render ettiği yapılandırılmış yanıtı döndürür. 

`AIEmailModal`, kullanıcıya dönük inceleme adımı olan yüzeyler için canonical tüketicidir. Başsız çağıranlar (ör. başka inceleme olmadan commit yapan recommendation action handler'lar) modalı render etmeden alttaki API'yi doğrudan çağırır. 

## 7. Geçiş planı

10-15 haftaya yayılmış 7 PR halinde sıralanmıştır. Her PR bağımsız olarak yayına alınabilir. Sıralama, veri bağımlılıklarına saygı duyar: tüketicilerden önce temel, ihtiyaç duyan özelliklerden önce bağlam blokları ve alan semantiğine bağlı bağlam blokları (hedef kitle) ise alan etiketleme UI'ı geldikten sonra. 

### 7.1 PR sırası ve kapsam

| PR | Adı | Kapsam | Müşteriye görünür mü? |
| --- | --- | --- | --- |
| 9 | Temel + email-generate proof | `/lib/ai/client.ts`, `/lib/ai/usage/log.ts`, `/lib/ai/context/`{brand,org,industry}.ts oluştur. `/api/email/generate` route'unu desenin birebir proof'u olarak taşı. `ai_usage` şemasını eksik denetim alanlarıyla genişlet. Sistem alanı ve üyelik şablonu alanları için varsayılan `tags` değerlerini tohumla (küçük bir içerik migration'ı). | Hayır — e-posta çıktısı aynı |
| 10 | Birleşik email-content component'i | `AIEmailModal`'ı paylaşılan bir component'e çıkar. Prop contract'ı emailId'den `GenerationContext`'e refactor et (`campaign_email` \| `journey_step` \| `standalone`). Birleşik backend route'unu oluştur. Modalı, e-posta adımı başına üretim için journey editor içine bağla. event/form/recipe/audience üzerinden bağlam farkındalığıyla CTA türetmeyi içerir. | Evet — yolculuk e-postaları marka + bağlam ile AI tarafından üretilebilir |
| 11 | Form/event agent geçişi | Form-agent ve event-agent trigger'ları onay e-postası göndermeyi bırakır. Kontrol journeys'e geçer (ilk yolculuk adımı olarak onay). Agent trigger'ları "yolculuğa kaydet + gelen kutusu için konuşma thread'i aç" kapsamına daralır. HTML üretim tekrarları kaybolur. | Kısmen — daha temiz mimari, gözlemlenebilir olarak aynı akış |
| 11p | Alan etiketleme UI'ı | `/dashboard/settings/ai-ready` adresinde kişi alanlarını anlamsal etiketlerle işaretlemek için müşteri yüzlü UI. İlk çerçeveye göre daha basit; çünkü sistem alanları önceden etiketli (PR 9'da evrensel varsayılanlar tohumlanır) ve şablon alanları sektör başına önceden etiketli (bu da PR 9'da tohumlanır). UI yalnızca özel alanlar için gerçek etkileşim gerektirir. Hazırlık yüzdesini görünür biçimde gösterir. | Evet — admin özel alanları etiketleyebilir; ilk ziyarette büyük ölçüde tamamlanmış bir durum görür |
| 12 | Bağlam blokları (methodology, plan, insights, audience, assets) | `/lib/ai/context/`{methodology,plan,insights,audience,field-semantics,assets}.ts oluştur. Field-semantics, PR 11p'deki veriyi tüketir. Audience, field-semantics'e bağlıdır. Assets, mevcut `content_assets` altyapısını AI tüketicilerine açar. Knowledge block chat-only yapıdan tüm özelliklere genellenir. | Hayır — alt yapı katmanı |
| 13 | AI içerikli recommendation action handler'lar | Today sayfası komuta merkezinin "Build the campaign" aksiyonunu; gerçek hedef kitleler, birleşik component üzerinden AI içerikli gerçek yolculuklar oluşturacak şekilde bağla. Her bağlam bloğu buraya akar (görsel seçimi için assets dahil). Güven ilerleyişinin Phase 2'si burada yanar. Segment düzeyinde hiper-kişiselleştirme etkinleşir. | Evet — Phase 2 yeteneği canlı |
| 14 | Today sayfası + Retain dashboard + ⌘K palette | Insights yenilemesinin müşteriye dönük yüzeyleri. Today komuta merkezi olarak. Üyelik için Retain dashboard. ⌘K analitik palette. | Evet — lansmana hazır yüzeyler |

### 7.2 Bağımlılıklar

| Engelleyici | Önünü açtığı şey |
| --- | --- |
| PR 9 temeli | Sonraki her PR (istemci sarmalayıcıyı ve ilk bağlam bloklarını sağlar) |
| Alan etiketleme UI'ı (11p) | Faydalı veri döndüren field-semantics block, gerçek iş yapan audience block, Phase 2 recommendation derinliği |
| Birleşik email-content component'i (PR 10) | Journey content (PR 10'un kendisi), form/event agent geçişi (PR 11 — agent'ler HTML üretmeyi bırakır), recommendation action handler'lar (PR 13) |
| Tüm bağlam blokları (PR 12) | Zengin ve bağlamsal AI içerikli PR 13 action handler'lar |
| PR 13 | Güven inşası ilerleyişinin Phase 2'si — temizliğin müşteriye görünür değeri |

### 7.3 Karar noktaları

Takvim içine yerleştirilmiş üç kontrol noktası — kapsamı kesinleştirmek veya ayarlamak için anlar: 

- **4. haftanın sonu (PR 10 sonrası)** — birleşik email-content component'i gerçekten kilit taş olacak kadar iyi çalışıyor mu? Evetse devam et. Zorlanıyorsa journey-content entegrasyonunu v2'ye bırak ve lansman için şablonlara yaslan. 

- **8. haftanın sonu (PR 12 sonrası)** — alan etiketleme UI'ı yayında ve kullanıcılar gerçekten etiketleme yapıyor mu? Değilse audience block seyrek veri döndürür ve Phase 2 recommendation'lar gücünün yarısını kaybeder. Karar: etiketleme için iki hafta daha uzat mı, yoksa zengin hedef kitle bağlamı olmadan mı gönder? 

- **10. haftanın sonu (PR 13 sonrası)** — recommendation-to-action akışı kabul edilebilir içerik üretiyor mu? Evetse gönder. Çıktı kalitesi düşükse, PR 14 bunu görünür kılmadan önce prompt tuning için zaman ayır. 

### 7.4 Risk kaydı

Gözler açık olunması gereken belirli riskler: 

- **Ön-üretim varsayımı** — temizlik, bugün form-agent veya event-agent kullanan canlı müşteriler olmadığını varsayıyor. Pilot müşteriler bu özellikleri kullanmaya başladığında, agent'ten gelen onay e-postası yolunu devre dışı bırakmak sil-ve-yeniden-kur konusu değil, geçiş konusu olur. 

- **Alan etiketleme UI'ı mühendislikten çok UX işidir** — ekran, 40+'dan fazla kişi alanı olan kuruluşlar için yönetilebilir hissettirmeli, `tags` önerilerini makul sunmalı ve mükemmel etiketleme yapmayanı cezalandırmamalıdır. Bunu hafife alırsan zaman çizelgesi sessizce kayar. 

- **Geçiş sonrası prompt tuning** — birleşik component'e taşınan her route, çıktı kalitesinin değişebileceği bir andır. Geçişten sonra yüzey başına 2-3 gün yan yana test planla. 

- **5-8. haftalar görünmezdir** — hiçbir müşteriye dönük şey ilerlemiyormuş gibi göründüğü, motivasyonun düşebileceği tehlikeli pencere. Bunun beklenen bir durum olduğunu, bir başarısızlık modu olmadığını ekibe anlatmaya değer. 

- **Müşteri geri bildirim döngüsü** — 6. haftaya kadar hiçbir pilot müşteri Phase 1 özelliklerini görmezse, Phase 2 karanlıkta inşa ediliyor demektir. Hangi pilot müşterinin neyi, ne zaman göreceği konusunda bilinçli olmak gerekir. 

## 8. Veri mimarisi etkileri

Bu dokümanı inceleyen veri mimarı için özellikle ilgili noktalar. Şema etkileri, çoklu kiracı izolasyonu, denetim ve AI alt yapı katmanını destekleyen alan semantiği katmanı. 

### 8.1 Şema eklemeleri ve değişiklikleri

Temizlik şu şema değişikliklerini gerektirir; ihtiyaç duydukları iniş sırasına yaklaşık olarak göre listelenmiştir: 

| PR | Tablo | Değişiklik | Gerekçe |
| --- | --- | --- | --- |
| 9 | `ai_usage` | Şu sütunları ekle: `user_id`, model, latency_ms, success, `error_message`, created_at, `prompt_hash`, `output_hash`, `consent_status`, `data_residency_region`, `trace_id`, `content_filter_outcome` | Yalnızca maliyet takibi değil, uyumluluk denetim izi |
| 11p | `contact_field_definitions` | Daha önceki geçişte `description`, `field_tags`, `ai_suggested_tags` ile zaten genişletildi. Bunu UI doldurur. | Doldurulduğunda AI-ready katman faydalı hâle gelir |
| 12 | `audience_contexts` (yeni) | Filtreler + field-semantics'ten türetilen "hedef kitle X anlamsal olarak Y demektir" için opsiyonel materialised view. View veya table olabilir. | Performans — audience block sık çağrılır |
| 13 | `recommendation_actions` | Mevcut tablo genişletilir: `ai_call_trace_id`, `action_journey_id`, `action_audience_id` | Recommendation commit'ini tetiklediği AI çağrılarına bağlar |
| 14 | `ai_recommendations` | Mevcut tablo. Şunları ekle: `confidence_type` ('counted' \| 'suggested'), `source_signal_id`, `plan_goal_id`, `programme_id` | Phase 2 yüzeyi plan farkındalığı taşıyan recommendation'lar gösterir |

### 8.2 Çoklu kiracı izolasyonu

Her tabloda `org_id` vardır ve `profiles.id` = `auth.uid()` deseni üzerinden RLS ile korunur. AI ile ilgili eklemeler de istisnasız aynı deseni izler: 

- `ai_usage`: `org_id` bazında RLS. Yazımı istemci sarmalayıcı içinden service role yapar. 

- `contact_field_definitions` üzerindeki alan semantiği genişletmesi: mevcut tablonun RLS'si bunu da kapsar. 

- Recommendation tabloları: `org_id` bazında RLS. 

- Knowledge tabloları: mevcut `org_id` bazlı RLS. Küratörlü içerik kapsam dışı değildir ama sıralanır. 

Mimari açıdan önemli nokta şu: AI çağrıları server-side çalışır ve service-role Supabase client kullanır. Sarmalayıcı, `org_id` değerini authenticated session'dan okur ve bunu her bağlam bloğu okuması için kapsam belirleme primitive'i olarak kullanır. `org_id` olmadan hiçbir AI çağrısı yoktur. 

Kuruluşlar arası veri sızıntısı risk yüzey alanı, önem sırasına göre: 

- **Knowledge retrieval** — vector search, kuruluş kapsamlı içerikte `org_id` ile filtreleme yapmalıdır. Küratörlü içerik paylaşılır. Kapsamı arayan değil retrieval function uygular. 

- **Benchmarks (insights block)** — tasarım gereği kuruluşlar arası agregatlar döndürür. Tek bir kuruluşun tespitini önlemek için minimum-N eşiği (5-10) uygulamalıdır. Eşiğin altında blok "n/a" döndürür. 

- **Logs ve audit trails** — `ai_usage` kuruluş bazında kapsamlanır. Kuruluşlar arası raporlama (iç kullanım için) müşteri yüzlü sorgudan değil, ayrı bir service-role view üzerinden yapılır. 

### 8.3 Veri alt yapı katmanı olarak alan semantiği

Mimaride veri katmanı açısından stratejik olarak en önemli parça budur. O olmadan AI geneldir. Onunla birlikte AI, yenilemeler, etkileşim ve yaşam döngüsü aşaması hakkında sektöre özgü iş terimleriyle akıl yürütür. 

Şema (zaten prod'da): 

`contact_field_definitions` şu sütunlara sahiptir: `description` (serbest metin iş anlamı), `field_tags` (v1 için 8 kontrollü kelime dağarcığı değerine CHECK constraint ile bağlı anlamsal `tags` dizisi), `ai_suggested_tags` (insan onayı bekleyen AI önerisi `tags`). 

Üyelik v1 için 8 etiketli kelime dağarcığı: kesin değerleri `tag_labels` table'ını sorgulayarak veya `membership_framework_seed_v1` migration'ını inceleyerek doğrula. B2B ve diğer dikey sektörler gönderildikçe kelime dağarcığı ya küresel olarak ya da dikey sektör bazında büyür (açık ürün kararı). 

#### Alan etiketleme katman yapısı

Kişi alanları mevcut kişiler ayarları UI'ında üç katmana ayrılır. Alan etiketleme bunların her birine farklı uygulanır: 

| Katman | Etiketleme yaklaşımı | Neden |
| --- | --- | --- |
| Sistem alanları (11, evrensel) | Evrensel varsayılanlarla önceden etiketlenir, PR 9'da içerik olarak tohumlanır. Salt okunur — kuruluş bazında override yok. | Sistem alanlarının anlamı evrenseldir (email = kimlik, timezone = iletişim tercihi, last_activity = etkileşim sinyali). Bir kuruluş alanın başka bir anlama gelmesini istiyorsa bu override değil, özel alandır. |
| Şablon alanları (sektör bazında) | Sektör başına önceden etiketlenir, framework ile birlikte içerik olarak tohumlanır. Salt okunur — kuruluş bazında override yok. | Şablon alanları, sektörün neyin önemli olduğuna dair görüş sahibi yaklaşımıdır (member_since = yaşam döngüsü göstergesi, renewal_date = yenileme sinyali). Override edilebilir etiketleme, görüş sahibi sektör şablonu fikrinin amacını bozar. |
| Özel alanlar (kuruluşun oluşturduğu) | Kullanıcı başlangıç sürecinde veya sonrasında etiketler. AI; alan adı, türü ve varsa örnek veriye göre etiket önerir. Kullanıcı onaylar veya override eder. | Özel alanlar tanım gereği kuruluşa özgüdür. Kuruluş alanın ne anlama geldiğini bilir ve AI'a söyleyebilir. AI, mevcut özel alanların toplu etiketlenmesindeki sürtünmeyi azaltmak için öneri yapar. |

Bu katman yapısı, "alan etiketleme UI'ı"nı (PR 11p) her alanı sıfırdan etiketlemekten anlamlı biçimde daha basit hâle getirir. Tipik bir kuruluş şunları görür:

- **Sistem alanları:** önceden etiketli, sistem etiketiyle salt okunur gösterilir
- **Şablon alanları:** önceden etiketli, şablon etiketiyle salt okunur gösterilir
- **Özel alanlar:** AI önerili etiketler gösterilir, kullanıcı kabul eder veya override eder

Çoğu kuruluş ekrana geldiğinde alanların yaklaşık %80'inin zaten etiketlenmiş olduğunu görür ve yalnızca kendi özel eklemeleriyle ilgilenir. "5 dakikada AI-ready" vaadini mümkün kılan şey budur — işin büyük kısmı müşteri çabasına değil, müşteriyle etkileşimden önce içerik tohumlamasına dayanır.

Alan semantiği, birkaç aşağı akış bağlam bloğunun kapısıdır:

- **Audience block**, segmentleri sütun düzeyi filtreler yerine iş terimleriyle tanımlamak için alan semantiğine ihtiyaç duyar ("90 gün içinde yenilenecek") ; "renewal_date < now() + 90 days" gibi değil.
- **Insights block**, hangi alanların sinyal, hangilerinin tanımlayıcı, hangilerinin tercih olduğunu bilmek için alan semantiğini kullanır.
- **Phase 2 recommendation handler'lar**, doğru kavrama referans veren metin üretmek için alan semantiğini kullanır ("yenilenecek üyeleriniz" vs "renewal_date değeri yaklaşan kişiler").

#### Paralel bir alt yapı katmanı olarak varlık metadata'sı

`content_assets` table'ı zaten varlıklar için benzer bir desen uygular: 

- `description` (yüklemede `/api/content/analyse` aracılığıyla görseller için AI tarafından üretilir)
- `tags` (AI tarafından üretilen string dizisi)
- `ai_analysed` (AI'ın işlediğini gösteren işaret)
- `content_type` ve `mime_type` (image | audio | video | file ve belirli format) 

Assets context block için şema değişikliği gerekmez. Gerekli olan blokun kendisidir — bu verinin diğer özellikler için (e-posta üretimi, yolculuk içeriği, bülten oluşturma) AI prompt'una açılması. Phase 2 hiper-kişiselleştirme için bu blok, AI'ın alıcı segmentinin ilgi alanına veya e-postanın konusuna uyan görseller önermesini sağlar. 

Lansmanda görsel varlıklar otomatik olarak AI ile etiketlenir. PDF, video ve ses varlıkları ise henüz AI ile analiz edilmez — kullanıcı tarafından verilmiş adlara sahiptirler ama `description` veya `tags` yoktur. AI analizinin görsel olmayan içerik türlerine genişletilmesi v2 konuşmasıdır. 

### 8.4 Denetim ve gözlemlenebilirlik

Genişletilmiş `ai_usage` table'ı, AI ile ilgili her şey için tek doğruluk kaynağı hâline gelir. Raporlama ve özellik bazlı analiz bu table üzerinden çalışır. Başka log yüzeyi yoktur. 

Belirli gözlemlenebilirlik gereksinimleri: 

- Kuruluş başına, özellik başına, ay başına maliyet takibi — eğer sisteme inerse kullanıma dayalı fiyatlandırmayı ve maliyet farkındalığıyla özellik önceliklendirmesini destekler. 

- Özellik başına latency takibi — müşteri şikâyetlerinden önce yavaş yüzeyleri tespit etmek için gereklidir. 

- Retry takibi — her doğrulama retry'ı log'lanır. Aynı prompt üzerinde retry deseni görmek, tuning gerektiren bir prompt olduğunu gösterir. 

- Hata takibi — `error_message` sütunu hata modunu yakalar. Toplu bakıldığında hangi prompt'ların en kırılgan olduğunu gösterir. 

- Denetim bağlantısı — `trace_id`, tek bir kullanıcı aksiyonunu (ör. "kullanıcı X recommendation üzerinde Build the campaign'a tıkladı") tüm aşağı akış AI çağrılarına bağlar (hedef kitle `description`, yolculuk üretimi, e-posta adımı başına içerik). Herhangi bir çıktıya itiraz edildiğinde AI Act kapsamındaki "bunun neden yapıldığını açıklama" yükümlülüğü için gereklidir. 

## 9. Uyumluluk ve altyapı için ileriye bakış

Bugün alınan kararlar, lansman sonrası kurumsal uyumluluk standartlarını karşılamayı ya da Azure altyapısına geçişi engellememelidir. 

### 9.1 Uyumluluk standartları yığını

| Standart | Kapsam | Lansmanda geçerli mi? |
| --- | --- | --- |
| GDPR (UK + EU) | İşleme için hukuki dayanak, veri sahibi hakları, ihlal bildirimi, DPA. EU müşterilerine hizmet veren UK merkezli ürün için zaten zorunlu. | Evet — zorunlu |
| SOC 2 Type 2 | Güvenlik, kullanılabilirlik, işleme bütünlüğü, gizlilik, mahremiyet kontrolleri. Kurumsal satışın kapı sertifikası. | 12 ay içinde yol açılmalı — tipik kurumsal müşteri talebi |
| EU AI Act | "Sınırlı risk" AI için şeffaflık yükümlülükleri (recommendation engine büyük olasılıkla bu kapsamdadır); herhangi bir şey "yüksek risk" olarak sınıflanırsa daha ağır yükümlülükler. | Şeffaflık yükümlülükleri kademeli tarihlerde devreye girer — ilk dalga 2025-2026 |
| ISO 42001 | AI yönetim sistemi standardı. Yeni (2023). 2026'da kurumsal beklenti hâline geliyor. | 18 ay içinde yol açılmalı |
| HIPAA / health data | Sağlıkla ilişkili veri gelirse. | Üyelik kuruluşları için beklenmiyor |

### 9.2 Altyapı geçiş rotası

| Şuradan | Şuraya | Temizlik tasarımına etkisi |
| --- | --- | --- |
| GitHub | GitHub Enterprise | Mimari olarak yok — operasyonel geçiş |
| Supabase | Postgres on Azure | RLS ve şema taşınabilir. Auth, storage, edge functions için karşılıklar gerekir. Şema migration'ları mümkün olduğunca satıcıdan bağımsız SQL olmalıdır. |
| Vercel | Azure App Service | Next.js taşınabilir. Inngest SaaS olarak kalır ya da Azure Functions'a taşınır. Environment-variable desenleri Vercel'e özgü varsayımlar yapmamalıdır. |
| Anthropic direct API | Azure AI Foundry | İstemci sarmalayıcı geçiş arayüzünün KENDİSİDİR. Başından itibaren sağlayıcı değişimine göre tasarlanmıştır. |

7. bölümde açıklanan temizlik çalışması altyapı geçişini yapmaya çalışmaz. Onun için tasarım yapar. Özellikle:

- **Sağlayıcı soyutlaması olarak istemci sarmalayıcı** — "Anthropic SDK sarmalayıcısı" değil. İç contract sağlayıcıdan bağımsızdır. Maliyet çevirisi, içerik filtreleme, retry davranışı ve doğrulama, sağlayıcıdan bağımsız biçimde bu katmanda gerçekleşir.
- **Satıcıdan bağımsız SQL olarak şema migration'ları** — mümkün olduğunda Supabase'e özgü sözdiziminden kaçın. ANSI Postgres'e bağlı kal.
- **Environment variables** — AI_PROVIDER (anthropic | azure_foundry | etc.), AI_REGION, AI_MODEL_DEFAULT vb. Kodlanmış değil, yapılandırma odaklı.
- **`ai_usage` içindeki `data_residency_region` sütunu** — bugün her çağrı anthropic.com'a gidiyor olsa bile bölgeyi ilk günden log'la. Geçiş olduğunda sütun zaten oradadır. 

### 9.3 Özellikle Azure AI Foundry hakkında

Azure AI Foundry, Anthropic modellerini OpenAI, Mistral ve diğerleriyle birlikte tek bir Azure-native API yüzeyi üzerinden barındırır. Sweetspot için beklenen faydalar: 

- Müşteri gerektiriyorsa EU bölgelerinde veri yerleşimi 

- Azure ekosisteminin geri kalanıyla entegre kurumsal denetim ve uyumluluk özellikleri 

- Azure tüketiminin geri kalanıyla tek faturalandırma yüzeyi 

- Azure standardını kullanan kurumsal müşteriler için tedarik sürecinde daha kolay yol 

Mevcut gereksinimlerle karşılaştırılarak kontrol edilmesi gereken bilinen sürtünmeler: 

- Model kullanılabilirlik gecikmesi — yeni Anthropic model sürümleri tipik olarak AI Foundry'de doğrudan API'dan haftalar sonra görünür. Lansman, yalnızca doğrudan Anthropic'te olan belirli bir modele bağlı olmamalıdır. 

- Özellik eşdeğerliği boşlukları — prompt caching, computer use ve diğer özellikler AI Foundry'ye ilk günde gelmeyebilir. AI Foundry üzerindeki mevcut Claude sürümlerinin bugün kullanılan üretim desenlerini desteklediğini doğrulamak gerekir. 

- Fiyatlandırma — Azure fiyatlandırması Anthropic direct'ten farklıdır, bazen anlamlı ölçüde. `/lib/ai/usage/cost.ts` içindeki maliyet hesaplaması sağlayıcıya özgü fiyatlandırma tablolarını desteklemelidir. 

Önerilen yol: sarmalayıcı yerinde olacak şekilde Anthropic direct üzerinde lansman yap. Azure AI Foundry'ye geçişi, lansman istikrarlı olduğunda ve özellik eşdeğerliği doğrulandığında v1.5 PR olarak yap. 

### 9.4 İçerik filtreleme ve PII

Çıktı içeriği filtreleme, hoş olsa iyi olur türünde değil; uyumlulukla ilgili bir tasarım kararıdır. Gereksinimler: 

- **PII tespiti** — çıktılar, girdide bulunmayan e-posta adresleri, telefon numaraları veya diğer PII'ların kazara ifşası için taranır. Desenler, ciddiyete göre engeller veya işaretler. 

- **Yasaklı içerik filtreleri** — temel küfür ve düzenlenmiş konu tespiti. Müşteri tarafından yapılandırılabilir eşikler. 

- **Düzeltme/sansürleme loglaması** — içerik engellendiğinde veya değiştirildiğinde neyin ve neden filtrelendiğini log'la. AI Act'in açıklanabilirlik yükümlülükleri için gereklidir. 

Mimari karar şudur: filtreleme, model döndükten sonra ve içerik tüketen route'a teslim edilmeden önce, istemci sarmalayıcıda yapılır. Tek bir yerde merkezileştirilmiş, denetlenebilir ve filtre sağlayıcıları geliştikçe değiştirilebilir. 

## 10. Açık sorular

API biçimini veya veri modelini etkileyen ve en baştan çözülmesi gereken kararlar. Bazıları teknik (veri mimarı karar verebilir). Bazıları ürün stratejisiyle ilgili (ürün ekibi karar verir). Bazıları ise ticari (müşteri veya partner görüşmeleri karar verir). 

### 10.1 Mimari düzeyi

- **İstemci sarmalayıcı kapsamı.** PR 9'da minimal sürüm mü (loglama + retry + özellik bazlı model seçimi) yoksa tam sürüm mü (doğrulama + içerik filtresi + maliyet hesaplaması da dahil)? Öneri: PR 9 için minimal, `/schemas/` geldiğinde PR 11'de genişlet. 

- **Prompt ayırma stratejisi.** Prompt'ları exported string/function'lar olarak `/lib/ai/prompts/` içine mi çıkaralım, yoksa bağlam bloklarını route'ların içinde mi birleştirelim? Öneri: çıkar — güçlü biçimde. Inline prompt'lar her değişikliği tüm dosyanın yeniden yazımı hâline getirir. 

- **Bağlam bloğu dönüş biçimi.** String fragment mı, yoksa biçimlendirme method'ları olan yapılandırılmış object mi? Öneri: `.toPromptString()` ve ayrı getter'ları olan yapılandırılmış object. Route'ların ihtiyaç duyduklarını seçmesini sağlar. 

- **`ai_usage` sütunlarının nihai hâli.** PR 9 şema migration'ı inmeden önce veri mimarı ile tam hedef sütun setini teyit et. 

### 10.2 Marka ve içerik

- **Şablon başına marka rolü override'ları.** "Bu belirli newsletter CTA için secondary değil accent kullanıyor." `campaign_emails` üzerinde mi, yoksa şablonda mı saklanmalı? v2'ye ertele mi yoksa PR 10'a dahil et mi? Öneri: ertele. 

- **Chat'te marka dahil etme stratejisi.** Multi-turn chat için marka system message içinde bir kez mi olmalı, yoksa her turda yeniden mi enjekte edilmeli? Öneri: markanın tüm yanıtlar için geçerli olduğunu açıkça söyleyen instruction ile yalnızca system message içinde. Daha ucuz, daha basit. 

- **Agent marka derinliği.** Agent'ler yalnızca inbound olduğunda tam brand block mu almalı, yoksa ince bir dilim mi? Öneri: varsayılan olarak tam blok ver, aşırı stilizasyon görülürse agent bazında geri kıs. 

### 10.3 Veri ve bağlam

- **Alan etiketleme UI'ı v1 kapsamı.** Çözüldü: `/dashboard/settings/ai-ready` adresinde ayrı sayfa (kişiler ayarları içine inline değil). Üç katmanlı görünüm: sistem alanları önceden etiketli ve salt okunur, şablon alanları önceden etiketli ve salt okunur, özel alanlar ise AI önerili `tags` ile etkileşimli. Çoklu etiket yeteneği şemada kalır ama UI varsayılan olarak alan başına tek etiket kullanır; gerçekten birden fazlasını gerektiren örnekler görülünce yeniden değerlendirilir. 

- **Etiket kelime dağarcığının genişlemesi.** B2B / non_profit / wealth_management geldikçe 8 etiketli kelime dağarcığı büyür. Dikey sektör override'lı küresel model mi, yoksa tamamen dikey sektör bazlı mı? Ürün kararı. 

- **KB ingestion UX.** Müşteri kuruluş bazlı KB'ye içeriği nasıl ekler? Dosya yükleme, URL scrape ("web sitemizi içe aktar"), manuel notlar, toplu yapıştırma? Her biri farklı bir yüzeydir ve başlangıç sürecini şekillendirir. Ayrı bir planlama konuşmasına değer. 

- **Lansmanda KB içerik türleri.** v1'de hangi biçimler desteklenecek? Dokümanlar, web sayfaları, düz metin, bunların hepsi mi? 

- **Küratörlü knowledge içeriğinin kaynağı.** Sweetspot'un editoryal KB katmanını kim yazar (en iyi uygulamalar, düzenleyici rehberlik, sektör playbook'ları)? İç ekip mi, partner kaynaklı mı, yoksa AI üretip insan incelemesiyle mi? Ürün kararı. 

- **Her zaman açık mı, seçici KB retrieval mı.** Her zaman açık daha basit ama token açısından pahalı. Seçici yaklaşım, KB'nin ne zaman ilgili olduğuna karar verecek bir classifier gerektirir. Öneri: her zaman açıkla başla, token maliyetlerini gördükten sonra optimize et. 

- **AI üretiminde otomatik varlık önerisi.** E-posta veya newsletter üretirken AI varlık kütüphanesinden otomatik öneri mi sunsun, yoksa kullanıcı varlık seçimini davet edene kadar beklesin mi? UX'i etkiler. Varsayılan öneri: Phase 2'de otomatik öner, pazarlamacı commit öncesi önizlemede incelesin. 

- **Görsel olmayan varlıklarda AI analizi.** Bugün yalnızca görseller yüklemede AI tarafından oluşturulan açıklama ve `tags` alıyor. PDF, video ve ses dosyaları da analiz edilmeli mi (PDF için metin çıkarma, ses/video için transcript)? v2 konuşması. 

### 10.4 Uyumluluk ve altyapı

- **SOC 2 hazırlık takvimi.** Hedef denetim penceresi nedir? Bu, denetim altyapısının (log'lar, kontrol kanıtları, erişim gözden geçirmeleri) ne kadarının lansmanda, ne kadarının lansman sonrasında hemen hazır olması gerektiğini etkiler. 

- **EU AI Act risk sınıflandırması.** Sweetspot recommendation engine'i ve Phase 2 içerik üretimi büyük olasılıkla şeffaflık yükümlülükleri olan "sınırlı risk" kategorisindedir. Lansmandan önce hukuki inceleme ile bunu doğrulamak ve hangi disclosure UX'inin gerektiğini kapsamlamak gerekir. 

- **Lansmanda veri yerleşimi.** Erken müşteriler AI çağrıları için EU bölgesi işleme gerektiriyor mu? Gerektiriyorsa Azure AI Foundry geçişi lansman bağımlılığına dönüşür. Gerektirmiyorsa lansman sonrası uygundur. 

- **Maliyet kontrolleri.** Kuruluş başına günlük harcama limiti, özellik başına eşzamanlılık sınırı, uyarı eşiği. Şimdi eklemek kolaydır, ilk şaşırtıcı faturadan sonra sonradan eklemek acı vericidir. 

## 11. Sözlük

Bu doküman boyunca kullanılan terimler, alfabetik sırayla. Birçoğu Sweetspot'a özgüdür ve standart sektör kelime dağarcığı değildir. 

**Varlık bağlam bloğu.** AI özelliklerine `content_assets` kütüphanesini açan `/lib/ai/context/assets.ts` bloğu. Bir kuruluş ve bir bağlam verildiğinde, AI'ın üretilen çıktıda belirli varlıklara referans verebilmesi için ilgili varlıkları (görseller, video, ses, dosyalar) açıklamaları, `tags` değerleri ve URL'leriyle birlikte döndürür. Görsel yüklemeleri için mevcut AI etiketleme altyapısıyla desteklenir. 

**Agent.** Çok adımlı, konuşma yürüten, karar veren varlık. Örnekler: chat agent (gelen mesajları işler), strategy agent (Plan-Build-Launch-Learn döngüsü). Tek çağrılık AI invocations, agent değil handler veya generator'dır. 

**Varlık biçimi.** Bir AI route'unun ürettiği çıktı kategorisi. Üç biçim vardır: markalı HTML içerik, yapısal JSON, metadata. Farklı biçimlerin marka farkındalığı gereksinimleri ve birleştirme öncelikleri farklıdır. 

**Marka rolü.** 8 adlandırılmış anlamsal rolden biri (heading, body, link, cta_bg, cta_text, canvas, callout_bg, divider). Bir palette token'ına veya özel bir hex değerine eşlenir. `brand_settings`.`color_roles` JSONB içinde tanımlanır. 

**Komuta merkezi.** Today sayfasının Insights'ın yeni giriş kapısı olması. Önceliklendirilmiş recommendation card'lar, mini takvim, AI palette. Uzun vadeli vizyon: AI planı yürütür, pazarlamacı istisna durumunda devreye girer (güven ilerleyişinin Phase 4'ü). 

**Bileşenlere ayrılabilir bağlam bloğu.** AI özelliklerinin prompt'larına birleştirdiği, yapılandırılmış object döndüren function. Kurumsal anlayışın her boyutu için bir blok vardır (brand, org, industry, methodology, field-semantics, audience, plan, insights, knowledge). 

**Bağlam farkındalığıyla üretim.** Çevresel bağlam object'i alan (hangi yolculuk, hangi etkinlik, hangi hedef kitle, hangi plan hedefi) ve bunu CTA'ları önceden doldurmak, hedef kitlelerin adını koymak, hedeflere referans vermek ve metni uyarlamak için kullanan AI üretimi. 

**Alan semantiği.** Her kişi alanının iş bağlamında ne anlama geldiğini anlatan kişi alanı tanımları üzerindeki etiketler (yenileme sinyali, etkileşim sinyali, yaşam döngüsü göstergesi vb.). AI-ready temel. 

**Pilot müşteri.** Lansman öncesinde ekiple yakın çalışan, genel kullanıma açılmadan önce geri bildirim veren müşteri. "Paying customer" veya "prospect"tan farklıdır. 

**Hedef.** Bir pazarlama planındaki; hedef, başlangıç seviyesi, son tarih ve mevcut gidişat içeren ilan edilmiş sonuç. Türler sektör bazında framework tarafından yönlendirilir. 

**İşleyici.** Bir çalışma zamanı olayına yanıt veren tek çağrılık AI invocation (form gönderildi, etkinliğe kayıt yapıldı, gelen yanıt alındı). Çok adımlı değildir. Bugünkü form-agent ve event-agent, yanlış isimlendirilmiş handler'lardır. 

**Hiper-kişiselleştirme, segment düzeyinde.** AI, birden fazla hedef kitle segmentine göre uyarlanmış varyant içeren tek bir e-posta üretir. Aynı gönderim içinde farklı yaşam döngüsü aşamaları veya kıdem katmanları için farklı metinler üretir. Phase 2, lansman hedefi. 

**Hiper-kişiselleştirme, alıcı bazında.** AI, her bir alıcı için benzersiz içerik üretir — konu, gövde, varlıklar, CTA bu belirli kişiyi dikkate alır. Gönderim pipeline'ı teslimat anında alıcı bazında birleştirme yapar. Phase 3+, maliyet kontrol desenlerine bağlıdır. Tipik desen, maliyeti sınırlamak için variant-based hybrid'dir (AI N varyant üretir, alıcı bazlı mantık birini seçer). 

**Alan etiketleme katmanları.** Kişi alanları üç katmana ayrılır: sistem alanları (11, evrensel, hardcoded, önceden etiketli salt okunur), şablon alanları (sektör tarafından tohumlanmış, önceden etiketli salt okunur) ve özel alanlar (kuruluş tarafından oluşturulur, AI önerileriyle kullanıcı `tags`). Etiketleme UI'ı, her alanı sıfırdan etiketlemekten anlamlı ölçüde daha basittir — alanların çoğu önceden etiketlenmiş gelir. 

**Sektör şablonu.** Bir kuruluşun kayıt sırasında bağlandığı dikey sektör (membership, b2b, non_profit, wealth_management). Kelime dağarcığını, metodolojiyi, kıyaslama verilerini ve varsayılanları belirler. 

**Pazarlama framework'ü.** Sektör başına küratörlü, metodoloji destekli içerik. Bir dikey sektörde pazarlama stratejisinin nasıl yürütüldüğünü açıklar. Sense-Decide-Do-Sustain yapısı üzerine kuruludur. 

**Pazarlama planı.** Bir framework'ün belirli bir dönem için (genellikle bir çeyrek) müşteri tarafından somutlaştırılması. Hedefler, programlar, hedef kitle tanımları, KPI'lar ve durum içerir. 

**Phase 1 / Phase 2.** Güven inşası aşamaları. Phase 1: kurala dayalı öneriler, açık onay. Phase 2: onaylı AI tarafından üretilen içerik, öneriler plan hedeflerine referans verir. Her ikisi de lansmanı hedefler. 

**Önizle ve onayla.** Komuta merkezi için tavizsiz tasarım kuralı: tek tıkla asla gönderim yapılmaz. Her aksiyon; hedef kitle önizlemesi, içerik önizlemesi, öngörülen etki ve commit anında audit trail girişi gösterir. 

**Program.** Bir plan hedefi içindeki tutarlı yürütme birimi. Hedef kitleyi, taktikleri (journey/campaign/content brief), takvimi, KPI'ları ve durumu bir araya getirir. Aktivasyon birimidir. 

**Öneri kartı.** Today sayfasındaki birleştirilmiş primitive. Tek bir card içinde insight + recommendation + action öğelerini birleştirir. Kurala dayalıysa "Counted", AI tarafından üretilmişse "Suggested" olur. 
