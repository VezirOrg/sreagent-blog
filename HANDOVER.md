# HANDOVER — sreagent-blog

**Live with 1 post (SQL MCP part 1, TR+EN). Post 2 (SRE Agent knowledge in git) is planned; a lab demo comes before any draft, and five questions to Emre are open (2026-10-06).**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English. This repository is public, history included: everything committed must pass the scrub rules in
`docs/writing-guide.md` §4. Internal discussion, raw notes and unapproved material stay outside the repo.

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D25). Read it first.
- `docs/writing-guide.md`: what every post must have, front matter, shortcodes, scrub checklist, TR/EN parity, review flow.
- `content/posts/<slug>/`: one page bundle per post (`index.en.md`, `index.tr.md`, `feature.*`).
  Live: `sql-mcp-part-1`, "Setting up SQL MCP for Azure SRE Agent", series part 1.
- `archetypes/posts/`: `hugo new content posts/<slug>` creates a TR+EN bundle with every required section.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus a lab-name denylist kept outside the repo).
  The Pages workflow runs it before every build.
- `.github/workflows/pages.yml`: every push to `main` builds with Hugo 0.167.0 extended and deploys to Pages.
  The base URL comes from `config/_default/hugo.toml` (D19). Record-only commits (HANDOVER, docs) that must not
  redeploy carry `[skip ci]` in the message.
- `themes/blowfish`: git submodule pinned at v3.8.0. Upgrading the theme means moving the submodule in its own commit.
- `layouts/shortcodes/site-topics.html`: the series and tags block on the home page.

## Author profile (D21)

The site carries **no personal or career text about Emre** unless he approved that exact text, relayed by his assistant.
`config/_default/languages.{en,tr}.toml` hold name + headline only ("Azure Cloud Solution Architect" /
"Azure Bulut Çözüm Mimarı"), no `bio`. The home pages show the headline; post pages show the name only. Rule is also in
`docs/writing-guide.md` §7 and the Turkish summary.

## Privileges in posts (D22)

Always say **who runs** a privileged command separately from **what the service identity gets** (writing guide §7).
`sql-mcp-part-1` was fixed accordingly on 2026-10-04 (commit 8ec0082).

## Post 2 — SRE Agent knowledge in git (D23–D25)

Topic: keep runbooks in a git repo as the single source; a CI step pushes them into the indexed knowledge base; the
same repo is connected through Code Access; the repo's root instruction file points to the runbooks; frequent
procedures become skills.

- **The plan lives outside the repo**, in `files/261006-post2-plan.md` (Drive). It holds the title options, the
  outline (skeleton only), an evidence table for 13 claims (📄 public doc / ✅ demo / still unproven), the demo plan
  (§5: tests D-a…D-e, private demo repo, GitHub Actions CI, evidence handling, cost and time) and the questions.
  Discussion log: `files/tartisma.md`. The internal source (`files/261006-post2-kaynak-…`) never enters the repo.
- **Rules (D24, D25):** no quotes from the source and no attribution to any team or group; every claim rests on public
  docs or our own demo. Demo first, draft second. The demo repo is private (VezirOrg); a public companion repo only on
  Emre's word.
- **Live-change rule:** every change to a live system (lab, agent, repo connection, document upload, Entra app, role)
  needs the go of Emre's assistant, and is written into the log below **before** it starts.
- **Findings so far (public sources only, no lab run):**
  - `srectl` is not publicly released (Microsoft's own sre-agent repo says so; not on NuGet on 2026-10-06), and
    `srectl doc upload` is undocumented. Public equivalents: `azmcp sreagent docs memories add` and the data-plane
    `/api/v1/agentmemory/upload` and `DELETE …/document/{name}`.
  - Learn contradicts itself: older pages say a connected repo is indexed as knowledge; a newer page moves repos to
    Code Access. Only demo test D-a settles it.
  - Injection of `AGENTS.md` into every turn and its ~3,000-character limit are not documented publicly (demo D-c).
- **Blocked:** checking whether the agent in the running lab resource group is fit for the demo. This Mac has no
  `az` login and no Azure credentials in `.env`. The read-only checklist is in plan §5.3. The other lab is down.

### Live-change log

Format: date, approved by, what is about to change, then the result. Lab names are kept out of this file (they are in
the scrub denylist in `files/`).

- **L1 · 2026-10-06 · go: Emre via his assistant (D30, D31).** Create a new resource group in Sweden Central holding a
  new SRE Agent built from Microsoft's IaC templates (`minimal` recipe: managed identity, Log Analytics, App Insights),
  Review mode, low access, monthly limit **500 AAU**. The agent monitors only its own new resource group. The deploying
  identity gets SRE Agent Administrator on this agent (template default); Emre's account gets the same role on this
  agent only. Nothing else is touched. Result: done. The template's deployer role assignment hardcodes a user principal
  and failed for a service principal; patched locally to `ServicePrincipal` and redeployed. Baseline: 0 knowledge
  sources, 0 repos, 0 skills, 0 connectors, limit 500 AAU.
- **L2 · 2026-10-06 · go: D30, D31.** Create the private demo repo under VezirOrg with the canary runbooks,
  `AGENTS.md` and a knowledge-sync workflow (manual trigger only until D-a is done). Result: done, private.
- **L3 · 2026-10-06 · go: D30, D31.** CI identity: a user-assigned managed identity in the demo resource group with a
  GitHub OIDC federated credential (demo repo, `main` branch only) and SRE Agent Administrator on the demo agent only.
  No Entra app, no secret, no other role. Result: done; the identity holds exactly one role assignment.
- **L4 · 2026-10-06 · go: D32.** Guardrail layer 1 on the demo agent: a common prompt limiting it to the demo repo (the
  same text sits at the top of the demo repo's `AGENTS.md`). Result: done. Whether a common prompt reaches the main
  agent on every turn is not documented; the refusal test shows whether layer 1 works.
- **L5 · 2026-10-06 · go: D32.** Register a GitHub credential on the demo agent (never printed) and connect **only**
  the demo repo through Code Access. Review mode and low access stay. Result: done; one repo, clone ready.
- **L6 · 2026-10-06 · go: D30, D31.** Knowledge uploads from CI: the demo repo's workflow runs on push to `main`
  (paths `docs/**`) and by hand, and uploads the runbooks to the demo agent's knowledge base through the public
  data-plane API; deleted files are deleted from the knowledge base. Test changes: one runbook edited, one deleted.
  Result: done. Uploads and push trigger work; the documented single-document delete answered HTTP 500 although the
  document was gone, so the sync script now verifies deletes against the file list.
- **L7 · 2026-10-06 · go: D30, D31 (test D-e).** Add one runbook to the demo repo (uploaded by CI) and the same
  procedure as one skill on the demo agent, with different canaries, to see which one the agent uses. Result: done.
- **L8 · 2026-10-06 · go: D30, D31 (within L5).** The Code Access clone had not refreshed 70 minutes after several pushes.
  Try to refresh it: first the documented repo connectivity test, then, if needed, re-save the same single repo
  connection. Nothing else changes. Result: _pending_.

## Publishing a post

1. `hugo new content posts/<slug>`; write both languages with `draft: true`. Pass `scripts/scrub-check.sh` before every
   commit: drafts are public in the repo too.
2. Build a private preview and send it for review:
   `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo -s . --buildDrafts --baseURL / -d <tmp>/site`, then drop
   `CNAME`, `*.xml`, `*.json`, and rewrite relative links ending in `/` to `/index.html` for static hosting.
   The first post's preview was a private claude.ai artifact whose cover page links into the built site.
3. Emre approves → set `draft: false` in both languages, commit `post: publish <slug>`, push. The workflow deploys
   in about a minute. Check `https://sreagent.emreguclu.io/posts/<slug>/` and `/tr/posts/<slug>/` answer 200.
4. Add a D-entry for the approval in `docs/decisions.md`.

Run at most one `hugo server` at a time on this machine, and stop it afterwards. One-off `hugo` builds are enough for checks.

## Open decisions for Emre

Post 2 (asked 2026-10-06; full options in the plan §6, answer as `P2-x=letter`):

- **P2-2** Say publicly that the Learn docs are outdated? A openly / B with dated evidence, softly / C no / D decide
  after the demo (recommended: D, leaning B).
- **P2-5** `srectl`: A Emre provides a build and access, it becomes the main path / B public path only, `srectl` noted
  as "not yet public" / C not mentioned (recommended: A if possible, else B).
- **P2-6** Title: T-A "Keep Azure SRE Agent knowledge in git: one source, two paths" (recommended) / T-B / T-C.
- **P2-7** Demo agent: A a separate clean agent, deleted afterwards (recommended) / B the existing lab agent, only if
  the §5.3 checklist is clean.
- **P2-8** Who runs live steps: A Emre or his assistant, guided by the session / B the session gets an Azure identity
  via `.env`, with a go before each step.

Earlier, site-wide:

The current state holds until he answers (D17):

- **LIS-CC, the content license**: none is stated. Suggested: CC BY 4.0 for text, MIT for code snippets. Currently no
  license file and only "© 2026 Emre Güçlü" in the footer.
- **Language layout**: English at the root, Turkish under `/tr/` (D8). Keep or flip.
- **Part 2 teaser**: the first post ends with "Next in the series: monitoring this setup". Keep (and write part 2) or drop.
- **PNG cover**: the feature image is SVG, which social link previews do not render. A 1200 × 630 PNG next to it would
  fix that; this machine has no SVG-to-PNG converter, so either install one or Emre supplies the image.

## Later

- GitHub Actions: `actions/checkout@v4`, `configure-pages@v5` and `upload-pages-artifact@v3` target Node 20 and are
  being forced onto Node 24. Move to versions built for Node 24 when they exist.
- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. Watch the first run after that date; the workflow only needs
  `curl`, `dpkg` and the Hugo `.deb`.
- Blowfish v3.8.0 declares support for Hugo up to 0.166; Hugo 0.167 prints a compatibility warning but builds cleanly
  (D11). Re-check when either moves.
- `configure-pages` is still in the workflow but its base URL is no longer used (D19); it can stay or go.
