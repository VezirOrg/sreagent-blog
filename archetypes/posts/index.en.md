---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
description: ""
date: {{ .Date }}
draft: true
series: ["Series name"]
series_order: 1
tags: []
showTableOfContents: true
---

<!-- See docs/writing-guide.md. Every section below is required. -->

✅ = proven in the lab · 📄 = documented only, not tested by us.

## Goal and audience

## Prerequisites

| Area | Requirement | |
|---|---|---|

## Architecture

{{< mermaid >}}
flowchart LR
  A[Client] -->|label every arrow| B[Service]
{{< /mermaid >}}

## Steps

### 1. First step

{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
```
{{< /tab >}}
{{< /tabs >}}

## Verification

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|

## What we learned
