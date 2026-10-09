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

## 2026-10-06 — Post 2 answers (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D26 | **The post does not say the Learn docs are outdated.** It says the public docs are not yet clear on this point, so we settled it by testing in a lab. | P2-2. |
| D27 | **`srectl` is used** for the CI upload, even though it is not publicly released or official. The session obtains and installs it itself; if it cannot be obtained, the work stops and the session reports what it tried and what Emre needs to provide. | P2-5. The post still names the public alternative for readers who cannot get `srectl`. |
| D28 | **Title: "Keep Azure SRE Agent knowledge in git: one source, two paths"** (TR: "Azure SRE Agent bilgisini git'te tutmak: tek kaynak, iki yol"). | P2-6, option T-A. |
| D29 | **The demo runs on a fresh, clean agent in its own new resource group**, created only for the demo and deleted once the results are clear. No existing agent or resource group is touched. | P2-7. Deletion waits for Emre's word, relayed by his assistant. |
| D30 | **The session runs the live demo steps itself**, with an Azure identity loaded by direnv from outside the repo; secret values are never printed. Emre's go covers the demo plan's live steps (new resource group and agent, a private demo repo, GitHub Actions with OIDC and the SRE Agent Administrator role scoped to the demo agent only, document uploads, tests D-a to D-e) with an active-flow cap of 500 AAU, each step logged before it starts. Anything outside that plan stops and is asked. | P2-8. |
| D31 | **A new demo lab, including its own SRE Agent, is built for Post 2 and lives until the post is published.** It is torn down after publishing, on the word of Emre's assistant (amends D29: no teardown right after the demo). Tests that do not need `srectl` start now, and the knowledge upload is first proven through the public data-plane API. The `srectl` CI job is added when the package is available, and `srectl` stays the post's main path (D27). | `srectl` is not publicly released; the package is requested from Emre. |
| D32 | **For the private demo only, Code Access uses an existing GitHub credential of the assistant's account** instead of a new single-repo token, behind a four-layer guardrail: (1) the agent's instructions and the demo repo's root `AGENTS.md` limit it to the demo repo and forbid touching any other repository or opening PRs or issues elsewhere; (2) only the demo repo is connected, and the agent stays in Review mode with low access; (3) a demo test asks for another repository and must see a refusal, otherwise the work stops; (4) at teardown the Code Access connection is removed first, then the agent is deleted, and the credential is rotated. The credential is never printed, committed or logged. | Emre's explicit word, via his assistant. The guardrail is behavioral, not technical. **The post does not recommend a wide token**: it recommends a fine-grained, single-repo, read-only token. |
| D33 | **The demo keeps the credential from D32 after a finding: Code Access stores the repository credential in plain text inside the agent's sandbox, where the agent can read and use it.** The guardrail stays as it is; the credential is rotated at teardown. The post says that the token is visible in the agent's sandbox and recommends only a fine-grained, single-repo, read-only token. | Emre, via his assistant (TOK-B). Details are kept outside the repo. |
| D34 | **The post's main path for the knowledge sync is the public data-plane API**, through a Python script built from Emre's own bash example (endpoint from ARM, token for `https://azuresre.dev`, multipart upload, indexer status). `srectl` gets only a short note that a CLI exists but is not public yet. Replaces D27. | Emre (SRC-A), via his assistant. No public download source for `srectl` was found. The post credits Emre's example as the script's origin; names from his own lab never appear. |
| D35 | **Post 2 covers one path only: git → CI (`tools/sre_kb_sync.py`) → Knowledge.** Code Access appears only briefly, as the reason for this approach (a connected repository does not go into Knowledge). The root instruction file, its length limit, pointers in it and repository refresh behavior stay out of the post. The demo's Code Access connection and its credential are removed now. | Emre, via his assistant. Notes on the left-out findings are kept outside the repo. |

## 2026-10-06 — Post 2 approved (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D36 | **"Keep Azure SRE Agent knowledge in git: one source, two paths" (TR + EN) is approved and published.** "Two paths" means knowledge for the long tail and skills for weekly procedures, both from one repository. The script's origin stays worded as a bash snippet run by hand. PowerShell tabs stay, with a short note that they were not run by us and follow the documentation. After publishing, the demo lab is torn down and the private demo repository is archived. | TASLAK-ONAY, R-1, R-2, R-3. |

## 2026-10-08 — A lab per post (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D37 | **BLOG-LAB: every post that needs a demo gets its own lab.** By default it is built from the shared lab template with domain member servers, by the lab template's own session, and the details are handed to this project. A smaller, minimal lab is used only if this project proposes it with a reason, a cost estimate and a teardown plan, and Emre approves. The lab is torn down after its post is published (D31, D36). Another project's lab is never reused. | The template's name and the lab's names stay outside the repo (scrub denylist). This project does not build labs itself. |

## 2026-10-08 — Post 3 setup (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D38 | **Post 3 (restricting SRE Agent's VM commands with managed Run Command, `runAsUser`, a custom role and Azure Policy) is tested on its own lab's SRE Agent.** The agent's identity gets only Reader (already there) and the custom role, on the test VM only; both are removed at teardown. The Policy is assigned on the test VM, not the resource group. **The wrapping tool (the strongest level) is described in the post, not demonstrated.** **The run-as password lives only in the lab agent's instructions**; the session measures whether it appears in the agent's logs and the post shows the result as a warning. The value is never printed. | A2, L1, P1. Drafting starts only after the test results are relayed to Emre. |

## 2026-10-08 — Post 3 scope (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D39 | **Post 3 is short and plain, for people who give Azure SRE Agent's managed identity access to VMs.** Thesis: (1) a custom role that allows managed Run Command (`virtualMachines/runCommands/*` read and write) and leaves out action Run Command (`runCommand/action`, `az vm run-command invoke`, which runs as SYSTEM/root); (2) an Azure Policy that denies a managed run command with no `runAsUser` or a `runAsUser` outside an allowed list (example: `sre-agent`), and also one that pulls its script from a URI or gallery or writes output to a blob. Evidence is the API tests T1–T7 only (run as an admin identity; Policy holds for every caller); agent tests are not part of the post. Limits stated: Windows needs `runAsPassword` and the Secondary Logon service; at most 25 managed run commands per VM; scale sets and Arc machines are other resource types, out of scope; RBAC cannot check parameter values, which is why the Policy is needed; Policy applies to every caller at its scope, so assign it narrowly (we assigned it on the VM). It ends with a short warning that Emre may drop: the run-as password the agent uses ends up in its logs, so keep secrets out of its reach, keep secret-read roles off its identity, limit its network reach, review its on-behalf-of requests; a tool with its own identity is the stronger option, described only. | Replaces the four-level ladder in the earlier plan. Drafted outside the repo first; private preview; published only on Emre's approval. No change to the lab for this post. |

## 2026-10-09 — Review skill in the repo (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D40 | **The project skill `tech-blog-review` is added at `.claude/skills/tech-blog-review/SKILL.md`**, copied byte for byte from Emre's text; sessions edit it only on his word. It reviews or restructures a technical post for a newcomer reader: fact-check the load-bearing claims, structure, language, with a strong Turkish review. | Not part of the site: Hugo builds only from its own folders, and `.claude/` is not one of them. |

## 2026-10-09 — Review before approval (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D41 | **Every new post is reviewed with the `tech-blog-review` skill and fixed before Emre sees it for approval.** Flow: draft → review with `.claude/skills/tech-blog-review` (TR and EN each reviewed on its own terms) → apply the fixes → private preview with a short review summary (top findings, what was changed, anything left for Emre to decide) → Emre approves → publish. In the fix step, facts, commands and test results change only where the review flagged them, and anything Emre must verify is marked, as the skill says. The original draft is kept as a dated copy beside the draft, outside the repo. | Adds a step before D5's approval; D5 still holds. The flow is written out in `docs/writing-guide.md` §6. |
