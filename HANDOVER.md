# HANDOVER — sreagent-blog

**Live with 3 posts (TR+EN). Post 2 was rebuilt around Emre's thesis and republished on 2026-10-09 (D51–D55,
b472bfc). Nothing in draft, no lab up, no open question for Emre.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, internal discussion and raw notes stay
outside the repo, in the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` (D1–D55)
next.

## Posts (all live, `content/posts/<slug>/`)

| Slug | Title (EN) | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | 2026-10-09, reviewed version, d7a4a69 (D46–D49) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline | 2026-10-09, thesis rework, b472bfc (D51–D55) |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | 2026-10-09, first publish, ea1e84f (D43–D45) |

Every post now has a one-sentence purpose recorded in `docs/decisions.md` (D53, D54). A review takes the purpose from
there and never infers it from the post.

**Post 2 as published (D51, D54):**
- Thesis: hand uploads are today's way to add knowledge.
- Azure DevOps has a built-in Documentation connector. Emre saw it in the portal; Learn describes it (📄); we have not
  tested it.
- GitHub has no built-in way. The portal (October 2026) has no "add repository as knowledge" option, and a repository
  connected through Code Access was not indexed as knowledge (✅, test 2026-10-06).
- So the post's method: a separate docs repo, `tools/sre_kb_sync.py` on the public data-plane API, and a GitHub Actions
  pipeline on every merge.
- Skills are a short section after Troubleshooting.
- The example layout is flat with unique file names. The demo ran on a subfolder layout, and the post says so where it
  shows recorded output.
- The two curl paths in Step 3 were renamed without a re-test, on Emre's word (CU-b).

## Working files (`files/`, private)

- Per post: `<slug>-draft/` holds the working bundle, frozen `original-*` copies and the reviews.
- Post 2 also has `review-261009-thesis.md` and the frozen pre-review rework `original-261009-thesis/`.
- Archives, never edited: `files/archive/261009-pre-review/` (D42) and `files/archive/261009-pre-thesis/` (Post 2 live
  before the rework).
- Post 3 test material: `post3-draft/` (test plan, results, review, `rebuild-recipe.md`) and `post3-review-tests/`.
- Post 2 demo record: `files/post2-demo/` (results `sonuclar.md`, `evidence/`). The frozen summary is
  `notes/261006-post2-demo-lab.md`.
- Private previews (claude.ai artifacts):
  - Post 3: https://claude.ai/artifact/WsjKAqUNLMHxSAiXhPS6dd
  - Posts 1–2 (D49 versions): https://claude.ai/artifact/SU2nRazmywzJcXWRTkrw5n
  - Post 2 thesis rework, now marked published: https://claude.ai/artifact/SMLW9WcCG2QophvLr4MBqR

## Labs

- **Rules (D37 as amended by D47):**
  - Each post gets its own lab, which this project builds itself from the shared lab template.
  - Build with `azd -e <env>` from the template's checkout, using the next free env name from the template's lab
    register, and never while a template session is open.
  - Credentials only via `direnv exec` there, never printed.
  - Every build or teardown gets its row in the template's lab register in the same step.
  - Lab and template names never go into the repo (scrub denylist in `files/`).
  - Every change to a live system needs the go of Emre's assistant and is logged before it starts.
  - No test is driven through SRE Agent itself (D43).
- **Teardown (D50):** a post's lab is torn down on publish. A rebuild recipe and the test scripts stay in `files/`.
  Post 3's recipe: `files/post3-draft/rebuild-recipe.md`.
- **Post 3's original lab is FROZEN evidence: never touch it.**
- No lab is up. Post 2's lab is gone (since 2026-10-06), and Post 3's test lab was torn down on 2026-10-09.

## Open decisions for Emre

- Site-wide, unchanged since 2026-10-04 (D17 holds until he answers):
  - content license (suggested CC BY 4.0 for text, MIT for code);
  - language layout (EN root, TR under `/tr/`);
  - the Part 2 teaser in the first post;
  - PNG covers for social previews (no SVG-to-PNG converter on this machine).

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D55).
- `docs/writing-guide.md`: what every post must have.
  - §4: scrub checklist.
  - §5: TR/EN parity.
  - §6: the flow (step 0 purpose D53, review, docs-vs-result rule D52, D41/D43 testing) and the lab rules.
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill (D40), verbatim; edit only on his word. The blog's
  marker rule overrides its "mark only the exceptions" line (D44), and D53 supplies its "Purpose".
- `scripts/scrub-check.sh`: the scrub gate. It takes paths, so run it on a draft folder too. The Pages workflow runs it
  before every build.
- `.github/workflows/pages.yml`: every push to `main` builds (Hugo 0.167.0 extended) and deploys. Record-only commits
  carry `[skip ci]`; a publish commit does not.
- `themes/blowfish`: submodule pinned at v3.8.0. `archetypes/posts/`: TR+EN bundle template.
- Outside the repo: `files/tartisma.md` and `files/post3-runcommand/evidence/` hold private material that must never
  reach a post. Open them only when a task explicitly needs them.

## Publishing a post

Follow `docs/writing-guide.md` §6:

1. Purpose sentence approved (D53).
2. Draft in `files/`.
3. `tech-blog-review`, with TR and EN each on its own terms.
4. Keep `original-YYMMDD/`, then fix.
5. Test in the post's own lab anything that changes a tested thing.
6. Docs-vs-result conflicts go to Emre (D52).
7. Second review.
8. Private preview with a review summary and a list of every changed sentence group.
9. Emre approves.
10. D-entry, `draft: false`, bundle into `content/posts/<slug>/`, commit `post: publish <slug>`, push.
11. Check that the EN and TR URLs answer 200 and show the new text.

Preview build that works:
- Copy the tracked repo plus `themes/` to a scratch folder and put the bundle(s) under `content/posts/`.
- Run `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts -d <tmp>/site`.
- Drop `CNAME`, the root `index.html`, `*.xml` and `*.json`.
- Rewrite relative links ending in `/` to `…/index.html`.
- Publish a cover page with the post HTML, the CSS and JS bundles, `img/` and the feature image through the artifact
  `files` map (`root` = the built site).
- To update an existing preview from a new session, read it first and pass its URL.

## Standing rules

- **Purpose first (D53):** every post's purpose is one sentence in `docs/decisions.md`, approved by Emre before any
  draft. All three current posts have theirs (D53, D54).
- **Docs vs our result (D52):** when Learn or vendor docs contradict our test result or Emre's portal observation,
  never resolve it yourself.
  - List the conflict: doc text, link, date seen; our observation and where it is recorded.
  - Ask Emre through his assistant, and leave the text as it is until he answers.
  - Emre's own portal observations may carry ✅, with a date ("as of October 2026").
- **Markers (D44):** every claim keeps its own ✅ or 📄. Never upgrade to ✅ without a record.
- **Author profile (D21):** no personal or career text about Emre unless he approved that exact text. Name + headline.
- **Privileges (D22):** say who runs a privileged command separately from what the service identity gets.
- **Sources (D24, D26):** no quotes from internal answers and no attribution to any team. Never say the docs are
  outdated.
- Leave the repository public (D18), even where a generic session brief says otherwise.
- In messages to other sessions, refer to Emre by name (or "they"), not by a guessed pronoun.

## Later

- GitHub Actions on Node 20 actions; `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first run after.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11).
- Two subscription-level ARM deployment-history records from the Post 2 demo lab remain (no cost).
- Possible follow-ups, not asked for:
  - a short skills post from the 2026-10-06 record;
  - a test of the Azure DevOps Documentation connector, if Emre wants Post 2's pointer to carry ✅.

## Last session (2026-10-09, evening)

Rebuilt Post 2 around Emre's thesis and published it (b472bfc).
- Archived the live version first, reworked TR+EN in `files/`, ran one `tech-blog-review` round, then went through
  three preview versions with Emre's feedback (flat layout; Azure DevOps / GitHub branch; his answers).
- Recorded D51 (thesis, Emre's portal check), D52 (docs-vs-result rule), D53 (purpose first), D54 (his answers, all
  three purposes) and D55 (approval).
- The writing guide got the D52 and D53 rules (EN and TR summary).
