# Decisions

Durable decisions for this site. Newest at the bottom. Each one is dated and says who decided.

## 2026-10-04 — Founding decisions (Emre)

| # | Decision | Notes |
|---|---|---|
| D1 | A blog plus hands-on lab guides about **Azure SRE Agent, MCP and Data API builder (DAB)**, published at **https://sreagent.emreguclu.io**. | |
| D2 | **Hugo + Blowfish** theme, **Turkish and English**, author **Emre Güçlü**. | Theme pinned to a released tag (see D7). |
| D3 | **One repository** (`VezirOrg/sreagent-blog`) holds the site, its docs and its working record. It will become **public**. | Private until Emre approves the first post. Making it public is Emre's decision only. |
| D4 | Because the repo will be public, **everything committed must be publishable**: no lab identifiers (tenant, subscription, app, object IDs, resource names, host names), no secrets, no customer data, no internal tooling details. | Raw notes, internal discussion and unapproved drafts are kept outside the repo. |
| D5 | **Every post is approved by Emre before it goes live.** | See the review step in [writing-guide.md](writing-guide.md). |
| D6 | **Hosting: GitHub Pages**, built and deployed by a GitHub Actions workflow, custom domain `sreagent.emreguclu.io` via `static/CNAME`. | DNS (`CNAME sreagent → vezirorg.github.io`) and the org domain verification TXT record are done by Emre. Pages can only be enabled after the repo is public. |
| D7 | **Theme is pinned**: Blowfish as a git submodule checked out at a release tag. | Upgrading the theme is a deliberate commit that moves the submodule. |
