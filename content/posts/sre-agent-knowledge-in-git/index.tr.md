---
title: "Azure SRE Agent bilgisini git'te tutmak: tek kaynak, iki yol"
description: "Runbook'lar git'te yaşar; bir GitHub Actions işi her değişikliği kamuya açık data-plane API ile agent'ın knowledge base'ine taşır. Ekleme, değişiklik ve silme merge'ü izler; CI kimliğinin tek bir agent üzerinde tek bir rolü vardır."
date: 2026-10-06
draft: false
tags: ["azure-sre-agent", "knowledge", "github-actions", "entra-id", "skills"]
showTableOfContents: true
---

Runbook'ları Azure SRE Agent'a elle yüklemek ilk gün çalışır. Otuzuncu günde knowledge base ile git'teki runbook'lar
artık aynı şeyi söylemez: pull request'te yapılan bir düzeltme agent'a hiç ulaşmaz, emekliye ayrılmış bir runbook'tan hâlâ
cevap verilir ve agent'ın hangi sürümü okuduğunu kimse söyleyemez. Bir runbook'un yazıldığı tek yerin git olmasını,
agent'ın knowledge base'inin de her merge'ü kendiliğinden izlemesini istedik.

✅ = lab'imizde kanıtlandı · 📄 = yalnız belgede var (Microsoft Learn ya da Microsoft'un public örnekleri), bizde test edilmedi.
Bütün komutları zsh'te çalıştırdık. PowerShell sekmeleri bizim tarafımızda test edilmedi; dokümantasyona dayanıyor. 📄

## Amaç ve hedef kitle

**Amaç.** Sonunda runbook'lar bir git reposunun tek bir klasöründe duruyor. `main`'e yapılan her merge kısa bir GitHub
Actions işini çalıştırıyor: yeni ve değişen dosyaları agent'ın knowledge base'ine yüklüyor, sildiklerinizi oradan da
siliyor. İş OIDC ile oturum açıyor: hiçbir yerde secret saklanmıyor ve kimliği Azure'da tek bir agent'a dokunabiliyor,
başka hiçbir şeye değil.

**Kimler için.** Azure SRE Agent işleten ve runbook'larını GitHub'da tutan ya da tutmak isteyen mühendisler. `az`, GitHub
Actions ve Azure rol atamaları size yabancı olmamalı.

## Neden repoyu bağlayıp bırakmıyoruz

SRE Agent bir repoyu **Code Access** ile de bağlayabiliyor. Bunun repodaki dokümanları knowledge base'e koyduğunu varsaymak
cazip. Kamuya açık dokümantasyon bu noktada henüz net değil; biz de bunu yeni bir agent ve benzersiz "kanarya" dizeleri
taşıyan private bir repoyla lab'de test ederek karara bağladık:

- Repo bağlandıktan hemen sonra knowledge base'in dosya listesi **boştu**. Repo bunun yerine agent'ın çalışma alanına
  klonlandı. ✅
- Yalnızca repoda bulunan bir kanaryayı **sadece knowledge base'inde** araması istendiğinde agent iki kez de
  "Memory Search: found 0 relevant results" dedi. ✅
- Aynı soru düz cümleyle sorulduğunda cevabı klonlanmış dosyalarda **Grep Search** ile buldu ve GitHub'daki dosya ile
  satıra link verdi. ✅

Yani bağlı bir repo **dosya** olarak aranıyor; **knowledge** olarak indekslenmiyor. Runbook'larınızın knowledge base'de,
memory search'ten kaynak gösterilerek gelmesini istiyorsanız, onları bir şeyin yüklemesi gerekiyor. O şey aşağıdaki iş.

{{< alert icon="triangle-exclamation" >}}
Yine de bir repoyu Code Access ile bağlarsanız, ona **yalnız o repo için, salt okunur (Contents: Read) bir fine-grained
token** verin. Bizim lab'imizde token, agent'ın sandbox'ında, klonun git credential dosyasında düz metin olarak duruyordu
ve agent onu okuyup kendi başına kullanabildi. ✅ Agent'la sohbet edebilen herkesin onu görebileceğini varsayın.
{{< /alert >}}

## Ön koşullar

| Alan | Gereksinim | |
|---|---|---|
| SRE Agent | Çalışan bir agent; agent memory açık (varsayılan olarak açıktır) | ✅ |
| Azure rolleri | CI kimliğini oluşturup rolünü atamak için, bir kez, agent'ın kaynak grubunda **Owner** ya da **User Access Administrator** yetkisi olan biri | ✅ |
| CI kimliği | GitHub federated credential'lı bir user-assigned managed identity; agent üzerinde **SRE Agent Administrator** | ✅ |
| GitHub | Actions açık bir repo; repository variable tanımlama yetkisi | ✅ |
| Admin makinesi | Oturum açılmış Azure CLI; yerel dry-run için `azure-identity` ve `requests` kurulu Python 3.10+. zsh ya da PowerShell | ✅ zsh / 📄 PowerShell |

Data-plane çağrıları agent üzerinde **SRE Agent Administrator** ister. 📄 Bu rol yoksa her çağrı
`403 Forbidden: Access denied by PDP` döner. ✅

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

1. Runbook'lar yalnız pull request ile değişir; böylece review'dan geçer ve geçmişi tutulur. ✅
2. `main`'e `docs/**`'a dokunan bir push işi başlatır. ✅
3. ve 4. İş, GitHub'ın OIDC token'ını kimlik için bir Entra token'ıyla değiştirir, sonra `https://azuresre.dev` audience'lı
   bir token ister. Ortada client secret yok. ✅
5. Betik yeni ve değişen dosyaları yükler, kaldırılanları siler ve indexer'ı bekler. ✅
6. Sohbette agent içeriği memory search ile bulur ve dokümanı kaynak gösterir. ✅

**Güven sınırı.** CI kimliğinin tam olarak bir rol ataması var: bu agent üzerinde SRE Agent Administrator. Hiçbir Azure
kaynağında rolü yok; iş `allow-no-subscriptions` ile oturum açıyor. ✅ Rol, agent'ın kendisi üzerinde geniş: skill, hook,
connector ve scheduled task'ları da yönetebiliyor. 📄 Workflow dosyasını ve `main` branch'ini buna göre koruyun.

## Adımlar

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

Knowledge base **düzdür**: bir dosya taban adıyla saklanır ve aynı adla yüklenen dosya eski dokümanın yerine geçer. 📄
Farklı klasörlerdeki iki `latency.md` birbirinin üzerine yazar; bu yüzden betik, iki dosyanın taban adı aynıysa
çalışmayı reddediyor. ✅ Runbook'lara klasörün tamamında benzersiz adlar verin (`payments-latency.md`,
`storage-latency.md`).

`.kbignore`, git'te kalan ama knowledge base'e hiç gitmeyen yol öneklerini satır satır listeler:

```text
# Paths under docs/runbooks that are never uploaded to the knowledge base (prefix match).
docs/runbooks/only-in-repo/
```

### 2. CI kimliğini oluşturun

Bu komutları, kaynak grubunda Owner ya da User Access Administrator yetkisi olan bir yönetici bir kez çalıştırır.
**Kimliğin aldığı** tek şey var: bu tek agent üzerinde SRE Agent Administrator. Entra app registration ve secret
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
Bazı GitHub organizasyonları sayısal ID'ler içeren yeni OIDC subject'ini gönderiyor:
`repo:<org>@<org-id>/<repo>@<repo-id>:ref:refs/heads/main`. Bizimki öyleydi. ✅ İlk çalıştırma o zaman `AADSTS700213` ile
düşer ve hata mesajı GitHub'ın gönderdiği subject'i birebir yazar; onu federated credential'a kopyalayın.
{{< /alert >}}

Üç **repository variable** tanımlayın (secret değil; hiçbiri hassas değil): `AZURE_CLIENT_ID` (kimliğin client ID'si),
`AZURE_TENANT_ID` ve `SRE_AGENT_ENDPOINT`. Endpoint'i bir kez ARM'den okuyun:

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

İş endpoint'i ARM yerine bir variable'dan okuyor; böylece kimliğin Reader rolüne ihtiyacı kalmıyor. ✅

### 3. Senkron betiğini ekleyin

Bu iş, elle çalıştırdığımız dört çağrılık bir bash parçası olarak başladı: agent endpoint'ini ARM'den oku,
`https://azuresre.dev` için token al, dosyaları multipart olarak yükle, indexer'a bak.

```bash
ENDPOINT=$(az resource show \
  --ids /subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.App/agents/$AGENT \
  --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv)
TOKEN=$(az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv)
curl -X POST "$ENDPOINT/api/v1/agentmemory/upload" -H "Authorization: Bearer $TOKEN" \
  -F "files=@docs/runbooks/payments/db-failover.md" -F "files=@docs/runbooks/network/dns-failover.md"
curl "$ENDPOINT/api/v1/agentmemory/indexer-status" -H "Authorization: Bearer $TOKEN"
```

Tek bir yükleme için bu yeterli. Ama sildiğiniz bir runbook'u kaldırmıyor ve aynı adlı iki dosyanın birbirinin üzerine
yazmasını engellemiyor. `tools/sre_kb_sync.py` aynı dört çağrının büyümüş hali:

- **Kimlik doğrulama** `DefaultAzureCredential` ile: kendi makinenizde `az login`, GitHub Actions'ta OIDC, başka yerde
  managed identity. Dosya adları ve HTTP kodları dışında hiçbir şey yazdırılmıyor. ✅
- **Endpoint** `--endpoint` ile ya da `--subscription`, `--resource-group` ve `--agent` ile ARM'den. ✅
- Klasör **özyinelemeli** dolaşılıyor; yalnız `.md` ve `.txt`, `.kbignore` uygulanıyor, aynı taban adı reddediliyor,
  dosya başına 16 MB, yüklemeler 100 MB'lık istek sınırının altında gruplanıyor. ✅ (sınırlar 📄)
- **`--git-base`**: yalnız o commit'ten bu yana değişenleri yüklüyor, kaldırılanları siliyor. Bu bayrak yoksa her dosya
  yükleniyor (aynı ad eskisinin yerine geçer). ✅
- **`--prune`**: klasörde olmayan dokümanları da siliyor. Yalnız knowledge base'in tamamı git'e aitse kullanın; agent'ın
  sohbetten kaydettiği dokümanları da siler. 📄
- Yüklenen her dosya indekslenmiş görünene ve indexer çalışana kadar **bekliyor**; zaman aşımında hata veriyor. ✅
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

### 4. Workflow'u ekleyin

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

Bir push o push'un commit aralığını kullanır; yalnız değişen dosyalar gönderilir. Elle çalıştırma (`workflow_dispatch`)
klasörün tamamını yükler; yeni bir agent'ı böyle doldurursunuz. Diff için `fetch-depth: 0` gerekli. `concurrency` iki
merge'ün aynı anda senkron yapmasını engelliyor. ✅

### 5. Önce yerelde deneyin

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

Gerçek çalıştırma için kendi hesabınızın agent üzerinde SRE Agent Administrator rolü olmalı ✅; endpoint'i ARM'den
çözüyorsanız agent kaynağını okuma yetkisi de gerekir. 📄

## Doğrulama

Her durumu runbook'a koyduğumuz bir kanarya diziyle kanıtladık; sonra yeni bir sohbette agent'tan **yalnız** knowledge
base'ini kullanmasını istedik. Kanarya, modelin başka hiçbir yerden bilemeyeceği uydurma bir bilgidir ("failover
sahibi violet rota"); cevapta görünüyorsa dokümandan gelmiştir. ✅

| Durum | İşin log'u | Agent'ın memory search'ten cevabı | |
|---|---|---|---|
| İlk senkron | `upload 3 file(s) -> HTTP 200`, indexer `Success, processed 3, failed 0`; iki klasör derindeki bir runbook dahil | Üç kanarya da, her biri kendi dokümanıyla | ✅ |
| Runbook ekleme | `upload 1, delete 0` ve `+ docs/runbooks/network/dns-failover.md` | Yeni kanarya ve onaylayan kişi | ✅ |
| Runbook değiştirme | Yalnız düzenlenen dosya için `upload 1` | Yeni sahip ve `-v2` kanaryası; eski cevap kalmadı | ✅ |
| Runbook silme | `upload 0, delete 1`, `delete latency.md -> HTTP 200` | Silinen kanaryayı "içeren doküman yok" | ✅ |
| Hariç tutulan yol | `only-in-repo/`'dan hiçbir şey yüklenmedi | "Hiçbir knowledge dokümanında yok" | ✅ |

Her çalıştırma uçtan uca 26 ile 34 saniye sürdü; senkron adımının kendisi, indeksleme dahil 6 ile 20 saniye. ✅

Durumu kendiniz kontrol etmek için:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
TOKEN=$(az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $TOKEN" "$ENDPOINT/api/v1/AgentMemory/files"
curl -s -H "Authorization: Bearer $TOKEN" "$ENDPOINT/api/v1/agentmemory/indexer-status"
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$TOKEN = az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv
Invoke-RestMethod -Headers @{ Authorization = "Bearer $TOKEN" } -Uri "$ENDPOINT/api/v1/AgentMemory/files"
Invoke-RestMethod -Headers @{ Authorization = "Bearer $TOKEN" } -Uri "$ENDPOINT/api/v1/agentmemory/indexer-status"
```
{{< /tab >}}
{{< /tabs >}}

```json
{"files":[{"name":"db-failover.md","isIndexed":true,"errorReason":null}, ...],"continuationToken":""}
```

Portalda aynı dosyalar **Builder > Knowledge base** altında **Indexed** durumuyla görünür. 📄 Sohbette bir araç kartında
`Memory Search: Found 1 relevant results` yazar ve cevap dokümanın adını verir. ✅

## Sık kullanılan prosedürler: onları skill yapın

Knowledge, agent aramaya karar verdiğinde aranır. **Skill** farklıdır: açıklaması agent'ın talimatlarında durur ve iş
eşleştiğinde agent skill'i kendisi yükler. 📄 Aynı iade prosedürünü, farklı kanaryalarla, iki yere de koyduk ve beş yeni
sohbette beş farklı ifadeyle sorduk. Agent **beşinde de skill'i** kullandı, knowledge dokümanını hiç kullanmadı; memory
search bile çalıştırmadı. ✅ Beş soru küçük bir örneklem, bir benchmark değil; ama dokümantasyonun anlattığıyla örtüşüyor.
Nöbetçinizin her hafta kullandığı iki üç prosedürü aynı repoda sürümlenen skill'ler olarak tutun, uzun kuyruğu knowledge
base'e bırakın. Tek kaynaktan iki yol bunlar. Skill'i `PUT {endpoint}/api/v2/extendedAgent/skills/<name>` ile oluşturduk ✅;
skill'leri CI'dan senkronlamak aynı kalıbı izler ve burada ele alınmıyor.

## srectl hakkında bir not

Microsoft'un örnekleri `srectl` adlı bir SRE Agent CLI'ından ve onun `srectl doc upload` komutundan söz ediyor. 📄 Bu
araç henüz kamuya açık değil; bu yüzden bu yazı yalnız bugün herkesin çağırabildiği kamuya açık data-plane API'yi
kullanıyor.

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|
| `AADSTS700213: No matching federated identity record found for presented assertion subject 'repo:<org>@<id>/…'` | Organizasyon sayısal ID'li yeni OIDC subject'ini gönderiyor | Hatadaki subject'i federated credential'a kopyalayın ✅ |
| Her data-plane çağrısında `403 Forbidden: Access denied by PDP` | Çağıranın agent üzerinde SRE Agent Administrator rolü yok ya da atama henüz yayılmadı | Rolü agent kaynağında atayın; bir dakika bekleyin ✅ |
| `azure/login` "No subscriptions found" ile düşüyor | Kimliğin, tasarım gereği, hiçbir Azure kaynağında rolü yok | `allow-no-subscriptions: true` 📄 |
| `DELETE …/agentmemory/document/<name>` `500 Failed to delete document` dönüyor ama doküman silinmiş | Lab'imizde bir kez görüldü; sonraki silme 200 döndü | Betik dosya listesini yeniden okuyor; doküman listede yoksa silmeyi tamam sayıyor ✅ |
| Runbook git'te silindi ama agent hâlâ ondan cevap veriyor | Senkron yalnız yüklüyor; silen bir şey yok | `--git-base` (workflow öyle çalışıyor) ya da `--prune` ile çalıştırın ✅ |
| `two or more files share a base name` | Knowledge base düz | Dosyalardan birinin adını değiştirin ✅ |
| `Agent memory is disabled. Cannot upload documents.` | Agent'ta knowledge kapalı | Agent ayarlarından açın 📄 |

## Ne öğrendik

- Code Access ile bağlanan bir repo dosya olarak aranıyor; knowledge olarak indekslenmiyor. CI işi dosyaları yükleyene
  kadar memory search onun için hiçbir şey döndürmedi. ✅
- Tam bir senkron için kamuya açık data-plane API yeterli: yükleme, listeleme, silme ve indexer durumu. Ekleme,
  değişiklik ve silme merge'ten sonraki yarım dakika içinde agent'a ulaştı. ✅
- Düz bir yükleme döngüsünün unuttuğu kısım silme. Onu git diff'ten yönetin ve dosya listesiyle doğrulayın; çünkü silme
  çağrısının kendisi olmamış bir hatayı bildirebiliyor. ✅
- Knowledge base düz. Benzersiz dosya adı bir üslup tercihi değil, kural. ✅
- CI kimliğinin tek bir agent üzerinde tek bir role ihtiyacı var, secret'a değil: federated credential'lı bir managed
  identity. ✅
- Her hafta kullanılan az sayıdaki prosedür için skill, knowledge base'deki aynı metni beşte beş geçti. ✅
