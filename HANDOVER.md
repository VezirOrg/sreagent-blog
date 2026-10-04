# HANDOVER — sreagent-blog

**Live at https://sreagent.emreguclu.io with 1 post (SQL MCP part 1, TR+EN). Repo public, Pages on, HTTPS enforced.**

Blog and lab guides about Azure SRE Agent, MCP and Data API builder, by Emre Güçlü. Hugo + Blowfish, Turkish and
English. This repository is public, history included: everything committed must pass the scrub rules in
`docs/writing-guide.md` §4. Internal discussion, raw notes and unapproved material stay outside the repo.

## Where things are

- `docs/decisions.md`: every decision, dated (D1–D20). Read it first.
- `docs/writing-guide.md`: what every post must have, front matter, shortcodes, scrub checklist, TR/EN parity, review flow.
- `content/posts/<slug>/`: one page bundle per post (`index.en.md`, `index.tr.md`, `feature.*`).
  Live: `sql-mcp-part-1`, "Setting up SQL MCP for Azure SRE Agent", series part 1.
- `archetypes/posts/`: `hugo new content posts/<slug>` creates a TR+EN bundle with every required section.
- `scripts/scrub-check.sh`: scrub gate (GUIDs, private IPs, tokens, secrets, plus a lab-name denylist kept outside the repo).
  The Pages workflow runs it before every build.
- `.github/workflows/pages.yml`: every push to `main` builds with Hugo 0.167.0 extended and deploys to Pages.
  The base URL comes from `config/_default/hugo.toml` (D19).
- `themes/blowfish`: git submodule pinned at v3.8.0. Upgrading the theme means moving the submodule in its own commit.
- `layouts/shortcodes/site-topics.html`: the series and tags block on the home page.

## Publishing a post

1. `hugo new content posts/<slug>`; write both languages with `draft: true`. Pass `scripts/scrub-check.sh` before every
   commit: drafts are public in the repo too.
2. Build a private preview and send it for review:
   `HUGO_RELATIVEURLS=true HUGO_UGLYURLS=true hugo -s . --buildDrafts --baseURL / -d <tmp>/site`, then drop
   `CNAME`, `*.xml`, `*.json`, and rewrite relative links ending in `/` to `/index.html` for static hosting.
   The first post's preview was a private claude.ai artifact whose cover page links into the built site.
3. Emre approves → set `draft: false` in both languages, commit `post: publish <slug>`, push. The workflow deploys
   in about a minute. Check `https://sreagent.emreguclu.io/posts/<slug>/` and `/tr/posts/<slug>/` answer 200.
4. Add a D-entry for the approval in `docs/decisions.md`.

Run at most one `hugo server` at a time on this machine, and stop it afterwards. One-off `hugo` builds are enough for checks.

## Open decisions for Emre

The current state holds until he answers (D17):

- **LIS-CC, the content license**: none is stated. Suggested: CC BY 4.0 for text, MIT for code snippets. Currently no
  license file and only "© 2026 Emre Güçlü" in the footer.
- **Language layout**: English at the root, Turkish under `/tr/` (D8). Keep or flip.
- **Part 2 teaser**: the first post ends with "Next in the series: monitoring this setup". Keep (and write part 2) or drop.
- **PNG cover**: the feature image is SVG, which social link previews do not render. A 1200 × 630 PNG next to it would
  fix that; this machine has no SVG-to-PNG converter, so either install one or Emre supplies the image.

## Later

- GitHub Actions: `actions/checkout@v4`, `configure-pages@v5` and `upload-pages-artifact@v3` target Node 20 and are
  being forced onto Node 24. Move to versions built for Node 24 when they exist.
- `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. Watch the first run after that date; the workflow only needs
  `curl`, `dpkg` and the Hugo `.deb`.
- Blowfish v3.8.0 declares support for Hugo up to 0.166; Hugo 0.167 prints a compatibility warning but builds cleanly
  (D11). Re-check when either moves.
- `configure-pages` is still in the workflow but its base URL is no longer used (D19); it can stay or go.
