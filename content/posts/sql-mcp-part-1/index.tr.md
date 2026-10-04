---
title: "Azure SRE Agent için SQL MCP kurulumu"
description: "Azure SRE Agent'a Data API builder üzerinden SQL Server DMV'lerine salt okunur erişim: gMSA, Kerberos, SQL'de nesne yok, VNet üzerinden managed identity ile connector ve yolda bulduğumuz hata davranışları."
date: 2026-10-04
draft: false
series: ["Azure SRE Agent için SQL MCP"]
series_order: 1
tags: ["azure-sre-agent", "mcp", "dab", "sql-server", "entra-id", "gmsa", "kerberos"]
showTableOfContents: true
---

Azure SRE Agent'ın "sql02'de en çok hangi wait var?" ve "şu an kaç kullanıcı oturumu açık?" sorularını, eline hiçbir
zaman bir SQL komut satırı vermeden cevaplamasını istedik. `sysadmin` yok, serbest sorgu yok, SQL Server'larda yardımcı
veritabanı yok, genel uç nokta yok. Bu yazı bunu **Data API builder (DAB) 2.1.5** ve onun MCP uç noktasıyla nasıl
kurduğumuzu ve yolda neyin kırıldığını anlatıyor.

✅ = lab'imizde kanıtlandı · 📄 = yalnız belgede var (Microsoft Learn ya da DAB kaynak kodu), bizde test edilmedi.

## Amaç ve hedef kitle

**Amaç.** Sonunda agent, listelediğiniz her sunucuda yedi SQL Server DMV view'ını (wait'ler, sayaçlar, bellek,
oturumlar, istekler, sorgu istatistikleri) okuyor. Bunu, agent'ın kendi managed identity'siyle kimlik doğrulayan ve
VNet'inizin içinden geçen bir MCP connector'ı üzerinden yapıyor. SQL Server tarafında yalnızca düşük yetkili tek bir gMSA,
Kerberos ile görünüyor. SQL'de bir login dışında hiçbir şey oluşturulmuyor.

**Kimler için.** SRE Agent kullanan ya da kullanmak üzere olan ve veritabanı sağlığını ona göstermek isteyen Azure ve
SQL Server mühendisleri. Active Directory (gMSA), T-SQL login'leri, Entra uygulama kayıtları ve `az rest` size yabancı
olmamalı.

## Parçalar nasıl birleşiyor

DAB, JSON config'te listelenen veritabanı nesnelerini API olarak sunan, Microsoft'un açık kaynak motorudur. Biz yalnız
**MCP uç noktasını** kullanıyoruz (`/mcp`, Streamable HTTP); REST ve GraphQL kapalı. DAB'ın kendine ait SQL'i yoktur: her
araç çağrısı, sizin tanımladığınız bir view üzerinde bir `SELECT`'e dönüşür. ✅

{{< mermaid >}}
flowchart LR
  subgraph AZ["Azure VNet (genel uç nokta yok)"]
    AG["Azure SRE Agent<br/>system-assigned MI"]
    subgraph HOST["mcp01 (domain üyesi)"]
      DAB["DAB 2.1.5 /mcp<br/>gMSA ile zamanlanmış görev"]
    end
  end
  ENTRA["Entra ID<br/>uygulama sql-mcp-api, rol MCP.Read"]
  SQL1[("sql01<br/>DMV view'ları")]
  SQL2[("sql02<br/>DMV view'ları")]
  AG -- "1 api://appId için token" --> ENTRA
  AG -- "2 HTTP :5000 + Bearer + X-MS-API-ROLE" --> DAB
  DAB -- "3 imza anahtarları, giden 443" --> ENTRA
  DAB -- "4 TDS 1433, gmsa-dab$ ile Kerberos" --> SQL1
  DAB -- "4" --> SQL2
{{< /mermaid >}}

1. Agent, **managed identity**'siyle Entra'dan `api://<appId>` için token ister. Token'ı yalnız `MCP.Read` uygulama
   rolüne sahip kimlikler alır: uygulama atama zorunlu tutar. ✅
2. Connector, token ve `X-MS-API-ROLE: MCP.Read` başlığıyla VNet üzerinden `http://mcp01.contoso.local:5000/mcp`
   adresini çağırır. ✅
3. DAB `aud`, `iss` ve imzayı (anahtarlar Entra'dan giden 443 ile alınır) ve rolü kontrol eder. ✅
4. DAB, SQL Server'a **gMSA** olarak Kerberos ile bağlanır. Çağıranın kimliğini aktarmaz. ✅

**Agent'ın eline geçen**, salt okunur üç araçtır: `describe_entities` (ne var, kolon açıklamalarıyla), `read_records`
(filtre, sıralama, kolon seçimi, ilk N) ve `aggregate_records` (count, sum, avg, min, max, group by). "Sorgu çalıştır"
diye bir araç yoktur. ✅

## Ön koşullar

| Alan | Gereksinim | |
|---|---|---|
| SRE Agent | Egress modu **Azure VNet**, özel DNS çözümlemesi açık | ✅ |
| | **Remote MCP server access = kapalı** (MCP trafiğini VNet'inizde tutar) | ✅ |
| | System-assigned managed identity (user-assigned da olur) | ✅ / 📄 |
| Active Directory | KDS root key'i olan bir domain; gMSA için Domain Admin | ✅ |
| MCP host'u | Domain üyesi Windows Server, genel IP yok. Token imza anahtarları için Entra'ya **giden TCP 443**. İnternetten gelen trafik yok | ✅ |
| SQL Server | `##MS_ServerPerformanceStateReader##` için **2022 ve sonrası** (biz 2025 ile çalıştık). 2016–2019 için `VIEW SERVER STATE` gerekir | ✅ 2025 / 📄 eskiler |
| Ağ | Agent alt ağı → MCP host'u TCP 5000; host adı agent alt ağından çözülebilir | ✅ |
| Entra | Uygulama kaydı oluşturup uygulama rolü atayabilen biri | ✅ |
| Admin makinesi | Oturum açılmış Azure CLI. zsh ya da PowerShell | ✅ zsh / 📄 PowerShell |

HTTPS şart değil: connector VNet içinde `http://` kabul ediyor. ✅ Şirket içi SQL Server'lar da VPN ya da ExpressRoute
üzerinden aynı şekilde çalışır; yeter ki agent alt ağı host'a ulaşabilsin. 📄

## Adımlar

Admin makinesinde çalışan komutlar iki sekmede. Kabuğunuzu bir kez seçin; sayfadaki bütün bloklar ona uyar. Bir Windows
sunucusunda ya da SQL'de çalışan komutlar tek sefer yazıldı.

### 1. gMSA'yı oluşturun (bir domain controller'da)

```powershell
# KDS root key: once per forest. Production: -EffectiveImmediately, then wait 10 h.
if (-not (Get-KdsRootKey)) { Add-KdsRootKey -EffectiveImmediately }
New-ADServiceAccount -Name gmsa-dab -DNSHostName gmsa-dab.contoso.local `
  -PrincipalsAllowedToRetrieveManagedPassword 'mcp01$'
```

### 2. gMSA'ya bir login ve bir rol verin (her SQL Server'da, sysadmin olarak)

```sql
CREATE LOGIN [CONTOSO\gmsa-dab$] FROM WINDOWS WITH DEFAULT_DATABASE = [master];
ALTER SERVER ROLE [##MS_ServerPerformanceStateReader##] ADD MEMBER [CONTOSO\gmsa-dab$];
SELECT IS_SRVROLEMEMBER('sysadmin', N'CONTOSO\gmsa-dab$') AS is_sysadmin;   -- expect 0
```

`##MS_ServerPerformanceStateReader##`, `VIEW SERVER PERFORMANCE STATE` demektir: performans DMV'leri, başka bir şey
değil. Tablo verisi yok, güvenlik DMV'leri yok, hiçbir şeyi değiştirme imkânı yok. Veritabanı kullanıcısı da
oluşturulmuyor. ✅

2016–2019'da bunun yerine `GRANT VIEW SERVER STATE` kullanın. Daha geniştir (güvenlikle ilgili durumu ve başka
oturumların sorgu metnini de kapsar). 📄

{{< alert icon="circle-info" >}}
**Yetki yoksa iki view hata vermez, yanlış söyler.** `sys.dm_exec_sessions` ve `sys.dm_exec_requests` bu durumda
**yalnız DAB'ın kendi oturumunu** döndürür. Sayılar geçerli görünür ama yanlıştır. "Satır dönüyor" diye değil,
`sys.server_permissions` ile kontrol edin. 📄 (Learn; biz yalnız 2025 ile çalıştık)
{{< /alert >}}

### 3. DAB'ı MCP host'una kurun (yerel admin olarak)

```powershell
Install-WindowsFeature RSAT-AD-PowerShell
Install-ADServiceAccount gmsa-dab
Test-ADServiceAccount gmsa-dab                       # True
```

Sonra aynı host'ta:

1. gMSA'ya **Log on as a batch job** hakkını verin (zamanlanmış görev bunu ister).
2. DAB'ın GitHub sürümündeki kendi kendine yeten `dab_net10.0_win-x64-2.1.5.zip` dosyasını `C:\dab\bin` altına açın.
   .NET kurmak gerekmez. `C:\dab\bin\Microsoft.DataApiBuilder.exe --version` çıktısı `2.1.5` olmalı. **Sürümü
   sabitleyin**: `allowed-hosts` 2.1.5 ile geldi.
3. `C:\dab\config` (gMSA: okuma) ve `C:\dab\logs` (gMSA: değiştirme) klasörlerini oluşturun.
4. Servis işini *gören* zamanlanmış görevi kaydedin (DAB bir Windows servisi değildir):

```powershell
$cmd = '/c set ASPNETCORE_URLS=http://0.0.0.0:5000&& C:\dab\bin\Microsoft.DataApiBuilder.exe start --config dab-config.json > C:\dab\logs\dab.log 2>&1'
$a = New-ScheduledTaskAction -Execute cmd.exe -Argument $cmd -WorkingDirectory C:\dab\config
$t = New-ScheduledTaskTrigger -AtStartup
$p = New-ScheduledTaskPrincipal -UserId 'CONTOSO\gmsa-dab$' -LogonType Password   # no password for a gMSA
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'DAB-MCP' -Action $a -Trigger $t -Principal $p -Settings $s -Force
```

5. TCP 5000'i **yalnız** agent ve VM alt ağlarına açın. Windows Firewall açık kalır:

```powershell
New-NetFirewallRule -Name dab-mcp-5000 -DisplayName 'DAB MCP 5000 (VNet only)' -Direction Inbound `
  -Protocol TCP -LocalPort 5000 -RemoteAddress <agent-subnet>,<vm-subnet> -Action Allow -Profile Any
```

### 4. DAB yapılandırmasını yazın

Dosya düzeni göründüğünden daha önemli; nedenini [bulgular](#finding-2) anlatıyor.

- **`dab-config.json`, kök dosya**: runtime, sunucu dosyalarının listesi ve bir **yer tutucu** veri kaynağı.
- **Her SQL Server için bir dosya** (`sql01.json`, `sql02.json`): bağlantı dizesi ve entity'leri.
- **Bir entity = bir sunucudaki bir DMV view'ı**, adı `<sunucu>_<view>`: `sql01_wait_stats`, `sql02_sessions`.

Kök dosya (`C:\dab\config\dab-config.json`):

```json
{
  "data-source": {
    "database-type": "mssql",
    "connection-string": "Server=dab-placeholder.invalid;Database=master;Integrated Security=True;Encrypt=True;TrustServerCertificate=True",
    "health": { "enabled": false, "name": "placeholder" }
  },
  "data-source-files": [ "sql01.json", "sql02.json" ],
  "entities": {},
  "runtime": {
    "rest": { "enabled": false },
    "graphql": { "enabled": false },
    "mcp": {
      "enabled": true, "path": "/mcp",
      "allowed-hosts": [ "mcp01", "mcp01.contoso.local" ],
      "dml-tools": { "describe-entities": true, "read-records": true, "aggregate-records": true,
                     "create-record": false, "update-record": false, "delete-record": false, "execute-entity": false }
    },
    "host": {
      "mode": "production",
      "authentication": {
        "provider": "EntraId",
        "jwt": { "audience": "<appId>", "issuer": "https://login.microsoftonline.com/<tenant-id>/v2.0" }
      }
    },
    "cache": { "enabled": false }
  }
}
```

Bir sunucu dosyası (`sql01.json`), tek entity ve üç kolonuna kısaltılmış hâli:

```json
{
  "data-source": {
    "database-type": "mssql",
    "connection-string": "Server=sql01.contoso.local;Database=master;Integrated Security=True;Encrypt=True;TrustServerCertificate=True;Application Name=dab-mcp",
    "health": { "name": "sql01" }
  },
  "entities": {
    "sql01_wait_stats": {
      "description": "sql01: sys.dm_os_wait_stats",
      "source": { "object": "sys.dm_os_wait_stats", "type": "view" },
      "fields": [
        { "name": "wait_type", "primary-key": true },
        { "name": "wait_time_ms", "description": "Total wait time for this wait type in ms, including signal_wait_time_ms." },
        { "name": "signal_wait_time_ms", "description": "Part of wait_time_ms spent waiting for CPU after the resource was ready (CPU pressure)." }
      ],
      "graphql": { "enabled": false },
      "cache": { "enabled": false },
      "permissions": [ { "role": "MCP.Read", "actions": [ "read" ] } ]
    }
  }
}
```

Sunucu başına yedi view ve DAB'ın her biri için istediği anahtar:

| Entity | DMV view'ı | Anahtar |
|---|---|---|
| `wait_stats` | `sys.dm_os_wait_stats` | wait_type |
| `perf_counters` | `sys.dm_os_performance_counters` | object_name, counter_name, instance_name |
| `sys_memory` | `sys.dm_os_sys_memory` | total_physical_memory_kb |
| `memory_clerks` | `sys.dm_os_memory_clerks` | memory_clerk_address |
| `sessions` | `sys.dm_exec_sessions` | session_id |
| `requests` | `sys.dm_exec_requests` | session_id, request_id |
| `query_stats` | `sys.dm_exec_query_stats` | sql_handle, statement_start_offset, statement_end_offset, plan_handle |

Zor yoldan öğrendiğimiz kurallar:

- **Her kolonu `fields` içinde listeleyin**, agent'ın filtrelediği kolonlara açıklama yazın. `describe_entities` yalnız
  `fields` içindekileri gösterir. İlk denemede agent 72 "kullanıcı oturumu" saydı, çünkü `is_user_process` kolonundan
  habersizdi; kolon açıklanınca 2 dedi, doğrusu da buydu. ✅
- **`anonymous` rolü yok.** Her entity'yi yalnız `MCP.Read` okuyabilir. ✅
- Her yerde **önbellek kapalı**: bunlar canlı DMV'ler. ✅
- **Entity'leri tek tek ekleyin** ve log'u izleyin. Tek bir hatalı entity bütün DAB'ı durdurur. ✅

Başlatın: `Start-ScheduledTask DAB-MCP`; ardından `Get-NetTCPConnection -LocalPort 5000 -State Listen` çıktısında
`0.0.0.0` görünür.

### 5. Entra uygulamasını oluşturun ve agent'a rolünü verin (admin makinesi)

`api://<appId>` tanımlayıcı URI'li, **v2 token**'lı, uygulamalar için tek bir `MCP.Read` rolü olan, atamayı **zorunlu**
tutan ve bu rolü agent'ın managed identity'sine atayan `sql-mcp-api` uygulama kaydı. Blok tekrar çalıştırılabilir.

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
AGENT=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.App/agents/<agent>
AGENT_MI_OID=$(az resource show --ids "$AGENT" --api-version 2026-01-01 --query identity.principalId -o tsv)
APPID=$(az ad app list --display-name sql-mcp-api --query "[0].appId" -o tsv)
[ -n "$APPID" ] || APPID=$(az ad app create --display-name sql-mcp-api --query appId -o tsv)
az ad app update --id "$APPID" --identifier-uris "api://$APPID"
az rest -m PATCH --url "https://graph.microsoft.com/v1.0/applications(appId='$APPID')" \
  --body '{"api":{"requestedAccessTokenVersion":2}}'
ROLE=$(az ad app show --id "$APPID" --query "appRoles[?value=='MCP.Read'].id" -o tsv)
if [ -z "$ROLE" ]; then
  ROLE=$(uuidgen | tr 'A-Z' 'a-z')
  az rest -m PATCH --url "https://graph.microsoft.com/v1.0/applications(appId='$APPID')" \
    --body "{\"appRoles\":[{\"allowedMemberTypes\":[\"Application\"],\"displayName\":\"MCP.Read\",\"description\":\"Read DMVs through SQL MCP\",\"id\":\"$ROLE\",\"isEnabled\":true,\"value\":\"MCP.Read\"}]}"
fi
SPID=$(az ad sp list --filter "appId eq '$APPID'" --query "[0].id" -o tsv)
[ -n "$SPID" ] || SPID=$(az ad sp create --id "$APPID" --query id -o tsv)
az rest -m PATCH --url "https://graph.microsoft.com/v1.0/servicePrincipals/$SPID" --body '{"appRoleAssignmentRequired":true}'
az rest -m POST --url "https://graph.microsoft.com/v1.0/servicePrincipals/$SPID/appRoleAssignedTo" \
  --body "{\"principalId\":\"$AGENT_MI_OID\",\"resourceId\":\"$SPID\",\"appRoleId\":\"$ROLE\"}"
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$AGENT = '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.App/agents/<agent>'
$AGENT_MI_OID = az resource show --ids $AGENT --api-version 2026-01-01 --query identity.principalId -o tsv
$APPID = az ad app list --display-name sql-mcp-api --query "[0].appId" -o tsv
if (-not $APPID) { $APPID = az ad app create --display-name sql-mcp-api --query appId -o tsv }
az ad app update --id $APPID --identifier-uris "api://$APPID"
'{"api":{"requestedAccessTokenVersion":2}}' | Out-File -Encoding ascii ver.json
az rest -m PATCH --url "https://graph.microsoft.com/v1.0/applications(appId='$APPID')" --body '@ver.json'
$ROLE = az ad app show --id $APPID --query "appRoles[?value=='MCP.Read'].id" -o tsv
if (-not $ROLE) {
  $ROLE = [guid]::NewGuid().Guid
  @{ appRoles = @(@{ allowedMemberTypes = @('Application'); displayName = 'MCP.Read'; description = 'Read DMVs through SQL MCP'; id = $ROLE; isEnabled = $true; value = 'MCP.Read' }) } |
    ConvertTo-Json -Depth 5 | Out-File -Encoding ascii roles.json
  az rest -m PATCH --url "https://graph.microsoft.com/v1.0/applications(appId='$APPID')" --body '@roles.json'
}
$SPID = az ad sp list --filter "appId eq '$APPID'" --query "[0].id" -o tsv
if (-not $SPID) { $SPID = az ad sp create --id $APPID --query id -o tsv }
'{"appRoleAssignmentRequired":true}' | Out-File -Encoding ascii req.json
az rest -m PATCH --url "https://graph.microsoft.com/v1.0/servicePrincipals/$SPID" --body '@req.json'
@{ principalId = $AGENT_MI_OID; resourceId = $SPID; appRoleId = $ROLE } | ConvertTo-Json | Out-File -Encoding ascii asg.json
az rest -m POST --url "https://graph.microsoft.com/v1.0/servicePrincipals/$SPID/appRoleAssignedTo" --body '@asg.json'
```
{{< /tab >}}
{{< /tabs >}}

İki tuzak: `az ad app update --set api…` hata verir ("Couldn't find 'api'"), Graph PATCH'i bu yüzden. Bir uygulama
rolünün id'si de bir kez oluşunca değiştirilemez, var olanın yeniden kullanılması bu yüzden. ✅ Rolü, agent ilk kez token
istemeden **önce** atayın: managed identity token'ları 24 saate kadar önbellekte kalır ve erken alınmış bir token'da
`roles` claim'i olmaz. 📄

### 6. MCP trafiğini VNet'te tutun, sonra connector'ı ekleyin (admin makinesi)

"Remote MCP server access" **kapalı** olunca MCP trafiği VNet'inizden geçer. Açıkken Microsoft'un ağı üzerinden internete
çıkar ve özel bir host'a ulaşamaz. `egress` nesnesini bütün olarak gönderin. ✅

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az rest -m PATCH --url "https://management.azure.com$AGENT?api-version=2026-01-01" \
  --body '{"properties":{"sandboxConfiguration":{"egress":{"mode":"AzureVNet","vnetConfiguration":{"usePrivateDnsResolution":true},"allowHttpMcpServerNetworkAccess":false}}}}'
az rest -m GET --url "https://management.azure.com$AGENT?api-version=2026-01-01" \
  --query properties.sandboxConfiguration.egress.allowHttpMcpServerNetworkAccess     # false
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
'{"properties":{"sandboxConfiguration":{"egress":{"mode":"AzureVNet","vnetConfiguration":{"usePrivateDnsResolution":true},"allowHttpMcpServerNetworkAccess":false}}}}' |
  Out-File -Encoding ascii egress.json
az rest -m PATCH --url "https://management.azure.com${AGENT}?api-version=2026-01-01" --body '@egress.json'
az rest -m GET --url "https://management.azure.com${AGENT}?api-version=2026-01-01" `
  --query properties.sandboxConfiguration.egress.allowHttpMcpServerNetworkAccess     # false
```
{{< /tab >}}
{{< /tabs >}}

Şimdi connector. Portalda: **Builder → Connectors → Add connector → MCP server**, Streamable-HTTP, URL
`http://mcp01.contoso.local:5000/mcp`, kimlik doğrulama **Managed identity** (system-assigned), scope
`api://<appId>/.default`, özel başlık `X-MS-API-ROLE` = `MCP.Read`, sonra üç aracı seçin. 📄 (portal yolu; biz aşağıdaki
ARM çağrısını çalıştırdık ✅)

`connector.json` içinde sır yok. Araç adlarının önüne connector'ın adı gelir:

```json
{"properties":{"dataConnectorType":"Mcp","dataSource":"placeholder","identity":"system",
 "extendedProperties":{"type":"http","endpoint":"http://mcp01.contoso.local:5000/mcp",
   "authType":"AzureARM","armScope":"api://<appId>/.default",
   "X-MS-API-ROLE":"MCP.Read",
   "selectedTools":["dmv_describe_entities","dmv_read_records","dmv_aggregate_records"],
   "toolsVisibleToMetaAgent":["dmv_describe_entities","dmv_read_records","dmv_aggregate_records"]}}}
```

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az rest -m PUT --url "https://management.azure.com$AGENT/connectors/dmv?api-version=2026-01-01" \
  --body @connector.json -o none
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az rest -m PUT --url "https://management.azure.com${AGENT}/connectors/dmv?api-version=2026-01-01" `
  --body '@connector.json' -o none
```
{{< /tab >}}
{{< /tabs >}}

`authType: AzureARM`, portaldaki "Managed identity" seçeneğinin yazdığı değerdir; özel başlıklar `extendedProperties`
içinde düz anahtar olarak durur. Sonradan yapılan bir `GET`, `endpoint`, `armScope` ve başlığı `null` gösterir; bunlar
yalnız yazılabilir alanlardır. ✅

## Doğrulama

**SQL'de, sysadmin olarak**: DAB'ın oturumu gMSA'dır, Kerberos ile gelir ve sysadmin değildir. ✅

```sql
SELECT s.login_name, c.auth_scheme, IS_SRVROLEMEMBER('sysadmin', s.login_name) AS is_sysadmin
FROM sys.dm_exec_sessions s JOIN sys.dm_exec_connections c ON c.session_id = s.session_id
WHERE s.program_name LIKE 'dab-mcp%';            -- CONTOSO\gmsa-dab$   KERBEROS   0
```

**Agent'a sorun**: *"sql01'de şu an kaç kullanıcı oturumu var?"* ve *"sql02'de en çok hangi wait türü var?"*. Konuşmada
`MCP Tool` çağrıları görünür. Hemen ardından `sqlcmd` ile karşılaştırın: aynı wait türleri, aynı sırada (değerler
kümülatif) ve `sqlcmd`'de bir oturum fazla (kendisi). ✅

**Yalnız agent okuyabilir** ✅:

- host'un kendi managed identity'si `api://<appId>` için token alamaz: `AADSTS501051`, atanmamış;
- bir ARM token'ı HTTP 401 alır (yanlış audience);
- `X-MS-API-ROLE` başlığı olmadan agent'ın çağrıları `NoEntitiesConfigured` döner.

**Yol VNet'tir.** MCP host'unda Filtering Platform denetimini bir dakikalığına açın, agent'a bir şey sorun ve 5000
portuna gelen bağlantıların kaynaklarını listeleyin. Hepsi agent alt ağında olmalı. ✅

```powershell
auditpol /set /subcategory:"Filtering Platform Connection" /success:enable
# ...ask the agent a question, then:
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=5156; StartTime=(Get-Date).AddMinutes(-10)} |
  Where-Object { $_.Message -match 'Destination Port:\s+5000' -and $_.Message -match 'Inbound' } |
  ForEach-Object { [regex]::Match($_.Message,'Source Address:\s+(\S+)').Groups[1].Value } |
  Group-Object | ForEach-Object { "$($_.Count) x $($_.Name)" }
auditpol /set /subcategory:"Filtering Platform Connection" /success:disable   # it fills the Security log fast
```

## Neler bulduk

### Bulgu 1: erişilemeyen tek bir SQL Server, açılışta bütün DAB'ı durdurur

DAB açılırken **her** entity'nin şemasını okur. O anda herhangi bir SQL Server'a erişilemiyorsa DAB kapanır. Sağlıklı
sunucular da onunla birlikte gider. ✅

- `dab.log` şunu yazar: `Unable to complete runtime initialization … Cannot obtain Schema for entity sql02_wait_stats …
  A network-related or instance-specific error`. Entity'nin öneki hangi sunucu olduğunu söyler. ✅
- Sunucu geri geldiğinde **kendiliğinden toparlanmaz**. Görevin "hata olursa yeniden başlat" ayarı hiç devreye girmez:
  `cmd.exe` sorunsuz başlamış, DAB -1 ile çıkmıştır ve Task Scheduler bunu *completed* olarak kaydeder (olay 201, dönüş
  kodu 4294967295, seviye Information). Onu yalnız `Start-ScheduledTask DAB-MCP` geri getirir. ✅
- Görev çıktıyı `>` ile yönlendirir, yani **her başlatma `dab.log`'un üzerine yazar**. Yeniden başlatmadan önce okuyun. ✅
- Application log'a `.NET Runtime` 1000 "Hosting failed to start" düşer; hiçbir sunucunun adını vermez. ✅
- Bir sunucu **DAB çalışırken** ölürse yalnız onun entity'leri hata verir (ilk çağrı yaklaşık 15 sn sonra, bağlantı
  zaman aşımı) ve sunucu dönünce kendiliğinden düzelir. ✅

{{< alert icon="triangle-exclamation" >}}
**Görevi değil, dinleyiciyi izleyin.** Bir SQL Server'ı yamaladıktan ya da MCP host'unu yeniden başlattıktan sonra TCP
5000'de bir şeyin dinlediğini (ya da bir MCP `initialize` çağrısının başarılı olduğunu) dışarıdan kontrol edin. Görev
durumu *Ready* der ve zararsız görünür. DAB'ı yalnız bütün SQL Server'ları ayaktayken yeniden başlatın.
{{< /alert >}}

### Bulgu 2: `.off` çözümü {#finding-2}

DAB 2.1.5'te bir veri kaynağı ya da entity için **`enabled` bayrağı yok**. Bariz anahtarları, sunuculardan birinin var
olmayan bir adı gösterdiği bir config kopyasında denedik:

| Deneme | Sonuç |
|---|---|
| Ölü sunucunun bütün entity'lerinde `"mcp": false` | DAB yine açılışta düşer ✅ |
| Üstüne veri kaynağında `health.enabled: false` | yine düşer ✅ |
| `sql02.json` dosyasının adını `sql02.json.off` yapmak | **açılır, sql01'in 7 entity'siyle** ✅ |

Nedeni DAB'ın yükleyicisinde: `data-source-files` içinde listelenen ama **diskte olmayan bir dosya sessizce atlanır**.
📄 (kaynak kod) ✅ (davranış). Her sunucunun, ilki dahil, kendi dosyası olmasının ve kökte yalnız bir **yer tutucu** veri
kaynağı bulunmasının nedeni bu: DAB 2.1.5 veri kaynağı olmayan bir kökü reddeder ("Invalid connection-string"), adı
çözülemeyen ve entity'si olmayan yer tutucuya ise hiç bağlanmaz. ✅ Her DAB yükseltmesinden sonra bunu yeniden test edin;
sonraki bir sürüm ona bağlanmayı deneyebilir. 📄

Bir sunucuyu host'ta devreden çıkarmak:

```powershell
$s = 'sql02'
Rename-Item "C:\dab\config\$s.json" "$s.json.off"
Stop-ScheduledTask DAB-MCP; Get-Process Microsoft.DataApiBuilder -EA SilentlyContinue | Stop-Process -Force
Start-ScheduledTask DAB-MCP; Start-Sleep 15
[bool](Get-NetTCPConnection -LocalPort 5000 -State Listen -EA SilentlyContinue)   # True = DAB is up
```

Ya da bir Azure VM için admin makinesinden, VM agent'ı üzerinden (SSH gerekmez). 📄 (çalıştırılmadı)

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az vm run-command invoke -g <rg> -n mcp01 --command-id RunPowerShellScript --query 'value[0].message' -o tsv --scripts \
  'Rename-Item C:\dab\config\sql02.json sql02.json.off; Stop-ScheduledTask DAB-MCP; Get-Process Microsoft.DataApiBuilder -EA SilentlyContinue | Stop-Process -Force; Start-ScheduledTask DAB-MCP; Start-Sleep 15; [bool](Get-NetTCPConnection -LocalPort 5000 -State Listen -EA SilentlyContinue)'
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
'Rename-Item C:\dab\config\sql02.json sql02.json.off; Stop-ScheduledTask DAB-MCP; Get-Process Microsoft.DataApiBuilder -EA SilentlyContinue | Stop-Process -Force; Start-ScheduledTask DAB-MCP; Start-Sleep 15; [bool](Get-NetTCPConnection -LocalPort 5000 -State Listen -EA SilentlyContinue)' |
  Set-Content takeout.ps1
az vm run-command invoke -g <rg> -n mcp01 --command-id RunPowerShellScript --scripts '@takeout.ps1' --query 'value[0].message' -o tsv
```
{{< /tab >}}
{{< /tabs >}}

Geri almak için iki adı yer değiştirip yeniden başlatın. Atlama sessiz olduğundan `data-source-files` içindeki bir yazım
hatası da bir sunucuyu sessizce düşürür. Her değişiklikten sonra DAB'ın yükleyeceği entity'leri sayın ve sayı 7 × sunucu
sayısının altına düşünce alarm verin:

```powershell
$c = 'C:\dab\config'; $root = Get-Content "$c\dab-config.json" -Raw | ConvertFrom-Json
$n = 0
foreach ($f in $root.'data-source-files') {
  if (Test-Path "$c\$f") { $n += @((Get-Content "$c\$f" -Raw | ConvertFrom-Json).entities.PSObject.Properties).Count }
  else { "MISSING: $f (DAB skips it silently)" } }
"entities DAB will load: $n"
Get-ChildItem "$c\*.json.off" -EA SilentlyContinue | ForEach-Object { "TAKEN OUT: $($_.Name)" }
```

Toparlanmayı **bilerek elle** bıraktık. Otomatik bir yeniden deneme döngüsü, ölü sunucu çıkarılana ya da geri gelene
kadar yine başarısız olur ve sorunu gizler.

### Bulgu 3: sunucu yapılandırması neden açılmıyor

Doğal bir sonraki soru "sql01'de MAXDOP kaç?" oldu. DAB bunu SQL'de bir nesne olmadan cevaplayamıyor:

- `sys.configurations`, `sys.database_scoped_configurations` ve `sys.dm_server_registry` view'larında **`sql_variant`**
  kolonlar var. DAB bir view'ın şemasını `SELECT *` ile okur ve filtre modelini yalnız `fields` içindekilerden değil,
  bütün kolonlardan kurar. `sql_variant`'ın karşılığı yok, bu yüzden **DAB açılışta düşer**; kolonu `fields` dışında
  bırakmak da işe yaramaz. 📄 (DAB kaynak kodu; kolon tipleri kontrol edildi ✅)
- `SERVERPROPERTY()` ve `@@VERSION` fonksiyondur. DAB yalnız tablo, view ve stored procedure sunar. DMV fonksiyonlarını
  denedik (`dm_exec_sql_text`, `dm_db_index_physical_stats`, `dm_io_virtual_file_stats`): DAB, SQL hatası 216 ile
  ("parameters were not supplied") açılamaz. ✅
- Her şeyi düz tiplere çeviren bir sarmalayıcı view işe yarardı, ama o SQL'de bir nesnedir ve bu tasarım buna izin
  vermez. Yapılandırma soruları `sqlcmd` ve SSMS'te kalıyor.

### Bulgu 4: sınır kapasite değil, hata bağımlılığı

Tek bir DAB'a, her biri yedi entity'li 50 veri kaynağına kadar yükledik ve ölçtük. Veri kaynakları iki gerçek
sunucumuzun takma adlarıydı. ✅

| Sunucu | Dinleyici ayakta / ilk okuma | Bellek (working set) | `describe_entities` tam / `nameOnly` / tek entity |
|---|---|---|---|
| 2 | 2.1 s / 4.9 s | 132 MB | 74 KB / 2.3 KB / 1.5 KB |
| 10 | 2.4 s / 5.2 s | 152 MB | 368 KB / 11 KB / 1.5 KB |
| 25 | 3.5 s / 6.2 s | 161 MB | 921 KB / 27 KB / 1.5 KB |
| 50 | 5.2 s / 8.0 s | 176 MB | 1.8 MB / 54 KB / 1.5 KB |

25 sunucuda agent, "sql17'de en çok hangi wait var" ve "sql22'de kaç kullanıcı oturumu var" için doğru entity'yi kendi
buldu: önce `nameOnly` ile `describe_entities` çağırdı (18 KB), sonra tek bir entity'yi; oturum sayısı `sqlcmd` ile
aynıydı. 921 KB'lık tam açıklamayı hiç çekmedi. ✅

Yani sunucuları DAB başına sayıya göre değil, **hata alanı ve bakım penceresine** göre gruplayın ve her grubu
**25 ya da daha az** tutun (test ettiğimiz büyüklük). 25 ayrı gerçek sunucuyla ağ gecikmesi ve bağlantı havuzları
ölçülmedi. 📄

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|
| Yeniden başlatmadan sonra DAB açılmıyor; `dab.log`: `Cannot obtain Schema for entity …` | Açılışta bir SQL Server'a erişilemedi | Sunucuyu geri getirin ya da dosyasının adını `.off` yapın, sonra `Start-ScheduledTask DAB-MCP` |
| DAB duruyor, bütün entity'ler kapalı | Tek bir hatalı entity (fonksiyon, `sql_variant`'lı view, yazım hatası) | Son sağlam config'e dönün; entity'leri tek tek ekleyin |
| HTTP 401, `invalid_token` | Yanlış `aud`/`iss`, ya da host imza anahtarları için Entra'ya ulaşamıyor | DAB `audience` = `<appId>` (`api://…` değil, GUID), issuer `…/v2.0`; Entra'ya giden 443 |
| `NoEntitiesConfigured` ya da `PermissionDenied` | `X-MS-API-ROLE` başlığı yok, rol `authenticated` kalıyor | Başlığı connector'a ekleyin |
| HTTP 403 | Başlıktaki rol token'da yok | `MCP.Read` rolünü agent'ın kimliğine atayın |
| Token'da `roles` yok | Managed identity token'ı atamadan önce alınmış ve önbellekte | Bekleyin (~24 saate kadar); bir dahaki sefere ilk kullanımdan önce atayın |
| Connector bağlanmıyor | Ad agent alt ağından çözülmüyor, firewall kuralı yok, DAB `0.0.0.0`'da değil, remote MCP access açık ya da `Host` `allowed-hosts`'ta yok | Hepsini kontrol edin; `Get-NetTCPConnection -LocalPort 5000 -State Listen` |
| Sessions/requests tek oturum gösteriyor | Login'in yetkisi eksik; bu view'lar o zaman yalnız DAB'ın kendi oturumunu döndürür | gMSA için `sys.server_permissions`'a bakın |
| `dab.log` boş | Production modunda normal | Bunun yerine dinleyiciyi ve bir MCP çağrısını kontrol edin |

## Ne öğrendik

1. **DMV view'ları evet; DMV fonksiyonları hayır.** SQL'de hiçbir nesne olmadan DAB view'ları sunar. Sorgu metni, index
   parçalanması ve dosya I/O bir sarmalayıcı ister; bu bir config ayarı değil, bir tasarım kararıdır.
2. **Bir gMSA ve `##MS_ServerPerformanceStateReader##` yeterli.** Tek login, Kerberos, veritabanı kullanıcısı yok,
   sysadmin değil.
3. **Uçtan uca managed identity, hiçbir yerde sır yok.** Token'ı agent'ın MI'ı alır, uygulama rolü kapıyı tutar, DAB
   doğrular. Statik bir bearer token da çalışır ve bir günde süresi dolar.
4. **Açılışta erişilemeyen tek sunucu bütün sunucuları düşürür ve kimse yeniden başlatmaz.** Dinleyiciyi dışarıdan izleyin;
   Task Scheduler başarı raporlar.
5. **Kapatma anahtarı yok, ama eksik dosya atlanıyor.** Sunucu başına bir dosya ve yer tutucu bir kök, bunu temiz ama
   sessiz bir `.off` anahtarına çevirir. Entity'leri sayarak sesini açın.
6. **Kolonlarınızı açıklayın.** `is_user_process` bir açıklamaya kavuşana kadar agent "72 kullanıcı oturumu" dedi.

**Serinin devamı:** bu kurulumu izlemek: yukarıdaki hata sinyallerine, görev durumuna güvenmeden alarm kurmak.
