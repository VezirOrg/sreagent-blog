---
title: "Windows sunucular için kara kutu, bölüm 4: agent olayı inceliyor"
description: "Azure SRE Agent, Arc'a bağlı bir sunucudaki PerfMon kara kutusunun iki saatlik kaydını bir skill ile analiz ediyor: önce sakin bir saat, sonra bilerek yük bindirdiğimiz ve doğru cevabını önceden yazdığımız bir saat. Agent neyi buldu, neyi yanlış söyledi ve tek bir analiz kaça mal oluyor?"
date: 2026-10-14
draft: false
series: ["Windows sunucular için kara kutu"]
series_order: 4
tags: ["azure-sre-agent", "perfmon", "azure-arc", "skills"]
showTableOfContents: true
---

[Bölüm 1]({{< relref "/posts/perfmon-blackbox-part-1" >}}), gece 03:10'da yavaşlayan ve bunu açıklayacak hiçbir verisi olmayan bir sunucuyla başlamıştı. [Bölüm 2]({{< relref "/posts/perfmon-blackbox-part-2" >}})'de
kara kutuyu kurduk, [bölüm 3]({{< relref "/posts/perfmon-blackbox-part-3" >}})'te kaydın makinede nasıl tutulduğunu ve saatte bir nasıl yüklendiğini gördük. Bu son
bölümde kara kutunun asıl varlık nedeni olan soruyu soruyoruz: **bu sunucuda ne oldu?**

Azure SRE Agent'a, bölüm 2 ve 3'te kullandığımız Arc'a bağlı arc1 sunucusunun iki saatini soruyoruz. İlki sakin bir
saat. İkincisinde **sorunu bilerek biz oluşturduk**: bir lab betiğiyle bir bellek sızıntısı ve kısa süreli yüksek CPU
yükü. Kayıt dışa aktarılmadan önce bunların tam zamanları bir dosyaya yazıldı. Böylece agent'ın cevabını satır satır
doğru cevapla karşılaştırabiliyoruz. Bunların hiçbiri gerçek bir olay değil; önemli olan her yerde bunu açıkça
belirtiyoruz.

✅ = lab'imizde doğrulandı · 📄 = yalnızca belgelere dayanıyor (Microsoft Learn, playbook'un dokümanları ve kodu), biz
test etmedik. Saatler UTC, 2026-10-14.

## Amaç ve hedef kitle

**Amaç.** Agent'ın bir kara kutu kaydını adım adım nasıl incelediğini, cevabının önceden bilinen doğruyla ne kadar
örtüştüğünü ve tek bir analizin kaça mal olduğunu görmek.

**Hedef kitle.** Azure SRE Agent'ı kullanan ya da kullanmayı düşünen ve agent'ın performans verisi üzerine yaptığı
analize ne kadar güvenilebileceğini merak eden SRE'ler ve Windows yöneticileri.

## Ön koşullar

| Ne | Neden | |
|---|---|---|
| Bölüm 2'deki kara kutu ve `perfmon-triage` skill'i | agent'ın hem kayıtlara hem de onları okuyan skill'e ihtiyacı var | ✅ |
| Agent'ta, depolamanın private endpoint'ini çözen VNet integration | skill zip'i private endpoint üzerinden indirir | ✅ |
| Soruyu soran kişi için agent üzerinde **SRE Agent Standard User** | agent'la sohbet edebilen rol ([Learn: user roles](https://learn.microsoft.com/azure/sre-agent/user-roles)) | 📄 |

## Agent skill'i nasıl kullanıyor

{{< mermaid >}}
flowchart LR
  Q["Bir thread'de soru:<br/>arc1'in son kaydını analiz et"] --> A["SRE Agent<br/>perfmon-triage skill'ini seçer"]
  A -->|perfmon_fetch_latest.py<br/>kendi kimliği, private endpoint| ST[("perfmon/&lt;sub&gt;/&lt;rg&gt;/arc1/...")]
  ST -->|en yeni zip, hash ve<br/>manifest kontrol edilir| CSV["CSV, 360 örnek"]
  CSV -->|perfmon_csv_to_sqlite.py| DB[("SQLite")]
  DB -->|perfq.py: orient,<br/>breadth, depth, bağ testleri| R["Thread'de sıralı rapor"]
{{< /mermaid >}}

Skill ham veriyi modelden uzak tutar. Agent kendi sandbox'ında Python çalıştırır: bir betik sunucunun en yeni zip'ini
indirip manifest'e göre kontrol eder, ikincisi CSV'yi bir SQLite veritabanına aktarır, bir sorgu kütüphanesi de sabit
bir kontrol listesindeki (CPU, bellek, disk, ağ, süreçler) soruları yanıtlar. Model yalnızca bu yanıtları okur;
360 × 1.800 sayının hiçbirini görmez. 📄 Thread'de bu süreç, "Phase 0: orient" adımından rapora kadar yaklaşık on
terminal adımı olarak görünür. ✅

İki saat için de aynı soruyu, her seferinde yeni bir thread'de sorduk: ✅

```text
Analyse the latest PerfMon capture of arc1. The captures are in the storage account <account>.
```

## 1. saat: sakin bir saat

**Kayıt:** `arc1_20261014-070704_20261014-080654.zip`; eksiksiz, boşluksuz, 10 saniyede bir alınmış 360 örnek. Agent
yaklaşık 6 dakikada yanıt verdi. ✅

![Agent'ın sakin saat raporu: karar WARNING, makine zor kullanılır değil; 07:45–07:50'de kısa bir Windows Update yükü; önem sırasına göre sorunlar: ani CPU ve IO yükü, commit artışı, hard page fault, disk okuma gecikmesi, gc_worker arka plan yükü](img/agent-idle.png)

**Karar: WARNING, "not hard to use".** Hiçbir kontrol beş dakika boyunca eşiğin üstünde kalmadı. Agent 07:45'te ani
bir yük buldu: %94,8 CPU, 31'lik işlemci kuyruğu, yaklaşık 800 MB fazladan commit edilmiş bellek, hard page fault'lar
ve 106 ms disk okuma gecikmesi; hepsi aynı on saniyede başlamış ve 07:50 civarında geçmiş. Agent bu yükü Windows
Update'e bağladı, çünkü Windows Update'in çalışan süreci `TiWorker` 07:45:55'te görünmüştü. ✅

Bu ne anlama geliyor:

- **Bu saat için elimizde doğru cevap yok**, o yüzden puanlayamıyoruz. Windows Update açıklaması akla yatkın; agent da
  bunun yalnızca zamanlamaya dayandığını kendisi belirtti: süreçler çok kısa sürdüğü için bağ testi çalışamadı. Bir
  nedeni dile getirmenin dürüst yolu da bu. ✅
- **Kara kutuyu yöneten süreci de gördü.** Beşinci maddedeki `gc_worker` (bir çekirdeğin %5–9'u), yapılandırmayı
  15 dakikada bir denetleyen Machine Configuration sürecidir. 📄 Agent onu normal saydı ve "info" olarak işaretledi. ✅
- **Bir ölçüm sapmasını ayıkladı**: 07:19'da, öncesinde ve sonrasında hiç okuma olmayan tek bir 208 ms'lik okuma
  gecikmesi örneği. ✅

## 2. saat: bilerek oluşturulmuş bir sorun

**Sorunu nasıl oluşturduk.** Playbook'taki lab betiği `make-trouble.ps1`, Windows'un `powershell.exe` dosyasının adı
değiştirilmiş iki kopyasını tek seferlik bir SYSTEM görevi olarak başlatır: `bbleak` bellek ayırır ve hiç geri vermez,
`bbcpu` bütün mantıksal CPU'ları meşgul tutar. Hiçbir şey kurulmaz; bu bir lab aracıdır, paketin parçası değildir. 📄
Betiği yarı sürede ve saatte 1.200 MB sızıntıyla çalıştırdık. Çalışırken yazdığı doğru cevap dosyası (kısaltılmış): ✅

```json
{
  "host": "arc1",
  "cpus": 2,
  "problems": [
    { "id": "leak", "process": "bbleak", "counter": "Private Bytes",
      "per_hour_bytes": 1258291200, "from": "2026-10-14 08:25:04", "to": "2026-10-14 08:47:34" },
    { "id": "cpu", "driver": "bbcpu", "counter": "Processor Information\\% Processor Time",
      "from": "2026-10-14 08:30:04", "to": "2026-10-14 08:36:04", "minutes": 6 }
  ],
  "capture_first": "2026-10-14 08:07:04",
  "capture_last": "2026-10-14 09:06:54"
}
```

Saatlik dışa aktarım bu saatin kaydını 09:07:10'da eksiksiz ve boşluksuz yükledi. Soruyu 09:10:37'de sorduk; yanıt
09:17:17'de geldi. ✅

![Agent'ın bilerek oluşturulan sorunla ilgili raporu: bbcpu CPU'yu tamamen meşgul ettiği için makine yaklaşık 6 dakika (08:30–08:36) zor kullanılıyor; bbleak sürekli büyüdü ama RAM'i tüketmedi; önem sırasına göre sorunlar, CPU critical; kök neden zinciri önce bbcpu, sonra MsSense](img/agent-planted.png)

**Karar: "hard to use for ~6 minutes (08:30–08:36)", CPU critical**; sızıntı ikinci bulgu olarak geçiyor. ✅

### Rapor doğru cevapla yan yana

| | Doğru cevap (bizim oluşturduğumuz) | Agent'ın raporu | |
|---|---|---|---|
| CPU yükü, süreç | `bbcpu` | `bbcpu`, PID 6784, 200%'ün yaklaşık %151'i | ✅ |
| CPU yükü, zaman | 08:30:04 – 08:36:04, 6 dk | 08:30:05'te başladı, "6 min from 08:30:15", 08:35:55'te durdu | ✅ |
| Sızıntı, süreç | `bbleak` | `bbleak`, PID 704, 08:25:04'te başladı, yaklaşık 08:47'de çıktı | ✅ |
| Sızıntı, hız | saatte 1.200 MB (1.258.291.200 bayt) | "31 MB → 548 MB at 1.3 GB/h" | ✅ yakın |
| Önem derecesi | 2 CPU'lu bir makinede 6 dakika boyunca tam dolu CPU | CPU **critical**; bellek, disk ve paging "info" | ✅ |
| Uydurulan bir şey | — | bizim oluşturduklarımız dışında sorun olarak gösterilen bir şey yok | ✅ |

Agent ayrıca yük sırasında CPU'ya yaklaşık %37 ekleyen `MsSense`'i (Microsoft Defender for Endpoint) adıyla belirtti.
Bunu biz oluşturmadık: sunucudaki gerçek Defender, yoğun çalışan bir sürece tepki veriyor. Rapor onu zincirde ikinci
sıraya koyuyor. ✅

### Puan: 100 üzerinden 95

Playbook, bilerek sorun oluşturulan her çalışmayı sabit bir puanlama tablosuyla, bir betik aracılığıyla ve doğru cevap
dosyasıyla karşılaştırarak puanlar. 📄 Bu çalışmanın sonucu:

| Madde | Puan | Bu çalışma |
|---|---|---|
| Zip, sunucu ve kaydın zaman aralığı adıyla belirtilmiş | 10 + 5 + 5 | 20 |
| Sızıntı bulundu: `bbleak` ve gerçek hızın ±%40'ı içinde bir büyüme hızı | 30 | 30 |
| CPU yükü bulundu: CPU, ±2 dakika içinde doğru başlangıç zamanı ve `bbcpu` adı | 30 | 30 |
| Yalnızca sızıntı için "critical" denmemiş | 5 | 5 |
| Uydurulan bir şey yok (commit, paging file, disk ya da ağ sorunu denmemiş; hiçbiri oluşturulmadı) | 5 | 5 |
| **"caused by", "because" ya da "drives" geçen her satırın arkasında bir `LINK:` satırı var** (skill'in bağ testi) | 5 | **0** |
| Raporda ham veri yok (30'dan fazla sayı içeren satır yok) | 5 | 5 |
| **Toplam** (geçme şartı: 80 ve üstü, oluşturulan her sorun bulunmuş) | 100 | **95, geçti** ✅ |

Beş puan ifade yüzünden gitti: karar cümlesi "CPU saturation **caused by** the `bbcpu` stress-test process" diyor,
ama raporda bunu destekleyen bir `LINK:` satırı yok. Raporun kendisi de `bbcpu` yalnızca iki zaman diliminde görüldüğü
için bağ testinin çalışamadığını yazıyor. Vardığı sonuç doğru; ancak skill'in kuralı açık: bir bağ testi nedeni
desteklemedikçe "coincides with" (aynı zamana denk geliyor) denmeli. ✅

## Tek bir analiz kaça mal oluyor

arc1'deki iki analiz 34 ve 37 Azure Agent Unit (AAU) harcadı; bir gün önce iis1'de bilerek sorun oluşturduğumuz analiz
de yaklaşık 35. ✅ Resmi fiyatla bu, **bölgeye göre derin analiz başına kabaca 3,5–5 USD** ediyor; Sweden Central'da
yaklaşık 3,9 USD. Fiyat tablosu, always-on maliyeti ve 10 ile 100 sunucu için örnek hesap [bölüm 2'de]({{< relref "/posts/perfmon-blackbox-part-2" >}}). 📄

## Bu testin göstermedikleri

- **Gerçek bir olay.** Yükü biz oluşturduk ve süreç adları (`bbcpu`, `bbleak`) çok şey ele veriyordu: agent onlara
  "stress-test binaries" bile dedi. Gerçek bir sorun kendini adıyla tanıtmaz.
- **Birden fazla saat, makine ya da soru.** Gerçek bir inceleme çoğu zaman birkaç kaydı kapsar; skill bir zaman
  aralığındaki kayıtları da getirebiliyor, playbook bunu ayrıca test etti. 📄
- **Nedeni bilinmeyen bir sorunda agent'ın ne yaptığı.** Sıradaki test bu olacak: nedenini kimsenin bilmediği,
  anonimleştirilmiş gerçek bir 24 saatlik kayıt, ayrı bir yazıda.

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|
| Agent zip'i listeleyemiyor ya da indiremiyor | VNet integration yok ya da private DNS hesabın adını çözmüyor | private DNS çözümlemesi olan bir VNet integration (bölüm 2) 📄 |
| Skill container'ı okurken 403 alıyor | okuma rolü yalnızca agent'ın user-assigned kimliğine verilmiş, oysa agent'ın terminali system-assigned kimliğiyle oturum açıyor | okuma rolünü iki kimliğe de verin (bölüm 2, adım 1) ✅ |
| Skill yeni bir sunucu için kayıt bulamıyor | ilk dışa aktarım henüz çalışmadı | ilk dışa aktarımı bekleyin (bölüm 3) 📄 |
| Rapor "complete: false" diyor | manifest boşlukları nedenleriyle yazıyor (yeniden başlatma, yerel sınır, okunamayan parça) | boşluklara bakın; bölüm 3 her nedeni açıklıyor ✅ |

## Ne öğrendik

- **Agent bilerek oluşturduğumuz iki sorunu da doğru zaman ve hızlarla buldu** ve makineyi zor kullanılır hâle
  getirenin 6 dakika boyunca tam dolu çalışan CPU olduğunu doğru sıraladı. 100 üzerinden 95.
- **Tek hatası içerikte değil, ifadedeydi**: skill'in istediği bağ testi olmadan söylenmiş bir neden.
- **Sakin saatte telaşa kapılmadı**: "not hard to use", kısa bir Windows Update yükü ve arka planda kara kutuyu yöneten
  süreç.
- **Skill modeli ham veriden uzak tutuyor**; bir analiz yaklaşık 35 AAU, yani kabaca 3,5–5 USD.
- **Bilerek oluşturulan bir sorun, zincirin çalıştığını kanıtlar; agent'ın muhakemesini değil.** Nedeni bilinmeyen bir
  sorundaki muhakemesi sıradaki yazının konusu.

## Seri tek paragrafta

[Bölüm 1]({{< relref "/posts/perfmon-blackbox-part-1" >}}), kara kutunun sorundan sonra değil, sorundan önce çalışıyor olması gerektiğini anlattı. [Bölüm 2]({{< relref "/posts/perfmon-blackbox-part-2" >}})'de
Windows sunuculara yalnızca Azure Policy ve Machine Configuration ile bir PerfMon kara kutusu kurduk ve maliyetini
hesapladık. [Bölüm 3]({{< relref "/posts/perfmon-blackbox-part-3" >}})'te sunucunun içine baktık: bir veri toplayıcı, üç görev, bir klasör, her boşluğu nedeniyle
yazan bir manifest ve sunucunun kendi kimliğiyle yaptığı yükleme. Bu bölümde Azure SRE Agent'a ne olduğunu sorduk ve
cevabını önceden yazdığımız doğru cevapla karşılaştırdık. Bir sunucu bir dahaki sefere gece 03:10'da yavaşladığında
veri hazır olacak.
