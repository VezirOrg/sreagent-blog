---
title: "Let Azure SRE Agent run commands on a VM, but not as SYSTEM"
description: "A custom role that allows managed Run Command and leaves out action Run Command, plus an Azure Policy that only lets a managed run command run as a user you name. Tested with eight calls against a real VM."
date: 2026-10-08
draft: false
tags: ["azure-sre-agent", "run-command", "azure-policy", "rbac"]
showTableOfContents: true
---

If you give Azure SRE Agent's managed identity a role like Virtual Machine Contributor, it can run any script on your
VMs as **SYSTEM** (Windows) or **root** (Linux). That is what `az vm run-command invoke` does, and the role allows it.
We wanted the agent to keep running commands, but as a plain local user that we choose.

It takes two pieces: a custom role that allows **managed** Run Command and leaves out **action** Run Command, and an
Azure Policy that denies a managed run command unless it runs as an allowed user. In four steps:

1. Create a local, non-admin user on the VM.
2. Create the custom role and assign it to the agent's identity on that VM.
3. Create the policy and assign it on the same VM.
4. Tell the agent to run commands only as managed run commands, as that user.

✅ = proven in our lab · 📄 = documented only (Microsoft Learn), not tested by us.
We ran every admin-machine command in zsh. The PowerShell tabs were not tested on our side. 📄

## Goal and audience

**Goal.** By the end of this post, the agent's identity can create managed run commands on one VM, and every one of
them runs as a local user named `sre-agent`, which is not an administrator. A run command with no user, with another
user, with a script from a URL or with output to a blob is denied before it reaches the VM.

**Audience.** Anyone who gives Azure SRE Agent's managed identity access to VMs. You should know Azure role assignments
and have assigned an Azure Policy before.

## Two kinds of Run Command

| | Action Run Command | Managed Run Command |
|---|---|---|
| CLI | `az vm run-command invoke` | `az vm run-command create` |
| Permission | `Microsoft.Compute/virtualMachines/runCommand/action` | `Microsoft.Compute/virtualMachines/runCommands/write` |
| Runs as | SYSTEM on Windows, root on Linux 📄 | the user in `runAsUser`, if you set one 📄 |
| What it is | a POST action | a child resource of the VM 📄 |

The difference that matters here is the last row. A managed run command is a resource, so Azure Policy can read its
properties, including `runAsUser`. RBAC cannot: a role grants an operation, it never looks at the values in the request.
That is why the role alone is not enough. 📄

## Prerequisites

| Area | Requirement | |
|---|---|---|
| Azure roles | Someone with **Owner** or **User Access Administrator** on the VM's resource group, once, to create the role and assign the role and the policy | ✅ |
| Policy definition | A role at the **subscription** that can create policy definitions, for example Resource Policy Contributor. Someone who is Owner only on the resource group gets `AuthorizationFailed` here | ✅ (role name 📄) |
| Agent identity | The managed identity SRE Agent uses for Azure; its principal (object) ID | ✅ |
| VM | A Windows VM with the VM agent running | ✅ |
| Run-as user | A local, non-admin user on the VM (here `sre-agent`) and its password | ✅ |
| Windows service | **Secondary Logon** (`seclogon`): Microsoft Learn says managed Run Command needs it running for run-as on Windows. In our lab, run-as worked even with it disabled | 📄 / ✅ |
| Admin machine | Azure CLI signed in; `jq` for the zsh tab. zsh or PowerShell | ✅ zsh / 📄 PowerShell |

## Architecture

{{< mermaid >}}
flowchart LR
  A["SRE Agent<br/>managed identity"] -- "PUT runCommands/x<br/>runAsUser=sre-agent" --> ARM["Azure Resource Manager"]
  A -. "POST runCommand/action<br/>(invoke)" .-> ARM
  ARM -- "1. RBAC: custom role<br/>has runCommands/write,<br/>no runCommand/action" --> P["2. Azure Policy on the VM<br/>runAsUser in allowed list?<br/>no scriptUri, no blob output?"]
  P -- "allowed" --> VM["VM agent runs the script<br/>as local user sre-agent<br/>(not an admin)"]
  P -- "denied" --> D["RequestDisallowedByPolicy"]
  ARM -. "invoke: AuthorizationFailed" .-> X["403"]
{{< /mermaid >}}

Two checks happen in Azure Resource Manager before anything reaches the VM. RBAC decides whether the identity may call
the operation at all. Policy then looks at the request body and denies it if the user or the script source is wrong.

## Steps

An operator with Owner or User Access Administrator on the resource group runs steps 2–3 (a local administrator does
step 1 on the VM); the policy definition in step 3 also needs the subscription-level role from the prerequisites. The
agent's identity is not an Owner: it gets only the custom role below, on one VM.

### 1. Create the run-as user on the VM

A local administrator runs this on the VM, once. It creates a local user that is **not** in Administrators and checks
that Secondary Logon is not disabled. 📄

```powershell
$pw = Read-Host -AsSecureString "Password for sre-agent"
New-LocalUser -Name 'sre-agent' -Password $pw -Description 'Run Command run-as user for SRE Agent'
Get-Service seclogon | Select-Object Name, Status, StartType   # StartType must not be Disabled
```

Give this user only what the agent needs to read or fix on that machine (log folders, a service it may restart). Every
script the agent runs gets exactly these rights.

### 2. Create the custom role and assign it to the agent

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

There is no `runCommand/action` in the list, so `az vm run-command invoke` is outside the role. There is also no
`runCommands/delete`: the agent never deletes, an operator cleans up.

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

If the identity already has Virtual Machine Contributor, Contributor or Owner anywhere above this VM, remove it. Those
roles include `runCommand/action`, and Azure RBAC is additive: a narrower assignment does not take away what a wider one
grants. 📄

### 3. Create the policy and assign it on the VM

`policy-runcommand-runasuser.json` denies a managed run command when `runAsUser` is missing or not in the list, when
the script comes from a URI or a gallery, or when output or errors go to a blob:

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

**Assign it narrowly.** The policy applies to **every** caller at its scope, people and pipelines included, not just the
agent. Assigned on a resource group or subscription, it also blocks an admin's run command with no `runAsUser`. We
assigned it on the one VM the agent manages. ✅ A new assignment can take a while to start denying, so wait before
testing. 📄

### 4. Tell the agent how to run commands

The agent now has one way to run a script on the VM: a managed run command with `runAsUser` set. In its instructions,
say so plainly:

```text
To run a command on vm01, use:
az vm run-command create -g <rg> --vm-name vm01 --name <short-unique-name> \
  --script "<script>" --run-as-user sre-agent --run-as-password <password> --timeout-in-seconds 120
Then read the result with:
az vm run-command show -g <rg> --vm-name vm01 --name <same-name> --instance-view
Never use az vm run-command invoke.
```

On Windows the agent also needs the user's password. With the instruction above, that password sits in plain text in
the agent's instructions. This is the weak point of this setup; see the warning at the end.

## Verification

We ran eight calls against a Windows VM with the policy assigned on that VM. Seven were run with an admin identity: the
policy holds for every caller, so a deny for an admin is a deny for the agent too. T4 was run with an identity that holds
only the custom role, on that VM. With the same identity, T1 was denied and T3 ran as `sre-agent`, as in the table.

| # | Call | Expected | Result |
|---|---|---|---|
| T1 | `create` with no `--run-as-user` | denied by policy | `RequestDisallowedByPolicy` ✅ |
| T2 | `create --run-as-user Administrator` | denied by policy | `RequestDisallowedByPolicy` ✅ |
| T3 | `create --run-as-user sre-agent` | runs as `sre-agent`, not admin | `vm01\sre-agent`, `isAdmin=False` ✅ |
| T4 | `invoke` (action Run Command), identity with only the custom role | denied by RBAC | `AuthorizationFailed` ✅ |
| T5 | `create --script-uri https://…` | denied by policy | `RequestDisallowedByPolicy` ✅ |
| T6 | `update` T3's command to `--run-as-user Administrator` | denied by policy | `RequestDisallowedByPolicy` ✅ |
| T7 | `create --output-blob-uri https://…` | denied by policy | `RequestDisallowedByPolicy` ✅ |
| T8 | `create --error-blob-uri https://…` | denied by policy | `RequestDisallowedByPolicy` ✅ |

T3, the allowed call:

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

Expected: `instanceView.executionState` is `Succeeded` and `instanceView.output` contains:

```text
vm01\sre-agent
isAdmin=False
```

The response to `create` returns `runAsUser` but not the password. ✅

A denied call (T1) looks like this:

```text
ERROR: (RequestDisallowedByPolicy) Resource 't1' was disallowed by policy.
Policy identifiers: '[{"policyAssignment":{"name":"runcommand-runasuser-vm01", ...}}]'.
```

To check T4 on your own agent, ask it to run `az vm run-command invoke` on the VM. It should get `AuthorizationFailed`.

## Limits

- **Windows needs a password.** On Windows, run-as needs `runAsPassword` as well as `runAsUser`, and the Secondary
  Logon service must be running. 📄 In our lab, run-as worked even with Secondary Logon disabled. ✅
- **25 managed run commands per VM.** Old ones stay as resources until someone deletes them. The role has no delete, so
  plan a cleanup by an operator. 📄
- **VMs only.** Scale sets (`virtualMachineScaleSets/virtualMachines/runCommands`) and Arc machines
  (`Microsoft.HybridCompute/machines/runCommands`) are other resource types. This role and policy do not cover them. 📄
- **RBAC cannot check values.** A role grants `runCommands/write` or it does not; it cannot say "only as `sre-agent`".
  That is the Policy's job. 📄
- **Policy affects everyone at its scope.** Keep the assignment on the VMs the agent manages. ✅

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `RequestDisallowedByPolicy` on a call that should pass | `runAsUser` is missing, misspelled or not in `allowedRunAsUsers`, or the call carries a script URI or blob URI | Fix the call or the assignment's parameter ✅ |
| `AuthorizationFailed` on `az vm run-command invoke` | Action Run Command is not in the role | Expected. Use `create` ✅ |
| Run-as fails on Windows | Wrong password, or Secondary Logon disabled | Check the password; set `seclogon` to Manual 📄 |
| New run commands fail after a while | 25 managed run commands already exist on the VM | An operator deletes old ones 📄 |

## What we learned

- Action Run Command always runs as SYSTEM or root. Within Run Command, the only way to run as another user is managed
  Run Command with `runAsUser`. 📄
- RBAC can split the two kinds of Run Command apart, but it cannot see who a command runs as. Azure Policy can, because
  a managed run command is a resource with a `runAsUser` property. ✅
- One policy covers all four ways around it: no user, another user, an external script, and output to a blob. A later
  `update` to another user is denied as well. ✅
- The allowed path works: the script ran as `vm01\sre-agent`, not an administrator. ✅
- Assign the policy on the VM, not higher. It applies to every caller, admins included. ✅

{{< alert icon="triangle-exclamation" >}}
**The run-as password ends up in the agent's logs.** The agent has to send the password with every call, and SRE Agent
records the input of every tool call and every az command it runs in Application Insights. 📄 So treat the run-as user as known to anyone who can read those logs:
keep real secrets out of the agent's reach, do not give its identity roles that read secrets (Key Vault, storage
keys), limit its network reach to the VM management ports, and do not approve its on-behalf-of requests without
reading them. The stronger option is a tool with its own identity that holds the password and runs a fixed set of
commands, so the agent never sees it. We only describe it here; we have not built it.
{{< /alert >}}
