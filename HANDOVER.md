# HANDOVER — sreagent-blog

**Post 4 (PerfMon triage) has its evidence but no text: skill v2 ran on SRE Agent (Srv02 blind, Srv13 hourly), the
skill moved to VezirOrg/sreagent-playbook, Post 4's lab is DOWN. Next: Post 4's slug, outline and draft. Three posts
live.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, data and raw notes stay outside the
repo, in the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` (D1–D74) next.

## Next steps

1. **Post 4 text (nothing drafted yet).** Purpose in D56 (Emre may reword). Slug and outline first, then the D5/D41
   flow (draft in `files/<slug>-draft/`, review, fixes, private preview, publish only on Emre's approval).
   - The post announces the playbook repo and links to it (D72): VezirOrg/sreagent-playbook,
     `playbooks/perfmon-blackbox/`.
   - D64: the post states that Learn's ARM skills path (`Microsoft.App/agents/skills`) answered "internal tenants
     only" in our tenant and that we used the data plane (`/api/v2/extendedAgent/skills/{name}`) instead.
   - Material is listed under "Post 4" below. Every claim keeps ✅ or 📄 (D44); conflicts with Learn go to Emre (D52).
2. **Open for Emre (ask through the owner):**
   - Were threads `2369f953…` (88 AAU) and `46a41a0b…`
     (31 AAU), both started 2026-10-10 before our first run that day, his own runs? They hold real names (they ran on
     unmasked data), are not in our lab log, and are quoted nowhere. Full IDs in `files/post4-files/aau/aau-261011.md`.
   - The first blind run's thread `003d6c2f…` (v1.1, Srv02) was read as 2.5 AAU on 2026-10-09 but is not among the 8
     rows of his 2026-10-11 screenshot. The agent is gone; only he can say which reading stands.
   - Site-wide, unchanged since 2026-10-04 (D17 holds until he answers): the content license, the language layout, the
     Part 2 teaser, PNG covers.
3. **Method questions now owned by the playbook repo (not here):** RULE6 (a `link_test` for every "because") and the
   5-minute VERDICT CEILING (it caps a recurring 20–40 s stall at "warning" even when the user names that stall as the
   problem). They are open in the playbook's decisions; Post 4 may describe them but this repo does not change the
   skill any more.

## Posts (all live, `content/posts/<slug>/`)

| Slug | Title (EN) | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | 2026-10-09, reviewed version, d7a4a69 (D46–D49) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline | 2026-10-09, thesis rework, b472bfc (D51–D55) |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | 2026-10-09, first publish, ea1e84f (D43–D45) |

Every post's purpose is a sentence in `docs/decisions.md` (D53, D54; Post 4: D56).

## Post 4 (evidence complete, no text)

**Purpose (D56):** find the critical performance problems in a real, anonymised 24-hour PerfMon capture whose cause
is unknown, and dig into the ones that make the machine hard to use, by letting Azure SRE Agent query it as SQLite
through a skill, without burning tokens on raw data.

**How it works now (D62, D67, D68, D71):**
- The skill takes the raw PerfMon CSV, converts it to SQLite with its own script (one database per host), and
  analyses with `perfq.py`. Two separate scripts (D67).
- Masking is a lab step before anything reaches the skill: CSV masked with a dated private mapping, rule b (names of
  5+ characters anywhere, shorter ones as whole words, D68), and a required check against the full scrub denylist
  that fails on any hit (D71).
- The code now lives in VezirOrg/sreagent-playbook (D72, D74). This repo keeps no copy.

**Results (scores in `files/post4-files/`):**
- Srv02 (24 h, 10 s, ground truth `baseline-findings.md`, F1–F4):
  - local blind rounds: v1.0 3 errors, v1.1 0 errors, v2 0 wrong figures (round 3, D62);
  - agent, v1.1 blind (2026-10-09): found F1/F2, 4 wrong figures, 1 unproven cause, a wrong "Critical";
  - agent, v2 blind (2026-10-11, thread `8f095f15…`): right severity, exact leak rate (19.6 per 1,000 requests),
    3 small wrong figures, still one untested causal story (night memory growth ← GC pause ← leaked handles), missed
    one blip.
- Srv11–13 (3 h, 1 s, prompt names "a memory problem every hour", D61):
  - agent, v1.1 (2026-10-10): each found the hourly Guest Agent `CollectGuestLogs` cycle; 3 × "Critical"; an unproven
    link (one process's handles → kernel pool);
  - agent, v2 on Srv13 (2026-10-11, thread `d1922b9c…`): all "warning", no unproven link, exact times, but missed one
    of the three hourly events and framed it as a memory squeeze; 3 small wrong figures.
- AAU per thread (Emre's portal reading, 2026-10-11): v1.1 Srv11/12/13 = 42/27/28; v2 Srv02 = 33; v2 Srv13 = 45; a
  void v2 run still cost 27.

**Files** (`files/post4-files/`, private):
- `baseline-findings.md`, `skill-test-rounds.md` (rounds 1–3), `agent-vs-local.md` (v1.1 and v2 runs).
- `skill/` (v1, v1.1), `skill-v2/` (the v2 package with `UPLOAD.md` and `deploy-skill.sh`), `skill-backup/` (v1.1 as
  it was live, sha256 29d531f9…).
- `aau/`: Emre's screenshot and `aau-261011.md` (thread ID → title, run, AAU, wall time, tool calls). Possible post
  material.
- The lab log `*-log-full.md` (rows L1–L33) and the evidence folder (`261011/` holds today's prompts, reports, scores
  and all 12 thread JSONs saved before teardown).
- Data: the raw Srv02 CSV, `raw-261010/`, `capture-masked.db(.zip)`. Mappings `mask-mapping*.csv` (four, the newest
  `-261011`). **Never delete or overwrite a mapping.** A verified copy of the source data and the denylist is in the
  playbook project's Drive folder (`source-data/`, with SHA256SUMS).
- For the data owners (Turkish, offline HTML, real names): `findings-real-names.html`, `findings-agent-real-names.html`,
  `agent-vs-local.html`, `sunucular-261010-gercek-adlar.html`.

**Data rules (D57, D60, D62, D71):** only masked CSVs (and databases built from them) are used anywhere; mappings live
only on Drive and are kept permanently; real names never go into the repo, a post, a prompt, the storage or a message
between sessions. On 2026-10-11 a product name missed by the 2026-10-10 mapping was found in two old masked databases
in the lab storage; both blobs were deleted (D71) and the denylist check now stops that.

## Labs

- **Rules (D37, D47, D50, D58):** each post gets its own lab from the shared lab template; next free env name from the
  template's register with a row in the same step; credentials only via `direnv exec`; lab and template names never in
  this repo; teardown with a rebuild recipe kept in `files/`; no test of a post's claim through SRE Agent itself (D43),
  except where the agent run is the subject (Post 4).
- **Post 4's lab is DOWN** (torn down 2026-10-11 on Emre's word, D73, before Post 4 is published): 14 min, resource
  group gone, no leftovers, the template's register row DOWN and its audit clean. Rebuild recipe and commands are in
  the lab log. The agent and its threads are gone; their JSONs are saved privately.
- Lessons from Post 4's lab: its VNet's only DNS server is the domain controller, so the DC must be running for any
  agent run (a run with the DC deallocated fails at managed-identity sign-in); the VMs deallocate themselves on a
  schedule; the chat script's 90-second idle window can end polling early while the agent waits for a long command
  (`poll-thread.sh` in the evidence folder uses 5 minutes).
- Post 3's original lab is FROZEN evidence: never touch it. Never touch other projects' labs.

## Standing rules

- **Scrub gate (D58):** local git hooks run `scripts/scrub-check.sh` (pre-commit on staged files, pre-push on the
  tracked tree minus the theme). The hooks live in `.git/hooks/` and are not committed; recreate them if missing. The
  denylist is `files/scrub-denylist.txt` (never committed). One older record-only commit with lab names stays in
  history (Emre: no rewrite).
- Purpose first (D53). Docs vs our result: list conflicts for Emre, never resolve them yourself (D52). Markers ✅/📄
  (D44). Author profile (D21). Privileges (D22). Sources (D24, D26). Repo public (D18).
- In messages to other sessions, refer to Emre by name (or "they"); never a real name from the data.

## Where things are

- `docs/decisions.md` (D1–D74), `docs/writing-guide.md` (§4 scrub, §5 TR/EN parity, §6 flow).
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill, verbatim (D40).
- `scripts/scrub-check.sh`: the scrub gate.
- `.github/workflows/pages.yml`: builds and deploys on push to `main`. Record-only commits carry `[skip ci]`.
- Preview build: copy the tracked repo plus `themes/` to a scratch folder, then
  `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts`; publish it as a claude.ai artifact.
- The PerfMon skill, converter and masking tools: VezirOrg/sreagent-playbook, `playbooks/perfmon-blackbox/`.

## Later

- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first Pages run after it.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11).
- Google Drive's file provider on this Mac sometimes returns "Resource deadlock avoided" (the old short lab log is
  still locked). Keep working copies in the session scratchpad and retry.

## Last session (2026-10-11, on demand)

Skill v2 end to end (D62–D74): raw-CSV input with its own converter, the four v1.2 method fixes, masking moved to a
lab step with rule b and a denylist check; local blind round 3 passed; the lab principal got SRE Agent Administrator
on the agent only and the data-plane write path was proven with a throwaway skill; v1.1 backed up and v2 uploaded
through the API; agent runs on Srv02 (blind) and Srv13 (hourly prompt) scored by SQL; a masking gap found and fixed
(two old blobs deleted); source data copied to the playbook project; AAU mapped to threads; Post 4's lab torn down;
`tools/` and `lab/` removed from this repo (now in the playbook repo).
Repo note: the vezir brief says this repo should be private; it is public by D18 (the Pages blog) and stays public.
