---
title: "Azure SRE Agent bilgisini git'te tutmak: tek kaynak, iki yol"
description: "Runbook'lar git'te yaşar; bir GitHub Actions workflow'u her değişikliği public data-plane API ile agent'ın knowledge base'ine taşır. Ekleme, değişiklik ve silme merge'ü izler; CI kimliğinin tek bir agent üzerinde tek bir rolü vardır."
date: 2026-10-06
draft: false
tags: ["azure-sre-agent", "knowledge", "github-actions", "entra-id", "skills"]
showTableOfContents: true
---

Runbook'ları Azure SRE Agent'a elle yüklemek ilk gün işe yarar. Otuzuncu günde knowledge base ile git'teki runbook'lar
artık aynı şeyi söylemez: pull request'te yapılan bir düzeltme agent'a hiç ulaşmaz, kullanımdan kaldırılmış bir
runbook'tan hâlâ yanıt verilir ve agent'ın hangi sürümü okuduğunu kimse söyleyemez. Bir runbook'un yazıldığı tek yerin git olmasını,
agent'ın knowledge base'inin de her merge'ü kendiliğinden izlemesini istedik.

✅ = lab'imizde kanıtlandı · 📄 = yalnızca dokümantasyonda var (Microsoft Learn, Microsoft'un public örnekleri ya da bu yazıda gösterilen kod), bizim tarafımızda test edilmedi.
Bütün komutları zsh'te çalıştırdık. PowerShell sekmeleri bizim tarafımızda test edilmedi; dokümantasyona dayanıyor. 📄

## Amaç ve hedef kitle

**Amaç.** Yazının sonunda runbook'lar bir git reposunun tek bir klasöründe duruyor. `main`'e yapılan ve `docs/`
altındaki dosyaları değiştiren her merge, kısa bir GitHub Actions workflow'unu çalıştırıyor: workflow yeni ve değişen
dosyaları agent'ın knowledge base'ine yüklüyor, sildiklerinizi oradan da siliyor. Workflow OIDC ile oturum açıyor:
hiçbir yerde secret saklanmıyor ve kullandığı kimlik Azure'da yalnızca tek bir agent'a erişebiliyor, başka hiçbir şeye
değil. Başlıktaki iki yoldan ikincisini, yani nöbetçi ekibinizin her hafta kullandığı birkaç prosedürü, yazının
sonundaki skill bölümü anlatıyor.

**Kimler için.** Azure SRE Agent işleten ve runbook'larını GitHub'da tutan ya da tutmak isteyen mühendisler. `az`, GitHub
Actions ve Azure rol atamaları size yabancı olmamalı.

## Neden repoyu bağlayıp bırakmıyoruz

SRE Agent bir repoyu **Code Access** ile de bağlayabiliyor. Bunun, repodaki dokümanları knowledge base'e koyduğu
sanılabilir; Microsoft Learn de artık bağlı bir repoyu bir knowledge kaynağı olarak anlatıyor. 📄 Biz bunu 2026-10-06'da
yeni bir agent ve benzersiz "kanarya" dizeleri (modelin başka hiçbir yerden bilemeyeceği uydurma bilgiler) taşıyan
private bir repoyla lab'de test ettik:

- Repo bağlandıktan hemen sonra knowledge base'in dosya listesi **boştu**. Repo bunun yerine agent'ın çalışma alanına
  klonlandı. ✅
- Agent'tan, yalnızca repoda bulunan bir kanaryayı **sadece kendi knowledge base'inde** aramasını iki kez istedik. İki
  seferde de "Memory Search: found 0 relevant results" yanıtını verdi. ✅
- Aynı soruyu sade bir cümleyle sorduğumuzda yanıtı klonlanmış dosyalarda **Grep Search** ile buldu ve GitHub'daki
  dosyaya ve satıra link verdi. ✅

Yani lab'imizde bağlı bir repo **dosya** olarak arandı; **knowledge** olarak indekslenmedi. Runbook'larınızın knowledge base'e
girmesini ve memory search sonuçlarında kaynak olarak gösterilmesini istiyorsanız, onları bir şeyin yüklemesi gerekir.
Bu işi aşağıdaki workflow yapıyor.

{{< alert icon="triangle-exclamation" >}}
Yine de bir repoyu Code Access ile bağlarsanız, ona **yalnızca o repo için, salt okunur (Contents: Read) bir fine-grained
token** verin. Bizim lab'imizde token, agent'ın sandbox'ında, klonun git credential dosyasında düz metin olarak duruyordu
ve agent onu okuyup kendi başına kullanabildi. ✅ Agent'la sohbet edebilen herkesin onu görebileceğini varsayın.
{{< /alert >}}

## Ön koşullar

| Alan | Gereksinim | |
|---|---|---|
| SRE Agent | Agent memory'si açık, çalışan bir agent (yeni agent'ımızda hiçbir değişiklik gerekmedi) | ✅ |
| Azure rolleri | CI kimliğini oluşturup rolünü atamak için, bir kez, agent'ın kaynak grubunda **Owner** (ya da **Contributor** ile birlikte **User Access Administrator**) rolü olan biri | 📄 |
| CI kimliği | GitHub federated credential'lı bir user-assigned managed identity; agent üzerinde **SRE Agent Administrator** | ✅ |
| GitHub | Actions'ı açık bir repo; repository variable tanımlama yetkisi | ✅ |
| Admin makinesi | Oturum açılmış Azure CLI; yerel dry-run için `azure-identity` ve `requests` kurulu Python 3. zsh ya da PowerShell | ✅ zsh / 📄 PowerShell |

Knowledge dokümanı yüklemek için **SRE Agent Standard User** yeterli; silmek için **SRE Agent Administrator** gerekir,
bu yüzden senkron kimliği Administrator alır. 📄 Agent üzerinde hiçbir rol yokken data-plane çağrılarımız
`403 Forbidden: Access denied by PDP` hatası verdi. ✅

## Mimari

{{< mermaid >}}
flowchart LR
  DEV["Mühendis"] -- "1 pull request, review, merge" --> GH["GitHub reposu<br/>docs/runbooks/**"]
  GH -- "2 main'e push (docs/**)" --> GA["GitHub Actions<br/>knowledge-sync"]
  GA -- "3 OIDC token" --> ENTRA["Entra ID<br/>user-assigned MI üzerinde<br/>federated credential"]
  ENTRA -- "4 https://azuresre.dev için token" --> GA
  GA -- "5 upload / delete / status<br/>data plane, HTTPS" --> AG["SRE Agent<br/>knowledge base"]
  AG -- "6 memory search, kaynak gösterme" --> CHAT["Sohbet ve olaylar"]
{{< /mermaid >}}

1. Runbook'lar yalnızca pull request ile değişmeli (`main`'i koruyun); böylece review'dan geçer ve geçmişi tutulur. Bu
   bizim önerimiz; demo repomuz `main`'e doğrudan push alıyordu.
2. `main`'e yapılan ve `docs/**` altındaki dosyaları değiştiren bir push, workflow'u başlatır. ✅
3. ve 4. Workflow, GitHub'ın OIDC token'ını kimlik için bir Entra token'ıyla takas eder, sonra `https://azuresre.dev`
   audience'lı bir token ister. Hiçbir client secret yok. ✅
5. Betik yeni ve değişen dosyaları yükler, kaldırılanları siler ve indexer'ı bekler. ✅
6. Sohbette agent içeriği memory search ile bulur ve dokümanı kaynak gösterir. ✅

**Güven sınırı.** CI kimliğinin yalnızca bir rol ataması var: bu agent üzerinde SRE Agent Administrator. Hiçbir Azure
kaynağında rolü yok; workflow `allow-no-subscriptions` ile oturum açıyor. ✅ Ancak bu rol, agent'ın kendisi üzerinde
geniş yetki veriyor: skill'leri, hook'ları, connector'ları ve scheduled task'ları da yönetebiliyor. 📄 Workflow dosyasını ve `main` branch'ini buna göre koruyun.

## Adımlar

Kısaca: (1) repo düzenini kurun, knowledge base'e gitmeyecek yollar için bir `.kbignore` ekleyin; (2) CI kimliğini
oluşturun: GitHub federated credential'lı ve agent üzerinde tek bir rolü olan bir managed identity; (3) senkron betiğini
ekleyin; (4) betiği önce yerelde `--dry-run` ile deneyin; (5) betiği çalıştıran workflow'u ekleyin.

### 1. Repo düzenini kurun

```text
docs/runbooks/
  payments/db-failover.md
  payments/refund-replay.md
  network/dns-failover.md
  only-in-repo/...          (excluded through .kbignore)
tools/sre_kb_sync.py
.kbignore
.github/workflows/knowledge-sync.yml
```

Knowledge base **düzdür**, klasör tutmaz: bir dosya klasör yolu olmadan, yalnızca dosya adıyla saklanır ve aynı adla
yüklenen dosya eski dokümanın yerine geçer. 📄 Farklı klasörlerdeki iki `latency.md` birbirinin üzerine yazar; bu
yüzden betik, aynı adı taşıyan iki dosya bulursa çalışmadan hata veriyor. 📄 (aşağıdaki betik; bu durumu tetiklemedik) Runbook'lara klasörün tamamında benzersiz adlar verin (`payments-latency.md`,
`storage-latency.md`).

`.kbignore`, git'te kalan ama knowledge base'e hiç yüklenmeyen yolların öneklerini, her satıra bir tane olacak şekilde
listeler:

```text
# Paths under docs/runbooks that are never uploaded to the knowledge base (prefix match).
docs/runbooks/only-in-repo/
```

### 2. CI kimliğini oluşturun

Bu komutları, kaynak grubunda Owner (ya da Contributor ile birlikte User Access Administrator) rolü olan bir yönetici
bir kez çalıştırır. 📄
**Kimliğin aldığı** tek şey var: bu tek agent üzerinde SRE Agent Administrator. Entra'da app registration ya da secret
oluşturulmuyor.

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
RG=<rg>; AGENT=<agent>; ORG=<github-org>; REPO=<github-repo>

az identity create -g $RG -n id-kb-sync -o none
az identity federated-credential create -g $RG --identity-name id-kb-sync -n github-main \
  --issuer https://token.actions.githubusercontent.com \
  --subject "repo:$ORG/$REPO:ref:refs/heads/main" \
  --audiences api://AzureADTokenExchange -o none

AGENT_ID=$(az resource show -g $RG -n $AGENT --resource-type Microsoft.App/agents --query id -o tsv)
MI_PRINCIPAL=$(az identity show -g $RG -n id-kb-sync --query principalId -o tsv)
az role assignment create --assignee-object-id $MI_PRINCIPAL --assignee-principal-type ServicePrincipal \
  --role "SRE Agent Administrator" --scope $AGENT_ID -o none
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$RG = "<rg>"; $AGENT = "<agent>"; $ORG = "<github-org>"; $REPO = "<github-repo>"

az identity create -g $RG -n id-kb-sync -o none
az identity federated-credential create -g $RG --identity-name id-kb-sync -n github-main `
  --issuer https://token.actions.githubusercontent.com `
  --subject "repo:${ORG}/${REPO}:ref:refs/heads/main" `
  --audiences api://AzureADTokenExchange -o none

$AGENT_ID = az resource show -g $RG -n $AGENT --resource-type Microsoft.App/agents --query id -o tsv
$MI_PRINCIPAL = az identity show -g $RG -n id-kb-sync --query principalId -o tsv
az role assignment create --assignee-object-id $MI_PRINCIPAL --assignee-principal-type ServicePrincipal `
  --role "SRE Agent Administrator" --scope $AGENT_ID -o none
```
{{< /tab >}}
{{< /tabs >}}

{{< alert icon="circle-info" >}}
Bazı GitHub organizasyonları, sayısal ID'ler içeren yeni OIDC subject biçimini gönderiyor:
`repo:<org>@<org-id>/<repo>@<repo-id>:ref:refs/heads/main`. Bizim organizasyonumuz da böyle gönderiyordu. ✅ Bu durumda
ilk çalıştırma `AADSTS700213` hatası verir ve hata mesajı GitHub'ın gönderdiği subject'i birebir gösterir; onu federated
credential'a kopyalayın.
{{< /alert >}}

Üç **repository variable** tanımlayın (secret olarak değil; hiçbiri hassas değil): `AZURE_CLIENT_ID` (kimliğin client
ID'si), `AZURE_TENANT_ID` ve `SRE_AGENT_ENDPOINT`. Client ID'yi ve endpoint'i bir kez okuyun:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az identity show -g $RG -n id-kb-sync --query clientId -o tsv
az resource show --ids $AGENT_ID --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az identity show -g $RG -n id-kb-sync --query clientId -o tsv
az resource show --ids $AGENT_ID --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv
```
{{< /tab >}}
{{< /tabs >}}

Workflow endpoint'i ARM yerine variable'dan okuyor; bu yüzden kimliğin Reader rolüne ihtiyacı yok. ✅

### 3. Senkron betiğini ekleyin

Betik, elle çalıştırdığımız dört çağrılık bir bash parçası olarak başladı: agent endpoint'ini ARM'den oku,
`https://azuresre.dev` için token al, dosyaları multipart olarak yükle, indexer'ın durumuna bak.

```bash
SUB=<sub>   # RG and AGENT as in step 2
ENDPOINT=$(az resource show \
  --ids /subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.App/agents/$AGENT \
  --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv)
TOKEN=$(az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv)
curl -X POST "$ENDPOINT/api/v1/agentmemory/upload" -H "Authorization: Bearer $TOKEN" \
  -F "files=@docs/runbooks/payments/db-failover.md" -F "files=@docs/runbooks/network/dns-failover.md"
curl "$ENDPOINT/api/v1/agentmemory/indexer-status" -H "Authorization: Bearer $TOKEN"
```

Tek bir yükleme için bu yeterli. Ama sildiğiniz bir runbook'u knowledge base'den kaldırmıyor ve aynı adlı iki dosyanın
birbirinin üzerine yazmasını engellemiyor. `tools/sre_kb_sync.py` aynı dört çağrının genişletilmiş hâli:

- **Kimlik doğrulama** `DefaultAzureCredential` ile: kendi makinenizde `az login`, GitHub Actions'ta OIDC, başka ortamlarda
  managed identity. Token ya da secret yazdırılmıyor: çıktı dosya adları, sayılar, HTTP kodları, indexer durumu ve hata
  durumunda yanıt gövdesinin ilk 300 karakterinden oluşuyor. 📄 (aşağıdaki betik)
- **Endpoint** `--endpoint` ile ya da `--subscription`, `--resource-group` ve `--agent` ile ARM'den. ✅
- Klasör **alt klasörleriyle birlikte** taranıyor: yalnızca `.md` ve `.txt` dosyaları alınıyor, `.kbignore`
  uygulanıyor. ✅ Aynı adı taşıyan dosyalar reddediliyor, dosya başına sınır 16 MB, yüklemeler 100 MB'lık istek
  sınırının altında kalacak şekilde gruplanıyor. 📄 (sınırlar: Learn; geri kalanı: aşağıdaki betik)
- **`--git-base`**: yalnızca o commit'ten bu yana değişenleri yüklüyor ve kaldırılanları siliyor. Bu seçenek
  verilmezse her dosya yükleniyor (aynı adlı dosya eskisinin yerine geçer). ✅
- **`--prune`**: klasörde olmayan dokümanları da siliyor. Yalnızca knowledge base'in tamamını git yönetiyorsa kullanın;
  aksi halde agent'ın sohbetten kaydettiği dokümanları da siler. 📄
- Yüklenen her dosya indekslenmiş görünene ve indexer çalışana kadar **bekliyor**. ✅ Süre dolarsa hata veriyor. 📄
  (aşağıdaki betik)
- **`--dry-run`** planı yazdırıyor, hiçbir şeyi değiştirmiyor. ✅

```python
#!/usr/bin/env python3
"""Sync a folder of runbooks from git into an Azure SRE Agent knowledge base.

Uses the public data-plane API:
  POST   {endpoint}/api/v1/agentmemory/upload            multipart, field "files", one part per file
  GET    {endpoint}/api/v1/AgentMemory/files             documents and their isIndexed flag
  DELETE {endpoint}/api/v1/agentmemory/document/{name}   remove one document
  GET    {endpoint}/api/v1/agentmemory/indexer-status    indexer run state

Auth: DefaultAzureCredential (az login locally, OIDC or managed identity in CI). The caller needs
SRE Agent Administrator on the agent. No secret is read from or written to the console.

The knowledge base is flat: a file is stored under its base name, and a second file with the same name
replaces the first. The script therefore refuses to run when two files share a base name.
"""
import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests
from azure.identity import DefaultAzureCredential

ARM = "https://management.azure.com"
API_VERSION = "2025-05-01-preview"
MAX_FILE = 16 * 1024 * 1024        # per file
MAX_BATCH = 90 * 1024 * 1024       # per request (service limit is 100 MB)
EXTENSIONS = (".md", ".txt")


def log(msg):
    print(msg, flush=True)


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


class Agent:
    def __init__(self, cred, endpoint):
        self.cred, self.endpoint = cred, endpoint.rstrip("/")

    def _headers(self):
        return {"Authorization": "Bearer " + self.cred.get_token("https://azuresre.dev/.default").token}

    def get(self, path, **kw):
        return requests.get(self.endpoint + path, headers=self._headers(), timeout=60, **kw)

    def post(self, path, **kw):
        return requests.post(self.endpoint + path, headers=self._headers(), timeout=300, **kw)

    def delete(self, path):
        return requests.delete(self.endpoint + path, headers=self._headers(), timeout=60)

    def documents(self):
        """Return {name: isIndexed} for every uploaded document."""
        docs, token = {}, ""
        while True:
            r = self.get("/api/v1/AgentMemory/files", params={"continuationToken": token} if token else None)
            r.raise_for_status()
            body = r.json()
            for f in body.get("files", []):
                docs[f["name"]] = bool(f.get("isIndexed"))
            token = body.get("continuationToken") or ""
            if not token:
                return docs


def resolve_endpoint(cred, a):
    if a.endpoint:
        return a.endpoint
    if not (a.subscription and a.resource_group and a.agent):
        fail("give --endpoint, or --subscription, --resource-group and --agent")
    url = (f"{ARM}/subscriptions/{a.subscription}/resourceGroups/{a.resource_group}"
           f"/providers/Microsoft.App/agents/{a.agent}?api-version={API_VERSION}")
    tok = cred.get_token("https://management.azure.com/.default").token
    r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=60)
    if r.status_code != 200:
        fail(f"could not read the agent from ARM (HTTP {r.status_code})")
    return r.json()["properties"]["agentEndpoint"]


def load_excludes(path):
    if not path or not os.path.exists(path):
        return []
    with open(path) as f:
        return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]


def excluded(path, prefixes):
    p = path.replace(os.sep, "/")
    return any(p.startswith(x) for x in prefixes)


def local_files(root, prefixes):
    files = []
    for d, _, names in os.walk(root):
        for n in names:
            p = os.path.join(d, n)
            if n.endswith(EXTENSIONS) and not excluded(p, prefixes):
                files.append(p)
    files.sort()
    by_name = {}
    for p in files:
        by_name.setdefault(os.path.basename(p), []).append(p)
    clashes = {n: ps for n, ps in by_name.items() if len(ps) > 1}
    if clashes:
        for n, ps in clashes.items():
            log(f"  name clash: {n} <- {', '.join(ps)}")
        fail("two or more files share a base name; the knowledge base is flat, so rename them "
             "(for example payments-db-failover.md)")
    for p in files:
        if os.path.getsize(p) > MAX_FILE:
            fail(f"{p} is larger than 16 MB")
    return files


def git_changes(root, base, head, prefixes):
    """Files added or modified, and files deleted, under root between two commits."""
    out = subprocess.check_output(["git", "diff", "--no-renames", "--name-status", base, head, "--", root], text=True)
    changed, deleted = [], []
    for line in out.splitlines():
        status, path = line.split("\t", 1)
        if not path.endswith(EXTENSIONS) or excluded(path, prefixes):
            continue
        (deleted if status == "D" else changed).append(path)
    return changed, deleted


def batches(paths):
    batch, size = [], 0
    for p in paths:
        s = os.path.getsize(p)
        if batch and size + s > MAX_BATCH:
            yield batch
            batch, size = [], 0
        batch.append(p)
        size += s
    if batch:
        yield batch


def upload(agent, paths):
    for b in batches(paths):
        parts = [("triggerIndexing", (None, "true"))]
        handles = []
        for p in b:
            fh = open(p, "rb")
            handles.append(fh)
            parts.append(("files", (os.path.basename(p), fh, "text/plain")))
        try:
            r = agent.post("/api/v1/agentmemory/upload", files=parts)
        finally:
            for fh in handles:
                fh.close()
        log(f"upload {len(b)} file(s) -> HTTP {r.status_code}")
        if r.status_code >= 300:
            fail(f"upload failed: {r.text[:300]}")
        for p in b:
            log(f"  + {p}")


def delete(agent, names):
    for n in names:
        r = agent.delete(f"/api/v1/agentmemory/document/{requests.utils.quote(n)}")
        log(f"delete {n} -> HTTP {r.status_code}")
        if r.status_code < 300 or r.status_code == 404:
            continue
        # Observed: the endpoint can answer 500 although the document is gone. Trust the list.
        if n in agent.documents():
            fail(f"delete failed for {n}: {r.text[:300]}")
        log(f"  {n} is no longer listed; delete done")


def wait_indexed(agent, want, gone, started, timeout):
    deadline = time.time() + timeout
    while True:
        docs = agent.documents()
        missing = sorted(n for n in want if not docs.get(n))
        stale = sorted(n for n in gone if n in docs)
        st = agent.get("/api/v1/agentmemory/indexer-status")
        last = (st.json().get("lastExecution") or {}) if st.status_code == 200 else {}
        ran_after = (last.get("endTime") or "") >= started
        if not missing and not stale and (ran_after or not want):
            log(f"indexer: {last.get('status')} at {last.get('endTime')}, "
                f"processed {last.get('documentsProcessed')}, failed {last.get('documentsFailed')}")
            return docs
        if time.time() > deadline:
            fail(f"timed out; not indexed: {missing}; still present: {stale}")
        time.sleep(10)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", default=os.getenv("SRE_AGENT_ENDPOINT"))
    ap.add_argument("--subscription", default=os.getenv("AZURE_SUBSCRIPTION_ID"))
    ap.add_argument("--resource-group", default=os.getenv("SRE_AGENT_RESOURCE_GROUP"))
    ap.add_argument("--agent", default=os.getenv("SRE_AGENT_NAME"))
    ap.add_argument("--docs", default="docs/runbooks", help="folder to sync, walked recursively")
    ap.add_argument("--exclude-file", default=".kbignore", help="path prefixes that are never uploaded")
    ap.add_argument("--git-base", help="upload only what changed since this commit, and delete what was removed")
    ap.add_argument("--git-head", default="HEAD")
    ap.add_argument("--prune", action="store_true",
                    help="also delete documents that are not in the folder (only when git owns the whole knowledge base)")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    prefixes = load_excludes(a.exclude_file)
    files = local_files(a.docs, prefixes)
    names = {os.path.basename(p) for p in files}

    if a.git_base and set(a.git_base) != {"0"}:
        changed, removed = git_changes(a.docs, a.git_base, a.git_head, prefixes)
        to_upload = [p for p in files if p in set(changed)]
        to_delete = sorted({os.path.basename(p) for p in removed} - names)
    else:
        to_upload, to_delete = files, []

    cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    agent = Agent(cred, resolve_endpoint(cred, a))
    if a.prune:
        to_delete = sorted(set(to_delete) | (set(agent.documents()) - names))

    log(f"{len(files)} file(s) in {a.docs}; upload {len(to_upload)}, delete {len(to_delete)}")
    if a.dry_run:
        for p in to_upload:
            log(f"  would upload {p}")
        for n in to_delete:
            log(f"  would delete {n}")
        return

    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    if to_upload:
        upload(agent, to_upload)
    delete(agent, to_delete)
    docs = wait_indexed(agent, {os.path.basename(p) for p in to_upload}, set(to_delete), started, a.timeout)
    log("knowledge base: " + ", ".join(f"{n}{'' if ok else ' (not indexed)'}" for n, ok in sorted(docs.items())))


if __name__ == "__main__":
    main()
```

### 4. Önce yerelde deneyin

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
pip install azure-identity requests
python3 tools/sre_kb_sync.py --subscription <sub> --resource-group <rg> --agent <agent> --dry-run
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
pip install azure-identity requests
python tools/sre_kb_sync.py --subscription <sub> --resource-group <rg> --agent <agent> --dry-run
```
{{< /tab >}}
{{< /tabs >}}

```text
3 file(s) in docs/runbooks; upload 3, delete 0
  would upload docs/runbooks/payments/api/latency.md
  would upload docs/runbooks/payments/db-failover.md
  would upload docs/runbooks/payments/refund-replay.md
```

Örnek, repoyu aşağıdaki Doğrulama testlerinden önceki hâliyle gösteriyor: repoda hâlâ Silme testinin kaldırdığı
`payments/api/latency.md` vardı, Ekleme testinin oluşturduğu `network/dns-failover.md` ise henüz yoktu. ✅

Gerçek çalıştırma (`--dry-run` olmadan) için kendi hesabınızın agent üzerinde SRE Agent Administrator rolü olmalı ✅;
endpoint'i ARM'den alıyorsanız agent kaynağını okuma yetkisi de gerekir. 📄

### 5. Workflow'u ekleyin

```yaml
name: knowledge-sync

on:
  push:
    branches: [main]
    paths: ["docs/**", ".kbignore"]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

concurrency:
  group: knowledge-sync
  cancel-in-progress: false

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          allow-no-subscriptions: true
      - run: pip install --quiet azure-identity requests
      - name: Sync docs/runbooks into the knowledge base
        env:
          SRE_AGENT_ENDPOINT: ${{ vars.SRE_AGENT_ENDPOINT }}
          BASE: ${{ github.event_name == 'push' && github.event.before || '' }}
        run: |
          if [ -n "$BASE" ]; then
            python3 tools/sre_kb_sync.py --docs docs/runbooks --git-base "$BASE" --git-head "$GITHUB_SHA"
          else
            python3 tools/sre_kb_sync.py --docs docs/runbooks
          fi
```

Push ile tetiklenen çalıştırma o push'un commit aralığını kullanır; böylece yalnızca değişen dosyalar gönderilir. ✅ Elle
çalıştırma (`workflow_dispatch`) klasörün tamamını yükler; yeni bir agent'ı böyle doldurursunuz. Diff için
`fetch-depth: 0` gerekli. `concurrency`, iki merge'ün senkronunun aynı anda çalışmasını engelliyor. 📄 (yukarıdaki
workflow)

## Doğrulama

Her durumu, runbook'a koyduğumuz bir kanarya dizesiyle kanıtladık; sonra yeni bir sohbette agent'tan **yalnızca**
kendi knowledge base'ini kullanmasını istedik. Kanarya, modelin başka hiçbir yerden bilemeyeceği uydurma bir bilgidir
("failover sahibi violet rota"); yanıtta görünüyorsa dokümandan gelmiştir. ✅

| Durum | Workflow log'u | Agent'ın memory search ile verdiği yanıt | |
|---|---|---|---|
| İlk senkron | `upload 3 file(s) -> HTTP 200`, indexer `Success, processed 3, failed 0`; iki klasör derindeki bir runbook dahil | Üç kanarya da, her biri kendi dokümanıyla | ✅ |
| Runbook ekleme | `upload 1, delete 0` ve `+ docs/runbooks/network/dns-failover.md` | Yeni kanarya ve onaylayan kişi | ✅ |
| Runbook değiştirme | Yalnızca düzenlenen dosya için `upload 1` | Yeni sahip ve `-v2` kanaryası; eski yanıt kalmadı | ✅ |
| Runbook silme | `upload 0, delete 1`, `delete latency.md -> HTTP 200` | Silinen kanaryayı "içeren doküman yok" | ✅ |
| Hariç tutulan yol | `only-in-repo/`'dan hiçbir şey yüklenmedi | "Hiçbir knowledge dokümanında yok" | ✅ |

Her çalıştırma uçtan uca 26 ile 34 saniye arasında sürdü; senkron adımının kendisi, indeksleme dahil, 6 ile 20 saniye
arasında. ✅

Durumu kendiniz kontrol etmek için:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
ENDPOINT=$(az resource show --ids $AGENT_ID --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv)
TOKEN=$(az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" "$ENDPOINT/api/v1/AgentMemory/files"
curl -s -H "Authorization: Bearer $TOKEN" "$ENDPOINT/api/v1/agentmemory/indexer-status"
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$ENDPOINT = az resource show --ids $AGENT_ID --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv
$TOKEN = az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv
Invoke-RestMethod -Headers @{ Authorization = "Bearer $TOKEN" } -Uri "$ENDPOINT/api/v1/AgentMemory/files"
Invoke-RestMethod -Headers @{ Authorization = "Bearer $TOKEN" } -Uri "$ENDPOINT/api/v1/agentmemory/indexer-status"
```
{{< /tab >}}
{{< /tabs >}}

```json
{"files":[{"name":"db-failover.md","isIndexed":true,"errorReason":null}, ...],"continuationToken":""}
```

Portalda aynı dosyalar **Builder > Knowledge base** altında **Indexed** durumuyla görünür. 📄 Sohbette bir tool kartında
`Memory Search: Found 1 relevant results` yazar ve yanıt dokümanın adını verir. ✅

## Sık kullanılan prosedürler: onları skill yapın

Knowledge, agent aramaya karar verdiğinde aranır. **Skill** farklıdır: açıklaması agent'ın talimatlarında durur ve görev
eşleştiğinde agent skill'i kendisi yükler. 📄 Aynı iade prosedürünü, farklı kanaryalarla, iki yere de koyduk ve beş yeni
sohbette beş farklı ifadeyle sorduk. Agent **beşinde de skill'i** kullandı, knowledge dokümanını hiç kullanmadı; memory
search bile çalıştırmadı. ✅ Beş soru küçük bir örneklem, bir benchmark değil; ama sonuç dokümantasyonun anlattığıyla örtüşüyor.
Nöbetçi ekibinizin her hafta kullandığı iki üç prosedürü, aynı repoda sürümlenen skill'ler olarak tutun; seyrek
kullanılanları knowledge base'e bırakın. Tek kaynaktan çıkan iki yol bunlar. Skill'i agent üzerinde oluşturduk ✅ (`PUT {endpoint}/api/v2/extendedAgent/skills/<name>` ile 📄);
skill'leri CI'dan senkronlamak da aynı yaklaşımla yapılır; bu yazıda ele alınmıyor.

## srectl hakkında bir not

Microsoft'un örnekleri `srectl` adlı bir SRE Agent CLI'ından ve onun `srectl doc upload` komutundan söz ediyor. 📄 Bu
araç henüz herkese açık olarak yayımlanmadı; bu yüzden bu yazı yalnızca bugün herkesin çağırabildiği public data-plane
API'yi kullanıyor.

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|
| `AADSTS700213: No matching federated identity record found for presented assertion subject 'repo:<org>@<id>/…'` | Organizasyon sayısal ID'li yeni OIDC subject'ini gönderiyor | Hatadaki subject'i federated credential'a kopyalayın ✅ |
| Her data-plane çağrısında `403 Forbidden: Access denied by PDP` | Çağıran kimliğin agent üzerinde SRE Agent Administrator rolü yok ya da atama henüz etkinleşmedi | Rolü agent kaynağında atayın ✅; yeni bir atamanın etkinleşmesi 10 dakikayı bulabilir 📄 |
| `azure/login` "No subscriptions found" hatası veriyor | Kimliğin, tasarım gereği, hiçbir Azure kaynağında rolü yok | `allow-no-subscriptions: true` 📄 |
| `DELETE …/agentmemory/document/<name>` `500 Failed to delete document` dönüyor ama doküman silinmiş | Lab'imizde bir kez görüldü | Betik dosya listesini yeniden okuyor; doküman listede yoksa silmeyi başarılı sayıyor ✅ |
| Runbook git'te silindi ama agent hâlâ ondan yanıt veriyor | Senkron yalnızca yükleme yapıyor; silen bir adım yok | `--git-base` (workflow öyle çalışıyor) ✅ ya da `--prune` 📄 ile çalıştırın |
| `two or more files share a base name` | Knowledge base düz | Dosyalardan birinin adını değiştirin 📄 |
| `Agent memory is disabled. Cannot upload documents.` | Agent'ta knowledge kapalı | Agent ayarlarından açın 📄 |

## Ne öğrendik

- Lab'imizde Code Access ile bağlanan bir repo dosya olarak arandı; knowledge olarak indekslenmedi. CI workflow'u dosyaları
  yükleyene kadar memory search onun için hiçbir şey döndürmedi. ✅
- Tam bir senkron için public data-plane API yeterli: yükleme, listeleme, silme ve indexer durumu. Ekleme, değişiklik
  ve silme, merge'den 26 ile 34 saniye sonra agent'a ulaştı. ✅
- Basit bir yükleme döngüsünün atladığı kısım silmedir. Silmeleri git diff'e göre yapın ve sonucu dosya listesinden
  doğrulayın; çünkü silme çağrısı, aslında olmayan bir hata bildirebiliyor. ✅
- Knowledge base düz. Benzersiz dosya adı bir üslup tercihi değil, kural. 📄
- CI kimliğine tek bir agent üzerinde tek bir rol yetiyor; secret gerekmiyor: federated credential'lı bir managed
  identity yeterli. ✅
- Her hafta kullanılan birkaç prosedürde skill, knowledge base'deki aynı metne beşte beş üstün geldi. ✅
