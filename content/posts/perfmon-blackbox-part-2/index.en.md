---
title: "A black box for Windows servers, part 2: set it up and know what it costs"
description: "A PerfMon flight recorder on every Windows server, deployed by Azure Policy and Machine Configuration with nothing installed, uploading to private storage with the server's own identity. The setup at release v1.0.1, what a fresh install took, and what it costs."
date: 2026-10-14
draft: false
series: ["A black box for Windows servers"]
series_order: 2
tags: ["azure-sre-agent", "azure-policy", "machine-configuration", "azure-arc", "perfmon"]
showTableOfContents: true
---

[Part 1]({{< relref "/posts/perfmon-blackbox-part-1" >}}) began with a server that slowed down at 03:10 and left no trace by morning. Without performance data
from that moment, the root cause is a guess. Azure SRE Agent, Microsoft's AI agent for operations, can investigate
such a moment, but only if the data exists. This part makes sure it does.

This series builds a **black box for Windows servers**: a flight recorder that is always on, keeps the recent past on
the disk, and hands it over when someone asks. It has four parts, and they tell one story:

1. **[Part 1]({{< relref "/posts/perfmon-blackbox-part-1" >}}): why a black box.** Data collected only after the problem costs time and work; a recorder that is
   already running, and an expert who can read it, do not.
2. **Part 2 (this post): set it up.** Azure Policy and Machine Configuration put the recorder on every server, and the
   data moves to private storage. Step by step, with what it costs.
3. **[Part 3]({{< relref "/posts/perfmon-blackbox-part-3" >}}): inside the machine.** How the recording is kept on the server, what happens on a restart or a full disk,
   and how the server uploads with its own identity.
4. **[Part 4]({{< relref "/posts/perfmon-blackbox-part-4" >}}): the agent investigates.** Azure SRE Agent reads a capture and explains what made the server hard to use.

Everything here comes from a public playbook,
[VezirOrg/sreagent-playbook, `playbooks/perfmon-blackbox`](https://github.com/VezirOrg/sreagent-playbook/tree/perfmon-blackbox/v1.0.1/playbooks/perfmon-blackbox),
at release **[perfmon-blackbox/v1.0.1](https://github.com/VezirOrg/sreagent-playbook/releases/tag/perfmon-blackbox/v1.0.1)**.

✅ = proven in our lab · 📄 = documented only (Microsoft Learn, the playbook's docs, Azure prices), not tested by us.
🔎 = seen on an install outside our lab, not re-run by us.
Every admin-machine command comes in two tabs. We ran the zsh one, as the playbook writes it. ✅ The PowerShell tab is
our translation for Windows and was not run by us; it uses Windows PowerShell 5.1 or PowerShell 7. 📄

## Goal and audience

**Goal.** At the end, every Windows server in a scope records a PerfMon log all the time. Every few hours it uploads
the recent window, as a zip, into its own folder of a private storage account. Your SRE Agent has a skill that can
read those zips. Nothing from us is installed on the servers.

**Audience.** Azure administrators and SREs who run Windows servers on Azure VMs or as Arc-enabled servers. You
should know Azure Policy assignments and role assignments, and be able to run the Azure CLI. You do not need to know
Machine Configuration: the post explains the part you need.

## Prerequisites

| What | Why | |
|---|---|---|
| Windows Server 2016 or later | the recorder uses only Windows' own tools: Windows PowerShell 5.1, `logman`, `relog`, `schtasks` | 📄 (we ran Windows Server 2022 ✅) |
| Azure VMs: the built-in initiative *Deploy prerequisites to enable Guest Configuration policies on virtual machines* | gives each VM a system-assigned identity and the Machine Configuration extension | ✅ |
| Arc-enabled servers: Connected Machine agent 1.10 or later | it brings Machine Configuration and the identity | 📄 (we ran 1.68 ✅) |
| A private endpoint for the storage, resolvable from the servers | uploads go to `<account>.blob.core.windows.net` over the private endpoint, port 443 | ✅ |
| **VNet integration on the SRE Agent**, resolving the same private endpoint | without it the skill cannot read a single capture | ✅ |
| Deployer rights: **Owner on the subscription** | the policy definitions need Owner or Resource Policy Contributor at **subscription** scope; the assignments and their role grants need Owner, or Resource Policy Contributor + User Access Administrator, on the machines' resource group and on the storage; resource-group Owner alone is not enough, and Contributor + Role Based Access Control Administrator cannot create definitions or assignments ([deploy.md, prerequisites](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md#prerequisites); [Learn](https://learn.microsoft.com/azure/governance/policy/overview#azure-rbac-permissions-in-azure-policy)) | 📄 |
| On the admin machine: Azure CLI, Python 3, git; on Windows also a bash (Git Bash or WSL) | Python generates the policy definitions; the skill upload is a bash script | ✅ |

## The black box in brief

[Part 1]({{< relref "/posts/perfmon-blackbox-part-1" >}}) walks through the whole flow diagram; here is the short version. On every server a **circular binary
PerfMon log** (the playbook calls it the *ring*) is always running: 512 MB and one sample every 10 seconds by default,
and since the newest data overwrites the oldest, the disk cannot fill up. 📄 Every few hours (every 4 by default) the
server exports everything since its last export, a CSV and a manifest that names every gap, in one zip, and uploads it
with **its own managed identity** into **its own folder** of a private storage account. The SRE Agent reads it from
there when you ask. ✅ Azure Policy and Machine Configuration put the recorder on each server and keep it there; nothing
of ours is installed. 📄 How the recording works inside the server is [part 3]({{< relref "/posts/perfmon-blackbox-part-3" >}}).

**The setup at a glance.** (1) A private storage account with no keys and no public access. (2) Two policy
definitions that carry the package. (3) Assignments with exactly the rights they need, then a remediation. (4) The
analysis skill on your SRE Agent.

## Our lab

We ran the setup on three servers. The names in the screenshots are the lab's own:

- **dc** and **iis1**: Azure VMs with Windows Server 2022. The playbook's docs call the IIS server `vm1`; it is the
  same role as our iis1.
- **arc1**: an Arc-enabled server. To test the Arc path without an on-premises machine, it is an Azure VM prepared as
  Learn's *Evaluate Azure Arc-enabled servers on an Azure VM* describes. Its Azure metadata endpoint (IMDS) is blocked, so
  it really uploads through the Arc agent's endpoint (HIMDS).

All three received the package from a container in our own storage (the playbook's "storage mode", step 2b below),
so the servers needed no internet access for it. ✅ The other mode, the package straight from the GitHub release, was
tested by the playbook on an Azure VM and on an Arc-enabled server (its tests T20b and T20d). 📄

## Set it up, step by step

The reference is the release's deployment guide,
[deploy.md at v1.0.1](https://github.com/VezirOrg/sreagent-playbook/blob/perfmon-blackbox/v1.0.1/playbooks/perfmon-blackbox/docs/deploy.md).
This is its path for one subscription, shortened. Placeholders are in `<…>`.

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
git clone --branch perfmon-blackbox/v1.0.1 https://github.com/VezirOrg/sreagent-playbook.git
cd sreagent-playbook/playbooks/perfmon-blackbox
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
git clone --branch perfmon-blackbox/v1.0.1 https://github.com/VezirOrg/sreagent-playbook.git
cd sreagent-playbook/playbooks/perfmon-blackbox
```
{{< /tab >}}
{{< /tabs >}}

### Step 0: Machine Configuration prerequisites (Azure VMs, once per scope)

An operator with Owner on the subscription runs this. The
initiative's own identity gets Contributor on the scope, as the playbook says; it needs it to add the identity and the
extension to each VM.

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
prereq=$(az policy set-definition list --query "[?displayName=='Deploy prerequisites to enable Guest Configuration policies on virtual machines'].name | [0]" -o tsv)
az policy assignment create -n gc-prereq --policy-set-definition "$prereq" --scope <scope> --mi-system-assigned --location <region>
pp=$(az policy assignment show -n gc-prereq --scope <scope> --query identity.principalId -o tsv)
az role assignment create --assignee-object-id $pp --assignee-principal-type ServicePrincipal --role Contributor --scope <scope>
for ref in $(az policy set-definition show -n "$prereq" --query "policyDefinitions[].policyDefinitionReferenceId" -o tsv); do
  az policy remediation create -n "gc-prereq-$ref" --policy-assignment gc-prereq --definition-reference-id "$ref" -g <rg> \
    --resource-discovery-mode ReEvaluateCompliance
done
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
$prereq = az policy set-definition list --query "[?displayName=='Deploy prerequisites to enable Guest Configuration policies on virtual machines'].name" -o tsv |
  Select-Object -First 1
az policy assignment create -n gc-prereq --policy-set-definition $prereq --scope <scope> --mi-system-assigned --location <region>
$pp = az policy assignment show -n gc-prereq --scope <scope> --query identity.principalId -o tsv
az role assignment create --assignee-object-id $pp --assignee-principal-type ServicePrincipal --role Contributor --scope <scope>
foreach ($ref in (az policy set-definition show -n $prereq --query "policyDefinitions[].policyDefinitionReferenceId" -o tsv)) {
  az policy remediation create -n "gc-prereq-$ref" --policy-assignment gc-prereq --definition-reference-id $ref -g <rg> `
    --resource-discovery-mode ReEvaluateCompliance
}
```
{{< /tab >}}
{{< /tabs >}}

`--resource-discovery-mode ReEvaluateCompliance` matters. A new assignment has no compliance results yet, so a plain
remediation finds nothing: it says "Succeeded" with 0 deployments. ✅ In our lab the extension was on the VM about
20 minutes after the start. ✅ Arc-enabled servers skip this step.

### Step 1: The private storage

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az deployment group create -g <storage-rg> -f infra/main.bicep \
  -p storageAccountName=<name> \
     privateEndpointSubnetId=<an ordinary subnet for private endpoints, not a delegated one> \
     blobPrivateDnsZoneId=<resource ID of privatelink.blob.core.windows.net> \
     readerPrincipalIds='["<agent system identity object ID>","<agent user-assigned identity object ID>"]'
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
'["<agent system identity object ID>","<agent user-assigned identity object ID>"]' | Set-Content reader-ids.json
az deployment group create -g <storage-rg> -f infra/main.bicep `
  -p storageAccountName=<name> `
     privateEndpointSubnetId=<an ordinary subnet for private endpoints, not a delegated one> `
     blobPrivateDnsZoneId=<resource ID of privatelink.blob.core.windows.net> `
     readerPrincipalIds=@reader-ids.json
```
{{< /tab >}}
{{< /tabs >}}

The agent's two identity object IDs are in the portal on the agent resource (Identity), or come from
`az resource show --ids <agent resource ID> --query identity`. 📄

You get a storage account with **no shared key**, **public network access disabled** and TLS 1.2; the container
`perfmon` with a 30-day lifecycle rule; the private endpoint; two custom roles (*PerfMon Blackbox Writer*, *PerfMon
Blackbox Deployer*); and read access on the container for both agent identities. ✅ It took about 2 minutes. ✅
Keep three outputs: `storageAccountResourceId`, `writerRoleDefinitionId` and, for storage mode,
`packageContainerResourceId`.

![Storage account, Networking: public network access Disabled](img/storage-public-access.png)

### Step 2: The policy definitions

The release notes give the package's URL and its SHA-256:

| | |
|---|---|
| package | `https://github.com/VezirOrg/sreagent-playbook/releases/download/perfmon-blackbox%2Fv1.0.1/PerfmonBlackbox.zip` |
| SHA-256 | `806BCADB69F556401DE19754AEB649B7611EB1AE18AA106A5BF0A537A99363DD` |
| `--version` | `1.0.1` |

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
python3 policy/build_policies.py --content-uri <package URL> --content-hash <sha256> --version 1.0.1 --out policy/out
p() { python3 -c 'import json,sys; v=json.load(open(sys.argv[1]))["properties"][sys.argv[2]]; print(v if isinstance(v,str) else json.dumps(v))' "$1" "$2"; }
for kind in vm arc; do
  f=policy/out/perfmon-blackbox-$kind.json
  az policy definition create -n perfmon-blackbox-$kind --mode Indexed --display-name "$(p $f displayName)" \
    --rules "$(p $f policyRule)" --params "$(p $f parameters)" --metadata "$(p $f metadata)"
done
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
python policy/build_policies.py --content-uri <package URL> --content-hash <sha256> --version 1.0.1 --out policy/out
foreach ($kind in 'vm', 'arc') {
  $f = "policy/out/perfmon-blackbox-$kind.json"
  python -c "import json,sys; d=json.load(open(sys.argv[1]))['properties']; [json.dump(d[k],open(sys.argv[2]+'-'+k+'.json','w')) for k in ('policyRule','parameters','metadata')]" $f $kind
  $name = (Get-Content $f -Raw | ConvertFrom-Json).properties.displayName
  az policy definition create -n "perfmon-blackbox-$kind" --mode Indexed --display-name $name `
    --rules "@$kind-policyRule.json" --params "@$kind-parameters.json" --metadata "@$kind-metadata.json"
}
```
{{< /tab >}}
{{< /tabs >}}

`-vm` targets Azure VMs, `-arc` Arc-enabled servers; create only what you need. **Pass all four parts**: rules,
parameters, metadata and display name. Machine Configuration builds each server's guest assignment from the
definition's `metadata.guestConfiguration`, so without the metadata storage mode does not work. ✅ 📄

### Step 2b: The package from your own storage (optional)

In **storage mode** the servers download the same zip from a container in your private storage, with their own
identity, and need no internet for the package. Copy the release zip unchanged into the `packages` container (the
hash pins it), then generate the `-storage` definitions:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
curl -sL -o PerfmonBlackbox.zip <package URL>
shasum -a 256 PerfmonBlackbox.zip            # must equal the SHA-256 above
# from a host inside the network, whose identity has Storage Blob Data Contributor on the packages container:
az storage blob upload --auth-mode login --account-name <account> -c packages -n PerfmonBlackbox.zip -f PerfmonBlackbox.zip --overwrite
python3 policy/build_policies.py --content-uri <package URL> --content-hash <sha256> --version 1.0.1 \
  --package-container-id <packageContainerResourceId> --out policy/out
# then create perfmon-blackbox-vm-storage / -arc-storage as in step 2 (name = file name)
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
Invoke-WebRequest -Uri <package URL> -OutFile PerfmonBlackbox.zip
(Get-FileHash PerfmonBlackbox.zip -Algorithm SHA256).Hash   # must equal the SHA-256 above
# from a host inside the network, whose identity has Storage Blob Data Contributor on the packages container:
az storage blob upload --auth-mode login --account-name <account> -c packages -n PerfmonBlackbox.zip -f PerfmonBlackbox.zip --overwrite
python policy/build_policies.py --content-uri <package URL> --content-hash <sha256> --version 1.0.1 `
  --package-container-id <packageContainerResourceId> --out policy/out
# then create perfmon-blackbox-vm-storage / -arc-storage as in step 2 (name = file name)
```
{{< /tab >}}
{{< /tabs >}}

Run the upload from inside the network: the account has no public access, so a laptop or a hosted CI runner cannot
reach it. `main.bicep` grants nobody write access on `packages`; you grant it to that host. In our lab, dc's identity
got Storage Blob Data Contributor on `packages` only. ✅ The Machine Configuration agent must be 1.29.98.0 or later
for this. On an Azure VM, read the version from the folder name under
`C:\Packages\Plugins\Microsoft.GuestConfiguration.ConfigurationforWindows\` (ours: 1.29.119.0); the extension's
`typeHandlerVersion` (1.1) is the handler, not the agent. ✅

{{< alert icon="triangle-exclamation" >}}
**Never assign both modes over the same machine.** Both write the same guest assignment, `PerfmonBlackbox`, and keep
overwriting each other. To switch, remove the old assignment and its role assignments first. 📄
{{< /alert >}}

### Step 3: Assign, grant, remediate

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az policy assignment create -n pbb-vm --policy perfmon-blackbox-vm --scope <scope> \
  --mi-system-assigned --location <region> \
  --params '{"StorageAccountResourceId":{"value":"<storageAccountResourceId>"},
             "WriterRoleDefinitionId":{"value":"<writerRoleDefinitionId>"}}'
pid=$(az policy assignment show -n pbb-vm --scope <scope> --query identity.principalId -o tsv)
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
@'
{"StorageAccountResourceId":{"value":"<storageAccountResourceId>"},
 "WriterRoleDefinitionId":{"value":"<writerRoleDefinitionId>"}}
'@ | Set-Content pbb-params.json
az policy assignment create -n pbb-vm --policy perfmon-blackbox-vm --scope <scope> `
  --mi-system-assigned --location <region> --params "@pbb-params.json"
$mi = az policy assignment show -n pbb-vm --scope <scope> --query identity.principalId -o tsv
```
{{< /tab >}}
{{< /tabs >}}

Storage mode uses `--policy perfmon-blackbox-vm-storage` and its own name (we used `pbb-vm-storage` and
`pbb-arc-storage`). The numeric parameters are **strings**: `{"ExportEveryHours":{"value":"1"}}`. A JSON number fails
with `InvalidPolicyParameterType`. ✅ We set `ExportEveryHours` to `"1"` to see a zip within the hour; the default is 4.

![The assignment's parameters on arc1's policy: MaxSizeMB 512, SampleIntervalSeconds 10, ExportEveryHours 1, ContainerName perfmon, LocalKeepMB 1024, Effect DeployIfNotExists](img/assignment-parameters.png)

**Who gets which rights.** You, the operator, create the assignment. Its **identity** gets exactly four roles:

- *Guest Configuration Resource Contributor* and *Reader* on the scope,
- *PerfMon Blackbox Deployer* on the storage resource group,
- *Role Based Access Control Administrator* on the storage account, **with a condition**: it may hand out only the
  Writer role (and, in storage mode, the built-in blob reader on the package container).

The four commands, as deploy.md step 3 gives them: ✅

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az role assignment create --assignee-object-id $pid --assignee-principal-type ServicePrincipal \
  --role "Guest Configuration Resource Contributor" --scope <scope>
az role assignment create --assignee-object-id $pid --assignee-principal-type ServicePrincipal \
  --role Reader --scope <scope>
az role assignment create --assignee-object-id $pid --assignee-principal-type ServicePrincipal \
  --role "PerfMon Blackbox Deployer" --scope <storage resource group ID>
w=<last segment of writerRoleDefinitionId>
az role assignment create --assignee-object-id $pid --assignee-principal-type ServicePrincipal \
  --role "Role Based Access Control Administrator" --scope <storageAccountResourceId> --condition-version 2.0 \
  --condition "((!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {$w, 2a2b9908-6ea1-4ae2-8e65-a410df84e7d1})) AND ((!(ActionMatches{'Microsoft.Authorization/roleAssignments/delete'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {$w, 2a2b9908-6ea1-4ae2-8e65-a410df84e7d1}))"
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az role assignment create --assignee-object-id $mi --assignee-principal-type ServicePrincipal `
  --role "Guest Configuration Resource Contributor" --scope <scope>
az role assignment create --assignee-object-id $mi --assignee-principal-type ServicePrincipal `
  --role Reader --scope <scope>
az role assignment create --assignee-object-id $mi --assignee-principal-type ServicePrincipal `
  --role "PerfMon Blackbox Deployer" --scope <storage resource group ID>
$w = '<last segment of writerRoleDefinitionId>'
$cond = "((!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {$w, 2a2b9908-6ea1-4ae2-8e65-a410df84e7d1})) AND ((!(ActionMatches{'Microsoft.Authorization/roleAssignments/delete'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {$w, 2a2b9908-6ea1-4ae2-8e65-a410df84e7d1}))"
az role assignment create --assignee-object-id $mi --assignee-principal-type ServicePrincipal `
  --role "Role Based Access Control Administrator" --scope <storageAccountResourceId> --condition-version 2.0 `
  --condition $cond
```
{{< /tab >}}
{{< /tabs >}}

`2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` is the built-in *Storage Blob Data Reader* role, the same in every tenant. If you created the assignment in
the portal, its identity is named after the assignment's internal ID, not its display name: take its object ID from
the assignment's *Managed Identity* tab (Principal ID). Then wait a minute and remediate:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az policy remediation create -n pbb-vm-1 --policy-assignment pbb-vm -g <rg> \
  --resource-discovery-mode ReEvaluateCompliance        # per resource group in scope
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az policy remediation create -n pbb-vm-1 --policy-assignment pbb-vm -g <rg> `
  --resource-discovery-mode ReEvaluateCompliance        # per resource group in scope
```
{{< /tab >}}
{{< /tabs >}}

Repeat for `perfmon-blackbox-arc` (`pbb-arc`). For each server the policy creates the guest assignment
`PerfmonBlackbox` and **one** role assignment of the Writer role. **The server gets no read right on the captures**,
and its write right carries a path condition: it can write only under `<sub>/<rg>/<server>/`. ✅ The playbook's docs say
the server applies the package within about an hour of the remediation (the first cycle only tests, the next one
applies). 📄 In our lab iis1 turned Compliant 31 minutes after the assignment. ✅

### Step 4: The skill on your SRE Agent

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
SRE_AGENT_ID=<agent resource ID> scripts/deploy-skill.sh skill/perfmon-triage            # dry run
SRE_AGENT_ID=<agent resource ID> scripts/deploy-skill.sh skill/perfmon-triage --apply    # create or update
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
# deploy-skill.sh is a bash script; on Windows run it with Git Bash's bash.exe or in WSL
$env:SRE_AGENT_ID = '<agent resource ID>'
bash scripts/deploy-skill.sh skill/perfmon-triage            # dry run
bash scripts/deploy-skill.sh skill/perfmon-triage --apply    # create or update
```
{{< /tab >}}
{{< /tabs >}}

The caller needs **SRE Agent Author** and **SRE Agent Standard User** on the agent; Administrator is not needed. ✅
Learn's page on the SRE Agent MCP server names **SRE Agent Administrator** for skill operations on the data plane;
our upload worked without it. 📄 The
script uses the agent's data-plane API: the ARM resource for skills answered "internal tenants only" in our tenant. ✅
Dry run and apply took 14 seconds, after about 10 minutes of waiting for the role grant to take effect. ✅

![The perfmon-triage skill in the agent's Skill builder, with its four files](img/skill.png)

## Check it

**1. The policy view.** In *Policy → Compliance*, both assignments Compliant: two Azure VMs and one Arc-enabled server. ✅

![Policy compliance: pbb-vm-storage 100% (2 out of 2), pbb-arc-storage 100% (1 out of 1)](img/policy-compliance.png)

**2. The guest assignments.** All three servers, one list, Azure VMs (`Microsoft.Compute`) and Arc
(`Microsoft.HybridCompute`) side by side. ✅

![Guest Assignments filtered to PerfmonBlackbox: dc, iis1 and arc1, all Compliant](img/guest-assignments.png)

Or from the CLI:

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az rest --method get --url "https://management.azure.com<server ID>/providers/Microsoft.GuestConfiguration/guestConfigurationAssignments/PerfmonBlackbox?api-version=2024-04-05" --query properties.complianceStatus
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az rest --method get --url "https://management.azure.com<server ID>/providers/Microsoft.GuestConfiguration/guestConfigurationAssignments/PerfmonBlackbox?api-version=2024-04-05" --query properties.complianceStatus
```
{{< /tab >}}
{{< /tabs >}}

**3. One server in detail.** arc1's guest assignment: configuration version 1.0.1, seven of seven resources
Compliant. The capacity resource writes its estimate as the reason: the 512 MB ring holds about 25.2 hours of
arc1's data, the local buffer about 50.4 hours, with the margin met. ✅ The same check on iis1 gave about 22.4 hours:
the figure depends mostly on the number of processes. ✅ If it did not fit, this resource would turn NonCompliant
before any data was lost. 📄

![arc1's PerfmonBlackbox guest assignment: version 1.0.1, 7 of 7 Compliant, capacity reason](img/guest-assignment-arc1.png)

**4. The first zips.** In the container, one folder per server: ✅

![The perfmon container: one folder per server, arc1, dc and iis1](img/blob-servers.png)

and in arc1's folder for the day, one zip per hour, 168 to 190 KiB each: ✅

![arc1's folder for 2026-10-14: four hourly zips](img/blob-arc1-hourly.png)

The portal lists blobs only from inside the network; we used a browser on a VM in the VNet (through Bastion). From
outside, the account answers with no data at all, which is what you want. ✅

## How the folders are laid out, and why

Every zip lands at:

```text
perfmon/<sub>/<rg>/<server>/yyyy/MM/dd/<server>_<startUTC>_<endUTC>.zip
```

For example `perfmon/<sub>/<rg>/arc1/2026/10/14/arc1_20261014-063918_20261014-070654.zip`. ✅ Each part has a job:

- **`<sub>/<rg>/<server>/` is the server's own prefix**, taken from its resource ID. It is what the Writer role's
  condition checks: a server can write only under its own prefix, never into another server's folder. ✅ The
  subscription and resource group in the path keep two servers with the same name apart. 📄
- **`yyyy/MM/dd/`** keeps a day together: you open one folder and see that day's exports, as in the screenshot above.
- **The file name carries the window**, the first and last sample. The skill picks the newest capture, or the zips
  that cover a time range, from the listing alone, without opening a zip. 📄
- The 30-day lifecycle rule deletes old zips by age, whatever the path. 📄

## What it costs

Prices are retail USD from the [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices),
queried **2026-10-14**, region **Sweden Central** where the price depends on the region. Your agreement may differ. 📄

**The recorder, per server and per deployment:**

| Item | Price | What it means here |
|---|---|---|
| Machine Configuration on an **Azure VM** | included | 0 📄 |
| Machine Configuration on an **Arc-enabled server** (meter "Guest Configuration Policy/Server") | 6.00 USD per server per month | **6.00 USD per Arc server** 📄 |
| Blob storage, Hot LRS | 0.0184 USD per GB per month | about 0.5 GB held per server under the 30-day rule → **about 0.01 USD per server** (0.03 USD for a busy server) |
| Private endpoint (Standard) | 0.01 USD per hour | **about 7.30 USD a month per deployment**, shared by all servers 📄 |
| Write operations, private endpoint data | 0.05 USD per 10,000 writes; 0.01 USD per GB | under 0.01 USD per server 📄 |

The storage volume is the playbook's measurement: about 1.9 KB per sample at around 117 processes and a 10-second
interval, which is about 16 MB a day per server. 📄 Our arc1 zips, 168 to 190 KiB per hour, fit that. ✅

**The SRE Agent** is billed in Azure Agent Units (AAU) ([Learn: pricing and billing](https://learn.microsoft.com/azure/sre-agent/pricing-billing)): 📄

| Part | Rate | USD (0.11 per AAU in Sweden Central) |
|---|---|---|
| Always-on flow, from creation until the agent is deleted | 4 AAU per agent-hour | about 0.44 an hour, **about 321 a month** |
| Active flow: the work, for example one analysis | AAU per million tokens, by model | see below |

The always-on cost belongs to the agent, not to the black box: one agent per environment serves this alongside its
other work. New customers can evaluate the agent for 30 days without the always-on charge. 📄

**One deep-dive analysis.** In our lab, three deep-dive analyses of a capture (two of them on a deliberately staged
load; part 4 shows one openly) each used about 35 AAU. ✅ Learn's own example for an "incident investigation" is about
35.3 AAU. 📄

So **one deep-dive analysis costs roughly 3.5 to 5 USD, depending on region**: about 3.9 USD in Sweden Central
(35 × 0.11). The price per AAU ("SRE Agent Unit", Retail Prices API, 2026-10-14): 📄

| Regions (examples) | USD per AAU | One analysis (about 35 AAU) |
|---|---|---|
| East US, East US 2, West US 2, Central US | 0.10 | about 3.5 USD |
| Sweden Central, UK South, Australia East | 0.11 | about 3.9 USD |
| West Europe, North Europe | 0.136 | about 4.8 USD |

**A worked example**, per month, Sweden Central:

| | 10 servers | 100 servers |
|---|---|---|
| Azure VMs: Machine Configuration | 0 | 0 |
| Arc-enabled servers instead: Machine Configuration | 60.00 USD | 600.00 USD |
| Storage (0.01 to 0.03 USD per server) | 0.10 to 0.30 USD | 1 to 3 USD |
| Private endpoint (one per deployment) | 7.30 USD | 7.30 USD |
| **Recorder total, Azure VMs** | **about 7.50 USD** | **about 8 to 10 USD** |
| **Recorder total, Arc-enabled servers** | **about 67.50 USD** | **about 608 to 610 USD** |
| SRE Agent always-on (if you have no agent yet) | about 321 USD | about 321 USD |
| Each deep-dive analysis | about 3.9 USD | about 3.9 USD |

On Azure VMs the recorder costs almost nothing; the private endpoint dominates. On Arc, the per-server Machine
Configuration charge dominates, unless your Arc servers are already covered: Windows Server Software Assurance
(attested) or Windows Server pay-as-you-go includes Azure Machine Configuration at no extra cost
([Learn: Windows Server Management enabled by Azure Arc](https://learn.microsoft.com/azure/azure-arc/servers/windows-server-management-overview)). 📄

## Limits

- **This is a community playbook, not a Microsoft product.** It is tested in our lab ([the playbook's
  tests](https://github.com/VezirOrg/sreagent-playbook/blob/perfmon-blackbox/v1.0.1/playbooks/perfmon-blackbox/docs/tests.md));
  read the code before you assign it to production servers.
- **Windows only.** The definitions target Windows Azure VMs and Windows Arc-enabled servers. 📄
- **Names are not local.** The two custom role names are unique in the whole Microsoft Entra tenant, and the policy
  definition names in the subscription. A second deployment needs its own names (deploy.md, "Names"). 📄
- **Removal** is a documented procedure (assignments, role assignments, definitions, custom roles, storage):
  [operations.md, Remove](https://github.com/VezirOrg/sreagent-playbook/blob/perfmon-blackbox/v1.0.1/playbooks/perfmon-blackbox/docs/operations.md#remove). 📄

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Remediation "Succeeded", 0 deployments | a new assignment has no compliance results yet | `--resource-discovery-mode ReEvaluateCompliance` ✅ |
| `InvalidPolicyParameterType` on the assignment | a numeric parameter passed as a JSON number | pass strings: `{"value":"1"}` ✅ |
| Storage mode: the guest assignment points at GitHub, or the download fails | the definition was created without its metadata | create it with `--metadata` and `--display-name` (step 2) ✅ |
| Storage mode: HTTP 403 on the package download right after a switch | the server's reader role on `packages` is not granted yet | wait for the remediation to grant it 📄 |
| The guest assignment stays NonCompliant on `[BlackboxCapacity]` | the ring or the local buffer does not hold the export window with a 1.5× margin | raise `LocalKeepMB` or `MaxSizeMB`, or export more often 📄 |
| The skill cannot list or read a capture | the agent has no VNet integration, or does not resolve the private endpoint | VNet integration with private DNS resolution (prerequisites) 📄 |
| The agent's terminal gets 403 on the container | the reader role went only to the agent's user-assigned identity; the terminal signs in as its system-assigned identity | `readerPrincipalIds` with both identities (step 1) ✅ |

## What a fresh install took

The playbook's second lab was a *fresh-eyes* install: only the README and deploy.md, no prior knowledge. These are the
timings of that install of v1.0.0 on 2026-10-13, on iis1. ✅ v1.0.1 ships the same package (same SHA-256); it changes
the generated policy definitions and the docs. 📄

| Step | Wall time |
|---|---|
| 0 Machine Configuration prerequisites → identity and extension on the VM | about 20 min |
| 1 `main.bicep` | about 2 min |
| 2 and 2b definitions, package into storage | about 1.5 min |
| 3 assignment, roles, remediation → guest assignment Compliant | about 31 min |
| first zip in storage (`ExportEveryHours` = 1) | 29 min after Compliant |
| 4 skill (dry run and apply) | 14 s |
| first answer from the agent | 6 min 57 s |

The install also found seven gaps in the docs. All are fixed in deploy.md and parameters.md at v1.0.1: ✅ 📄

| # | What we hit | Fixed in v1.0.1 |
|---|---|---|
| F1 | a remediation right after a new assignment found 0 resources | `--resource-discovery-mode ReEvaluateCompliance` in step 0 and step 3 |
| F2 | `az policy definition create` passed only the rules and the parameters; the metadata and display name were lost, and storage mode needs the metadata | step 2 passes all four parts |
| F3 | step 2b did not say who may upload the package into a private-endpoint-only account | the upload host and its Blob Data Contributor grant are spelled out |
| F4 | `ExportEveryHours` as a JSON number failed with `InvalidPolicyParameterType` | parameters.md: the numeric parameters are strings |
| F5 | which subnet for the private endpoint, and the third output for storage mode | named in step 1 |
| F6 | the template VMs already had a system identity, only the extension was missing | nothing to fix: the step handles it |
| F7 | the suggested version check returned the extension handler's version (1.1), not the agent's | the version comes from the folder name |

**Six more doc fixes we found** on a second fresh install, outside our lab. We did not re-run them. Learn documents
D1 and D4 📄, we saw D5 in our own lab ✅, and D2, D3 and D6 come from that install only 🔎. The playbook's deploy.md
now covers all six ([on main](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md)).

| # | What the install hit | What to do |
|---|---|---|
| D1 | creating the policy definitions failed with resource-group Owner, and Contributor + Role Based Access Control Administrator could create neither definitions nor assignments | Owner or Resource Policy Contributor at **subscription** scope for the definitions; Owner, or Resource Policy Contributor + User Access Administrator, for the assignments and their role grants ([prerequisites](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md#prerequisites)) 📄 |
| D2 | definitions created in the portal's policy definition editor lost `metadata.guestConfiguration`, and storage mode needs it | create them with the CLI (step 2) or a REST PUT of the generated file, then check that `metadata.guestConfiguration` is not empty ([3b, portal route](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md#3b-portal-route)) 🔎 |
| D3 | a portal-created assignment's identity could not be found by the assignment's name: it is named by a GUID | find it by its principal ID (assignment → *Managed Identity*). The portal also grants Role Based Access Control Administrator **without a condition** on the whole assignment scope: add the conditioned grant of step 3 and delete that one ([3b](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md#3b-portal-route)) 🔎 |
| D4 | with Privileged Identity Management, eligible role assignments did not work: an assignment identity cannot activate a role | make the role assignments **active and permanent** ([Learn](https://learn.microsoft.com/azure/role-based-access-control/pim-integration#pim-functionality)) 📄 |
| D5 | no `PerfmonBlackbox` event appeared after the install | expected: the first event is 1002, at the first export (part 3) ✅ |
| D6 | an existing storage account instead of `main.bicep` | works: a container `packages` with exactly that name and the release zip unchanged, the capture container (`perfmon`, or another name passed as `ContainerName`), the two custom roles, the agent's reader grant, a private endpoint; and **no storage role for the servers by hand**, the policy grants it ([1b](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/deploy.md#1b-or-an-existing-storage-account)) 🔎 |

## What we learned

- **A recorder can be installed without installing anything.** Azure Policy and Machine Configuration keep a data
  collector set and three scheduled tasks in place on every server, using only Windows' own tools.
- **The server's own identity is enough to upload, and it can write only its own folder.** No SAS, no shared key, no
  read right on the captures.
- **A new policy assignment needs `ReEvaluateCompliance` before its first remediation.** Without it the remediation
  reports success and does nothing.
- **Where the package comes from is part of the definition, not of the assignment.** Machine Configuration builds the
  guest assignment from the definition's metadata, so storage mode needs the metadata passed in full.
- **On Azure VMs the recorder costs about 7.50 USD a month for 10 servers.** The private endpoint is most of it. On
  Arc, it is 6 USD per server per month.

## Next: inside the machine

The setup is done: three servers record all the time, and an hourly zip appears in each server's folder. But what
exactly happens on the server? Where does the recording live between two exports, what happens when the server
restarts in the middle of it or the disk fills up, and how does a server with no keys prove who it is to the storage?

**[Part 3]({{< relref "/posts/perfmon-blackbox-part-3" >}})** opens arc1 and looks inside: the folder `C:\ProgramData\PerfmonBlackbox`, the data collector set, the
three scheduled tasks, and the first place to look when something goes wrong.
