---
title: "Windows sunucular için kara kutu, bölüm 1: Sorun çıkmadan kayıt başlasın"
description: "Sunucu gece yavaşladı, sabah elde veri yok. Çözümümüz: her Windows sunucuda bir PerfMon kara kutusu ve bu kaydı okuyan Azure SRE Agent."
images: ["social.png"]
date: 2026-10-14
draft: false
series: ["Windows sunucular için kara kutu"]
series_order: 1
tags: ["azure-sre-agent", "perfmon", "azure-policy", "azure-arc"]
showTableOfContents: true
---

Sunucu gece 03:10'da yavaşladı. Biri bakana kadar kendiliğinden düzeldi ve o sırada hiçbir şey kayıt almıyordu. Sabah
elde iz yok; yalnızca "dün gece sistem yavaştı" diye açılmış bir çağrı var.

Genelde yapılan, bir toplayıcı kurup sorunun tekrarlanmasını beklemektir. Bu günler sürebilir ve her günün bedelini iş
tarafı öder. Biz tersini istedik: **soru sorulduğunda kayıt zaten hazır olsun.**

Bu seride bunu birlikte çalışan iki parçayla kuruyoruz:

- **Her Windows sunucuda bir kara kutu.** Uçaklardaki kara kutu gibi sürekli kayıt alır, yakın geçmişi diskte tutar ve
  saatte bir teslim eder. Onu sunucuya Azure Policy yerleştirir; sunucuya ayrıca bir şey kurulmaz.
- **Kaydı okuyan bir uzman.** Microsoft'un operasyon ekipleri için geliştirdiği yapay zekâ agent'ı Azure SRE Agent,
  "bu sunucuda ne oldu?" gibi sade bir soruyu alır, kaydı getirir ve kanıtlarıyla yanıtlar.

Neden Log Analytics değil? Log Analytics içine alınan veriyi gigabayt başına ücretlendirir; her sunucudaki her sürecin
sayaçlarını sürekli göndermenin faturası hızla büyür
([Learn: Azure Monitor Logs cost](https://learn.microsoft.com/azure/azure-monitor/logs/cost-logs#data-size-calculation)) 📄.
Kara kutu ise kaydı Windows'un kendi veri toplayıcısıyla sunucuda tutar, yalnızca hazır dosyayı ucuz blob depolamaya
taşır ve agent ortak bir workspace'i sorgulamak yerine tek sunucunun kaydını doğrudan SQLite'a alır (bu bir tasarım
gerekçesi; Log Analytics'e karşı hız ölçmedik).

Bu yazıda iki parçanın nasıl birlikte çalıştığını tek bir akış şemasında görüyoruz; sonraki üç bölümde neyi adım adım
kuracağımızı da anlatıyoruz. Her şey açık kaynak bir playbook'a dayanıyor:
[VezirOrg/sreagent-playbook, `playbooks/perfmon-blackbox`](https://github.com/VezirOrg/sreagent-playbook/tree/main/playbooks/perfmon-blackbox).
Playbook'u kendi lab'imizde üç sunucuda çalıştırdık: dc ve iis1 (Azure VM) ile arc1 (Arc'a bağlı bir sunucu).

✅ = lab'imizde doğrulandı · 📄 = yalnızca belgelere dayanıyor (Microsoft Learn, playbook'un dokümanları), biz test
etmedik.

## Amaç ve hedef kitle

**Amaç.** Bu yazıyı bitirdiğinizde kara kutunun neyi kaydettiğini, kaydın anahtar kullanmadan özel depolamaya nasıl
ulaştığını, Azure SRE Agent'ın kaydı nasıl analiz ettiğini ve serinin hangi bölümünde hangi parçayı kurduğumuzu
bileceksiniz.

**Hedef kitle.** Windows sunucularını Azure'da çalıştıran ya da Azure Arc ile Azure'a bağlayan, performans verisine
sorun geçtikten sonra değil, sorun anında sahip olmak isteyen Windows yöneticileri ve SRE'ler. Temel Azure bilgisi
(abonelik, Azure Policy, managed identity) yeterli.

## Tüm döngü tek şemada

![Kara kutunun uçtan uca akışı: bir kez yapılan kurulum; Azure Policy ve Machine Configuration kara kutuyu sunucuya getirir; sunucu kaydeder, kaydı parçalara böler ve dışa aktarır; kendi kimliğiyle özel depolamaya yükler; Azure SRE Agent gerektiğinde kaydı alıp analiz eder; bulgulara göre atama ayarlanır](img/perfmon-blackbox-flow.tr.svg)

Şema üç banttan oluşuyor: **bir kez** yaptıklarınız, her sunucuda **kendiliğinden** ve sürekli çalışanlar, bir de biri
soru sorduğunda **ihtiyaç anında** devreye girenler. Numaraları sırayla izleyin.

### ① Bir kez yapılan kurulum

Üç şeyi yalnızca bir kez kurarsınız:

- **Özel bir depolama hesabı.** Hesaba yalnızca private endpoint üzerinden erişilir ve shared key kapalıdır; bu yüzden
  SAS üretilemez. Hesapla birlikte iki custom rol gelir: biri sunucunun yazmasına, diğeri Azure Policy'nin bu yetkiyi
  sunuculara dağıtmasına izin verir. ✅
- **Policy tanımları:** biri Azure VM'ler, biri Arc'a bağlı sunucular için. Her tanım kara kutu paketinin adresini ve
  SHA-256 değerini içerir; böylece hiçbir sunucuya başka bir paket gidemez. ✅
- **SRE Agent'a yüklenen skill,** `perfmon-triage`: agent'ın kaydı okurken kullandığı talimatlar ve betikler. ✅

### ② Azure Policy kara kutuyu sunucuya getirir

Policy'yi bir kapsama, örneğin bir kaynak grubuna ya da aboneliğe atarsınız. Gerisini Azure Policy ile Azure'un sunucu
içi yapılandırma hizmeti **Machine Configuration** halleder. Kapsamdaki her sunucuya `PerfmonBlackbox` adlı bir guest
assignment atanır ve paket, hash'i doğrulanarak indirilir. Yedi DSC kaynağı kara kutuyu kurar ve hep o hâlde tutar: biri
bir görevi silse bile görev bir sonraki denetimde, yaklaşık 15 dakika içinde geri gelir. 📄

Kara kutunun ayarları atamanın parametreleridir: kaydın nereye yükleneceği, en fazla ne kadar büyüyeceği (512 MB), ne
sıklıkla örnek alınacağı (10 saniyede bir) ve ne sıklıkla dışa aktarılacağı. ✅ Lab'de saatte bir dışa aktardık;
v1.0.1 sürümünde varsayılan 4 saatte birdir. ✅ 📄

Azure VM'lerde Machine Configuration için ek ücret ödenmez; Arc'a bağlı sunucularda sunucu başına ücret alınır. 📄

### ③ Sunucu kayıt alır

Her sunucuda Windows'un kendi aracı olan bir **PerfMon veri toplayıcı kümesi** çalışır ve kaydı *dairesel* bir ikili
dosyaya yazar: dosya dolduğunda en yeni örnek en eskisinin üzerine yazılır, bu yüzden disk asla dolmaz. arc1'de 512 MB
yaklaşık 25 saatlik veriye yetiyor. ✅

Geri kalan işi üç zamanlanmış görev yapar; görevler Windows'la birlikte gelen Windows PowerShell 5.1 ile çalışır:

- kayıt her 15 dakikada bir parça olarak kapatılır ve yeni parça başlar, ✅
- her dışa aktarımda, bir önceki dışa aktarımdan beri biriken parçalar tek bir CSV'de (UTC) birleştirilir; yanına her
  boşluğu nedeniyle (yeniden başlatma, saat değişikliği) birlikte yazan bir **manifest** eklenir ve hepsi tek bir
  zip'e konur, ✅
- sunucu yeniden başladığında eski dosya saklanır ve kayıt yeniden başlar. 📄

**Sunucuya bizden hiçbir şey kurulmaz.** Ek bir agent, servis ya da sürücü yok: yalnızca `logman`, `relog`, PowerShell
ve Görev Zamanlayıcı. 📄

### ④ Sunucu kaydı kendi kimliğiyle yükler

Sunucu zip'i **kendi managed identity'siyle** yükler: Azure VM bunu kendi instance metadata hizmeti üzerinden, Arc'a
bağlı sunucu ise Arc agent'ının hizmeti üzerinden yapar. ✅ Hiçbir yerde anahtar ya da SAS kullanılmaz. Sunucu
**yalnızca kendi klasörüne**, `perfmon/<sub>/<rg>/<server>/yyyy/MM/dd/` altına yazabilir; hiçbir kaydı, kendi kaydını
bile okuyamaz. ✅ Yükleme başarısız olursa sunucu yeniden dener; olmazsa bir sonraki dışa aktarım eksiği tamamlar. 📄
Eski zip'ler 30 gün sonra bir lifecycle kuralıyla silinir. 📄

### ⑤ Azure SRE Agent kaydı okur

Uzman burada devreye girer. Bir mühendis bir thread'de soru sorar, örneğin *"Analyse the latest PerfMon capture of
arc1"*. Agent `perfmon-triage` skill'ini seçer ve kendi sandbox'ında şunları yapar:

1. o sunucunun en yeni zip'ini (ya da bir zaman aralığındaki tüm zip'leri) kendi kimliğiyle, private endpoint
   üzerinden indirir ve CSV'yi manifest ile karşılaştırır; ✅
2. CSV'yi küçük bir SQLite veritabanına aktarır ve sabit bir kontrol listesinden geçirir: CPU, bellek, disk, ağ,
   süreçler; ✅
3. sonuçları önem sırasına göre bir raporla thread'e yazar. Skill, agent'tan bir nedeni ancak bir test o nedeni kanıta
   bağladığında söylemesini ister. ✅

Model ham sayıların hiçbirini görmez; yalnızca kontrol listesindeki soruların cevaplarını görür. Lab'imizde, bilerek
oluşturduğumuz ve doğru cevabını önceden yazdığımız bir soruna karşı agent iki sunucuda 100 üzerinden 95 ve 100 puan
aldı. ✅ Bu çalışmanın tamamı bölüm 4'te.

### Döngü tamamlanır

Agent'ın bulguları kara kutunun ayarlarını da değiştirebilir: daha kısa bir örnekleme aralığı, daha büyük bir dosya ya
da daha sık dışa aktarım. Atamanın bir parametresini değiştirirsiniz, Azure Policy bunu sunuculara dağıtır ve sonraki
kayıt daha ayrıntılı olur. 📄

## Size ne kazandırır

- **Sıkıştığınızda geçmiş elinizin altında.** "03:10'da ne oldu?" sorusunun cevabı zaten kayıtlı. Sunucu aniden
  kapanırsa en fazla son 15 dakika kaybolur ve manifest bunu açıkça yazar. 📄
- **Anahtar yok.** Yükleme, agent'ın erişimi ve isterseniz paket indirme de managed identity ile yapılır. ✅
- **Kurulacak ya da güncellenecek bir şey yok.** Windows'un kendi araçları Machine Configuration sayesinde yerinde
  kalır; hem Azure VM'lerde hem Arc'a bağlı sunucularda. ✅
- **Dakikalar içinde cevap.** Lab'imizde bir analiz yaklaşık 6 dakika sürdü. Bir analiz, agent'ın sürekli ödenen
  (always-on) ücretine ek olarak bölgeye göre kabaca 3,5–5 USD tutuyor; ayrıntılı tablo bölüm 2'de. ✅ 📄

## Seri için neler gerekiyor

| Ne | Neden | |
|---|---|---|
| Windows Server 2016 ya da üstü; Azure VM ya da Arc'a bağlı sunucu | kara kutu yalnızca Windows'un kendi araçlarını kullanır | 📄 (biz Windows Server 2022 ile çalıştırdık ✅) |
| Abonelikte Owner ya da bölüm 2'de listelenen ayrı ayrı yetkiler | Azure Policy tanımları, atamalar ve rol atamaları için | 📄 |
| Sunuculardan ve agent'tan depolamaya özel ağ erişimi | yükleme ve indirme yalnızca private endpoint üzerinden yapılır | ✅ |
| VNet integration'ı olan bir Azure SRE Agent | agent kayıtları aynı private endpoint üzerinden okur | ✅ |
| Azure CLI, Python 3 ve git kurulu bir admin makinesi (Windows'ta ayrıca Git Bash ya da WSL) | kurulum komutları zsh ve PowerShell için ayrı ayrı veriliyor | ✅ |

## Sonraki bölümlerde neler kuruyoruz

Hikâye aynı üç sunucuda devam ediyor.

- **[Bölüm 2]({{< relref "/posts/perfmon-blackbox-part-2" >}}): kurulum ve maliyet.** Depolama, policy'ler, atama ve skill; adım adım, her komut zsh ve PowerShell için
  ayrı, kurulumun çalıştığını gösteren kontroller ve bölge bölge maliyet tablosuyla.
- **[Bölüm 3]({{< relref "/posts/perfmon-blackbox-part-3" >}}): makinenin içi.** arc1'in içine bakıyoruz: klasör, veri toplayıcı, üç görev; yeniden başlatma ya da dolan
  bir disk kaydı nasıl etkiliyor ve bir sorun çıktığında ilk nereye bakılır.
- **[Bölüm 4]({{< relref "/posts/perfmon-blackbox-part-4" >}}): agent olayı inceliyor.** Azure SRE Agent'a arc1'in iki saatini soruyoruz: sakin bir saati ve bilerek bir
  sorun oluşturduğumuz bir saati. Agent neyi buldu, neyi yanlış söyledi ve bu cevap kaça mal oldu?

Bir sunucu bir dahaki sefere gece 03:10'da yavaşladığında kayıt zaten hazır olacak. Bölüm 2'de onu sunuculara
yerleştiriyoruz.
