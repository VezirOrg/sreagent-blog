# HANDOVER — sreagent-blog

**Live with 2 posts (TR+EN). Post 3 draft (VM Run Command: custom role + Azure Policy on `runAsUser`) still waits on Emre's approval; nothing published. New posts are now reviewed with `tech-blog-review` and fixed before Emre sees them (D41).**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English. This repository is public (D18), history included: everything committed must pass the scrub rules in
`docs/writing-guide.md` §4. Internal discussion, raw notes and unapproved material stay outside the repo, in `files/`.

## Post 3 — where it stands (2026-10-09)

Scope is D39: a custom role that allows managed Run Command and leaves out action Run Command (`invoke`), plus an Azure
Policy that denies a managed run command without an allowed `runAsUser` (and with a script URI, gallery script or blob
output). Short, plain, for people giving SRE Agent's managed identity VM access. It ends with a warning box about the
run-as password reaching the agent's logs, which Emre may drop.

- **Draft:** `files/post3-draft/sre-agent-vm-run-command/` (`index.en.md`, `index.tr.md`, `feature.svg`), `draft: true`,
  scrub-clean, TR/EN parity checked (same sections, 21 ✅ and 20 📄 in each). Slug `sre-agent-vm-run-command`.
- **Private preview:** https://claude.ai/artifact/WsjKAqUNLMHxSAiXhPS6dd (cover page linking into the built site; the
  site's own home page could not be included, so "home" links land on the cover). Sent to the vezir for Emre.
- **Inputs used, and only these:** `files/post3-runcommand/iac/` (role JSON, policy JSON, `p3-tests.sh`) and
  `files/post3-runcommand/evidence/api-tests-admin.log`. Open nothing else in that folder for this post.
- **Evidence notes (told to the vezir):**
  1. T4 (`invoke` outside the role) is **not in the log**; the log holds T1, T2, T3, T5, T6, T7. The post marks T4 📄
     (by the role's definition) and tells readers to test it on their own agent.
  2. "Password not returned by GET" is **not in the log** either. The post claims only what the log shows: the create
     response carries `runAsUser` but no password (✅).
  3. The App Insights measurement of the password in the agent's logs is not in the input files; the draft marks it ✅
     on the vezir's word. **The vezir recommends changing it to 📄** (the docs say the agent's tool inputs are logged),
     pending Emre. Not changed yet.
  All T tests ran as an admin identity; the post says so and why the Policy results still hold for the agent.
- **On approval:** apply Emre's changes (incl. the ✅→📄 above if he agrees) to both languages, add a D-entry, set
  `draft: false`, copy the bundle into `content/posts/sre-agent-vm-run-command/`, commit `post: publish
  sre-agent-vm-run-command`, push, check both URLs answer 200 (see "Publishing a post").
- **The Post 3 lab must NOT be torn down** (Emre's decision, 2026-10-09; overrides the teardown-after-publishing default
  of D37 for this lab). Nothing in it is changed or deleted by this project.
- **Credentials:** Emre decided no rotation. Do not raise it.

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D41). Read it first.
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill (D40), verbatim from his text. Use it to review or
  restructure a post (fact-check the key claims, structure, language, strong Turkish review). Edit it only on his word.
  Since D41 it is a fixed step of the publishing flow (below).
  Hugo does not build `.claude/`, so it never reaches the site (checked with a full build, 2026-10-09). The repo is
  public, so the skill text is public too; the vezir was told.
- `docs/writing-guide.md`: what every post must have, front matter, shortcodes, scrub checklist, TR/EN parity, and
  the publishing flow in §6 (draft → review → fix → preview → approval → publish).
- `CLAUDE.md`: short pointer for sessions to this file and the publishing flow.
- `content/posts/<slug>/`: one page bundle per post (`index.en.md`, `index.tr.md`, `feature.*`). Live:
  - `sql-mcp-part-1`: "Setting up SQL MCP for Azure SRE Agent", series part 1.
  - `sre-agent-knowledge-in-git`: "Keep Azure SRE Agent knowledge in git: one source, two paths", standalone.
- `notes/261006-post2-demo-lab.md`: frozen record of the Post 2 lab run (findings, live-change log L1–L10).
- `archetypes/posts/`: `hugo new content posts/<slug>` creates a TR+EN bundle with every required section.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus a lab-name denylist kept outside the
  repo in `files/scrub-denylist.txt`). The Pages workflow runs it before every build.
- `.github/workflows/pages.yml`: every push to `main` builds with Hugo 0.167.0 extended and deploys to Pages. Base URL
  from `config/_default/hugo.toml` (D19). Record-only commits (HANDOVER, docs, notes) carry `[skip ci]`.
- `themes/blowfish`: git submodule pinned at v3.8.0. Moving it is its own commit.
- `layouts/shortcodes/site-topics.html`: the series and tags block on the home page.

Outside the repo (`files/`, Drive): `tartisma.md` (discussion log), `post3-runcommand/` (Post 3 plan, IaC, tests, private
log), `post3-draft/` (the draft above), `261006-post2-plan.md`, `post2-demo/`, `post2-draft/`.

## Standing rules

- **Author profile (D21):** no personal or career text about Emre unless he approved that exact text, relayed by his
  assistant. Name + headline only.
- **Privileges (D22):** always say who runs a privileged command separately from what the service identity gets.
- **Sources (D24):** no quotes from internal answers and no attribution to any team or group; claims rest on public
  docs (📄) or our own lab (✅).
- **Live systems:** every change to a live system needs the go of Emre's assistant and is logged before it starts.
  Labs are built by the lab template's session (D37). Credentials come from Drive `.env` files via `direnv exec`;
  values are never printed.
- The session brief template says to make this repo private if found public; that conflicts with D18. Leave it public.

## Session 2026-10-09 (publishing flow)

On Emre's word, via the vezir: added D41 (review with `tech-blog-review` and fix before Emre sees a post) and wrote the
new flow into `docs/writing-guide.md` §6 (plus the checklist and Turkish summary), this file and a new `CLAUDE.md`.
Post 3 not touched.

## Session 2026-10-09 (skill)

On Emre's word, via the vezir: added D40 (commit 5b48869), then copied his `tech-blog-review` skill into
`.claude/skills/` byte for byte (commit d094d3c, sha256 matched). Both commits carry `[skip ci]`. Post 3 untouched; its
approval gate is still open with Emre.

Before that (2026-10-08/09): recorded Post 3's scope (D39), wrote the TR+EN draft and the private preview, reported to
the vezir. No Azure changes.

## Publishing a post

The flow is D41, written out in `docs/writing-guide.md` §6. Emre sees a post only after steps 1–3.

1. **Draft** both languages with `draft: true` **outside the repo** (`files/<post>-draft/`). Pass
   `scripts/scrub-check.sh <path>`.
2. **Review** with `.claude/skills/tech-blog-review`, TR and EN each on its own terms. Save the review as
   `files/<post>-draft/review-YYMMDD.md`.
3. **Fix.** Copy the draft bundle to `files/<post>-draft/original-YYMMDD/` first (never edit that copy), then apply the
   fixes to both languages. Facts, commands, code and test results (✅/📄 too) change only where the review flagged
   them; mark anything Emre must verify. Re-run the scrub check.
4. **Private preview** with a short **review summary** on its cover page: top findings, what was changed, what is left
   for Emre to decide. Build: copy the repo (without `files`, `.git`) to a scratch folder, add the bundle under
   `content/posts/`, then `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo -s . --buildDrafts --baseURL / -d
   <tmp>/site`; drop `CNAME`, `*.xml`, `*.json`; rewrite relative links ending in `/` to `…/index.html`. Publish as a
   private claude.ai artifact whose cover page links into the site; the site's root `index.html` cannot be a
   supporting file, leave it out. Republishing an existing preview from a new session: pass its URL as `url` after
   reading it. Send the link to the vezir for Emre.
5. **Emre approves** (his changes go back into the bundle, then a new preview) → D-entry, `draft: false` in both
   languages, copy the bundle into `content/posts/<slug>/`, commit `post: publish <slug>`, push. Check
   `https://sreagent.emreguclu.io/posts/<slug>/` and `/tr/posts/<slug>/` answer 200 (a single 503 right after deploy
   happened once and cleared on retry).

Run at most one `hugo server` at a time on this machine, and stop it afterwards.

## Open decisions for Emre

- **Post 3:** approve the draft (or changes); keep or drop the closing warning; ✅→📄 on the App Insights claim
  (vezir recommends 📄). Its draft and preview predate D41 and were not reviewed with the skill; whether Post 3 goes
  through the D41 review first is Emre's call. Do not review it until he says so.
- Site-wide, unchanged since 2026-10-04 (D17 holds until he answers): **content license** (suggested CC BY 4.0 text,
  MIT code); **language layout** (EN root, TR under `/tr/`); **Part 2 teaser** in the first post; **PNG covers** for
  social previews (no SVG-to-PNG converter on this machine).

## Later

- GitHub Actions `checkout@v4`, `configure-pages@v5`, `upload-pages-artifact@v3` target Node 20; move to Node 24 builds
  when they exist. `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first run after that.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11). Re-check when either moves.
- `configure-pages` is unused for the base URL (D19); it can stay or go.
- Two subscription-level ARM deployment-history records from the Post 2 demo lab remain (no cost); deletable if wanted.
