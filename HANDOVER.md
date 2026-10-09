# HANDOVER — sreagent-blog

**Post 4 (PerfMon triage skill) in step 2: skill v1.1 passed locally and ran on SRE Agent; next is v1.2 and two
reruns (D59). Three posts live; Post 4's lab is UP until Post 4 is published.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, data and raw notes stay outside the
repo, in the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` (D1–D59) next.

## Next steps

1. **Post 4, V (D59), first thing:**
   - Write skill v1.2 from v1.1 (`files/post4-files/skill/perfmon-triage-v1.1/`) with the four method fixes:
     - the verdict word follows the breach table (no breach ⇒ at most "warning");
     - `series()` prints the time of each bucket's peak;
     - a step that tests a causal link in time ("does X still grow after Y stopped?");
     - a helper that computes a leak's rate per request.
   - Never put an answer from the baseline into the skill; fix the method only.
   - Run one local blind round (fresh subagent, masked DB only, same prompt; see `skill-test-rounds.md` for set-up
     and rubric) and score it.
   - Emre updates the skill in the portal (Builder > Agent Canvas). The lab's deploying identity cannot write skills:
     data plane 403, ARM not available in this tenant.
   - Rerun on the lab's agent in a NEW thread with the same prompt (`q-blind.txt` and
     `agent-chat.sh` in the lab evidence folder). Add the result to `agent-vs-local.md`.
   - Emre re-reads the first run's AAU in the portal (his owner reminds him).
2. Post 4's slug, outline and drafting have not started. The purpose is in D56; drafting follows the D5/D41 flow.
3. Site-wide questions for Emre, unchanged since 2026-10-04 (D17 holds until he answers):
   - the content license;
   - the language layout;
   - the Part 2 teaser;
   - PNG covers.

## Posts (all live, `content/posts/<slug>/`)

| Slug | Title (EN) | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | 2026-10-09, reviewed version, d7a4a69 (D46–D49) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline | 2026-10-09, thesis rework, b472bfc (D51–D55) |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | 2026-10-09, first publish, ea1e84f (D43–D45) |

Every post's purpose is a sentence in `docs/decisions.md` (D53, D54; Post 4: D56).

## Post 4 (in progress, nothing drafted)

**Purpose (D56, Emre's words, he may reword):** find the critical performance problems in a real, anonymised 24-hour
PerfMon capture whose cause is unknown, and dig into the ones that make the machine hard to use. Azure SRE Agent does
this by querying the capture as a SQLite database through a skill, without burning tokens on raw data.

**Data:**
- Data rules (D57):
  - The capture is a friend's real 24-hour capture. Only the host name was anonymised.
  - It was **masked before any use**, with placeholders for app pool, site, queue, service, agent and product names.
  - Only the masked database is used anywhere (tests, Azure).
  - The real→placeholder mapping lives only on Drive, kept permanently with a dated backup. It restores real names
    for the private hand-over to the data owner.
- Tools (public, no names): `tools/perfmon_csv_to_sqlite.py` (CSV → SQLite) and `tools/perfmon_mask.py` (mask from a
  private mapping). The masking tool also rebuilds the index statistics and checks the raw bytes of the file.
- Ground truth (`baseline-findings.md`, SQL + numbers):
  - Nothing makes the machine hard to use.
  - F1: the IIS worker process leaks handles in step with requests (~19–20 per 1,000).
  - F2: native memory grows at night without load.
  - F3: single-sample blips.

**Results so far:**
- Local blind rounds (fresh Claude Code subagent, Claude Opus 5.5):
  - Round 1 (v1.0) made 3 errors, all in how the helpers printed.
  - Round 2 (v1.1) passed with 0 wrong figures, at ~55 k tokens and 6 runs.
- SRE Agent run (2026-10-09; model Claude Opus 4.6 and 2.5 AAU, both as Emre read them in the portal):
  - The agent loaded the skill by itself.
  - It pulled the 335 MB database from the lab's private storage in its terminal.
  - It found F1 and F2, invented no crisis, and linked the nonpaged pool to F1 (local round 2 missed that link).
  - It made 4 wrong figures and one unsupported causal claim, and labelled a trend "Critical".
  - Its 2.5 AAU looks too low for Opus 4.6 rates (lower bound ~3.9); the analysis is in `agent-vs-local.md`.
- The data reaches the agent through its terminal (VNet egress, managed identity), not the code interpreter. The
  skill's `perfq.py` is a real file in the agent's terminal.

**Files** (`files/post4-files/`, private):
- `baseline-findings.md`, `skill-test-rounds.md`, `skill/` (v1, v1.1).
- `capture-masked.db` (+ `.zip`; sha256 of the db starts 600ffc40). The original CSV is beside it.
- `mask-mapping.csv` + `mask-mapping-261009.csv`: **never delete or overwrite.**
- The lab log `*-log-full.md` (all steps, Q1–Q4 answers). An older short log beside it stayed locked by Drive; the
  full one replaces it.
- The lab evidence folder: threads, prompts, the chat script.
- `agent-vs-local.md`.
- For the data owner (Turkish, offline HTML, real names): `findings-real-names.html`,
  `findings-agent-real-names.html`, `agent-vs-local.html`.

## Labs

- **Rules (D37, D47, D50, D58):**
  - Each post gets its own lab, built by this project from the shared lab template.
  - Use the next free env name from the template's register (`docs/labs.md` there), with a register row in the same
    step.
  - Credentials only via `direnv exec`.
  - Lab and template names never go into this repo.
  - Teardown when the post is published, with a rebuild recipe kept in `files/`.
  - No test of a post's claim is driven through SRE Agent itself (D43). For Post 4 the agent run IS the subject.
- **Post 4's lab is UP** (built 2026-10-09, ~$21/day):
  - reduced: domain controller + one IIS VM (D58);
  - register reason: "skill v1.2 rerun pending";
  - name, resource IDs and the rebuild commands are in the lab log in `files/post4-files/`.
  - Tear it down when Post 4 is published, and set the register row to DOWN in the same step.
- Post 3's original lab is FROZEN evidence: never touch it. Never touch other projects' labs.

## Standing rules

- **Scrub gate (D58 addition):**
  - Local git hooks run `scripts/scrub-check.sh`: pre-commit on the staged files, pre-push on the tracked tree minus
    the theme.
  - The hooks live in `.git/hooks/` and are not committed. Recreate them if missing.
  - A flagged change is fixed before commit.
  - One older record-only commit with lab names stays in history (Emre: no rewrite).
- **Purpose first (D53).**
- **Docs vs our result (D52):** list conflicts for Emre and never resolve them yourself.
- **Markers (D44):** every claim keeps ✅ or 📄.
- **Author profile (D21).**
- **Privileges (D22).**
- **Sources (D24, D26).**
- **Repo public (D18).**
- **Post 4 data (D57):** masked before any use; real names never in the repo, the post, the agent or a message
  between sessions.
- In messages to other sessions, refer to Emre by name (or "they").

## Where things are

- `docs/decisions.md` (D1–D59), `docs/writing-guide.md` (§4 scrub, §5 TR/EN parity, §6 flow).
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill, verbatim (D40).
- `scripts/scrub-check.sh`: the scrub gate; the denylist is `files/scrub-denylist.txt` (never committed).
- `tools/`: the PerfMon converter and the masking tool.
- `.github/workflows/pages.yml`: builds and deploys on push to `main`. Record-only commits carry `[skip ci]`.
- Publishing flow and preview build: `docs/writing-guide.md` §6.
  - Preview: copy the tracked repo plus `themes/` to a scratch folder, then
    `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts`.
  - Publish it as a claude.ai artifact.

## Later

- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first Pages run after it.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11).
- Google Drive's file provider on this Mac intermittently returns "Resource deadlock avoided". Restarting Drive fixed
  it once. Keep working copies in the session scratchpad and sync with retries.

## Last session (2026-10-09 evening → 10-10)

Post 4, steps 1 and 2:
- D56 (purpose), D57 (masking) and D58 (lab, scrub gate) recorded.
- Converter and masking tools written; masked database verified.
- Baseline analysis done; skill written and tested in two local blind rounds.
- Lab built and the masked data uploaded; data path tested (Q1–Q4).
- Emre created the skill in the portal; one blind SRE Agent run.
- Three Turkish HTML reports for the data owner.
- D59 recorded (X, K, V).
