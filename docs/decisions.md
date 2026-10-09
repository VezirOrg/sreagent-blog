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
| D37 | **BLOG-LAB: every post that needs a demo gets its own lab.** *(Amended by D47: this project builds the lab itself; the "who builds" part below is superseded.)* By default it is built from the shared lab template with domain member servers, by the lab template's own session, and the details are handed to this project. A smaller, minimal lab is used only if this project proposes it with a reason, a cost estimate and a teardown plan, and Emre approves. The lab is torn down after its post is published (D31, D36). Another project's lab is never reused. | The template's name and the lab's names stay outside the repo (scrub denylist). ~~This project does not build labs itself.~~ Superseded by D47. |

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

## 2026-10-09 — Existing posts through the review (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D42 | **Every existing post goes through the D41 flow: Post 1 (`sql-mcp-part-1`), Post 2 (`sre-agent-knowledge-in-git`), both live, and the Post 3 draft. They are archived first.** "Archive" means keeping the current versions untouched; nothing is taken offline. Live posts stay live, unchanged, until Emre approves their reviewed versions; slugs, front matter and URLs stay as they are. Archive scheme: (1) an annotated git tag `posts-pre-review-261009` on `main` before any review change, pushed; (2) dated, untouched copies outside the repo in `files/archive/261009-pre-review/`: both live bundles (`index.tr.md`, `index.en.md`, `feature.svg`) and the Post 3 draft folder as it was. The archive is never edited afterwards. Order, per the skill's rule for several posts: Post 3 first; Posts 1 and 2 start only after Emre's OK on the direction. | Reviewed versions of the live posts are drafted in `files/<slug>-draft/` like new posts, and go live only by a `post:` commit after approval. |

## 2026-10-09 — Findings that need a test (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D43 | **A review finding that would change a tested thing is tested before it is applied.** "Tested thing": a command, code, sample output, test result, ✅/📄 marker, step order, or a new claim or alternative. Flow: (1) the review writes a **test plan** for each such finding: what to test, in which lab, the expected result and the pass criterion; (2) the session runs the tests in the post's own lab itself; (3) only changes whose tests **passed** are applied, and a newly tested claim gets ✅ with its public-safe result in the post; (4) the fixed post is reviewed **again**; (5) a clean second review goes on to the preview without asking; (6) a finding is **stuck** when its test fails, cannot be run, or the second review flags it again: it stops there, and a short plain report goes to Emre per finding (what the review wanted, what the test showed, the options). Emre decides. | Lab rules: tests run as an admin identity against the ARM API, the way the original post tests ran; **no test is driven through SRE Agent itself** (those stay Emre's; a finding that needs one is stuck). A lab that will be shown to others is left exactly as found: roles, policies and assignments restored, nothing that was there deleted; a stopped VM may be started and left running. If a post's lab is not up, none is built; that is a decision for Emre. **Post 3 (Emre, 2026-10-09):** its original lab is frozen evidence and is never touched again; the review's tests run in a new lab built for them by the lab template's session (as it was done for Post 3; from D47 on, this project builds labs itself), where the session applies the custom role and the Policy itself by following the post's own steps, which tests the steps too. Test logs stay outside the repo in `files/`. Where docs and our lab disagree, the lab result stands unless a new test changes it. UI strings stay as the UI shows them. Wording and structure fixes need no test. |

## 2026-10-09 — Post 3 approved; marker rule; Posts 1 and 2 (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D44 | **Every claim keeps its own ✅ or 📄 marker, in every post.** The blog's own rule (writing guide §2) wins over the `tech-blog-review` skill's "mark only the exceptions" line; a review does not flag marker density. | Blog-wide. The skill file is not edited (D40); this decision is the override. |
| D45 | **Post 3 (`sre-agent-vm-run-command`) is approved for publishing** after the review, the D43 lab tests and a second review, with these answers: Secondary Logon keeps the documented 📄 line and adds our ✅ result (run-as worked in our lab even with the service disabled); the App Insights password claim is 📄; User Access Administrator in the prerequisites is tested in the test lab before it keeps ✅ (if it fails, publishing stops for Emre); the error-blob test is added to the Verification table as T8; the Turkish description says "yalnızca" and matches the new Verification intro. | Tests ran as identities against the ARM API in a test lab built for the review, never through SRE Agent (D43). |
| D46 | **Posts 1 and 2 get language and structure fixes only, with no lab tests.** Every ✅ claim the session cannot confirm was actually run goes into a list for Emre; then a private preview and review summary, as for Post 3. They are not published without Emre's approval; until then the live versions stay as they are. | Starts after Post 3 is live. Archive from D42 stays the baseline. |

## 2026-10-09 — Who builds a post's lab (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D47 | **Amends D37: this project builds each post's lab itself, from the shared lab template.** D37 recorded Emre's 2026-10-06 words wrongly as "built by the lab template's own session". The blog session runs the template's `azd` from the template's own checkout, always with an explicit `-e <env>` and the next free env name per the template's lab register (`docs/labs.md` there); never while a session of the template project is open; credentials only via `direnv exec` in that checkout, never printed. **Every lab the blog builds or tears down gets its row in that lab register in the same step.** The rest of D37 stands: an own lab per post, member-server lab by default, a minimal lab only on this project's proposal and Emre's OK, another project's lab never reused, lab and template names on the scrub denylist. | Teardown timing is not changed by this entry; Emre is still deciding it. D37's note "this project does not build labs itself" is replaced by this entry. |

## 2026-10-09 — Posts 1 and 2 answers (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D48 | **Posts 1 and 2: E-1, DOC-1, U-1, Y-2.** **E-1:** fix inconsistencies inside each post from its own data and records (which number is which, timings stated as recorded, markers that disagree, sample output vs layout, variables set where the reader needs them, "try it locally" before the workflow step, Turkish terms and description, a marker on every claim). **DOC-1:** where Microsoft Learn now disagrees with our lab, keep the lab result and add the doc's statement as 📄 beside it; where the post's *reason* is now wrong, correct the reason. **U-1:** every ✅ without a record is made honest: 📄 where a doc backs it, narrowed to the recorded part where it says more than was run, softened or removed where neither backs it; each change is listed in the review summary. **Y-2:** the optional appendix move for Post 1's lab-diary tables is done only if it touches no code, anchor or front-matter-linked heading. Then a short second review (D43, no lab tests per D46) and an updated private preview listing every changed claim. Not published until Emre approves the preview. | Code blocks stay unchanged except the lines that set `$SUB`/`$ENDPOINT` in Post 2. |

## 2026-10-09 — Posts 1 and 2 approved (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D49 | **Posts 1 (`sql-mcp-part-1`) and 2 (`sre-agent-knowledge-in-git`) are approved for publishing** in the D48 version, with these answers: **L-E:** both legend extensions stay, so 📄 also covers "read from code, not run"; **H-K:** Post 1's Turkish Finding 3 heading stays as it is (no anchor change); **UI:** the connector path is written exactly as the portal shows it, and where the record does not show the portal's form, the live post's current form stays; **DAB-E:** every 📄 claim that rests on DAB source code gets a link to that source beside it. Links to the two renumbered Post 2 step headings are fixed if any page uses the old anchors. | Language and evidence fixes only; no lab tests (D46). |

## 2026-10-09 — When a post's lab is torn down (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D50 | **Option A: a post's lab is torn down when the post is published, as D37 says.** Before the teardown the session keeps, in `files/` (private), what is needed to rebuild the lab quickly: the **build recipe** (the template env settings, the post-specific objects and the exact commands that created them) and the **test scripts and test plan**. A later D43 re-test rebuilds the lab from that recipe (D47 rules) instead of keeping a lab up. The teardown gets its row in the template's lab register in the same step (D47). | Settles the open A/B/C teardown question. Post 3's original lab stays frozen evidence (Emre, 2026-10-09); this entry does not change that. |

## 2026-10-09 — Post 2's thesis (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D51 | **Post 2 (`sre-agent-knowledge-in-git`) is rebuilt around Emre's thesis, which is its purpose:** (1) adding knowledge to SRE Agent today means uploading Markdown files by hand, which is practical at the start; (2) managing the documents in a git repository is the better option for many reasons, but there is no such feature yet; (3) a repository connected through Code Access is **not** indexed as knowledge: its documents do not become knowledge; (4) so the documents live in a git repository of their own, a custom script pushes them into the agent's knowledge through the API, and a pipeline runs it on every update. Title, description, introduction, solution at a glance and conclusion are built on (1)→(4); the body (script, pipeline, tests) mostly stays. **Supersedes D28 and D36 where they differ:** "one source, two paths" is no longer the frame, and skills are no longer a headline path (where the skills section goes is Emre's call). D35 stands in substance (one path: git → CI → Knowledge; Code Access as the reason), with Code Access now carrying point (3) up front. The Code Access result stays ✅ as tested (empty knowledge list, 0 memory hits, answered by Grep over the clone); the post separates "the agent can read the repository" from "the documents are indexed as knowledge", and Learn's wording stays 📄 as Learn writes it (D26: never "outdated"). Point (2) is stated only as far as the evidence supports it. **Emre's portal check (2026-10-09):** the current SRE Agent portal has no option to add a repository as knowledge (no **Builder > Knowledge base > Add repository**, although Learn still describes one); repositories connect only through Code Access. The post states it without calling the docs outdated (D26): the docs describe adding a repository as a knowledge source (📄); the portal, as of October 2026, has no such option (✅, observed); a repository connected through Code Access was not indexed as knowledge (✅, 2026-10-06 test). Our 2026-10-06 test connected the repository through the agent's API as a Code Access repository (cloned into the Code Access folder), not through the portal. **Point (2) narrowed (Emre, 2026-10-09, settling D52 conflict C-1):** the portal has a **Documentation connector** whose settings point to Azure DevOps (his observation; not tried); Learn says it crawls an Azure DevOps wiki or Git repository every 24 hours (📄, not tested by us). So the post branches early: documents in Azure DevOps → the Documentation connector; documents on GitHub → no built-in way, this post's method. Point (2) reads "for GitHub there is no built-in way", not "no such feature". Point (3) unchanged. The body stays the GitHub path. | Flow: archive the live version (`files/archive/261009-pre-thesis/`, never edited), rework in `files/<slug>-draft/`, one `tech-blog-review` round and fixes, private preview with the options, publish only on Emre's approval. Tested content changes only per D43/D44; no new untested claims; the slug and URL do not change. |

## 2026-10-09 — When the docs contradict our result (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D52 | **Standing rule: when Microsoft Learn or other vendor docs contradict one of our test results, or Emre's own portal observation, the session does not resolve it.** No automatic "add the doc's line 📄 beside ours", no rewording toward the doc, no dropping our result. It lists the conflict (what the doc says, its link and the date it was seen; what we observed and where it is recorded) and asks Emre through his assistant; the post text stays as it is until he answers. | Replaces the blanket DOC-1 handling of D48 for every future review. Already-decided points stay decided (Post 2's Code Access point: D51). First use: Post 2's C-1 (Azure DevOps Documentation connector) went to Emre and he settled it (D51). |

## 2026-10-09 — A post's purpose comes first (Emre, via his assistant)

| # | Decision | Notes |
|---|---|---|
| D53 | **Standing rule: every post's purpose is written as one sentence in this file, with Emre's approval, before any draft is written.** Every review takes the purpose from that entry (the `tech-blog-review` skill's §1 "Purpose") and never infers it from the post. **Post 2 (`sre-agent-knowledge-in-git`), from D51:** "Show that adding knowledge to Azure SRE Agent today means uploading files by hand, that documents on Azure DevOps have a built-in Documentation connector while documents on GitHub have no built-in way (a repository connected through Code Access does not become knowledge), so GitHub documents belong in a git repository of their own, pushed into the agent's knowledge by a custom script that a pipeline runs on every update." (Narrowed after C-1, 2026-10-09; wording awaits Emre's OK.) Posts 1 and 3: one-sentence purposes are proposed to Emre and recorded here only once he approves them. | Rule written into `docs/writing-guide.md` §6 (planning and review steps). |

