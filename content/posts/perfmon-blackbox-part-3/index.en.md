---
title: "A black box for Windows servers, part 3: inside the machine"
description: "What the PerfMon black box does on a Windows server: the collector, three scheduled tasks and one folder, how it behaves on a restart or when the disk fills up, and how the server uploads with its own identity. Shown on an Arc-enabled server."
date: 2026-10-14
draft: false
series: ["A black box for Windows servers"]
series_order: 3
tags: ["azure-sre-agent", "perfmon", "machine-configuration", "azure-arc"]
showTableOfContents: true
---

In [part 2]({{< relref "/posts/perfmon-blackbox-part-2" >}}) we set the black box up: Azure Policy and Machine Configuration put a PerfMon recorder on every Windows
server, and each server now drops a zip into its own folder of a private storage account every hour. From Azure, that
is all you see: a Compliant guest assignment and a growing list of zips.

This part opens one of those servers and looks inside. The recorder runs only on the operating system's own tools.
This post shows how the recording is kept on the machine, how it behaves when the server restarts or the disk fills up,
and how the server uploads with its own identity to private storage, step by step, on **arc1**, an Arc-enabled server.

✅ = proven in our lab or in the playbook's lab tests · 📄 = documented only (Microsoft Learn, the playbook's docs and
code), not tested by us. The playbook is
[VezirOrg/sreagent-playbook, `playbooks/perfmon-blackbox`](https://github.com/VezirOrg/sreagent-playbook/tree/perfmon-blackbox/v1.0.1/playbooks/perfmon-blackbox)
at release v1.0.1; the screenshots are from arc1 on 2026-10-14, times in UTC.

## Goal and audience

**Goal.** After this post you know what each piece on the server is for, where to look first when something seems
wrong, and what the recorder does on its own when the server restarts, the storage cannot be reached or the disk
fills up.

**Audience.** Windows administrators and SREs who run the black box from part 2, or want to know what it would put
on their servers before they assign it. You should know Performance Monitor and Task Scheduler.

## Prerequisites

| What | Why | |
|---|---|---|
| The black box from part 2 on at least one server | there is something to look at | ✅ |
| Local administrator access to that server (RDP, Bastion or PowerShell remoting) | the folder is readable only by SYSTEM and Administrators | ✅ |
| Nothing else | every check below uses tools that ship with Windows | ✅ |

## The server side at a glance

{{< mermaid >}}
flowchart LR
  subgraph S["Windows server (arc1), runs as SYSTEM"]
    MC["Machine Configuration<br/>keeps 7 resources in place"] -->|creates and repairs| DCS["Data collector set<br/>circular .blg, 512 MB, 10 s"]
    MC -->|registers| T["Tasks: Boot, Roll, Export"]
    DCS -->|Roll every 15 min:<br/>close the file| P["pending\\<br/>closed pieces"]
    P -->|Export every N h:<br/>relog, gaps, manifest| Z["outbox\\<br/>one zip"]
  end
  Z -->|token from HIMDS<br/>own identity, no keys| ID["Entra ID"]
  Z -->|PUT Blob over the<br/>private endpoint| ST[("perfmon/&lt;sub&gt;/&lt;rg&gt;/arc1/...")]
{{< /mermaid >}}

Three things run on the server: a **data collector set** that records, and three **scheduled tasks** that close,
export and restart the recording. **Machine Configuration** keeps all of them in place and puts them back if someone
changes them. Everything lives in one folder, `C:\ProgramData\PerfmonBlackbox`. 📄

## The collector

In *Performance Monitor → Data Collector Sets → User Defined*, the set `PerfmonBlackbox` is Running. ✅
(`GAEvents` and `RTEvents` beside it belong to the Azure guest agent, not to the black box.)

![Performance Monitor on arc1: the user-defined data collector set PerfmonBlackbox is Running](img/collector-set.png)

The same from a prompt, `logman query PerfmonBlackbox` (here on iis1, an Azure VM of the same lab, shortened): ✅

```text
Name:                 PerfmonBlackbox
Status:               Running
Root Path:            %ProgramData%\PerfmonBlackbox\blg
Segment Max Size:     512 MB
Run as:               SYSTEM

Name:                 PerfmonBlackbox\Counters
Output Location:      C:\ProgramData\PerfmonBlackbox\blg\PerfmonBlackbox.blg
Circular:             On
Overwrite:            On
Sample Interval:      10 second(s)
```

**Circular** is the key word. The binary file never grows past 512 MB: when it is full, the newest sample overwrites
the oldest. 📄 The playbook tested this with a 16 MB file at a 1-second interval on arc1: it wrapped and never grew. ✅
On arc1, 512 MB holds about 25 hours of data (part 2); that is the black box's memory if every export fails. ✅

## The three scheduled tasks

In *Task Scheduler Library → PerfmonBlackbox*: ✅

![Task Scheduler on arc1: Boot (at system startup, has not yet run), Export (every hour, last run 7:07, success), Roll (every 15 minutes, last run 7:45, success); author PerfmonBlackbox, runs as SYSTEM](img/scheduled-tasks.png)

| Task | When | What it does |
|---|---|---|
| **Boot** | at every start of Windows | moves the file from before the restart to `pending\`, records the boot time, starts the collector again |
| **Roll** | every 15 minutes | stops the collector, moves the file to `pending\`, starts it again (about 3 seconds) |
| **Export** | every `ExportEveryHours` (here 1) | rolls once more, turns the pieces into one CSV, zips it with a manifest and uploads it |

All three run as **SYSTEM** with Windows PowerShell 5.1, and their description says "Azure Machine Configuration
package; do not edit". ✅ If you change one, Machine Configuration puts it back at its next check. 📄

**Boot says "The task has not yet run (0x41303)".** That is expected here: arc1 was never restarted after the
package was installed, so the Boot task has had no reason to run. ✅ It is not an error. The restart test is
[further down](#when-the-server-restarts).

## The folder

`C:\ProgramData\PerfmonBlackbox` on arc1: ✅

![C:\ProgramData\PerfmonBlackbox on arc1: the folders bin, blg, log, outbox, pending, work and the files config.json, state.json](img/folder.png)

One sentence each, taken from the playbook's code and docs: 📄

| Item | What it is |
|---|---|
| `bin\` | the files the package ships: the two scripts the tasks run (`Start-PerfmonBlackbox.ps1`, `Export-PerfmonBlackbox.ps1`) and, under `bin\collector\`, the collector template and the counter lists; Machine Configuration keeps them identical to the package. |
| `blg\` | the circular log the collector is writing right now, `PerfmonBlackbox.blg`. |
| `log\` | `perfmonblackbox.log`, the recorder's own text log: every roll, export, upload attempt and retry. |
| `outbox\` | the zip of the current export while it waits for its upload; it is deleted once the storage has accepted it, and a zip left by a failed upload is replaced by the next export. |
| `pending\` | the closed pieces of the recording, at most 15 minutes each, that wait for the next export; names like `20261013-174504-00-roll-m512.blg` say when and why each piece was closed (`roll`, `export`, `boot`, `recreate`, `start`). |
| `work\` | scratch space: the CSVs and the manifest of a running export (removed when the run ends) and the generated XML for the collector and the tasks. |
| `config.json` | the assignment's parameters as this server sees them (size, interval, export cadence, storage account, container, `LocalKeepMB`), written by Machine Configuration. |
| `state.json` | where the export stands: `last_ts` (the last sample of the last successful upload), the export sequence number, the recorded boot times and the last error. |

The folder's permissions allow only SYSTEM and Administrators. 📄 Nothing in it is a secret: the server holds no key
and no token on disk. 📄

## From a sample to a zip

Every 15 minutes, the Roll task closes the circular file into `pending\`. Windows cannot read a circular file while the
collector writes it, and only a closed file is safe after a bad shutdown. 📄 At export time:

1. **Roll** once more, so the last minutes are included.
2. **Check every piece** with `relog -q`: readable? how many samples, from when to when? One unreadable file makes a
   whole `relog` call fail, so it is set aside. 📄
3. **Merge** the good pieces with one `relog … -f csv` call into one CSV, keeping only samples after `last_ts`: no
   overlap with the previous zip, no hole. 📄
4. **Name every gap.** Any step between two samples longer than twice the interval goes into the manifest with a
   cause; `complete` is false if there is one. 📄
5. **Zip** the CSV with `manifest.json`, **upload**, and only after the storage accepted it move `last_ts` forward and
   delete the pieces. ✅

The manifest is the zip's own account of itself. A real one, from the first export on iis1 (2026-10-13, shortened;
IDs replaced): ✅

```json
{
  "package_version": "1.0.0",
  "machine_prefix": "<sub>/<rg>/iis1",
  "identity": "imds",
  "seq": 1,
  "first_sample_utc": "2026-10-13T17:37:25.569Z",
  "last_sample_utc": "2026-10-13T18:06:54.151Z",
  "rows": 178,
  "interval_s": 10,
  "buffer_hours": 21.7,
  "processes": 114,
  "roll_seconds": 2.8,
  "sources": [
    { "name": "20261013-174504-00-roll-m512.blg",   "reason": "roll",   "rows": 46 },
    { "name": "20261013-180003-00-roll-m512.blg",   "reason": "roll",   "rows": 90 },
    { "name": "20261013-180705-00-export-m512.blg", "reason": "export", "rows": 42 }
  ],
  "gaps": [],
  "complete": true
}
```

Three pieces (two 15-minute rolls and the export's own roll), 178 samples, no gap. `"identity": "imds"` says how this
Azure VM got its token; on arc1 it reads `himds` (see [below](#how-the-server-uploads-with-its-own-identity)). ✅

## When the server restarts

At boot, the Boot task moves the file from before the restart into `pending\`, writes the boot time into
`state.json` and starts the collector again. The next export joins the pieces before and after the restart, but never
in one `relog` call, because PerfMon's rate counters start from zero after a boot. The hole becomes a **`machine_off`
gap** in the manifest. 📄

The playbook's lab restarted arc1 on 2026-10-13 with the same package: the pieces before the restart were exported,
and the only gap was `machine_off`, 52 seconds. The first sample after the boot has an empty rate value, as it should. ✅

**Why the 15-minute roll exists.** An earlier build kept one open file until the export. A clean `az vm restart`
left that open file unreadable, and the samples before the restart were lost. ✅ Now the open file holds at most 15
minutes. If a shutdown still leaves it unreadable, it stays in `pending\` and is tried again by the next exports; after
three failed reads it is deleted, event 2003 is written, and the manifest reports the span as an **`unreadable_ring`**
gap. Data is never lost silently. ✅ (tested on an Azure VM)

## When the disk fills up

- **The recording cannot fill the disk.** The circular file has a fixed size (`MaxSizeMB`). ✅
- **The pieces waiting for export are capped.** `pending\` and `outbox\` together may use at most `LocalKeepMB`
  (1,024 MB by default). Above that the oldest pieces go first, event 2001 is written, and the next manifest reports a
  **`local_cap`** gap. 📄
- **The capacity check warns before that.** Machine Configuration measures how many hours the file and the local cap
  hold, and turns the guest assignment NonCompliant (resource `[BlackboxCapacity]`) if they do not hold 1.5 times the
  export window. On arc1 the reason reads "ring holds ~25.2 h …, LocalKeepMB holds ~50.4 h … margin ok". ✅

We did not test a disk that is already full for other reasons. What the collector does then is up to Windows. 📄

## When the storage cannot be reached

A failed token or upload is retried in the same run, after 5 and after another 10 minutes, each time with a fresh
token. If every attempt fails, event 3002 is written and nothing moves: `last_ts` stays, the pieces stay, and the next
successful export covers the whole window since `last_ts` in one zip. 📄 The playbook blocked the storage on an Azure VM
for about 3 minutes: the upload failed once, succeeded on the second attempt, and the next manifest was complete and
continuous. ✅ Nothing is lost as long as the outage is shorter than what `LocalKeepMB` holds (about 50 hours on arc1). ✅

## How the server uploads with its own identity

There is no key, no SAS and no secret on the server. The Export task gets an Entra ID token for
`https://storage.azure.com/` from the server's **system-assigned managed identity**: 📄

- **On an Azure VM** from the instance metadata endpoint, `http://169.254.169.254/metadata/identity/oauth2/token`.
- **On an Arc-enabled server** from the Connected Machine agent, `http://localhost:40342/metadata/identity/oauth2/token`.
  The first call returns 401 with the path of a challenge file under
  `C:\ProgramData\AzureConnectedMachineAgent\Tokens\`, which only administrators and the *Hybrid agent extension
  applications* group can read (the task runs as SYSTEM); the second call sends its content and gets the token.
  ([Learn: identity and authorization](https://learn.microsoft.com/azure/azure-arc/servers/security-identity-authorization#microsoft-entra-id-managed-identity))

Learn's evaluation setup for an Arc server on an Azure VM blocks the Azure metadata endpoint, so arc1's uploads really
go through the Arc agent. 📄 The playbook's upload test on arc1 recorded `identity=himds` in the manifest and "uploaded
with the machine identity (himds)". ✅

Then a plain REST call, `PUT Blob`, over the private endpoint, with `Content-MD5` so the storage service checks the
bytes, and three metadata values (`sha256`, `seq`, `complete`). Only an HTTP 201 counts as success. ✅ The token lives
in memory only; it is never written to disk or to the log. 📄

What the identity may do is the narrow part. The policy gives each server **one** role on the container, *PerfMon
Blackbox Writer*: write and add blobs only, no read, no delete, no list, and a condition that the blob path starts with
the server's own prefix, `<sub>/<rg>/arc1/`. The playbook's test tried to write outside that prefix and was denied. ✅

## Event Viewer: the first place to look

When something seems wrong on a server, open **Event Viewer → Windows Logs → Application** and filter on the source
**PerfmonBlackbox**. ✅ On arc1, four exports, four events 1002, one per hour:

![Event Viewer on arc1, Application log filtered on source PerfmonBlackbox: four events 1002, the newest saying "export 4 uploaded: …/arc1/2026/10/14/arc1_20261014-063918_20261014-070654.zip (167 samples, complete)"](img/event-1002.png)

| ID | Level | Meaning |
|---|---|---|
| **1002** | Information | an export was uploaded, complete: the blob name and the number of samples |
| 1001 | Information | the collector was started (at boot, or after a change) |
| 2002 | Warning | an export was uploaded, but with gaps; the message names them |
| 2001 | Warning | `LocalKeepMB` was reached: a piece was deleted before it was exported |
| 2003 | Warning | a piece could not be read three times and was deleted |
| 3001 | Error | the collector could not be started |
| 3002 | Error | an export failed after every retry; the next run tries the same window again |

(From the playbook's code. 📄)

**No event before the first export.** The event source `PerfmonBlackbox` is created by the first event the recorder
writes, and on a fresh server that is the first export. Until then Event Viewer shows nothing and
`Get-WinEvent -ProviderName PerfmonBlackbox` answers that there is no such provider. That is not a fault: wait for the
first export. It runs at 00:07 local time and then every `ExportEveryHours`, each time with a random delay of up to
10 minutes ([operations.md](https://github.com/VezirOrg/sreagent-playbook/blob/main/playbooks/perfmon-blackbox/docs/operations.md#events)). 📄 On iis1 the first 1002 came 29 minutes after it turned Compliant. ✅

From a prompt:

```powershell
Get-WinEvent -ProviderName PerfmonBlackbox -MaxEvents 5
```

If the events do not answer the question, the next places are, in order: `state.json` (`last_ts`, `last_error`) and
`log\perfmonblackbox.log` on the server, the guest assignment's reasons in Azure (part 2), and the newest zip's
`manifest.json` (`complete`, `gaps`). 📄

## What this post does not show

- **A disk already full for other reasons.** We did not test it.
- **An unreadable piece and a storage outage on arc1.** Both were tested by the playbook on an Azure VM; the code path
  is the same on Arc.
- **A restart of arc1 in this lab.** The restart result is from the playbook's earlier lab, on arc1 with the same
  package (v1.0.1 ships the v1.0.0 zip unchanged).
- The `logman` output and the manifest are iis1's, an Azure VM of the same lab; arc1 shows the same collector in its
  screenshot.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Event Viewer shows no `PerfmonBlackbox` source | no export has run yet | wait for the first export ✅ |
| Boot task: "has not yet run (0x41303)" | the server has not restarted since the install | nothing ✅ |
| Event 3002, and `state.json` shows `last_error` | the token or the upload failed three times (network, DNS of the private endpoint, the Writer role) | fix the path; the next export catches up from `last_ts` 📄 |
| Event 2002 with `local_cap` | uploads failed for longer than `LocalKeepMB` holds | fix the upload path; consider a larger `LocalKeepMB` 📄 |
| Event 2002 with `unreadable_ring` | a shutdown left the open piece unreadable (at most 15 minutes) | nothing; the loss is named in the manifest ✅ |
| Guest assignment NonCompliant on `[BlackboxCapacity]` | the file or the local cap holds less than 1.5 export windows | raise `MaxSizeMB` or `LocalKeepMB`, or export more often 📄 |
| A task or the collector was edited by hand | Machine Configuration corrects drift | nothing; it is put back at the next check 📄 |

## What we learned

- **Three tasks, one collector set and one folder** are the whole black box on a server, and Machine Configuration
  keeps them as the package says.
- **A circular file needs closing to be safe.** The 15-minute roll turns the recording into closed pieces, so a
  restart costs at most 15 minutes and the manifest says so.
- **Every loss has a name.** A restart, an unreadable piece, a local cap or a missing sample becomes a gap with a
  cause, and `complete` turns false.
- **The server proves who it is without a secret.** The managed identity's token, from IMDS or the Arc agent, is
  enough, and its role lets it write only its own folder.
- **Event Viewer first, and silence before the first export is normal.**

## Next: the agent investigates

The zips are in the storage, each with a manifest that names its gaps. Now the question from the first line of
part 1: what made the server slow? **[Part 4]({{< relref "/posts/perfmon-blackbox-part-4" >}})** asks Azure SRE Agent about two of arc1's hourly captures: first a quiet
hour, then an hour with a deliberately staged load whose ground truth we wrote down beforehand. It checks what the
agent finds, what it gets wrong and what one analysis costs.
