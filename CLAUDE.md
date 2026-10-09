# sreagent-blog

Read `HANDOVER.md` first: it is this project's memory and says where things stand. Decisions are in
`docs/decisions.md`; how a post is written and published is in `docs/writing-guide.md`.

This repository is public. Everything committed must pass the scrub rules in `docs/writing-guide.md` §4; drafts,
reviews, raw notes and internal discussion stay outside the repo, in the gitignored `files/` folder.

## Publishing flow (D5, D41)

Every new post, in this order. Emre sees a post only after step 3.

1. **Draft** TR and EN with `draft: true` in `files/<slug>-draft/`; pass `scripts/scrub-check.sh`.
2. **Review** with the project skill `.claude/skills/tech-blog-review`, TR and EN each on its own terms.
3. **Fix**: keep the original first (a dated copy, `files/<slug>-draft/original-YYMMDD/`), then apply the fixes. Never
   change facts, commands or test results unless the review flagged them; mark anything Emre must verify.
4. **Private preview** with a short review summary: top findings, what was changed, what is left for Emre to decide.
5. **Emre approves** → `draft: false`, bundle into `content/posts/<slug>/`, commit `post: publish <slug>`, push.

Nothing is published without Emre's approval. Full details: `docs/writing-guide.md` §6.
