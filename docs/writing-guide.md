# Writing guide

What **every** post on sreagent.emreguclu.io must have, how it is laid out, and how it gets approved.
English is the working language of this guide; a Turkish summary is at the end.

The model post is [`content/posts/sql-mcp-part-1/`](../content/posts/sql-mcp-part-1/). When in doubt, copy its shape.

## 1. The checklist

A post is ready for review only when every box is ticked, in **both** languages.

- [ ] **Goal and audience** in the first screen: what the reader will have at the end, and who it is for
      (role + what they must already know). One short paragraph each, no marketing.
- [ ] **Prerequisites**: a table of what must exist before step 1 (subscriptions, roles, versions, network paths,
      tools on the admin machine). Mark each row ✅ or 📄.
- [ ] **Architecture diagram** in Mermaid (`{{< mermaid >}}`), placed before the steps. Show the request path and
      the trust boundaries (identity, network). A diagram that only lists boxes is not enough: label the arrows.
- [ ] **Steps**, numbered, each with a heading. Commands for the **admin machine** come in two tabs, `zsh` and
      `PowerShell`, in **one tab group** (see §3), so one click switches the whole page. Commands that only exist on one
      side (T-SQL, a script that runs on a Windows VM) appear once, without tabs.
- [ ] **Verification**: how the reader proves each step worked, with the expected output.
- [ ] **Troubleshooting**: a symptom → cause → fix table, at least for the failures we actually hit.
- [ ] **Evidence markers** on every factual claim: ✅ = proven in our lab, 📄 = documented only (Learn, source code,
      release notes), not tested by us. The legend line goes near the top. Never mark something ✅ that we did not run.
      Every claim keeps its marker, even where the review skill says to mark only exceptions (D44).
- [ ] **What we learned**: the 3–6 findings worth remembering, written as plain statements, not a recap of the steps.
- [ ] **Feature image** (`feature.svg` or `feature.png`, 1200 × 630) in the page bundle. It is the card thumbnail on the
      home page and the hero on the post. Keep text in it language-neutral (it is shared by TR and EN).
- [ ] **Scrub checklist** passed (see §4). No lab identifiers, no secrets, no customer data.
- [ ] **TR and EN parity** (see §5).
- [ ] **Front matter** complete (see §2).
- [ ] **Reviewed and fixed** with `tech-blog-review`, TR and EN each on its own terms, before Emre sees it (see §6, D41).
- [ ] **Approval**: Emre approved this exact version (see §6). Until then `draft: true`.

## 2. Files and front matter

One post = one **page bundle**:

```text
content/posts/<slug>/
  index.en.md      English
  index.tr.md      Turkish
  feature.svg      card thumbnail + hero (or feature.png / feature.jpg)
```

`hugo new content posts/<slug>` creates the bundle from [`archetypes/posts/`](../archetypes/posts/).

Front matter, the same keys in both languages:

```yaml
---
title: "Setting up SQL MCP for Azure SRE Agent"        # sentence case, no trailing period
description: "One or two sentences. Used on the card and in search results."
date: 2026-10-04                                       # first publication date
lastmod: 2026-10-04                                    # set when the content changes materially
draft: true                                            # false only after Emre's approval
series: ["SQL MCP for Azure SRE Agent"]                # TR uses its own series title
series_order: 1
tags: ["azure-sre-agent", "mcp", "dab", "sql-server"]  # identical in TR and EN
showTableOfContents: true
---
```

- **Slug**: lowercase, hyphenated, English, short (`sql-mcp-part-1`). The same folder serves both languages.
- **Tags**: lowercase kebab-case, English in both languages, so a tag page collects both. Reuse existing tags before
  inventing one. Current set: `azure-sre-agent`, `mcp`, `dab`, `sql-server`, `entra-id`, `gmsa`, `kerberos`, `networking`.
- **Series**: the display name, translated per language. `series_order` is the same number in both.
- **Feature image**: found automatically by name (`*feature*`, `*cover*`, `*thumbnail*`). No front-matter key needed.

## 3. Shortcodes we use

**Shell tabs (one group per page).** The labels must be exactly `zsh` and `PowerShell` on every tab block, because the
group switches tabs by label:

```text
{{< tabs group="shell" >}}
{{< tab label="zsh" >}}
```bash
az group list -o table
```
{{< /tab >}}
{{< tab label="PowerShell" >}}
```powershell
az group list -o table
```
{{< /tab >}}
{{< /tabs >}}
```

PowerShell variants that pass JSON to `az rest` write the body to a file and use `--body '@file.json'`; it avoids
PowerShell's quoting. If a variant was not run by us, mark it 📄.

**Diagram:** `{{< mermaid >}} … {{< /mermaid >}}`.

**Callouts:** `{{< alert icon="triangle-exclamation" >}}` for a warning that can cost the reader an outage,
`{{< alert icon="circle-info" >}}` for context. At most three per post, or they stop meaning anything.

**Steps:** plain numbered `##` / `###` headings. They show up in the table of contents and can be linked.

## 4. Scrub checklist (the repo is public)

Everything committed here is public, including drafts. Before every commit of content, check:

- [ ] No **GUIDs**: tenant, subscription, app (client), object, principal, role or thread IDs. Use `<tenant-id>`, `<appId>`.
- [ ] No **resource names, host names, domain names or IP addresses** from the lab. Use the placeholders below.
- [ ] No **secrets**: tokens, keys, passwords, connection strings with credentials, SAS URLs. Not even expired ones.
- [ ] No **customer** names, data, screenshots or tickets.
- [ ] No internal tooling details (session names, rig paths, private repo names).
- [ ] Screenshots: cropped and checked for the same things (address bar, portal breadcrumbs, user menu).
- [ ] `scripts/scrub-check.sh` passes.

Standard placeholders:

| Thing | Placeholder |
|---|---|
| AD domain | `CONTOSO` / `contoso.local` |
| MCP host | `mcp01` |
| SQL Servers | `sql01`, `sql02` |
| gMSA | `gmsa-dab$` |
| Entra app | `sql-mcp-api`, id `<appId>` |
| Tenant, subscription, resource group, agent | `<tenant-id>`, `<sub>`, `<rg>`, `<agent>` |
| Subnets | `<agent-subnet>`, `<vm-subnet>` (or RFC 5737 documentation ranges such as `192.0.2.0/24`) |

`scripts/scrub-check.sh` greps `content/` for GUIDs, private IPv4 addresses and secret-looking strings, plus a
**denylist of real lab names** kept outside the repo (the denylist is itself identifying, so it never gets committed).

## 5. TR and EN parity

- Both files exist, have the same sections in the same order, the same commands, the same ✅/📄 markers, and the same
  numbers. A finding in one language is a finding in the other.
- Translate the prose, not the code. Commands, identifiers and product names stay as they are.
- Turkish style: plain, technical Turkish; English product terms stay English (managed identity, connector,
  scheduled task); Turkish suffixes attach with an apostrophe (`DAB'ın`, `token'ı`).
- When one language is edited, the other is edited in the same commit.

## 6. Review and approval

Every new post goes through these steps in order (D5, D41). Emre sees a post only after step 3.

1. **Draft.** Write both languages with `draft: true` **outside the repo**, in the gitignored `files/<slug>-draft/`
   folder. It must pass the scrub check (§4) and the checklist (§1).
2. **Review.** Review the draft with the project skill `.claude/skills/tech-blog-review`. Review the TR and the EN
   version **each on its own terms** (the Turkish one gets the skill's Turkish language review). Keep the full review
   beside the draft (`files/<slug>-draft/review-YYMMDD.md`).
3. **Fix.** First keep the original: copy the draft bundle to `files/<slug>-draft/original-YYMMDD/` and never edit
   that copy. Then apply the review's fixes to both languages and keep TR/EN parity (§5).
   - Never change a fact, a command, a code block or a test result (including a ✅/📄 marker) unless the review flagged
     it.
   - Mark anything Emre must verify, as the skill says; list each one in the review summary.
   - Keep front matter, slug and URLs.
   - **A finding that would change a tested thing** (command, code, sample output, test result, ✅/📄 marker, step
     order, a new claim or alternative) **is tested first** (D43): write a test plan (what, which lab, expected
     result, pass criterion), run it in the post's own lab as an admin identity against the ARM API (never through
     SRE Agent), restore the lab exactly, and apply only what passed; a newly tested claim gets ✅. Then review the fixed
     post again. A clean second review goes on to step 4. A stuck finding (test failed, could not run, or flagged
     again) stops and goes to Emre as a short plain report. Wording and structure fixes need no test. Test logs stay
     in `files/`.
   - Run the scrub check again.
4. **Private preview.** Build: `hugo --buildDrafts --relativeURLs --uglyURLs -d <tmp>` (from a scratch copy of the repo
   with the bundle added) and publish it as a **private** preview. Its cover page carries a short **review summary**:
   the top findings, what was changed, and anything left for Emre to decide.
5. **Approval.** Emre reviews it. His changes go back into the bundle; rebuild the preview and repeat until he
   approves this exact version.
6. **Publish.** On approval: set `draft: false` in **both** languages, set `date`, copy the bundle into
   `content/posts/<slug>/`, commit with `post: publish <slug>`, push. The Pages workflow builds and deploys `main`.
7. Nothing goes live without step 6. Making the repository public or enabling Pages is Emre's decision only.

**Labs (D37, D47).** A post that needs a demo gets its own lab, which this project builds itself from the shared lab
template: its `azd` from the template's checkout, always with an explicit `-e <env>` and the next free env name from the
template's lab register (`docs/labs.md` there), never while a session of the template project is open, credentials only
via `direnv exec` there. **Every lab the blog builds or tears down gets its row in that lab register in the same step.**
Lab and template names stay outside this repo (scrub denylist, §4).

## 7. Voice

The author is Emre Güçlü. Write the way he works: direct, concrete, technically precise, no hedging and no fluff.
Start from the real constraint, show the request path, say what broke and why. Prefer a number to an adjective
("DAB starts in 3.5 s with 25 servers", not "DAB starts quickly"). First person plural ("we") for lab work.

**Always say who runs a privileged command vs. what the service identity gets.** A step heading like "(as sysadmin)"
reads as if the service account were sysadmin. Name the operator ("a DBA with sysadmin rights runs these commands")
and state separately, in one plain sentence, the exact permission the service identity receives ("the gMSA is not
sysadmin; it gets only `##MS_ServerPerformanceStateReader##`"). Same for local admin, Owner, Global Admin, etc. (D22)

**No personal or career text about Emre** anywhere on the site (author profile, posts, home page, footer, images):
no years of experience, employers, roles held, or self-descriptions, unless Emre has approved that exact text,
relayed by his assistant. The guide copies his voice only. The author profile is name and title only (D21).

---

## Türkçe özet

Her yazıda olması gerekenler: **amaç ve hedef kitle**; **ön koşullar** tablosu; adımlardan önce **Mermaid mimari
diyagramı** (okları etiketli); numaralı **adımlar**, admin makinesi komutları **tek bir sekme grubunda** `zsh` ve
`PowerShell` olarak (bir tık bütün sayfayı değiştirir); her adım için **doğrulama**; **sorun giderme** tablosu
(belirti → neden → çözüm); her iddiada **✅ lab'de kanıtlandı / 📄 yalnız belgede** işareti; **"Ne öğrendik"** bölümü;
sayfa paketinde 1200 × 630 **kapak görseli** (`feature.svg`/`.png`, dil bağımsız metin).

Dosya düzeni: `content/posts/<slug>/index.en.md` + `index.tr.md` + `feature.*`. Front matter: `title`, `description`,
`date`, `draft`, `series` (dile göre çevrilir), `series_order`, `tags` (iki dilde aynı, İngilizce, küçük harf).

**Temizlik (repo public olacak):** GUID yok, lab kaynak/host/alan adı ve IP yok, sır yok, müşteri verisi yok;
standart yer tutucular kullanılır; `scripts/scrub-check.sh` geçmeli. Gerçek lab adlarının listesi repoya girmez.

**TR–EN eşliği:** iki dosya aynı bölümler, aynı komutlar, aynı işaretler ve aynı sayılarla; biri değişirse öteki aynı
commit'te değişir.

**Onay:** yazı `draft: true` ile repo dışında (`files/<slug>-draft/`) yazılır → `tech-blog-review` skill'i ile TR ve EN
ayrı ayrı gözden geçirilir → özgün taslak tarihli bir kopya olarak saklanır, düzeltmeler uygulanır (olgular, komutlar
ve test sonuçları yalnızca review işaret ettiyse değişir; Emre'nin doğrulaması gerekenler işaretlenir) → kısa bir
review özetiyle özel önizleme (test edilmiş bir şeyi değiştirecek bulgular önce post'un kendi lab'inde test edilir, yalnızca geçenler uygulanır, düzeltilmiş yazı yeniden review edilir; takılan bulgu kısa bir raporla Emre'ye gider, D43) → Emre onaylar → iki dilde `draft: false`, commit, push → workflow yayımlar (D41). Repoyu public yapmak ya da Pages'i açmak yalnız Emre'nin kararıdır.

**Lab'ler (D37, D47):** demo gerektiren her yazının kendi lab'i olur; bu proje onu ortak lab şablonundan kendisi kurar (şablonun checkout'undan `azd`, her zaman açık `-e <env>` ve şablonun lab kaydındaki sıradaki boş ad; şablon projesinin oturumu açıkken asla; kimlik bilgileri yalnızca oradaki `direnv exec` ile). Kurulan ya da kaldırılan her lab aynı adımda şablonun lab kaydına (`docs/labs.md`) satır olarak girer.

**Yazar hakkında metin yok:** Emre'nin onayladığı birebir metin (asistanı iletmişse) dışında sitede Emre hakkında kişisel
ya da kariyer metni yer almaz. Yazar kutusu yalnız ad ve unvan (D21). Rehber yalnız onun sesini taklit eder.

**Yetkiyi kimin kullandığı açık olmalı:** ayrıcalıklı bir komutu kimin çalıştırdığını (ör. "komutları sysadmin yetkili
bir DBA çalıştırır") ve servis kimliğinin tam olarak hangi yetkiyi aldığını (ör. "gMSA sysadmin değildir; yalnızca
`##MS_ServerPerformanceStateReader##` alır") her zaman ayrı ayrı yazın. "(sysadmin olarak)" gibi başlıklar yanlış okunur (D22).
