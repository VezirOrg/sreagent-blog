---
title: "A black box for Windows servers, part 1: record first, ask later"
description: "A Windows server slows down at night and by morning the data is gone. Our answer: a PerfMon black box on every server, read by Azure SRE Agent."
images: ["social.png"]
date: 2026-10-14
draft: false
series: ["A black box for Windows servers"]
series_order: 1
tags: ["azure-sre-agent", "perfmon", "azure-policy", "azure-arc"]
showTableOfContents: true
---

The server slowed down at 03:10. By the time anyone looked, it was fast again, and nothing had been recording. By
morning there is no trace, only a ticket that says "slow last night".

The usual next step is to set up a collector and wait for it to happen again. That can take days, and the business
pays for every one of them. We wanted the opposite: **the recording is already there when the question comes.**

This series builds that, with two parts that work together:

- **A black box on every Windows server.** A flight recorder that is always on, keeps the recent past on the disk, and
  hands it over every hour. Azure Policy puts it there; nothing is installed on the server.
- **An expert who reads it.** Azure SRE Agent, Microsoft's AI agent for operations, takes a question in plain words
  ("what happened on this server?"), fetches the recording and answers with evidence.

Why not Log Analytics? It bills by the gigabytes it ingests, so every process's counters from every server, all the
time, add up ([Learn: Azure Monitor Logs cost](https://learn.microsoft.com/azure/azure-monitor/logs/cost-logs#data-size-calculation)) 📄;
the black box records locally with Windows' own data collector, moves only the finished file to cheap blob storage,
and lets the agent load one server's capture straight into SQLite instead of querying a shared workspace (a design
reason, not a speed we measured against Log Analytics).

This post shows how the two fit together, in one diagram, and what the next three parts build step by step.
Everything comes from a public playbook,
[VezirOrg/sreagent-playbook, `playbooks/perfmon-blackbox`](https://github.com/VezirOrg/sreagent-playbook/tree/main/playbooks/perfmon-blackbox),
and we ran it in our own lab on three servers: dc and iis1 (Azure VMs) and arc1 (an Arc-enabled server).

✅ = proven in our lab · 📄 = documented only (Microsoft Learn, the playbook's docs), not tested by us.

## Goal and audience

**Goal.** At the end you know what the black box records, how the recording reaches private storage without a key,
how Azure SRE Agent analyses it, and which part of the series builds which piece.

**Audience.** Windows administrators and SREs who run Windows servers on Azure or connect them with Azure Arc, and want
performance data from the moment of a problem, not from after it. Basic Azure knowledge (subscriptions, Azure Policy,
managed identities) helps.

## The whole loop in one picture

![The black box end to end: one-time setup; Azure Policy and Machine Configuration deliver the recorder; the server records, rolls and exports; it uploads with its own identity into private storage; Azure SRE Agent fetches and analyses on demand; findings tune the assignment](img/perfmon-blackbox-flow.svg)

The diagram has three bands: what you do **once**, what runs **on its own**, all the time, on every server, and what
happens **on demand**, when someone asks. Follow the numbers.

### ① Set up once

You deploy three things, one time:

- **A private storage account.** Reachable only over a private endpoint, with shared keys off, so no SAS can exist. It
  comes with two custom roles: one lets a server write, one lets Azure Policy hand that right out. ✅
- **The policy definitions,** one for Azure VMs and one for Arc-enabled servers. Each carries the address and the
  SHA-256 of the recorder package, so no server can get a different package. ✅
- **The skill on your SRE Agent,** `perfmon-triage`: the instructions and scripts the agent uses to read a recording. ✅

### ② Azure Policy delivers the recorder

You assign the policy to a scope: a resource group, a subscription. From then on Azure Policy and **Machine
Configuration**, Azure's in-guest configuration service, take over. Every server in scope gets a guest assignment named
`PerfmonBlackbox` and the package, checked by its hash. Seven DSC resources set up the recorder and keep it that way: if
someone deletes a task, it comes back at the next check, within about 15 minutes. 📄

The assignment's parameters are the black box's settings: where to upload, how big the recording may grow (512 MB),
how often to sample (every 10 seconds) and how often to export. ✅ We exported every hour in the lab; the default of
release v1.0.1 is every 4 hours. ✅ 📄

On Azure VMs Machine Configuration has no extra charge; on Arc-enabled servers it is billed per server. 📄

### ③ The server records

Each server runs a **PerfMon data collector set**, Windows' own tool, writing a *circular* binary file: when it is
full, the newest sample overwrites the oldest, so the disk never fills up. On arc1, 512 MB holds about 25 hours. ✅

Three scheduled tasks do the rest, with Windows PowerShell 5.1 that ships with Windows:

- every 15 minutes the recording is closed into a piece and a new one starts, ✅
- on every export the pieces since the last export become one CSV (in UTC) and a **manifest** that names every gap
  and its cause (a restart, a clock change), packed into one zip, ✅
- after a restart the old file is kept and recording starts again. 📄

**Nothing of ours is installed.** No agent, no service, no driver: only `logman`, `relog`, PowerShell and the
scheduler. 📄

### ④ The server uploads with its own identity

The server uploads the zip with **its own managed identity**: an Azure VM through its instance metadata service, an
Arc-enabled server through the Arc agent's. ✅ There is no key and no SAS anywhere. The server may write **only into its
own folder**, `perfmon/<sub>/<rg>/<server>/yyyy/MM/dd/`, and cannot read any recording, not even its own. ✅ If an
upload fails, the server retries, and the next export catches up. 📄 After 30 days a lifecycle rule deletes old zips. 📄

### ⑤ Azure SRE Agent reads the recording

This is the expert. An engineer asks in a thread, for example *"Analyse the latest PerfMon capture of arc1"*. The
agent picks the `perfmon-triage` skill and, in its own sandbox:

1. downloads the newest zip of that server (or every zip of a time range) over the private endpoint, with its own
   identity, and checks the CSV against the manifest; ✅
2. turns the CSV into a small SQLite database and walks a fixed checklist: CPU, memory, disk, network, processes; ✅
3. writes a ranked report into the thread. The skill asks it to state a cause only where a test links it to the
   evidence. ✅

The model never sees the raw numbers, only the answers to the checklist. In our lab, against a problem we staged on
purpose and wrote down first, the agent scored 95 and 100 out of 100 on two servers. ✅ Part 4 shows the run in full.

### The loop closes

What the agent finds can change the black box itself: a shorter sample interval, a bigger file, a more frequent
export. You change a parameter of the assignment, Azure Policy rolls it out, and the next recording is sharper. 📄

## What it gives you

- **History when it hurts.** "What happened at 03:10?" is already recorded. A hard shutdown loses at most the last
  15 minutes, and the manifest says so. 📄
- **No keys.** The upload, the agent's access and, if you choose, the package download all use managed identities. ✅
- **Nothing to install or patch.** Windows' own tools, kept in place by Machine Configuration, on Azure VMs and
  Arc-enabled servers alike. ✅
- **An answer in minutes.** One analysis took about 6 minutes in our lab, and costs roughly 3.5 to 5 USD, depending
  on region, on top of the agent's always-on charge; part 2 has the full table. ✅ 📄

## What you need for the series

| What | Why | |
|---|---|---|
| Windows Server 2016 or later, as Azure VMs or Arc-enabled servers | the black box uses only Windows' own tools | 📄 (we ran Windows Server 2022 ✅) |
| Owner on the subscription, or the split rights part 2 lists | Azure Policy definitions, assignments and role grants | 📄 |
| A private network path from the servers and from the agent to the storage | uploads and downloads go over the private endpoint only | ✅ |
| An Azure SRE Agent with VNet integration | the agent reads the recordings over the same private endpoint | ✅ |
| An admin machine with Azure CLI, Python 3 and git (on Windows also Git Bash or WSL) | the setup commands, given for zsh and for PowerShell | ✅ |

## What the next parts build

The story continues on the same three servers.

- **[Part 2]({{< relref "/posts/perfmon-blackbox-part-2" >}}): set it up, and what it costs.** The storage, the policies, the assignment, the skill, step by step, with
  every command for zsh and PowerShell, the checks that prove it works, and a cost table per region.
- **[Part 3]({{< relref "/posts/perfmon-blackbox-part-3" >}}): inside the machine.** We open arc1: the folder, the collector, the three tasks, what a restart or a full
  disk does to the recording, and the first place to look when something goes wrong.
- **[Part 4]({{< relref "/posts/perfmon-blackbox-part-4" >}}): the agent investigates.** We ask Azure SRE Agent about two hours of arc1: a quiet one, and one with a
  problem we staged on purpose. What it found, what it got wrong, and what the answer cost.

The next time a server slows down at 03:10, the recording will already be there. Part 2 puts it there.
