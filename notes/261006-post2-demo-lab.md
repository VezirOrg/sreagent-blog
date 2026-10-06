# 2026-10-06 — Post 2 demo lab (frozen)

The lab run behind "Keep Azure SRE Agent knowledge in git: one source, two paths" (D26–D36). Lab names, raw evidence
and chat transcripts stay outside the repo, in `files/post2-demo/` (Drive). The lab was built, used and torn down on
the same day.

## What was proven (✅ in the post)

- A repository connected through Code Access is not indexed as knowledge: empty knowledge list after connecting,
  memory search 0 hits for a repo-only canary, the plain question answered by Grep over the clone.
- CI sync through the public data-plane API with `tools/sre_kb_sync.py`: first sync, add, change, delete and an
  excluded path, each confirmed in chat with knowledge search only. Runs 26–34 s; sync step 6–20 s.
- CI identity: user-assigned managed identity + GitHub federated credential, one role (SRE Agent Administrator) on the
  agent only, no secret.
- Same procedure as a skill and as a knowledge document: the agent used the skill 5 of 5 times.

## Measured but kept out of the post (D35)

- The root `AGENTS.md` of a connected repository is injected into the context and cut at exactly 3,000 characters.
- A pointer to the runbooks in `AGENTS.md` made no visible difference in a small repository.
- The Code Access clone did not refresh after seven pushes over 70+ minutes; re-saving the connection with the branch
  set explicitly re-cloned the latest commit.
- Code Access stores the repository credential in plain text in the agent's sandbox, where the agent can read it (this
  one is in the post as a warning).

## Other findings

- `srectl` has no public download source; the post uses the public API and mentions `srectl` in one note (D34).
- Microsoft's IaC template hardcodes the deployer role assignment as a user principal; a service-principal deploy fails
  until it is changed locally.
- The single-document delete endpoint once returned HTTP 500 although the document was gone.
- Some GitHub organizations send the newer OIDC subject with numeric IDs.

## Live-change log

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
  connection. Nothing else changes. Result: the connectivity test and a plain re-save did not refresh it; re-saving
  with the branch set explicitly re-cloned the latest commit. Follow-up measurement stopped (D35).
- **L9 · 2026-10-06 · go: D35.** Remove the demo agent's Code Access connection and the stored GitHub credential, then
  verify that the clone and the credential are gone from the agent's workspace. Result: done (2026-10-06 ~10:00 UTC):
  no repos, no GitHub credential listed; the workspace clone folder is empty and no credential file remains.
- **L10 · 2026-10-06 · go: D36 (teardown after publishing).** Remove the demo agent's knowledge documents, skill and
  guardrail prompt; delete the demo resource group entirely (agent, managed identities and their federated credential,
  Log Analytics, App Insights); check that no role assignment is left behind; archive the private demo repository (kept,
  not deleted). Nothing else is touched. Result: done (~10:35 UTC). Knowledge, skill and prompt lists empty;
  resource group deleted; 0 role assignments left for the deleted identities or scoped to the group; demo repository
  archived and private. Final meter reading: 191.4 AAU for the day (the agent lived about 2.2 hours).

