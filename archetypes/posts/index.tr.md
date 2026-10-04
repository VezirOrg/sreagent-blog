---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
description: ""
date: {{ .Date }}
draft: true
series: ["Seri adı"]
series_order: 1
tags: []
showTableOfContents: true
---

<!-- See docs/writing-guide.md. Every section below is required. -->

✅ = lab'de kanıtlandı · 📄 = yalnız belgede var, bizde test edilmedi.

## Amaç ve hedef kitle

## Ön koşullar

| Alan | Gereksinim | |
|---|---|---|

## Mimari

{{< mermaid >}}
flowchart LR
  A[Client] -->|label every arrow| B[Service]
{{< /mermaid >}}

## Adımlar

### 1. İlk adım

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

## Doğrulama

## Sorun giderme

| Belirti | Neden | Çözüm |
|---|---|---|

## Ne öğrendik
