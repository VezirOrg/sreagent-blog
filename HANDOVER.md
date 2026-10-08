# HANDOVER — sreagent-blog

**Live with 2 posts (TR+EN). Post 3 (restricting SRE Agent's VM commands with managed Run Command) is on hold: API tests passed, agent tests stopped, its lab is still up; waiting on Emre's decision for how the post continues.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English. This repository is public, history included: everything committed must pass the scrub rules in
`docs/writing-guide.md` §4. Internal discussion, raw notes and unapproved material stay outside the repo, in `files/`.

## Post 3 — where it stands (2026-10-08)

Topic: limit what SRE Agent can run on a VM with a ladder of controls: (1) an instruction, (2) a custom role with
managed Run Command (`runCommands/*`) but no `runCommand/action`, (3) an Azure Policy Deny on `runAsUser` and on
external script/output URIs, (4) a wrapper tool, described only (D38). The lab is its own (D37), built and owned by the
lab template's session; this project does not tear it down.

- **Done:** plan, role, policy and test script (`files/post3-runcommand/`); the policy aliases checked live; API tests
  T1–T7 as an admin identity all passed: no `runAsUser`, another user, `scriptUri`, output blob and PATCH to another
  user are all denied at deploy time; the allowed user runs as a non-admin; `invoke` is outside the role.
- **Not done:** agent tests A2–A5 and a meaningful password-in-logs count (T8; a read-only baseline exists). They stay
  unrun unless Emre says otherwise.
- **Still in place in the lab** (teardown list and full log in `files/post3-runcommand/`, private): the run-as local
  user on the test VM, the custom role and its assignment, the policy definition and assignment, an SRE Agent
  Administrator assignment for this project's identity on the lab agent, and leftover managed run commands on the test
  VM. Leave them until the vezir says; nothing is deleted without its word.
- **Open for Emre (via his assistant):** how Post 3 continues and who writes it; rotation of the lab's shared
  credentials.
- Private record: `files/tartisma.md` (2026-10-08 entries) and `files/post3-runcommand/261008-post3-plan.md` §8–§9.
  Some of that material must never reach the post or this repo; read the rules at the top of those entries first.

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D38). Read it first.
- `docs/writing-guide.md`: what every post must have, front matter, shortcodes, scrub checklist, TR/EN parity, review flow.
- `content/posts/<slug>/`: one page bundle per post (`index.en.md`, `index.tr.md`, `feature.*`). Live:
  - `sql-mcp-part-1`: "Setting up SQL MCP for Azure SRE Agent", series part 1.
  - `sre-agent-knowledge-in-git`: "Keep Azure SRE Agent knowledge in git: one source, two paths", standalone.
- `notes/261006-post2-demo-lab.md`: frozen record of the Post 2 lab run: what was proven, what was measured but left
  out of the post, other findings, and the full live-change log (L1–L10).
- `archetypes/posts/`: `hugo new content posts/<slug>` creates a TR+EN bundle with every required section.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus a lab-name denylist kept outside the
  repo in `files/scrub-denylist.txt`). The Pages workflow runs it before every build.
- `.github/workflows/pages.yml`: every push to `main` builds with Hugo 0.167.0 extended and deploys to Pages.
  The base URL comes from `config/_default/hugo.toml` (D19). Record-only commits (HANDOVER, docs, notes) carry
  `[skip ci]` in the message.
- `themes/blowfish`: git submodule pinned at v3.8.0. Upgrading the theme means moving the submodule in its own commit.
- `layouts/shortcodes/site-topics.html`: the series and tags block on the home page.

Outside the repo (`files/`, Drive): `tartisma.md` (discussion log), `post3-runcommand/` (Post 3 plan, IaC, tests, private log), `261006-post2-plan.md`, `post2-demo/` (results
table `sonuclar.md`, raw evidence, the `srectl` search), `post2-draft/` (the approved draft as sent for review).

## Standing rules

- **Author profile (D21):** no personal or career text about Emre unless he approved that exact text, relayed by his
  assistant. Name + headline only.
- **Privileges (D22):** always say who runs a privileged command separately from what the service identity gets.
- **Sources (D24):** no quotes from internal answers and no attribution to any team or group; claims rest on public
  docs (📄) or our own lab (✅).
- **Live systems:** every change to a live system needs the go of Emre's assistant and is logged before it starts.
  Every post that needs a demo gets its own lab, built by the lab template's session and torn down after publishing
  (D37). Credentials come from Drive `.env` files via `direnv exec`; values are never printed.

## Session 2026-10-06

Post 2 went from plan to published in one session: Emre's answers recorded (D26–D35), a fresh demo agent in its own
resource group, a private demo repository with a GitHub Actions sync, tests D-a…D-e, the draft, approval (D36),
publish (commit 8fa96aa, Pages run green, both language pages 200), then teardown (L10): resource group deleted, no
role assignments left, the private demo repository archived. Final meter: 191.4 AAU for the day. Details:
`notes/261006-post2-demo-lab.md`.

The GitHub credential used for Code Access during the demo (D32, D33) was removed from the agent at ~10:00 UTC;
**its rotation is with Emre's assistant**.

## Publishing a post

1. Write both languages with `draft: true` **outside the repo** (`files/<post>-draft/`), because every push to `main`
   deploys and the repo is public. Pass `scripts/scrub-check.sh <path>` on the draft.
2. Build a private preview: copy the repo to a scratch folder, add the bundle under `content/posts/`, then
   `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo -s . --buildDrafts --baseURL / -d <tmp>/site`; drop `CNAME`,
   `*.xml`, `*.json`; rewrite relative links ending in `/` (including bare `../`) to `…/index.html`. Publish as a
   private claude.ai artifact whose cover page links into the built site (88 files for Post 2).
3. Emre approves → add a D-entry, set `draft: false` in both languages, copy the bundle into `content/posts/<slug>/`,
   commit `post: publish <slug>`, push. The workflow deploys in about a minute. Check
   `https://sreagent.emreguclu.io/posts/<slug>/` and `/tr/posts/<slug>/` answer 200 (a single 503 right after deploy
   happened once and cleared on retry).

Run at most one `hugo server` at a time on this machine, and stop it afterwards. One-off `hugo` builds are enough for checks.

## Open decisions for Emre

Site-wide, unchanged since 2026-10-04; the current state holds until he answers (D17):

- **LIS-CC, the content license**: none is stated. Suggested: CC BY 4.0 for text, MIT for code snippets. Currently no
  license file and only "© 2026 Emre Güçlü" in the footer.
- **Language layout**: English at the root, Turkish under `/tr/` (D8). Keep or flip.
- **Part 2 teaser**: the first post ends with "Next in the series: monitoring this setup". Keep (and write it) or drop.
- **PNG cover**: feature images are SVG, which social link previews do not render. A 1200 × 630 PNG next to each would
  fix that; this machine has no SVG-to-PNG converter, so either install one or Emre supplies the images.

## Later

- GitHub Actions: `actions/checkout@v4`, `configure-pages@v5` and `upload-pages-artifact@v3` target Node 20 and are
  being forced onto Node 24. Move to versions built for Node 24 when they exist.
- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. Watch the first run after that date; the workflow only needs
  `curl`, `dpkg` and the Hugo `.deb`.
- Blowfish v3.8.0 declares support for Hugo up to 0.166; Hugo 0.167 prints a compatibility warning but builds cleanly
  (D11). Re-check when either moves.
- `configure-pages` is still in the workflow but its base URL is no longer used (D19); it can stay or go.
- Two subscription-level ARM deployment-history records from the demo lab remain (not resources, no cost). They can be
  deleted if wanted.
