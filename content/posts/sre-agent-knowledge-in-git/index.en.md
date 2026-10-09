---
title: "Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline"
description: "Azure SRE Agent takes knowledge as uploaded files, and a GitHub repository connected through Code Access does not become knowledge. Keep the documents in a GitHub repository of their own; a script pushes them through the public data-plane API, and a pipeline runs it on every merge."
date: 2026-10-06
draft: false
tags: ["azure-sre-agent", "knowledge", "github-actions", "entra-id", "skills"]
showTableOfContents: true
---

Azure SRE Agent answers from its knowledge base: the runbooks and guides your team gives it. Today you add them by
uploading files in the portal (**Builder > Knowledge base > Add file**) or by asking the agent to save one from chat. 📄
That is the practical way to start: a handful of Markdown files, and the agent can use them.

It stops being enough once the documents change. Runbooks are written by several people, need review and history, and
must reach the agent the moment they change. A git repository gives you review, history and rollback already, so the
documents belong in git. Where they can go next depends on where the repository lives:

- **Azure DevOps.** The portal has a **Documentation connector** whose settings point to Azure DevOps ✅, and Learn
  describes it as crawling an Azure DevOps wiki or Git repository and re-indexing it every 24 hours. 📄 We have not
  tested it.
- **GitHub.** There is no built-in way. The documentation describes adding a repository as a knowledge source 📄, but
  in the portal, as of October 2026, there is no such option: a GitHub repository connects only through **Code
  Access**. ✅ And the repository we connected through Code Access on 2026-10-06 did not become knowledge: the agent
  could read it, but memory search found nothing in it. ✅

This post is about the GitHub case. It keeps the documents in a git repository of their own, pushes them into the agent's knowledge base through
the public data-plane API with a short Python script, and runs that script on every merge from a pipeline (a GitHub
Actions workflow). Adds, edits and deletes reached the agent 26 to 34 seconds after the merge. ✅

✅ = proven in our lab · 📄 = documented only (Microsoft Learn, Microsoft's public samples, or the code shown in this post), not tested by us.
We ran every command in zsh. The PowerShell tabs were not tested on our side; they follow the documentation. 📄

## Goal and audience

**Goal.** By the end of this post, your runbooks live in one folder of their own git repository, and that repository is
the only place they are written. Every merge to `main` that touches `docs/` runs a short GitHub Actions job that uploads
new and changed files to the agent's knowledge base and deletes the ones you removed. The job signs in with OIDC: no
secret is stored anywhere, and its identity can touch one agent and nothing else in Azure.

**Audience.** Engineers who run Azure SRE Agent and keep their runbooks, or want to keep them, in GitHub. You should be
comfortable with `az`, GitHub Actions and Azure role assignments.

## Solution at a glance

Documents in Azure DevOps: try the Documentation connector first (📄, not tested by us). Documents on GitHub: these four
steps.

1. **Hand uploads are the start.** Upload a few files in the portal to see the agent use them. 📄
2. **Git is the source.** Move the documents into a repository of their own, `docs/runbooks/`, changed through pull
   requests.
3. **Code Access is not the bridge.** It is the only way to connect a GitHub repository in the portal today ✅, and in our lab
   it let the agent read the repository but did not put the documents into the knowledge base (next section). ✅
4. **A script and a pipeline are the bridge.** `tools/sre_kb_sync.py` uploads new and changed files, deletes removed
   ones and waits for the indexer, through the public data-plane API; a GitHub Actions workflow runs it on every merge. ✅

The [architecture](#architecture) shows the request path; the [steps](#steps) build it.

## Code Access lets the agent read the repository; it does not make it knowledge

Microsoft Learn describes two places to connect a repository: **Builder > Code Access**, which gives the agent code
search and file reads, and an **Add repository** card under **Builder > Knowledge base**, which connects a repository "so
your agent can index it as a knowledge source". 📄 In the portal, as of October 2026, there is no such card: a GitHub
repository connects only through Code Access. ✅ So Code Access is the path that matters, and the one we tested. We connected our
repository through it, by the agent's API rather than the portal. ✅

"Connecting a repository" can mean two different things:

- **The agent can read the repository.** The repository is cloned into the agent's workspace, and the agent searches
  the files with its file tools. ✅
- **The documents are indexed as knowledge.** They are listed in the knowledge base, indexed for semantic search 📄, and
  memory search finds and cites them ✅ (see [Verification](#verification)). An upload does this.

We tested which one a repository connected through Code Access gets, on 2026-10-06, with a fresh agent and a private repository carrying
unique "canary" strings (made-up facts the model cannot know from anywhere else):

- Right after the repository was connected, the knowledge base file list was **empty**. The repository was cloned into
  the agent's workspace instead. ✅
- We asked the agent, twice, to search **only its knowledge base** for a canary that exists only in the repository.
  Both times it answered "Memory Search: found 0 relevant results". ✅
- When we asked the same question in plain words, it found the answer with **Grep Search** over the cloned files and
  linked the file and line on GitHub. ✅

So in our lab a repository connected through Code Access was readable as **files**; its documents were not indexed **as knowledge**. ✅
If you want your runbooks in the knowledge base, with citations
from memory search, something has to upload them. That something is the script and the pipeline below.

{{< alert icon="triangle-exclamation" >}}
If you connect a repository through Code Access anyway, give it a **fine-grained token for that one repository, read-only
(Contents: Read)**. In our lab the token was stored in plain text inside the agent's sandbox, in the clone's git
credentials, and the agent could read it and use it on its own. ✅ Treat it as visible to anyone who can chat with the
agent.
{{< /alert >}}

## Prerequisites

| Area | Requirement | |
|---|---|---|
| SRE Agent | A running agent with agent memory enabled (our new agent needed no change) | ✅ |
| Azure roles | Someone with **Owner** on the agent's resource group (or **Contributor** plus **User Access Administrator**), once, to create the CI identity and assign its role | 📄 |
| CI identity | A user-assigned managed identity with a GitHub federated credential; **SRE Agent Administrator** on the agent | ✅ |
| GitHub | A repository with Actions enabled; permission to set repository variables | ✅ |
| Admin machine | Azure CLI signed in; Python 3 with `azure-identity` and `requests` for a local dry run. zsh or PowerShell | ✅ zsh / 📄 PowerShell |

Uploading knowledge documents needs **SRE Agent Standard User**; deleting them needs **SRE Agent Administrator**, so
the sync identity gets Administrator. 📄 Without a role on the agent, our data-plane calls returned
`403 Forbidden: Access denied by PDP`. ✅

## Architecture

{{< mermaid >}}
flowchart LR
  DEV["Engineer"] -- "1 pull request, review, merge" --> GH["GitHub repo<br/>docs/runbooks/**"]
  GH -- "2 push to main (docs/**)" --> GA["GitHub Actions<br/>knowledge-sync"]
  GA -- "3 OIDC token" --> ENTRA["Entra ID<br/>federated credential on<br/>user-assigned MI"]
  ENTRA -- "4 token for https://azuresre.dev" --> GA
  GA -- "5 upload / delete / status<br/>data plane, HTTPS" --> AG["SRE Agent<br/>knowledge base"]
  AG -- "6 memory search, citations" --> CHAT["Chat and incidents"]
{{< /mermaid >}}

1. Runbooks should change only through pull requests (protect `main`), so they get review and history. This is our
   recommendation; our demo repository took direct pushes to `main`.
2. A push to `main` that touches `docs/**` starts the job. ✅
3. and 4. The job exchanges GitHub's OIDC token for an Entra token for the identity, then asks for a token with the
   audience `https://azuresre.dev`. No client secret exists. ✅
5. The script uploads new and changed files, deletes removed ones, and waits for the indexer. ✅
6. In chat the agent finds the content with memory search and cites the document. ✅

**Trust boundary.** The CI identity holds exactly one role assignment: SRE Agent Administrator on this agent. It has no
role on any Azure resource, and the job logs in with `allow-no-subscriptions`. ✅ The role is broad on the agent itself:
it also manages skills, hooks, connectors and scheduled tasks. 📄 Protect the workflow file and the `main` branch
accordingly.

## Steps

At a glance: (1) lay out the repository, with a `.kbignore` for paths that stay out of the knowledge base; (2) create
the CI identity, a managed identity with a GitHub federated credential and one role on the agent; (3) add the sync
script; (4) try it locally with `--dry-run`; (5) add the workflow that runs it.

### 1. Lay out the repository

```text
docs/runbooks/
  payments-db-failover.md
  payments-refund-replay.md
  payments-latency.md
  storage-latency.md
  network-dns-failover.md
  only-in-repo/...          (excluded through .kbignore, never uploaded)
tools/sre_kb_sync.py
.kbignore
.github/workflows/knowledge-sync.yml
```

Why `payments-latency.md` and `storage-latency.md` sit side by side instead of in `payments/` and `storage/` folders:
the knowledge base keeps only the file name. Learn describes it for uploads from a folder: the folder hierarchy is not
kept (`runbooks/networking/dns-troubleshooting.md` appears as `dns-troubleshooting.md`), and uploading a file with an
existing name replaces the old document. 📄 So `payments/latency.md` and `storage/latency.md` would both become
`latency.md`, and the second upload would replace the first. The sync script sends only the file name and refuses to run
when two files share one. 📄 (the script below; we did not trigger it) Give every runbook a name that is unique across
the whole folder. A folder is fine for files that never reach the knowledge base, such as `only-in-repo/`.

`.kbignore` lists path prefixes that stay in git but never reach the knowledge base, one per line:

```text
# Paths under docs/runbooks that are never uploaded to the knowledge base (prefix match).
docs/runbooks/only-in-repo/
```

### 2. Create the CI identity

An administrator with Owner on the resource group (or Contributor plus User Access Administrator) runs these commands
once. 📄 **What the
identity gets** is one thing: SRE Agent Administrator on this one agent. No Entra app registration and no secret are
created.

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
Some GitHub organizations send the newer OIDC subject that includes numeric IDs:
`repo:<org>@<org-id>/<repo>@<repo-id>:ref:refs/heads/main`. Ours did. ✅ The first run then fails with `AADSTS700213`, and
the error message prints the exact subject GitHub presented; copy it into the federated credential.
{{< /alert >}}

Store three **repository variables** (not secrets; none of them is sensitive): `AZURE_CLIENT_ID` (the identity's client
ID), `AZURE_TENANT_ID` and `SRE_AGENT_ENDPOINT`. Read the client ID and the endpoint once:

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

The job reads the endpoint from a variable instead of ARM, so the identity needs no Reader role. ✅

### 3. Add the sync script

This started as a four-call bash snippet we ran by hand: read the agent endpoint from ARM, get a token for
`https://azuresre.dev`, upload the files as multipart, check the indexer.

```bash
SUB=<sub>   # RG and AGENT as in step 2
ENDPOINT=$(az resource show \
  --ids /subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.App/agents/$AGENT \
  --api-version 2025-05-01-preview --query properties.agentEndpoint -o tsv)
TOKEN=$(az account get-access-token --resource https://azuresre.dev --query accessToken -o tsv)
curl -X POST "$ENDPOINT/api/v1/agentmemory/upload" -H "Authorization: Bearer $TOKEN" \
  -F "files=@docs/runbooks/payments-db-failover.md" -F "files=@docs/runbooks/network-dns-failover.md"
curl "$ENDPOINT/api/v1/agentmemory/indexer-status" -H "Authorization: Bearer $TOKEN"
```

The paths follow the layout in step 1; our demo ran this snippet with the old subfolder paths
(`payments/db-failover.md`, `network/dns-failover.md`).

That is enough for one upload. It does not remove a runbook you deleted, and it does not stop two files with the same
name from overwriting each other. `tools/sre_kb_sync.py` is the same four calls, extended:

- **Auth** through `DefaultAzureCredential`: `az login` on your machine, OIDC in GitHub Actions, managed identity
  elsewhere. No token or secret is printed: the output is file names, counts, HTTP codes, the indexer status and, on an error,
  the first 300 characters of the response body. 📄 (the script below)
- **Endpoint** from `--endpoint`, or from ARM with `--subscription`, `--resource-group` and `--agent`. ✅
- **Recursive walk** of the folder, `.md` and `.txt` only, `.kbignore` applied. ✅ Duplicate base names rejected,
  16 MB per file, uploads batched below the 100 MB request limit. 📄 (limits: Learn; the rest: the script below)
- **`--git-base`**: uploads only what changed since that commit and deletes what was removed. Without it, every file is
  uploaded (same name replaces). ✅
- **`--prune`**: also deletes documents that are not in the folder. Use it only when git owns the whole knowledge base;
  it would remove documents the agent saved from chat. 📄
- **Waits** until every uploaded file shows as indexed and the indexer has run. ✅ It fails after a timeout. 📄 (the
  script below)
- **`--dry-run`** prints the plan and changes nothing. ✅

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

### 4. Try it locally first

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

The sample shows the repository before the Verification tests below: it still held `payments/api/latency.md`, which
the Delete test removed, and not yet `network/dns-failover.md`, which the Add test created. ✅ Our demo repository still
used subfolders (each file name unique), so the paths in this sample and in the Verification table are the recorded
ones and differ from the layout in step 1.

For a real run (without `--dry-run`), your own account needs SRE Agent Administrator on the agent ✅, and read access to
the agent resource if you resolve the endpoint from ARM. 📄

### 5. Add the workflow

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

A push-triggered run uses the commit range of that push, so only changed files are sent. ✅ A manual run
(`workflow_dispatch`) uploads the whole folder, which is how you seed a new agent. `fetch-depth: 0` is needed for the
diff. `concurrency` keeps two merges from syncing at the same time. 📄 (the workflow above)

## Verification

We proved each case with a canary string in the runbook, then asked the agent in a new chat to use **only** its
knowledge base. A canary is a made-up fact ("the failover owner is the violet rota") that the model cannot know from
anywhere else, so if it shows up, it came from the document. ✅

| Case | What the job logged | What the agent answered from memory search | |
|---|---|---|---|
| First sync | `upload 3 file(s) -> HTTP 200`, indexer `Success, processed 3, failed 0`; a runbook two folders deep included | All three canaries, each with its document | ✅ |
| Add a runbook | `upload 1, delete 0` and `+ docs/runbooks/network/dns-failover.md` | The new canary and its approver | ✅ |
| Change a runbook | `upload 1` for the edited file only | The new owner and the `-v2` canary; the old answer was gone | ✅ |
| Delete a runbook | `upload 0, delete 1`, `delete latency.md -> HTTP 200` | "No document contains" the deleted canary | ✅ |
| Excluded path | nothing uploaded from `only-in-repo/` | "Not in any knowledge document" | ✅ |

Each run took 26 to 34 seconds end to end; the sync step itself 6 to 20 seconds, indexing included. ✅

To check the state yourself:

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

In the portal the same files appear under **Builder > Knowledge base** with status **Indexed**. 📄 In chat, a tool card
reads `Memory Search: Found 1 relevant results` and the answer names the document. ✅

## A note on srectl

Microsoft's samples mention an SRE Agent CLI, `srectl`, including a `srectl doc upload` command. 📄 It is not publicly
released yet, so this post uses only the public data-plane API, which anyone can call today.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AADSTS700213: No matching federated identity record found for presented assertion subject 'repo:<org>@<id>/…'` | The organization sends the newer OIDC subject with numeric IDs | Copy the subject from the error into the federated credential ✅ |
| `403 Forbidden: Access denied by PDP` on every data-plane call | The caller lacks SRE Agent Administrator on the agent, or the assignment has not taken effect yet | Assign the role on the agent resource ✅; a new assignment can take up to 10 minutes 📄 |
| `azure/login` fails with "No subscriptions found" | The identity has no Azure resource role, by design | `allow-no-subscriptions: true` 📄 |
| `DELETE …/agentmemory/document/<name>` returns `500 Failed to delete document`, but the document is gone | Seen once in our lab | The script re-reads the file list and accepts the delete if the document is no longer listed ✅ |
| A runbook was deleted in git but the agent still answers from it | The sync only uploads; nothing deletes | Run with `--git-base` (the workflow does) ✅ or `--prune` 📄 |
| `two or more files share a base name` | The knowledge base is flat | Rename one file 📄 |
| `Agent memory is disabled. Cannot upload documents.` | Knowledge is turned off on the agent | Turn it on in the agent settings 📄 |


## Beyond knowledge: skills for weekly procedures

Knowledge is searched when the agent decides to search. A **skill** is different: its description sits in the agent's
instructions and the agent loads the skill itself when the task matches. 📄 We put the same refund procedure in both
places, with different canaries, and asked five differently worded questions in five new chats. The agent used the
**skill all five times** and the knowledge document never; it did not even run a memory search. ✅ Five questions are a
small sample, not a benchmark, but the result matches what the documentation describes. So the two or three
procedures your on-call uses every week may be better kept as skills, versioned in the same repository; the rest stays
in the knowledge base. We created the skill on the agent ✅, through `PUT {endpoint}/api/v2/extendedAgent/skills/<name>` 📄;
syncing skills from CI follows the same pattern and is not covered here.

## What we learned

- Uploading files by hand is how knowledge gets into SRE Agent today, and it is fine for a start. 📄 Once the
  documents change, git is the better home for them. On GitHub there is no built-in way to make them knowledge: a
  GitHub repository connects only through Code Access. ✅ On Azure DevOps, the Documentation connector is the built-in
  path 📄; we have not tested it.
- In our lab, a repository connected through Code Access was readable as files; it was not indexed as knowledge.
  Memory search returned nothing for it until the pipeline uploaded the files. ✅
- A short script on the public data-plane API is enough for a full sync: upload, list, delete and indexer status.
  Run from a pipeline, adds, edits and deletes reached the agent 26 to 34 seconds after the merge. ✅
- Deletes are the part a plain upload loop forgets. Drive them from the git diff, and verify against the file list,
  because the delete call itself can report a failure that did not happen. ✅
- The knowledge base is flat. Unique file names are a rule, not a style choice. 📄
- The pipeline's identity needs one role on one agent and no secret: a managed identity with a federated credential. ✅

Keep the documents in their own repository, review them like code, and let the pipeline carry every merge into the
agent's knowledge. If SRE Agent gets a built-in git sync for knowledge later, the script is the part you replace; the
repository stays.
