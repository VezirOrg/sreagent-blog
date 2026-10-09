---
title: "Azure SRE Agent VM'de komut çalıştırsın, ama SYSTEM olarak değil"
description: "Managed Run Command'a izin veren, action Run Command'ı dışarıda bırakan bir custom role ve managed run command'ın yalnızca sizin seçtiğiniz bir kullanıcıyla çalışmasına izin veren bir Azure Policy. Gerçek bir VM'de sekiz çağrıyla test edildi."
date: 2026-10-08
draft: false
tags: ["azure-sre-agent", "run-command", "azure-policy", "rbac"]
showTableOfContents: true
---

Azure SRE Agent'ın managed identity'sine Virtual Machine Contributor gibi bir rol verirseniz, VM'lerinizde istediği
script'i **SYSTEM** (Windows) ya da **root** (Linux) olarak çalıştırabilir. `az vm run-command invoke` tam olarak bunu
yapar ve rol buna izin verir. Biz agent'ın komut çalıştırmaya devam etmesini, ama bizim seçtiğimiz sıradan bir yerel
kullanıcı olarak çalıştırmasını istedik.

Bunun için iki parça yeterli: **managed** Run Command'a izin veren ve **action** Run Command'ı dışarıda bırakan bir
custom role ile izin verilen bir kullanıcıyla çalışmayan managed run command'ı reddeden bir Azure Policy. Dört adımda:

1. VM'de yönetici olmayan bir yerel kullanıcı oluşturun.
2. Custom role'ü oluşturun ve o VM'de agent'ın kimliğine atayın.
3. Policy'yi oluşturun ve aynı VM'e atayın.
4. Agent'a komutları yalnızca bu kullanıcıyla, managed run command olarak çalıştırmasını söyleyin.

✅ = lab'imizde kanıtlandı · 📄 = yalnızca dokümantasyonda var (Microsoft Learn), bizde test edilmedi.
Admin makinesindeki bütün komutları zsh'te çalıştırdık. PowerShell sekmeleri bizim tarafımızda test edilmedi. 📄

## Amaç ve hedef kitle

**Amaç.** Yazının sonunda agent'ın kimliği tek bir VM'de managed run command oluşturabiliyor ve bunların hepsi
`sre-agent` adlı, yönetici olmayan bir yerel kullanıcı olarak çalışıyor. Kullanıcısı olmayan, başka kullanıcıyla çalışan, script'i bir
URL'den çeken ya da çıktısını bir blob'a yazan run command, VM'e ulaşmadan reddediliyor.

**Kimler için.** Azure SRE Agent'ın managed identity'sine VM erişimi veren herkes. Azure rol atamalarını bilmeniz ve daha
önce bir Azure Policy atamış olmanız gerekir.

## İki tür Run Command

| | Action Run Command | Managed Run Command |
|---|---|---|
| CLI | `az vm run-command invoke` | `az vm run-command create` |
| Yetki | `Microsoft.Compute/virtualMachines/runCommand/action` | `Microsoft.Compute/virtualMachines/runCommands/write` |
| Kim olarak çalışır | Windows'ta SYSTEM, Linux'ta root 📄 | belirtirseniz `runAsUser`'daki kullanıcı 📄 |
| Nedir | bir POST action | VM'in alt kaynağı (child resource) 📄 |

Burada önemli olan fark son satır. Managed run command bir kaynak olduğu için Azure Policy onun `runAsUser` dahil
özelliklerini okuyabilir. RBAC okuyamaz: bir rol bir işleme izin verir, istekteki değerlere hiç bakmaz. Rolün tek başına
yetmemesinin nedeni bu. 📄

## Ön koşullar

| Alan | Gereksinim | |
|---|---|---|
| Azure rolleri | VM'in resource group'unda **Owner** ya da **User Access Administrator** yetkisi olan biri; rolü oluşturmak, rolü ve policy'yi atamak için bir kez | ✅ |
| Policy definition | **Subscription** düzeyinde policy definition oluşturabilen bir rol, örneğin Resource Policy Contributor. Yalnızca resource group'ta Owner olan biri burada `AuthorizationFailed` hatası alır | ✅ (rol adı 📄) |
| Agent kimliği | SRE Agent'ın Azure için kullandığı managed identity; principal (object) ID'si | ✅ |
| VM | VM agent'ı çalışan bir Windows VM | ✅ |
| Run-as kullanıcısı | VM'de yönetici olmayan bir yerel kullanıcı (burada `sre-agent`) ve parolası | ✅ |
| Windows servisi | **Secondary Logon** (`seclogon`): Microsoft Learn'e göre managed Run Command, Windows'ta run-as için bu servisin çalışıyor olmasını ister. Bizim lab'imizde servis devre dışıyken de run-as çalıştı | 📄 / ✅ |
| Admin makinesi | Oturum açılmış Azure CLI; zsh sekmesi için `jq`. zsh ya da PowerShell | ✅ zsh / 📄 PowerShell |

## Mimari

{{< mermaid >}}
flowchart LR
  A["SRE Agent<br/>managed identity"] -- "PUT runCommands/x<br/>runAsUser=sre-agent" --> ARM["Azure Resource Manager"]
  A -. "POST runCommand/action<br/>(invoke)" .-> ARM
  ARM -- "1. RBAC: custom role'de<br/>runCommands/write var,<br/>runCommand/action yok" --> P["2. VM'deki Azure Policy<br/>runAsUser izinli listede mi?<br/>scriptUri yok, blob çıktısı yok mu?"]
  P -- "izin" --> VM["VM agent script'i<br/>yerel kullanıcı sre-agent<br/>olarak çalıştırır (yönetici değil)"]
  P -- "red" --> D["RequestDisallowedByPolicy"]
  ARM -. "invoke: AuthorizationFailed" .-> X["403"]
{{< /mermaid >}}

VM'e bir şey ulaşmadan önce Azure Resource Manager'da iki kontrol yapılıyor. RBAC, kimliğin bu işlemi çağırıp
çağıramayacağına karar veriyor. Ardından Policy isteğin içeriğine (request body) bakıyor ve kullanıcı ya da script kaynağı yanlışsa
isteği reddediyor.

## Adımlar

2–3. adımları resource group'ta Owner ya da User Access Administrator yetkisi olan bir operatör çalıştırır (1. adımı
VM'de bir yerel yönetici yapar); 3. adımdaki policy definition için ayrıca ön koşullarda belirtilen subscription
düzeyindeki rol gerekir. Agent'ın kimliği Owner değildir: yalnızca aşağıdaki custom role'ü alır, o da tek bir VM'de.

### 1. VM'de run-as kullanıcısını oluşturun

Bunu VM'de bir yerel yönetici, bir kez çalıştırır. Administrators grubunda **olmayan** bir yerel kullanıcı oluşturur ve
Secondary Logon'un devre dışı olmadığını kontrol eder. 📄

```powershell
$pw = Read-Host -AsSecureString "Password for sre-agent"
New-LocalUser -Name 'sre-agent' -Password $pw -Description 'Run Command run-as user for SRE Agent'
Get-Service seclogon | Select-Object Name, Status, StartType   # StartType must not be Disabled
```

Bu kullanıcıya yalnızca agent'ın o makinede okuması ya da düzeltmesi gereken şeylere erişim verin (log klasörleri, yeniden
başlatabileceği bir servis). Agent'ın çalıştırdığı her script tam olarak bu yetkileri alır.

### 2. Custom role'ü oluşturun ve agent'a atayın

`role-vm-managed-runcommand-operator.json`:

```json
{
  "Name": "VM Managed Run Command Operator",
  "IsCustom": true,
  "Description": "Create, update and read managed run commands (runAsUser supported) on VMs. Action Run Command (runCommand/action, always SYSTEM/root) is intentionally excluded. No delete: cleanup is done by an operator.",
  "Actions": [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/instanceView/read",
    "Microsoft.Compute/virtualMachines/runCommands/read",
    "Microsoft.Compute/virtualMachines/runCommands/write",
    "Microsoft.Compute/locations/operations/read"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [ "/subscriptions/<sub>/resourceGroups/<rg>" ]
}
```

Listede `runCommand/action` yok, yani `az vm run-command invoke` rolün dışında. `runCommands/delete` da yok: agent
hiçbir şey silmez, temizliği bir operatör yapar.

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
VM_ID=$(az vm show -g <rg> -n vm01 --query id -o tsv)
az role definition create --role-definition @role-vm-managed-runcommand-operator.json
az role assignment create \
  --assignee-object-id <agent-principal-id> --assignee-principal-type ServicePrincipal \
  --role "VM Managed Run Command Operator" --scope "$VM_ID"
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$VM_ID = az vm show -g <rg> -n vm01 --query id -o tsv
az role definition create --role-definition '@role-vm-managed-runcommand-operator.json'
az role assignment create `
  --assignee-object-id <agent-principal-id> --assignee-principal-type ServicePrincipal `
  --role "VM Managed Run Command Operator" --scope $VM_ID
```
{{< /tab >}}
{{< /tabs >}}

Kimliğin bu VM'i kapsayan daha üst bir kapsamda Virtual Machine Contributor, Contributor ya da Owner rolü varsa
kaldırın. Bu roller `runCommand/action`'ı içerir ve Azure RBAC toplamalı çalışır: daha dar bir atama, daha geniş bir
atamanın verdiğini geri almaz. 📄

### 3. Policy'yi oluşturun ve VM'e atayın

`policy-runcommand-runasuser.json`, `runAsUser` yoksa ya da listede değilse, script bir URI'den ya da galeriden
geliyorsa, ya da çıktı veya hatalar bir blob'a gidiyorsa managed run command'ı reddeder:

```json
{
  "displayName": "Managed run commands must run as an allowed user and must not use external URIs",
  "mode": "All",
  "parameters": {
    "allowedRunAsUsers": { "type": "Array", "defaultValue": [ "sre-agent" ] },
    "effect": { "type": "String", "allowedValues": [ "Audit", "Deny", "Disabled" ], "defaultValue": "Deny" }
  },
  "policyRule": {
    "if": {
      "allOf": [
        { "field": "type", "equals": "Microsoft.Compute/virtualMachines/runCommands" },
        {
          "anyOf": [
            { "field": "Microsoft.Compute/virtualMachines/runCommands/runAsUser", "exists": "false" },
            { "field": "Microsoft.Compute/virtualMachines/runCommands/runAsUser", "notIn": "[parameters('allowedRunAsUsers')]" },
            { "allOf": [
              { "field": "Microsoft.Compute/virtualMachines/runCommands/source.scriptUri", "exists": "true" },
              { "field": "Microsoft.Compute/virtualMachines/runCommands/source.scriptUri", "notEquals": "" } ] },
            { "allOf": [
              { "field": "Microsoft.Compute/virtualMachines/runCommands/source.galleryScriptReferenceId", "exists": "true" },
              { "field": "Microsoft.Compute/virtualMachines/runCommands/source.galleryScriptReferenceId", "notEquals": "" } ] },
            { "allOf": [
              { "field": "Microsoft.Compute/virtualMachines/runCommands/outputBlobUri", "exists": "true" },
              { "field": "Microsoft.Compute/virtualMachines/runCommands/outputBlobUri", "notEquals": "" } ] },
            { "allOf": [
              { "field": "Microsoft.Compute/virtualMachines/runCommands/errorBlobUri", "exists": "true" },
              { "field": "Microsoft.Compute/virtualMachines/runCommands/errorBlobUri", "notEquals": "" } ] }
          ]
        }
      ]
    },
    "then": { "effect": "[parameters('effect')]" }
  }
}
```

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
jq '.policyRule' policy-runcommand-runasuser.json > rule.json
jq '.parameters' policy-runcommand-runasuser.json > params.json
az policy definition create --name runcommand-runasuser --mode All \
  --display-name "Managed run commands must run as an allowed user" \
  --rules rule.json --params params.json
az policy assignment create --name runcommand-runasuser-vm01 \
  --policy runcommand-runasuser --scope "$VM_ID" \
  --params '{"allowedRunAsUsers":{"value":["sre-agent"]}}'
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$def = Get-Content policy-runcommand-runasuser.json -Raw | ConvertFrom-Json
$def.policyRule | ConvertTo-Json -Depth 20 | Set-Content rule.json
$def.parameters | ConvertTo-Json -Depth 20 | Set-Content params.json
'{"allowedRunAsUsers":{"value":["sre-agent"]}}' | Set-Content assign-params.json
az policy definition create --name runcommand-runasuser --mode All `
  --display-name "Managed run commands must run as an allowed user" `
  --rules rule.json --params params.json
az policy assignment create --name runcommand-runasuser-vm01 `
  --policy runcommand-runasuser --scope $VM_ID `
  --params '@assign-params.json'
```
{{< /tab >}}
{{< /tabs >}}

**Kapsamı dar tutun.** Policy, kapsamındaki **her** çağıranı etkiler; yalnızca agent'ı değil, insanları ve pipeline'ları da.
Bir resource group'a ya da subscription'a atanırsa, bir yöneticinin `runAsUser`'sız run command'ını da engeller. Biz onu
agent'ın yönettiği tek VM'e atadık. ✅ Yeni bir atamanın reddetmeye başlaması biraz sürebilir; test etmeden önce bekleyin. 📄

### 4. Agent'a komutları nasıl çalıştıracağını söyleyin

Agent'ın artık VM'de script çalıştırmak için tek bir yolu var: `runAsUser` belirtilmiş bir managed run command. Bunu
talimatlarına açıkça yazın:

```text
To run a command on vm01, use:
az vm run-command create -g <rg> --vm-name vm01 --name <short-unique-name> \
  --script "<script>" --run-as-user sre-agent --run-as-password <password> --timeout-in-seconds 120
Then read the result with:
az vm run-command show -g <rg> --vm-name vm01 --name <same-name> --instance-view
Never use az vm run-command invoke.
```

Windows'ta agent'ın kullanıcının parolasına da ihtiyacı var. Yukarıdaki talimatla bu parola, agent'ın talimatlarında
düz metin olarak duruyor. Bu kurulumun zayıf noktası bu; sondaki uyarıya bakın.

## Doğrulama

Policy'nin atandığı bir Windows VM'de sekiz çağrı denedik. Yedisi bir admin kimliğiyle çalıştırıldı: policy her
çağıranda geçerli olduğu için bir admin'e verilen red, agent'a da verilir. T4'ü o VM'de yalnızca custom role'e sahip
bir kimlikle çalıştırdık. Aynı kimlikle T1 reddedildi, T3 ise tablodaki gibi `sre-agent` olarak çalıştı.

| # | Çağrı | Beklenen | Sonuç |
|---|---|---|---|
| T1 | `--run-as-user` olmadan `create` | policy reddeder | `RequestDisallowedByPolicy` ✅ |
| T2 | `create --run-as-user Administrator` | policy reddeder | `RequestDisallowedByPolicy` ✅ |
| T3 | `create --run-as-user sre-agent` | `sre-agent` olarak çalışır, yönetici değil | `vm01\sre-agent`, `isAdmin=False` ✅ |
| T4 | `invoke` (action Run Command), yalnızca custom role'e sahip kimlik | RBAC reddeder | `AuthorizationFailed` ✅ |
| T5 | `create --script-uri https://…` | policy reddeder | `RequestDisallowedByPolicy` ✅ |
| T6 | T3'ün komutunu `update` ile `--run-as-user Administrator` yapmak | policy reddeder | `RequestDisallowedByPolicy` ✅ |
| T7 | `create --output-blob-uri https://…` | policy reddeder | `RequestDisallowedByPolicy` ✅ |
| T8 | `create --error-blob-uri https://…` | policy reddeder | `RequestDisallowedByPolicy` ✅ |

İzin verilen çağrı, T3:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az vm run-command create -g <rg> --vm-name vm01 --name t3 \
  --script 'whoami; "isAdmin=" + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrators")' \
  --run-as-user sre-agent --run-as-password "$RUNAS_PW" --timeout-in-seconds 120
az vm run-command show -g <rg> --vm-name vm01 --name t3 --instance-view
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az vm run-command create -g <rg> --vm-name vm01 --name t3 `
  --script 'whoami; "isAdmin=" + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrators")' `
  --run-as-user sre-agent --run-as-password $env:RUNAS_PW --timeout-in-seconds 120
az vm run-command show -g <rg> --vm-name vm01 --name t3 --instance-view
```
{{< /tab >}}
{{< /tabs >}}

Beklenen sonuç: `instanceView.executionState` değeri `Succeeded` olur ve `instanceView.output` şunu içerir:

```text
vm01\sre-agent
isAdmin=False
```

`create` çağrısının yanıtı `runAsUser`'ı döndürüyor, parolayı döndürmüyor. ✅

Reddedilen bir çağrı (T1) şöyle görünür:

```text
ERROR: (RequestDisallowedByPolicy) Resource 't1' was disallowed by policy.
Policy identifiers: '[{"policyAssignment":{"name":"runcommand-runasuser-vm01", ...}}]'.
```

T4'ü kendi agent'ınızda doğrulamak için ondan VM'de `az vm run-command invoke` çalıştırmasını isteyin.
`AuthorizationFailed` hatası almalı.

## Sınırlar

- **Windows parola ister.** Windows'ta run-as için `runAsUser`'ın yanında `runAsPassword` da gerekir ve Secondary Logon
  servisi çalışıyor olmalıdır. 📄 Bizim lab'imizde Secondary Logon devre dışıyken de run-as çalıştı. ✅
- **VM başına 25 managed run command.** Eski run command'lar silinene kadar kaynak olarak durur. Rolde silme yok; temizliği bir
  operatörün yapmasını planlayın. 📄
- **Yalnızca VM'ler.** Scale set'ler (`virtualMachineScaleSets/virtualMachines/runCommands`) ve Arc makineleri
  (`Microsoft.HybridCompute/machines/runCommands`) farklı kaynak türleridir. Bu rol ve policy onları kapsamıyor. 📄
- **RBAC değer kontrol edemez.** Bir rol `runCommands/write` verir ya da vermez; "yalnızca `sre-agent` olarak" diyemez. Bu
  Policy'nin işi. 📄
- **Policy kapsamındaki herkesi etkiler.** Atamayı agent'ın yönettiği VM'lerde tutun. ✅

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|
| Geçmesi gereken bir çağrıda `RequestDisallowedByPolicy` | `runAsUser` yok, yanlış yazılmış ya da `allowedRunAsUsers`'da değil; ya da çağrıda script URI'si veya blob URI'si var | Çağrıyı ya da atamanın parametresini düzeltin ✅ |
| `az vm run-command invoke`'ta `AuthorizationFailed` | Action Run Command rolde yok | Beklenen durum. `create` kullanın ✅ |
| Windows'ta run-as başarısız | Parola yanlış ya da Secondary Logon devre dışı | Parolayı kontrol edin; `seclogon`'u Manual yapın 📄 |
| Bir süre sonra yeni run command'lar başarısız oluyor | VM'de zaten 25 managed run command var | Bir operatör eskileri siler 📄 |

## Ne öğrendik

- Action Run Command her zaman SYSTEM ya da root olarak çalışır. Run Command içinde başka bir kullanıcıyla çalıştırmanın
  tek yolu `runAsUser` ile managed Run Command. 📄
- RBAC iki tür Run Command'ı birbirinden ayırabiliyor, ama bir komutun kim olarak çalıştığını göremiyor. Azure Policy
  görebiliyor, çünkü managed run command `runAsUser` özelliği olan bir kaynak. ✅
- Tek bir policy dört kaçış yolunun hepsini kapatıyor: kullanıcı yok, başka kullanıcı, dışarıdan script ve blob'a çıktı.
  Sonradan başka bir kullanıcıya `update` da reddediliyor. ✅
- İzin verilen yol çalışıyor: script yönetici olmayan `vm01\sre-agent` olarak çalıştı. ✅
- Policy'yi daha yukarıya değil, VM'e atayın. Yöneticiler dahil her çağıranda geçerli. ✅

{{< alert icon="triangle-exclamation" >}}
**Run-as parolası agent'ın loglarına düşüyor.** Agent parolayı her çağrıyla göndermek zorunda ve SRE Agent her aracın
girdisini ve çalıştırdığı her az komutunu Application Insights'a kaydeder. 📄 Bu yüzden run-as kullanıcısının parolasını, bu logları okuyabilen herkesin
bildiğini varsayın: gerçek sırları agent'ın erişiminden uzak tutun, kimliğine sır okuyan roller (Key Vault, storage key'leri)
vermeyin, ağ erişimini VM yönetim portlarıyla sınırlayın ve on-behalf-of isteklerini okumadan onaylamayın. Daha güçlü
seçenek, parolayı kendisi tutan ve sabit bir komut setini çalıştıran, kendi kimliği olan bir araç; böylece agent parolayı
hiç görmez. Bu seçeneği yalnızca anlatıyoruz; kurmadık.
{{< /alert >}}
