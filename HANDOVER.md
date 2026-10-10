# HANDOVER — sreagent-blog

**Post 4 (PerfMon triage skill) in step 2: skill v1.1 ran on SRE Agent for 4 servers (1 blind, 3 with the symptom
stated); next is skill v1.2 and its rerun (D59 V). Three posts live; Post 4's lab is UP until Post 4 is published.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, data and raw notes stay outside the
repo, in the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` (D1–D61) next.

## Next steps

1. **Post 4, V (D59), first thing:**
   - Write skill v1.2 from v1.1 (`files/post4-files/skill/perfmon-triage-v1.1/`) with the four method fixes:
     - the verdict word follows the breach table (no breach ⇒ at most "warning");
     - `series()` prints the time of each bucket's peak;
     - a step that tests a causal link in time ("does X still grow after Y stopped?");
     - a helper that computes a leak's rate per request.
   - Never put an answer from the baseline into the skill; fix the method only.
   - The 3-server runs (below) show the same weak spots: a growth rate that isn't there, a wrong timestamp, and an
     unproven causal link (high kernel pool blamed on one process's handles). They support the same four fixes; they
     are not answers to put into the skill.
   - Run one local blind round (fresh subagent, masked DB only, same prompt; see `skill-test-rounds.md` for set-up
     and rubric) and score it.
   - Emre updates the skill in the portal (Builder > Agent Canvas). The lab's deploying identity cannot write skills:
     data plane 403, ARM not available in this tenant.
   - Rerun on the lab's agent in a NEW thread with the same prompt (`q-blind.txt` and
     `agent-chat.sh` in the lab evidence folder; `agent-chat.sh` needs `ep.txt` beside it, the agent endpoint from
     the agent's ARM `properties.agentEndpoint`). Add the result to `agent-vs-local.md`.
2. **Open for Emre (ask through the owner):**
   - **Masking judgement (2026-10-10):** on the 3 new DBs the masking tool's raw-byte scan still flags two 3-letter
     names. They occur by chance in binary bytes (SQLite index stats, float data); every text value in every table
     is clean. The session judged that clean and ran the agent. Options:
     - (a) accept: text-level scan plus explained byte hits;
     - (b) give the tool a minimum length or word-boundary rule for the raw-byte scan;
     - (c) stop masking such short generic names.
     Recommendation: (b).
   - Model and AAU of the three new threads and of the first blind run: Emre reads them in the portal.
3. Post 4's slug, outline and drafting have not started. The purpose is in D56; drafting follows the D5/D41 flow.
4. Site-wide questions for Emre, unchanged since 2026-10-04 (D17 holds until he answers):
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

**Data rules (D57, D60):**
- Every capture is masked before any use: hosts, app pools, sites, queues, services, agents, products.
- Only masked databases are used anywhere (tests, Azure).
- Real→placeholder mappings live only on Drive, kept permanently. They restore real names for private hand-overs.
- Real names never go into the repo, the post, an agent prompt, the storage or a message between sessions.
- Raw data that lands in the lab's storage is copied to Drive (sha256 checked) and deleted from the storage before
  any agent run.
- Tools (public, no names): `tools/perfmon_csv_to_sqlite.py` (CSV → SQLite) and `tools/perfmon_mask.py` (mask from a
  private mapping, rebuild index statistics, scan raw bytes).

**Capture 1 (Srv02, 24 h at 10 s):**
- Ground truth in `baseline-findings.md`:
  - nothing makes the machine hard to use;
  - F1: the IIS worker leaks handles (~19–20 per 1,000 requests);
  - F2: native memory grows at night without load;
  - F3: single-sample blips.
- Local blind rounds (fresh Claude Code subagent, Claude Opus 5.5):
  - round 1 (v1.0): 3 errors, all in helper output;
  - round 2 (v1.1): 0 wrong figures, ~55 k tokens.
- SRE Agent blind run (2026-10-09; Claude Opus 4.6, 2.5 AAU, both as Emre read them):
  - found F1 and F2, invented no crisis;
  - made 4 wrong figures and one unsupported causal claim, and labelled a trend "Critical";
  - analysis in `agent-vs-local.md`.
- Data path: private blob → agent terminal (VNet egress, managed identity) → terminal python3. `perfq.py` is a real
  file in the skill folder.

**Captures 2–4 (2026-10-10, D60, D61): three servers with a known "memory problem every hour", 3 h at 1 s each.**
- Hosts are Srv11–Srv13. Not blind (D61): the prompt adds "This server has a memory problem every hour."
- One thread per server, skill v1.1, ~8 min each.
- Result:
  - Each agent found the shared hourly cause by itself: the Azure Guest Agent's `CollectGuestLogs` runs every ~62 min,
    flushes the file cache, and C: write latency hits 0.7–0.9 s for 20–40 s.
  - Our SQL check found 1 wrong figure (Srv11), 1 wrong timestamp (Srv13), a few overstatements, and one unproven
    causal link in all three.
- No comparison with the blind run was asked for.

**Files** (`files/post4-files/`, private):
- `baseline-findings.md`, `skill-test-rounds.md`, `skill/` (v1, v1.1).
- `capture-masked.db` (+ `.zip`; the db's sha256 starts 600ffc40). The original CSV is beside it.
- `raw-261010/` (the three raw CSVs + `SHA256SUMS.txt`).
- Mappings: `mask-mapping.csv`, `mask-mapping-261009.csv`, `mask-mapping-261010.csv`. **Never delete or overwrite.**
- Lab log `*-log-full.md`: all steps; rows L8–L16 cover 2026-10-10.
- The lab evidence folder: threads, prompts, the chat script; `261010/` holds the three new threads.
- `agent-vs-local.md`.
- For the data owners (Turkish, offline HTML, real names): `findings-real-names.html`,
  `findings-agent-real-names.html`, `agent-vs-local.html`, `sunucular-261010-gercek-adlar.html` (3 servers: agent
  result + our check).
- The masked DBs for Srv11–13 are only in the lab's storage (rebuild: converter + mask with the 261010 mapping).

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

- `docs/decisions.md` (D1–D61), `docs/writing-guide.md` (§4 scrub, §5 TR/EN parity, §6 flow).
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

## Last session (2026-10-10, on demand)

Three-server task from Emre (D60, D61):
- raw CSVs saved to Drive and removed from the lab storage;
- masked, three agent threads run, one Turkish real-name HTML with our check;
- lab state unchanged.
Repo note: the vezir brief says this repo should be private; it is public by D18 (the Pages blog). Left public and
reported to the owner.
