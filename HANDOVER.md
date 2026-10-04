# HANDOVER — sreagent-blog

**First post approved and set live (`draft: false`); repo going public after a history audit, then Pages.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, for https://sreagent.emreguclu.io.
Hugo + Blowfish (pinned submodule, v3.8.0), Turkish and English. This repo will become public, so everything in it is
written to be publishable (see `docs/decisions.md` D3–D4 and the scrub rules in `docs/writing-guide.md` §4).

## Where things are

- `docs/decisions.md`: every decision, dated. Read first.
- `docs/writing-guide.md`: what every post must have, front matter, shortcodes, scrub checklist, review flow.
- `content/posts/sql-mcp-part-1/`: first post, "Setting up SQL MCP for Azure SRE Agent", series part 1, `draft: true`.
- `archetypes/posts/`: `hugo new content posts/<slug>` creates a TR+EN bundle with every required section.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus a denylist kept outside the repo).
- `.github/workflows/pages.yml`: builds and deploys to Pages; skipped while the repo is private.
- `static/CNAME`: `sreagent.emreguclu.io`.

## Session 2026-10-04 (first session)

- Recorded the founding decisions, wrote the writing guide, built the site skeleton, wrote the first post in both
  languages with all lab identifiers replaced by standard placeholders, and made a private preview for Emre.
- Preview build command: `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo --buildDrafts --baseURL / -d <tmp>`, then
  rewrite links ending in `/` to `/index.html` for static hosting.

## Next

1. Once the repo is public: enable Pages (source "GitHub Actions", custom domain `sreagent.emreguclu.io`), run the
   workflow, then enforce HTTPS once the certificate is issued. Emre does the DNS (CNAME + org domain verification TXT).

## Open questions for Emre (current state holds until he answers, D17)

- Content license (none stated yet).
- English at the root and Turkish under `/tr/`: keep or flip.
- The post ends with a teaser for part 2 (monitoring this setup): keep or drop.
