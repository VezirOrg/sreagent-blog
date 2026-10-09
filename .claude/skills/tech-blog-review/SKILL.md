---
name: tech-blog-review
description: Review or restructure a technical blog post (URL, file or pasted text) for a newcomer reader: fact-check key claims, fix structure, tighten language. Strong Turkish-language review. Use for 'review my blog post', 'blogumu review et', 'yazıyı gözden geçir'.
---

# Technical blog review

Review a technical blog post the way a demanding editor who also knows the technology would: check that the central claim is true, that a newcomer can follow it, that the structure matches how the reader will use it, and that the language is plain. The output is a review the author can act on, not a rewrite, unless the author asks for one.

## 1. Establish the brief

Before reviewing, know these four things. Take them from the request when given; infer from the post when obvious; ask one short question only when the purpose is unclear.

- **Purpose**: the gap or problem the post addresses, in one sentence. Everything is judged against this.
- **Reader**: default is someone who has never used the product and is comfortable with the surrounding tools (CLI, CI, cloud basics).
- **Language**: review each language version on its own terms. Write the review in the language the author is writing to you in.
- **Target structure**: use the author's if given, otherwise the default skeleton below.

## 2. Read the whole post

Fetch or read the full text, including code blocks, tables, diagrams, captions, the title, meta description and tags. If the post exists in more than one language, read the version under review in full and skim the other for differences. Do not review from a summary.

## 3. Check the load-bearing claims

A post built on a wrong premise fails no matter how well it reads, so this comes before structure.

List the claims the post depends on: "X is not possible", "the docs do not cover Y", limits, role names, API paths, default settings, security statements. Check each against primary documentation (the vendor's official docs; use a documentation connector if one is available, otherwise web search). Classify each:

- **Confirmed** by docs.
- **Contradicted or more nuanced**: say what the docs say and link them.
- **Not found in docs**: say "I could not find this documented", never "this does not exist".

Then:

- Narrow claims that are broader than the evidence ("there is no sync" may really be "there is no sync for this file type from this source").
- Name official alternatives the reader will find on their own, and say in one line why the post's approach is still worth it.
- Keep the author's own test findings as theirs. Never invent or upgrade test results.

Lead the review with these notes when any claim needs changing.

## 4. Review the structure

Default skeleton:

1. **Introduction**: what the product is in two sentences, the gap, what this post builds, who it is for. The problem must be stated in the first paragraph.
2. **Why the obvious alternative is not enough** (optional, short).
3. **Solution at a glance**: four to six high-level steps, plus a diagram if there is one.
4. **Requirements**: one table.
5. **Implementation**: steps in the order the reader performs them.
6. **Verification**: the few checks the reader runs.
7. **Limits and caveats**: preview status, scope limits, risky flags, permissions.
8. **Troubleshooting** (optional).
9. **Conclusion**: what was built, what it gives, next step.

Map every existing section to this skeleton in a table (new section, content, where it comes from). Then list what to cut or move:

- Material outside the stated purpose becomes a separate post or a one-line pointer.
- Lab diaries, evidence tables and timing measurements move to an appendix; instructions stay in the main flow.
- Long scripts are linked or collapsed, with a short summary of options in the text.
- A title or subtitle that does not say what the post does gets a concrete replacement; the meta description follows.

## 5. Check the content

- Every term is defined where it first appears, and one concept has one name throughout.
- Numbered lists match the diagram or steps they describe.
- Steps are in execution order (try locally before automating; first full run is its own step).
- Every value a command needs has a shown way to obtain it, and UI locations are spelled out.
- Examples are consistent across the post (file names, paths, sample output) and follow the post's own advice.
- Failure and edge cases are covered: what happens after a failed run, after a later config change, on delete.
- Evidence markers are used sparingly: state the default once, mark only the exceptions.
- On localized pages, no leftover untranslated UI strings, table headers or comments.
- Length fits the purpose; give a target word count when the post is much longer than it needs to be.

## 6. Review the language

Aim for short sentences, one idea each, in the voice of a colleague explaining at a whiteboard.

- Instructions use one consistent imperative form; observations from testing are kept apart, in past tense.
- Flag sentences that read as translated from another language and give a natural replacement.
- Give fixes as a table: current wording, suggested wording.

### Turkish posts

- Keep established English technical terms as they are (workflow, runbook, merge, pull request, data plane, knowledge base). Do not force translations; do define the term once.
- Replace calques with what a Turkish engineer would say. Typical cases: "kamuya açık API" → "public API"; "emekliye ayrılmış" → "kullanımdan kaldırılmış"; "... ile düşer" → "... hatası verir"; "taban adı" → "dosya adı"; "özyinelemeli dolaşılıyor" → "alt klasörleriyle birlikte taranıyor"; "uzun kuyruk" → "seyrek kullanılanlar"; "varsaymak cazip" → "sanılabilir".
- Avoid ambiguous everyday words for technical objects ("iş" for a CI job; use "workflow" or "job").
- Prefer "yalnızca" to "yalnız" as an adverb. Use one address form ("oluşturun") for all instructions.
- Check suffixes on English words and code spans (main'e, agent'ın, repo'yu or repoyu, consistently).

## 7. Write the review

Order, with the verdict first:

1. Two or three sentences: does the post achieve its purpose for the stated reader, and what is the main thing in the way.
2. Accuracy notes (section 3), if any.
3. Proposed structure table, then what to cut or move.
4. Content fixes as a short list.
5. Language table.
6. A sample rewrite of the introduction and the solution-at-a-glance steps, so the author can see the target tone.
7. Sources: links to every doc page used.

Be specific: quote the phrase, name the section, give the replacement. Leave out praise that changes nothing and findings the author cannot act on.

## 8. Rewriting (only when asked)

- Keep the original. Before changing a post, preserve the old version the way the author's project does it (a branch, an archive folder, a dated copy). If there is no convention, ask where to keep it.
- Keep facts, commands, code and test results exactly as the author wrote them unless the review flagged them. Mark anything the author must verify.
- Preserve front matter, slugs and URLs so links keep working.

## 9. Several posts

Review one post first and confirm the direction with the author. Then review the rest with the same brief, and deliver one summary table (post, verdict, top three fixes) followed by the per-post reviews. Note problems that repeat across posts once, at the top.
