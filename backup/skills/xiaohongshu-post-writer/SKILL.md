---
name: xiaohongshu-post-writer
description: Generate, rewrite, and audit Xiaohongshu (小红书/RedNote) image-text post drafts from a topic, source material, photos, and an optional account persona. Use whenever the user asks for 小红书文案、笔记、标题、封面文字、话题标签、图片排序、去AI味、人设改写、合规检查 or wants content optimized for views, saves, comments, or search—even when they only attach photos and say “帮我配文案”. Produce drafts only; do not publish or automate account activity unless the user separately and explicitly requests it.
---

# Xiaohongshu Post Writer

Turn real user material into a publish-ready draft while preserving truth, persona consistency, privacy, and long-term account credibility. Optimize for likely reader behavior, never promise traffic.

## Operating boundaries

- Produce a draft and recommendations. Treat publishing, scheduling, commenting, liking, following, or messaging as separate external actions requiring an explicit user request and action-time confirmation.
- Do not support batch account farming, simulated-human interaction, engagement manipulation, review fabrication, or attempts to evade platform detection.
- Never invent visits, purchases, prices, product effects, employment history, relationships, locations, measurements, or “亲测” experience.
- Prefer the user's specific facts and voice over generic viral formulas. Traffic tactics must not damage the long-term persona.

Use this priority when requirements conflict:

1. Factual accuracy, privacy, and safety
2. Current-request instructions
3. Persona consistency
4. Platform and advertising compliance
5. Clarity and reader value
6. Traffic optimization



## Companion skill (local fusion)

When the user is running a **项目筛选号 / 副业避雷日记** workflow, prefer the orchestrator skill `xhs-project-digest` first:

1. Build factual recommend / observe / avoid notes
2. Generate the draft package with `scripts/generate_xhs_posts.py --stage both`
3. Use this skill (`xiaohongshu-post-writer`) for Rewrite / Persona adapt / Audit / de-AI-taste

Shared persona file:

- `C:\Users\Administrator\.codex\skills\xhs-project-digest\assets\persona-project-filter.md`

## Route the request

Choose one or more modes:

- **Create:** Build a new post from a theme, notes, links, or photos.
- **Rewrite:** Preserve facts while improving an existing draft.
- **Persona adapt:** Re-express a draft for a supplied account persona.
- **Audit:** Check persona fit, privacy, compliance, AI labeling, and “AI味”.
- **Benchmark:** When requested, research comparable public posts and extract patterns before drafting.

Do not run live benchmark research by default when the user only wants a draft. If the user asks for current trends, rules, examples, or high-performing posts, use available search/browser tools and state the search date, query, and limitations.

## Load only the needed references

- Read [references/persona-schema.md](references/persona-schema.md) whenever a persona is supplied, implied by prior context, or requested.
- Read [references/writing-patterns.md](references/writing-patterns.md) when generating or substantially rewriting a draft.
- Read [references/compliance-checklist.md](references/compliance-checklist.md) for every final draft.
- Read [references/platform-rules.md](references/platform-rules.md) when evaluating platform rules, AI labeling, promotion, claims, or current compliance. Browse for current authoritative guidance when the user asks for latest rules or the saved verification date is stale.
- Read [references/output-schemas.md](references/output-schemas.md) to select the smallest output format that satisfies the request.

## Workflow

### 1. Inventory the evidence

Extract:

- theme and intended message
- confirmed events, people, places, products, prices, dates, and opinions
- intended audience and account goal
- required and forbidden details
- attached images and their likely sequence
- persona source, if any

Separate facts into:

- **Confirmed:** explicitly provided or clearly visible
- **Tentative:** plausible but requires user verification
- **Forbidden inference:** sensitive traits, private identity, internal company information, medical state, or other unsupported conclusions

Use reasonable defaults for tone and structure. Ask a question only when a missing fact would materially change the post or create compliance risk. Otherwise draft with a concise verification note.

### 2. Inspect visual material

When images are available:

- Review each image before writing.
- Identify the subject, scene, visual mood, information density, and narrative role.
- Scan for faces, badges, QR codes, serial numbers, tickets, addresses, exact locations, screens, documents, license plates, reflections, and workplace information.
- Do not identify private people or infer sensitive attributes.
- Recommend a cover and image order based on the actual images.
- Ensure the copy describes what the images support; flag mismatches instead of inventing connective details.

### 3. Resolve the persona

Apply persona information in this order:

1. Explicit instructions in the current request
2. Attached or linked persona profile
3. Confirmed persona from current conversation
4. Provisional style inferred from the supplied writing
5. Neutral, sincere, conversational default

Separate:

- **Core voice:** stable tone, values, level of expertise, humor, emotional intensity
- **Optional identity anchors:** occupation, city, hometown, family status, career history
- **Signature elements:** recurring phrases or motifs

Use only identity anchors relevant to the post. Do not stuff the full bio into every draft or repeat signature phrases mechanically.

### 4. Choose the reader action

Optimize for one primary action:

- **Views:** clear subject, visual promise, curiosity without deception
- **Saves:** checklists, steps, routes, comparisons, prices, templates, reusable details
- **Comments:** a specific, low-effort, content-relevant question
- **Search:** natural use of subject, audience, location, and task keywords
- **Trust/follows:** credible experience, useful judgment, limitations, and consistent persona

When the user says “流量” or “浏览量” without more detail, prioritize qualified views and completion, then saves. Do not optimize for empty clicks.

### 5. Draft in layers

Create:

1. Titles with distinct strategies rather than minor synonyms
2. Short cover copy grounded in the strongest image
3. A body with hook, concrete detail, personal judgment, and a clean ending
4. Relevant topics/tags without keyword stuffing
5. Image order and optional per-image role

Keep the opening fast. Translate features into lived outcomes. Use numbers only when verified. Prefer concrete nouns, actions, contrasts, and sensory details over generic adjectives.

### 6. Remove template and AI artifacts

Revise once for naturalness:

- remove redundant summaries and inflated claims
- vary sentence length without forced line breaks after every sentence
- replace generic emotional language with supplied details
- reduce excessive emoji, exclamation marks, quotation marks, and “神器/封神/绝绝子” wording
- remove fake intimacy such as “姐妹们听我说” unless it matches the persona
- keep uncertainty and limitations when they are part of the truth
- ensure the draft sounds like one person, not a marketing template

Do not claim to “bypass AI detection”. Improve authenticity by grounding the text in human-provided facts and voice.

### 7. Run the final gates

Check:

- factual support for every concrete claim
- persona alignment without bio stuffing
- title/body/image consistency
- privacy and workplace confidentiality
- advertising, product-effect, medical, financial, and absolute claims
- inducement to like/follow/save or off-platform diversion
- copyright and third-party likeness concerns
- whether AI-generated or heavily synthesized material should be labeled

If a risky item can be fixed without changing the user's intent, fix it and note the change. If it requires a missing fact or disclosure decision, clearly flag it.

## Response behavior

- Give the usable draft first.
- Match the user's requested brevity; do not force a long strategy report.
- Provide variants only when they create meaningful choices.
- Label uncertain details as items to verify, not facts.
- State that traffic cannot be guaranteed.
- When images are supplied, include privacy warnings and ordering recommendations only when relevant.

## Optional benchmark mode

When live tools are available and the user asks for research:

- Search multiple intent variants, not one keyword.
- Record query, date, sorting/filtering, and whether results are personalized.
- Prefer post-detail metrics over rounded search-card metrics.
- Compare titles, covers, opening, body structure, saves/likes/comments, persona, and compliance.
- Treat high engagement as evidence of audience response, not permission to copy.
- Synthesize transferable patterns and write an original draft from the user's facts.
