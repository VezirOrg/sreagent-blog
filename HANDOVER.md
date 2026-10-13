# HANDOVER — sreagent-blog

**Three posts live. Post 5 (monthly cost report) proved end to end on September data, its lab DOWN; Post 6 + Post 4
become the two-part "black box" series (D95), Post 6 waits for the playbook's shared lab on 2026-10-14. No new text
published.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English, https://sreagent.emreguclu.io. This repository is public (D18), history included: everything committed must
pass the scrub rules in `docs/writing-guide.md` §4. Drafts, reviews, test logs, data and raw notes stay outside the
repo, in the gitignored `files/` (a Google Drive folder). Read `CLAUDE.md` and `docs/decisions.md` (D1–D96) next.

## Open for Emre (asked through the owner on 2026-10-13; he answers via the next session)

1. **Series frame for D92 (Post 6's purpose).** Proposed: add only the opening clause "'Windows sunucular için kara
   kutu' serisinin ilk bölümü." in front of D92's sentence, the rest word for word. D56 (Post 4) stays word for word.
   Series name proposal: EN "A black box for Windows servers" / TR "Windows sunucular için kara kutu"; slugs
   `perfmon-blackbox-part-1` (Post 6) and `perfmon-blackbox-part-2` (Post 4). Record his answer as a decision first.
2. **Who takes the portal screenshots** in the shared lab (Emre, or a session with a browser tool). If nobody, Part 1
   uses text captures only.
3. **Docs vs test (D52), not resolved:** in the agent's terminal (RunInTerminal) a venv `pip install duckdb` from PyPI
   worked, PyPI answered and `subprocess` ran; Learn's code-interpreter page says no pip, no outbound, no subprocess
   (`notes/261013-post5-sandbox-test.md`).
4. **Post 5 skill v0.2:** not now (D94). Three small errors of the September demo are the candidates (an off range, an
   unproven cause, a wrong "limits" line); details and fixes in `files/post5-files/evidence-261013/demo2-score.md`.
5. Still open from before (unchanged): whether two Post 4 threads of 2026-10-10 were Emre's own runs, and the first
   blind run's AAU reading (details in `files/post4-files/aau/aau-261011.md`); site-wide: content license, language
   layout, the Part 2 teaser, PNG covers (D17 holds).

## Next steps

1. **Post 6 = black box series part 1** (D92, D95, D96): the recorder, the data path and the v1.0.0 setup.
   - Skeleton `files/post6-draft/skeleton-261013.md`; setup section drafted in EN against tag
     `perfmon-blackbox/v1.0.0` (playbook commit e0005bf): `files/post6-draft/setup-section-en-261013.md`. It is "as
     documented", not "as we ran it", until the shared lab.
   - **Shared lab (D96): the playbook session builds and owns it on 2026-10-14** (README-only fresh-eyes install).
     This project builds no lab of its own and only reads in it, from `files/post6-draft/ortak-lab-istekler.md`
     (timings, 6 screenshots, 7 text captures, one agent question).
   - Diagram: the EN post uses the playbook's `docs/img/perfmon-blackbox-flow.svg` at the tag; the TR post the
     Turkish SVG that sits beside it in the playbook repo (D81, D95).
   - Then the D5/D41 flow: draft TR + EN with `draft: true` in `files/<slug>-draft/`, review, fixes, private preview.
2. **Post 4 = series part 2** (D56 word for word, D64, D72, D81): the agent's triage of a real 24-hour capture.
   Nothing drafted. Material is listed under "Post 4" below. Links to Part 1 at its start and end.
3. **Post 5 (monthly cost report, outside the series, D76–D94):** text not started. The real run is **October's data,
   exported by the monthly schedule around 2026-11-05**; that needs a rebuilt lab (recipe in the lab log) and Emre's go.
   Post 5 links to the black box series as the same pattern (export → private storage → skill → SQLite).

## Posts (all live, `content/posts/<slug>/`)

| Slug | Title (EN) | Last change |
|---|---|---|
| `sql-mcp-part-1` | Setting up SQL MCP for Azure SRE Agent (series part 1) | 2026-10-09, d7a4a69 (D46–D49) |
| `sre-agent-knowledge-in-git` | Keep Azure SRE Agent knowledge in git, synced by a script and a pipeline | 2026-10-09, b472bfc (D51–D55) |
| `sre-agent-vm-run-command` | Let Azure SRE Agent run commands on a VM, but not as SYSTEM | 2026-10-09, ea1e84f (D43–D45) |

Every post's purpose is a sentence in `docs/decisions.md` (D53; Post 4: D56; Post 5: D76 with D80; Post 6: D92).

## Post 5 — monthly cost report from a FOCUS export (state 2026-10-13)

**Purpose (D76, D80):** "SRE Agent'a her ay geçen ayın maliyet raporunu, kaynakların metrikleriyle çaprazlayarak
yazdırmak: FOCUS export → private storage → skill → SQLite."

What exists and was proven (private log `files/post5-files/lab-log.md`, rows L1–L25):
- **FOCUS export on the lab subscription** (D82, D87): monthly "last month", FOCUS 1.0r2, CSV + gzip, partitioned,
  subscription scope, created by the lab service principal through the Exports REST API. Accepted although Learn's
  table does not list the subscription's billing account type (a docs gap, post material). First call needed the
  `Microsoft.CostManagementExports` provider registered. September back-filled: 208 rows, total = the Cost Management
  query ✅. Next scheduled run ~2026-11-05.
- **Export storage** in its own resource group, kept after the lab: public network access is forced to Disabled by a
  tenant governance policy (so D84's "selected networks" cannot hold); Cost Management still writes through the
  trusted-services path; the agent reads through a private endpoint from the lab VNet. Register row UP (POST5-EXPORT)
  in the lab template's register.
- **Skill `cost-monthly` v0.1** (private, `files/post5-files/skill/cost-monthly/`): `focus_fetch.py` (manifest-driven),
  `focus_to_sqlite.py`, `costq.py` (overview, MoM, odd days, new/gone, idle infra days, tags, unit prices, savings,
  top-N VMs × Azure Monitor CPU). Standard library only. Real-data traps fixed: FOCUS `ResourceType` is a display name
  and `ResourceId`/`x_ResourceType` mix case (normalised to `rid`/`rtype`); the metrics timespan needs `Z`.
- **Uploaded through the data plane** with SRE Agent Author + Standard User (D93, replacing D91 portal), read back
  identical. The portal guide `files/post5-files/skill/PORTAL-KURULUM.md` stays unused.
- **Demo 1:** 403, because the agent's terminal runs as its **system-assigned** identity, not the user-assigned one;
  the agent then tried to grant itself the role; no approval, nothing changed (post material). **Demo 2:** full
  report, every figure right by SQL, three small errors (open item 4). September is thin: all cost on one day, no
  tags, no earlier month, VMs deleted.
- **Sandbox test:** Python 3.12.3, SQLite 3.45.1, pandas 3.0.2, no duckdb/pyarrow; system pip refused (PEP 668); a
  venv pip install worked (open item 3).
- Lab torn down 2026-10-13 16:08Z (D94): extra roles removed first, register DOWN, audit clean. Cost ≈ $1.2 + AAU of
  4 threads (Emre reads it). Thread JSONs and outputs: `files/post5-files/evidence-261013/`.

## Post 4 — black box series part 2 (evidence complete, no text)

**Purpose (D56):** find the critical performance problems in a real, anonymised 24-hour PerfMon capture whose cause
is unknown, and dig into the ones that make the machine hard to use, by letting Azure SRE Agent query it as SQLite
through a skill, without burning tokens on raw data.

- The skill `perfmon-triage` (CSV → SQLite converter + `perfq.py`, D62, D67) lives in VezirOrg/sreagent-playbook,
  `playbooks/perfmon-blackbox/` (D72, D74); masking is a lab step with a denylist check (D68, D71).
- Results (scores in `files/post4-files/`): Srv02 local rounds v1.0 3 errors → v1.1 0 → v2 0; agent v1.1 blind: F1/F2
  found, 4 wrong figures, 1 unproven cause, a wrong "Critical"; agent v2 blind: right severity, exact leak rate, 3
  small wrong figures, one untested causal story. Srv11–13 (prompt names an hourly memory problem): v1.1 found the
  hourly Guest Agent cycle with 3 × "Critical"; v2 on Srv13 all "warning", missed one of three events. AAU per thread
  (Emre's reading): 42/27/28, 33, 45, a void run 27.
- The post states the ARM skills path answered "internal tenants only" and we used the data plane (D64).
- Files: `baseline-findings.md`, `skill-test-rounds.md`, `agent-vs-local.md`, skill packages and backup, `aau/`, the
  lab log and evidence folders, data and the masking mappings (**never delete or overwrite a mapping**), the
  real-name hand-over pages for the data owners. Data rules D57, D60, D62, D71: only masked data anywhere; real names
  never in the repo, a post, a prompt or a message between sessions.

## Labs

- **Rules (D37, D47, D50, D58, D90):** a post's lab comes from the shared lab template, with a register row in the
  same step (next free env number from the register); credentials only via `direnv exec`; lab, storage and template
  names never in this repo; teardown with a rebuild recipe kept in `files/`; remove extra role assignments before
  `azd down`, or they orphan at subscription scope.
- **No blog lab is up.** Post 4's and Post 5's labs are DOWN. Up and not ours: the frozen Post 3 lab (never touch it),
  the SQL MCP project's lab, Emre's other demos. Post 6 uses the playbook's lab (D96).
- Lessons: the template's VNet DNS is the DC, so the DC must run during agent runs; VMs deallocate nightly; the
  template now builds with zero IIS VMs (first done 2026-10-13); the agent's terminal is its system identity; a chat
  poll needs a long idle window (5 min) or it ends while the agent works.

## Standing rules

- **Scrub gate (D58):** local git hooks run `scripts/scrub-check.sh` (pre-commit on staged files, pre-push on the
  tracked tree minus the theme). Hooks live in `.git/hooks/`, not committed; recreate them if missing. Denylist
  `files/scrub-denylist.txt` (never committed).
- **Covers are exactly 1200 × 630 (D75).**
- Purpose first (D53). Docs vs our result: list for Emre, never resolve (D52). Markers ✅/📄 (D44). Author profile
  (D21). Privileges (D22). Sources (D24, D26). Repo public (D18). Never "ürün grubu". No personal text about Emre on
  public pages without his approval. Mask third-party data.
- In messages to other sessions, refer to Emre by name (or "they"); never a real name from the data.
- The rig's secret guard blocks a Bash command whose text names a secret-like variable, even inside file content
  written by a heredoc; write such files with the Edit/Write tools (reported to the owner as a false positive).

## Where things are

- `docs/decisions.md` (D1–D96), `docs/writing-guide.md` (§4 scrub, §5 TR/EN parity, §6 flow).
- `notes/261013-post5-sandbox-packages.md` (Learn on sandbox packages), `notes/261013-post5-sandbox-test.md` (result).
- `.claude/skills/tech-blog-review/SKILL.md`: Emre's review skill, verbatim (D40). `scripts/scrub-check.sh`.
- `.github/workflows/pages.yml`: builds and deploys on push to `main`. Record-only commits carry `[skip ci]`.
- Preview build: copy the tracked repo plus `themes/` to a scratch folder, then
  `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts`; publish it as a claude.ai artifact.
- Private: `files/post5-files/` (plan, lab log, skill, evidence), `files/post6-draft/` (skeleton, setup section,
  shared-lab requests), `files/post4-files/`.

## Later

- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19: watch the first Pages run after it.
- Blowfish v3.8.0 declares Hugo up to 0.166; 0.167 warns but builds (D11).
- Google Drive's file provider sometimes returns "Resource deadlock avoided"; work in the scratchpad and retry.

## Last session (2026-10-13, on demand)

Opened Post 5 (D76–D94) from the purpose to a working September demo and tore its lab down the same day; recorded
D81 (Post 4 must show the flow diagram) and Post 6's purpose (D92); drafted Post 6's skeleton and setup section
against the playbook's v1.0.0 tag; Emre made Posts 6 and 4 a two-part series with a shared lab (D95, D96).
