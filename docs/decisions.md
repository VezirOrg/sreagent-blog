# Decisions

Durable decisions for this site. Newest at the bottom. Each one is dated and says who decided.

## 2026-10-04 — Founding decisions (Emre)

| # | Decision | Notes |
|---|---|---|
| D1 | A blog plus hands-on lab guides about **Azure SRE Agent, MCP and Data API builder (DAB)**, published at **https://sreagent.emreguclu.io**. | |
| D2 | **Hugo + Blowfish** theme, **Turkish and English**, author **Emre Güçlü**. | Theme pinned to a released tag (see D7). |
| D3 | **One repository** (`VezirOrg/sreagent-blog`) holds the site, its docs and its working record. It will become **public**. | Private until Emre approves the first post. Making it public is Emre's decision only. |
| D4 | Because the repo will be public, **everything committed must be publishable**: no lab identifiers (tenant, subscription, app, object IDs, resource names, host names), no secrets, no customer data, no internal tooling details. | Raw notes, internal discussion and unapproved drafts are kept outside the repo. |
| D5 | **Every post is approved by Emre before it goes live.** | See the review step in [writing-guide.md](writing-guide.md). |
| D6 | **Hosting: GitHub Pages**, built and deployed by a GitHub Actions workflow, custom domain `sreagent.emreguclu.io` via `static/CNAME`. | DNS (`CNAME sreagent → vezirorg.github.io`) and the org domain verification TXT record are done by Emre. Pages can only be enabled after the repo is public. |
| D7 | **Theme is pinned**: Blowfish as a git submodule checked out at a release tag. | Upgrading the theme is a deliberate commit that moves the submodule. |

## 2026-10-04 — Build choices made while setting up the site (first session; Emre may revisit)

| # | Choice | Why |
|---|---|---|
| D8 | **English at the site root, Turkish under `/tr/`**; a language switch in the header. | One default language keeps URLs short; both languages are complete. Open for Emre to flip. |
| D9 | **Every post is a page bundle** with `index.en.md`, `index.tr.md` and a shared `feature.*` image. Tags are English in both languages; series titles are translated. | One folder per post keeps TR and EN together; shared tags collect both languages. |
| D10 | Home page: Blowfish `background` layout, **recent posts as cards with feature images**, plus a series and tags block (`layouts/shortcodes/site-topics.html`). Dark mode by default, switchable. | Emre's home page requirements. |
| D11 | **Hugo 0.167.0 extended**, locally and in CI. Blowfish v3.8.0 declares 0.163–0.166, so Hugo prints a compatibility warning; the build is clean. | Same version everywhere; pin moves deliberately. |
| D12 | The Pages workflow **skips both jobs while the repo is private**, and runs `scripts/scrub-check.sh` before building. | No failing runs before Pages exists; a last scrub gate before anything goes live. |
| D13 | `removePathAccents = true`: Turkish characters are dropped from URLs (`için` → `icin`). | ASCII URLs are easier to share and to host. |
| D14 | The real lab-name denylist for the scrub check lives **outside** the repo. | The list itself would identify the lab. |
| D15 | No content license stated yet. | Emre's call. |

## 2026-10-04 ~20:28 — First post approved (Emre)

| # | Decision | Notes |
|---|---|---|
| D16 | **"Setting up SQL MCP for Azure SRE Agent" (TR + EN) is approved** and published (`draft: false`). The repository goes public and GitHub Pages is enabled after a pre-public audit of the full git history. | Making the repo public is done by Emre's assistant, not by this project's session. |
| D17 | Until Emre decides otherwise: **no license file**, **English at the root and Turkish under `/tr/`**, the **part 2 teaser stays**, the **SVG cover stays**. | D8, D15 and the PNG question remain open. |

## 2026-10-04 evening — Site live

| # | Decision | Notes |
|---|---|---|
| D18 | The repository is **public** and **GitHub Pages** is on: source "GitHub Actions", custom domain `sreagent.emreguclu.io` (domain verified at org level). Every push to `main` builds and deploys. | HTTPS enforcement is switched on separately, after Emre confirms DNS. |
| D19 | The build takes its base URL from `config/_default/hugo.toml` (`https://sreagent.emreguclu.io/`), not from `configure-pages`. | `configure-pages` reports `http://` until HTTPS is enforced, which put `http://` into canonical and social links on the first deploy. |
| D20 | **HTTPS is enforced** on Pages; `http://` redirects (301) to `https://sreagent.emreguclu.io/`. | Switched on 2026-10-04 evening, after the certificate was issued. |

## 2026-10-04 — Author profile (Emre, BIO-1)

| # | Decision | Notes |
|---|---|---|
| D21 | **The site carries no personal or career text about Emre** unless he has approved that exact text, relayed by his assistant. The author profile is his **name and title only**: "Azure Cloud Solution Architect" (EN), "Azure Bulut Çözüm Mimarı" (TR); no `bio`. | The earlier headline and bio had not been approved and were removed. Rule recorded in [writing-guide.md](writing-guide.md) §7. |

## 2026-10-04 — Who holds a privilege (Emre, SYSADMIN-NETLE)

| # | Decision | Notes |
|---|---|---|
| D22 | **Posts always separate who runs a privileged command from what the service identity gets.** In `sql-mcp-part-1` the step 2 and verification headings said "as sysadmin", which read as if the gMSA were sysadmin. They now say a DBA with sysadmin rights runs the commands, and step 2 states that the gMSA is not sysadmin and gets only `##MS_ServerPerformanceStateReader##` (2016–2019: `VIEW SERVER STATE`). | Rule recorded in [writing-guide.md](writing-guide.md) §7. The `IS_SRVROLEMEMBER('sysadmin', …)` checks expecting 0 stay. |

## 2026-10-06 — Post 2 topic and order of work (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D23 | **Post 2 topic: keeping Azure SRE Agent knowledge in a git repository** instead of uploading documents one by one: git as the single source, a CI step that pushes the docs into the indexed knowledge base, the same repo connected through Code Access, a pointer in the repo's root instruction file, and frequently used procedures packaged as skills. | The plan, the claim-by-claim evidence table and the open questions are kept outside the repo until a draft exists. |
| D24 | **No quotes and no attribution.** The post does not quote the internal answer that prompted it and does not attribute the guidance to any team or group. Every claim is stated in our own words and rests on public documentation (📄) or our own demo (✅). | POST2-ALINTI. |
| D25 | **Demo first, draft second.** The post is drafted only after a lab demo has shown the core claims. The demo uses a **private** repository; a public companion repository only on Emre's word. Every change to a live system (lab, agent, repo connection, document upload) needs the go of Emre's assistant and is logged before it starts. | POST2-DEMO, POST2-SIRA. |
