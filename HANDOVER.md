# HANDOVER — sreagent-blog

**Live with 3 posts (TR+EN), all reviewed (D41–D49) and published. Nothing in draft, no lab up for this project;
lab teardown rule settled (D50: tear down on publish, keep a rebuild recipe in `files/`).**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, internal discussion and raw notes stay
outside the repo, in the gitignored `files/`. Read `CLAUDE.md` and `docs/decisions.md` (D1–D50) next.

## Posts (all live, `content/posts/<slug>/`)

| Slug | Title | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | 2026-10-09, reviewed version, commit d7a4a69 (D46–D49) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git: one source, two paths | 2026-10-09, reviewed version, commit d7a4a69 (D46–D49) |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | 2026-10-09, first publish, commit ea1e84f (D43–D45) |

What the 2026-10-09 review round settled, blog-wide:
- Every claim keeps its own ✅ or 📄 (D44). 📄 also covers "read from code, not run" (D49: Post 1's legend names DAB
  source and the portal's code, Post 2's names the code shown in the post). 📄 claims resting on DAB source link to the
  DAB v2.1.5 source, pinned by tag.
- Posts 1 and 2 got language, structure and evidence fixes only, no lab tests (D46, D48). A ✅ with no record was made
  📄, narrowed or removed. Post 1 now has an "Appendix: lab measurements" (`#appendix`). Post 2's steps 4 and 5 were
  swapped (try locally before the workflow).
- Post 3's review findings were tested in a separate test lab before they were applied (D43, D45).

Working files, all in `files/` (private): per post `<slug>-draft/` with the working bundle, a frozen
`original-261009/` (read-only) and `review-261009.md` (full review, ✅ trace, every change before → after). Post 3 also
has `post3-draft/test-plan-261009.md`, `test-results-261009.md`, `review-261009.md` and
the test log in `post3-review-tests/`. Private previews (claude.ai artifacts, match the live versions):
Post 3 https://claude.ai/artifact/WsjKAqUNLMHxSAiXhPS6dd · Posts 1–2 https://claude.ai/artifact/SU2nRazmywzJcXWRTkrw5n.

## Labs

- **Rules (D37 as amended by D47):** each post gets its own lab, which this project builds itself from the shared lab
  template: `azd -e <env>` from the template's checkout, next free env name from the template's lab register, never
  while a template session is open, credentials only via `direnv exec` there and never printed. Every build or
  teardown gets its row in the template's lab register in the same step. Lab and template names never go into the
  repo (scrub denylist in `files/`). Every change to a live system needs the go of Emre's assistant and is logged
  before it starts. No test is driven through SRE Agent itself (D43).
- **Teardown (D50, option A):** a post's lab is torn down when the post is published. Before teardown, keep in
  `files/` the build recipe (template env settings, post-specific objects, exact commands) and the test scripts and
  test plan, so a later D43 re-test rebuilds the lab instead of keeping it up. Teardown gets its lab-register row.
  Post 3's rebuild recipe (written after the fact): `files/post3-draft/rebuild-recipe.md`, scripts in
  `files/post3-review-tests/scripts/`.
- **Post 3's original lab is FROZEN evidence: never touch it** (Emre, 2026-10-09).
- **Post 3's test lab** (built for the D43 tests) was torn down on 2026-10-09, 13:02–13:13, by the template's session
  after Post 3 went live; it left nothing behind (its custom role and policy deleted first). To rebuild it, use the recipe above.
- **Post 2's lab** was torn down on 2026-10-06 (L10 in `notes/261006-post2-demo-lab.md`).

## Open decisions for Emre

- Site-wide, unchanged since 2026-10-04 (D17 holds until he answers): content license (suggested CC BY 4.0 text, MIT
  code); language layout (EN root, TR under `/tr/`); the Part 2 teaser in the first post; PNG covers for social
  previews (no SVG-to-PNG converter on this machine).

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D50). Read it first.
- `docs/writing-guide.md`: what every post must have, scrub checklist (§4), TR/EN parity (§5), the publishing flow
  (§6, D41/D43) and the lab rules (after §6, D47).
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill (D40), verbatim; edit only on his word. The blog's own
  marker rule overrides its "mark only the exceptions" line (D44).
- `CLAUDE.md`: short pointer to this file and the publishing flow.
- `notes/261006-post2-demo-lab.md`: frozen record of the Post 2 lab run.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus the lab-name denylist kept in
  `files/scrub-denylist.txt`). The Pages workflow runs it before every build.
- `.github/workflows/pages.yml`: every push to `main` builds (Hugo 0.167.0 extended) and deploys. Record-only commits
  carry `[skip ci]`; a publish commit does not.
- `themes/blowfish`: submodule pinned at v3.8.0. `archetypes/posts/`: TR+EN bundle template.
- Outside the repo (`files/`): `tartisma.md` and `post3-runcommand/evidence/` hold private material that must never reach
  a post; open them only when a task explicitly needs them.

## Publishing a post

Follow D41/D43 as written in `docs/writing-guide.md` §6: draft in `files/` → `tech-blog-review` (TR and EN each on its
own terms) → keep `original-YYMMDD/`, fix → tests in the post's own lab for anything that changes a tested thing → second
review → private preview with a review summary → Emre approves → D-entry, `draft: false`, bundle into
`content/posts/<slug>/`, commit `post: publish <slug>`, push, check EN and TR URLs answer 200 and show the new text.

Preview build that works: copy the tracked repo plus `themes/` to a scratch folder, put the bundle(s) under
`content/posts/`, run `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo -d <tmp>/site`, drop `CNAME`, `*.xml`, `*.json`,
rewrite relative links ending in `/` to `…/index.html`, leave out the root `index.html`, and publish a cover page with
the site files through the artifact `files` map (`root` = the scratch folder). To update an existing preview from a new
session, read it first and pass its URL.

## Standing rules

- **Purpose first (D53):** every post's purpose is one sentence in `docs/decisions.md`, approved by Emre before any
  draft; reviews take it from there. Post 2's is recorded; Posts 1 and 3 are proposed, awaiting Emre.
- **Docs vs our result (D52):** when Learn or vendor docs contradict our test result or Emre's portal observation, never
  resolve it yourself; list the conflict (doc text, link, date seen; our observation, where recorded) and ask Emre.
- **Author profile (D21):** no personal or career text about Emre unless he approved that exact text. Name + headline.
- **Privileges (D22):** say who runs a privileged command separately from what the service identity gets.
- **Sources (D24):** no quotes from internal answers, no attribution to any team; claims rest on public docs (📄) or
  our own lab (✅).
- Leave the repository public (D18), even where a generic session brief says otherwise.
- In messages to other sessions, refer to Emre by name (or "they"), not by a guessed pronoun.

## Later

- GitHub Actions on Node 20 actions; `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first run after.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11).
- Two subscription-level ARM deployment-history records from the Post 2 demo lab remain (no cost).

## Last session (2026-10-09, late)

Recorded Emre's teardown decision as D50 (option A) in `docs/decisions.md`, the writing guide's Labs paragraphs (EN, TR)
and here (d97f6d4). Post 3's test lab had already been torn down by the template's session; wrote its rebuild recipe
after the fact (`files/post3-draft/rebuild-recipe.md`) and saved the dc test scripts from an old scratchpad into
`files/post3-review-tests/scripts/` (fd2afa4). Earlier that day: Post 3 tested, reviewed and published (ea1e84f);
Posts 1 and 2 reviewed and republished (d7a4a69); D44–D49.
