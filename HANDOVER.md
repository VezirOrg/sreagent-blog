# HANDOVER — sreagent-blog

**Seven posts live; the black box series is on playbook v1.0.2 (live at 732df22, 2026-10-17). Open: giscus and
GoatCounter switch-on (wait for Emre's guide steps), 9 long titles (Emre's call), Post 5 not started.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. **Every push to `main` goes live** (`.github/workflows/pages.yml`,
which runs only on pushes to `main`; GitHub skips the run when the pushed tip commit says `[skip ci]`, so never push a
post change with a `[skip ci]` commit on top). Drafts, reviews, test logs, data and raw notes stay outside the repo, in
the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` next (D1–D132).

## Open items

1. **giscus ON (D128) and GoatCounter code (D129)** wait for Emre's steps in the Turkish guide
   `files/blog-etkilesim-seo-rehberi.md` (giscus app install, optional "Comments" category, GoatCounter signup, Search
   Console, Bing). When his answers come through the owner:
   - `config/_default/params.toml`: `giscus.enabled = true`; if he made the "Comments" category, replace the category
     and categoryId (now Announcements `DIC_kwDOU7kPL84DIc5a`) with its ID from
     `gh api graphql` (repository → discussionCategories). Repo ID `R_kgDOU7kPLw`.
   - `goatcounter.code = "<his code>"` (loads only in production builds).
   - Push, then check a live post: the giscus frame loads in the page's language; GoatCounter's script is in `<head>`.
2. **9 of 14 titles are over 60 characters** (Google may cut them). They are Emre's approved wording; shortening is his
   call (a shorter SEO title would need his words). Details in `files/seo-audit-261015.md`.
3. Smaller, left on purpose (audit): `og:locale` is `en`/`tr` rather than `en_US`/`tr_TR`; the home background image has
   no `alt` (theme partial, decorative).
4. **Post 5 (monthly cost report, D76–D94):** text not started. The real run is October's data, exported by the monthly
   schedule around 2026-11-05; needs a rebuilt lab (recipe in `files/post5-files/lab-log.md`) and Emre's go. It links to
   the black box series as the same pattern (export → private storage → skill → SQLite). Skill v0.2 not now (D94).
5. Still open from 2026-10-13, unchanged: docs vs test on the agent's sandbox (D52; `notes/261013-post5-sandbox-test.md`:
   a venv `pip install` worked although Learn says no pip/outbound); two Post 4 threads of 2026-10-10 and the first blind
   run's AAU reading (`files/post4-files/aau/`); site-wide content license.

## Posts (all live, `content/posts/<slug>/`, EN + TR)

| Slug | Title (EN) | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | ee094f7 (description, social.png) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline | a3f1d0e (D122 PowerShell tab), ee094f7 |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | ee094f7 |
| `perfmon-blackbox-part-1` | A black box for Windows servers, part 1: record first, ask later | 732df22 (v1.0.2 default line) |
| `perfmon-blackbox-part-2` | … part 2: set it up and know what it costs | 732df22 (v1.0.2, D131) |
| `perfmon-blackbox-part-3` | … part 3: inside the machine | a3f1d0e, ee094f7 |
| `perfmon-blackbox-part-4` | … part 4: the agent investigates | a3f1d0e, ee094f7 |

TR series title "Windows sunucular için kara kutu"; part 1 TR "… bölüm 1: Sorun çıkmadan kayıt başlasın" (D119).
Purposes: Part 1 D117, Part 2 D106, Part 3 D99 as edited (D126), Part 4 D114; earlier posts in D53.

## The black box series (D115–D132)

- Four parts (D115): need → setup and cost → inside the machine → the agent investigates (arc1, quiet hour and staged
  hour, 95/100). Source: VezirOrg/sreagent-playbook `playbooks/perfmon-blackbox`; the shared lab belongs to the playbook
  project (D96); this project built no lab. Lab names dc, iis1, arc1 only (D100).
- **Release state:** Part 2 points at playbook release `perfmon-blackbox/v1.0.2` (release/tag, clone branch, package URL,
  `--version 1.0.2`, doc links, default `ExportEveryHours` 1); Part 1's default line says v1.0.2 runs hourly by default.
  Zip SHA-256 `806bcadb…63dd` (unchanged since v1.0.0) checked live on 2026-10-17. **Kept at v1.0.1 on purpose (D132,
  KALSIN):** Part 2's "configuration version 1.0.1" and its screenshot alt text, "fixed … at v1.0.1" and the "Fixed in
  v1.0.1" table header; Part 3's tree link and v1.0.1 wording. They describe what the lab ran and measured. A future
  playbook release follows the same pattern (D127/D131): Emre's go, one commit, preview, his YAYINLA.
- Markers ✅ / 📄 / 🔎 (D44, D113). Every admin-machine shell example comes as zsh + PowerShell tabs, an unrun PowerShell
  variant marked 📄 (D116); commands that run only on a Windows server stay one block (D121).
- TR is written, not translated; "kara kutu", never "uçuş kaydedicisi" (D118, writing-guide).
- Part 1 says why not Log Analytics in two sentences, the cost one 📄 with a Learn link (D124).
- Cost message: roughly 3.5 to 5 USD per deep-dive analysis, depending on region (D105). Storage writes stay under
  0.01 USD per server a day at hourly exports (playbook cost.md).
- Never in a post: the playbook's bug B1 (D101), the agent's onboarding thread (D102); every consumption crop hides that
  row and the sidebar. Raw screenshots are never edited; crops and masks are copies.
- Links between parts: `{{< relref "/posts/perfmon-blackbox-part-N" >}}` (resolves in the page's language).
- Drafts, reviews and the TR change log stay in `files/perfmon-blackbox-part-{1..4}-draft/` and
  `files/perfmon-blackbox-tr-pass-261014.md`; the v1.0.2 diff in `files/perfmon-blackbox-part-2-draft/v102-update-261016.diff`.

## SEO, comments, analytics (D128–D130, ee094f7)

- Each post bundle has `social.png` (1200 × 630, rendered from `feature.svg`) and `images: ["social.png"]`; the site
  keeps the SVG. Site default `static/img/social-default.png`. Descriptions ≤ 160 characters. Both rules are in the
  archetypes and the writing-guide §1 checklist.
- Site overrides (theme untouched): `layouts/partials/extend-head-uncached.html` (hreflang x-default + GoatCounter),
  `schema.html` (BlogPosting with image and publisher; a copy of Blowfish v3.8.0's), `article-comments.html` and
  `comments.html` (giscus, posts only, behind the param).
- Discussions are enabled on the repo. GitHub's API cannot create a discussion category.
- Lighthouse (mobile, live): SEO 100, performance 99–100 on `/`, part 2 EN, part 1 TR. Audit: `files/seo-audit-261015.md`.
- To render a social.png from an SVG: headless Chromium from the Playwright cache, 1200 × 630 window, screenshot.

## Labs

- **No blog lab is up.** Post 4's (old) and Post 5's labs are DOWN. Not ours, never touch: the frozen Post 3 lab, the
  SQL MCP project's lab, the playbook's shared lab, Emre's demos.
- Rules (D37, D47, D50, D58, D90): a lab comes from the shared lab template with a register row in the same step;
  credentials only via `direnv exec`; lab, storage and template names never in this repo; teardown keeps a rebuild
  recipe in `files/`; remove extra role assignments before `azd down`.

## Standing rules

- **Publishing flow (D5, D41):** draft in `files/<slug>-draft/` → scrub → review skill → keep a dated original → private
  preview → Emre approves → `draft: false`, commit `post: publish <slug>`. Nothing goes live without his approval.
- **WIKI FIRST:** record a decision in `docs/decisions.md` (a `[skip ci]` commit) before the change it governs.
- **Parking work that waits for approval:** push it to a `pending/<topic>` branch (publishes nothing), keep `main` at
  `origin/main`. On approval: rebase onto `main`, scrub + build, fast-forward `main`, push, check live, delete the branch
  (`git branch -D` after `git merge-base --is-ancestor` — the rebased branch differs from its old remote copy).
- **Scrub gate (D58):** local git hooks run `scripts/scrub-check.sh` (pre-commit staged, pre-push tracked tree minus the
  theme); hooks live in `.git/hooks/`, recreate them if missing. Denylist `files/scrub-denylist.txt` (never committed).
  D109 allows the built-in Storage Blob Data Reader role ID.
- Before every push to `main`: scrub, local `hugo` build, link check. Record-only commits carry `[skip ci]`.
- Covers 1200 × 630 (D75). Purpose first (D53). Docs vs our result: list for Emre, never resolve (D52). Never "ürün
  grubu". No personal text about Emre on public pages without his approval. Mask third-party data; customer lessons
  never name or hint at a customer; real names from Post 4's data never appear anywhere, and the masking mappings are
  never deleted or overwritten.
- The rig's secret guard blocks a Bash command whose text names a secret-like variable, even inside file content; write
  such files with the Edit/Write tools and report the false positive to the owner.

## Where things are

- `docs/decisions.md` (D1–D132), `docs/writing-guide.md` (§1 checklist, §4 scrub, §5 TR/EN, §6 flow).
- `.claude/skills/tech-blog-review/SKILL.md` (Emre's review skill, verbatim, D40). `scripts/scrub-check.sh`.
- Preview build: copy the tracked repo plus `themes/` to a scratch folder,
  `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts`, publish as a private claude.ai artifact.
- Private (`files/`): series drafts, `seo-audit-261015.md`, `blog-etkilesim-seo-rehberi.md` (Emre's guide),
  `retrofit-sre-agent-knowledge-in-git/`, `post4-files/`, `post5-files/`, `post6-draft/` (superseded by the series).

## Later

- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first Pages run after it.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11). `schema.html` is a copy of the theme's:
  re-check it on a theme upgrade.
- Google Drive's file provider sometimes returns "Resource deadlock avoided"; work in the scratchpad and retry.

## Last session (2026-10-17, on demand)

On Emre's YAYINLA (via the owner): recorded D132 (publish; the three v1.0.1 mentions stay, KALSIN), rebased the parked
v1.0.2 update onto `main` with no conflicts, scrub and build clean, fast-forwarded and pushed `main` to 732df22. Pages
run 39010914368 succeeded. Live Part 1 and Part 2, EN and TR: 200, all six v1.0.2 links 200, zip SHA-256 matches on
both Part 2 pages. Branch `pending/v102-update` deleted (local and remote).
