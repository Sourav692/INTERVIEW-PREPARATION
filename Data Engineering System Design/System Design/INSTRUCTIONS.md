# Instruction Set: "System Design for Data Engineers" — Interview-Prep Explainer Generator

Paste this file's content (or just say "generate Chapter N using project instructions") in this
project any time you want a new chapter turned into study material. It tells Claude exactly what
to search for, what structure to produce, and what the two output files must contain.

---

## 0. Source material

Two books live in this project's knowledge:

| File | Role |
|---|---|
| `System_Design_V2.pdf` | **Primary source.** 18-chapter, narrative-driven edition (2026). Has "FAANG Signal," "War Story," "Anti-Pattern / Pattern," and "Cheat Sheet" call-out boxes. Use this book's chapter numbering (the ToC in this instruction file) as the authoritative structure. |
| `System_Design___Data_Engineers_old_version.pdf` | **Secondary source.** 2025 "Premium Edition." Same author, more classic framework/case-study layout (5-Step Framework, numbered Patterns 1–6, Case Studies 1–6). Mine this for extra case studies, extra trade-off tables, and alternate phrasings the newer edition compresses or drops. |

**Note on extraction quality:** `project_knowledge_search` returns V2 text with corrupted
characters in some passages (an artifact of the source PDF's font encoding — vowels are
frequently dropped, e.g. "syste" → "yte", "the" → "te"). This is a known, consistent pattern, not
a signal to stop. Read through it — the garbling is decodable from context (missing letters are
usually a single dropped vowel or "th"/"wh" digraph). Never quote the garbled text verbatim in
output; always reconstruct the clean, correct English and write output in normal prose. The old
version's text extracts cleanly and can be quoted/paraphrased more directly.

---

## 1. Chapter map (System Design V2 — authoritative)

| # | Chapter | Page |
|---|---|---|
| 1 | Preface | 1 |
| 2 | Why System Design for DEs | 3 |
| 3 | Fundamentals of Scale | 17 |
| 4 | Storage Engines | 43 |
| 5 | Data Modeling at Scale | 59 |
| 6 | Batch Systems | 75 |
| 7 | Streaming Systems | 90 |
| 8 | CDC & Replication | 105 |
| 9 | Lakehouse & Table Formats | 121 |
| 10 | Query Engines | 137 |
| 11 | Orchestration | 153 |
| 12 | Data Contracts & Governance | 168 |
| 13 | Reliability & Operations | 184 |
| 14 | Cost at Scale | 201 |
| 15 | The DE Interview Playbook | 218 |
| 16 | Case Studies | 233 |
| 17 | About the Author | 278 |
| 18 | Colophon | 280 |

Chapters 1, 17, 18 are front/back matter — skip unless explicitly requested. Chapters 2–16 are
the real content and each gets the full treatment below. Chapter 16 (Case Studies) is long enough
that each case study inside it should be treated as its own "sub-chapter" deliverable on request
(e.g. "Case Study 3: Fraud Detection").

---

## 2. Research step (do this before writing anything)

For every chapter request:

1. Run 3–6 `project_knowledge_search` calls against **System_Design_V2.pdf** using the
   chapter's distinctive keywords (section headers, named patterns, tool names) — not just the
   chapter title — to pull all its sub-sections, code blocks, war stories, and the cheat sheet.
2. Run 2–4 more searches against **System_Design___Data_Engineers_old_version.pdf** for the
   same topic to surface any extra trade-off tables, extra case studies, or a differently-phrased
   explanation worth including as a "supplementary" note.
3. Reconstruct every garbled V2 passage into clean English before using it. Do not fabricate
   content — if a sub-section isn't returned by search, search again with different keywords
   before assuming it doesn't exist.
4. Only after research is complete, draft the two output files.

---

## 3. Required content inventory per chapter

Every chapter deliverable (HTML + Markdown) MUST include all of the following, pulled
faithfully from the books — never invented:

1. **"What you'll be able to say by the end"** — the quoted "senior-sounding one-liners" block
   the book opens each chapter with.
2. **Core concept explanation** — the main teaching content, in clear prose, organized under
   headers/bullets (never a wall of text).
3. **At least one interactive/mermaid diagram** reproducing the chapter's key figure (e.g. the
   Iceberg metadata tree, the CDC pipeline, the 45-minute interview timeline) — see Section 5.
4. **Trade-off / decision tables** — reproduce every "OPTION / STRENGTHS / WEAKNESSES /
   PICK WHEN"-style table verbatim in structure (rows and content), formatted as a real table.
5. **Gotchas** — a dedicated section pulling together every "Anti-Pattern," "common trap,"
   "common misread," and "common challenge" the chapter lists. Label which book each came
   from only if there's a meaningful difference; otherwise merge silently into one clean list.
6. **War Stories** — reproduced as a distinctly styled callout (not blended into body text),
   since these are the book's memorable production-incident anecdotes.
7. **FAANG Signal(s)** — reproduced as a distinctly styled callout. These are the book's explicit
   "this is what separates senior from mid-level" notes — the single most interview-relevant
   content in each chapter. Never compress these away.
8. **Interviewer transcript excerpt** — if the chapter contains an interviewer/candidate
   dialogue (most do, especially in case studies and the deep-dive chapters), reproduce it as a
   labeled Q&A exchange, not paraphrased into third person.
9. **"Senior-level lines to say out loud"** — the book's scripted phrases (e.g. "I'd partition by
   the natural key... and carve out a dedicated shard for the top 0.1 percent of accounts by
   volume") — collect these into their own callout since they are literally interview answers.
10. **Cheat sheet** — reproduce the chapter's own end-of-chapter cheat sheet as a compact
    reference block (this is the "built to be photographed" section — treat it as the highest-
    density summary, suitable for last-minute review).
11. **Special notes** — anything the book flags as engine-specific quirks, compliance
    implications (GDPR, SOX), or "further reading" — keep further reading as its own short list.
12. **Code examples** — reproduce any `src/code-examples/...` SQL/code blocks in fenced code
    blocks with correct syntax highlighting.

If the old-version book has a relevant framework component the newer edition compresses (e.g.
the 5-Step Framework in Ch.2, or extra case studies in Ch.16), add it as a clearly labeled
"Supplementary (from the 2025 edition)" subsection rather than merging it silently into V2's voice.

---

## 4. Output 1 — Markdown file

- Filename: `chXX_kebab_case_title.md` (e.g. `ch03_fundamentals_of_scale.md`).
- Structure with real Markdown headers (`#`, `##`, `###`) — never fake headers with bold text.
- Use genuine Markdown tables for every trade-off table.
- Use blockquotes (`> `) for War Stories, FAANG Signals, and "senior lines to say out loud" —
  each type gets a bolded label inside the blockquote, e.g. `> **🚩 FAANG Signal**` /
  `> **⚠️ War Story**` / `> **✅ Say this out loud**` / `> **❌ Anti-Pattern**`.
- Every diagram is a **Mermaid** code block (` ```mermaid `), using the diagram type that best
  fits (`flowchart`, `sequenceDiagram`, `gantt` for the interview timeline, `erDiagram` for data
  models, etc.) — never a static image or ASCII art substitute.
- Code examples in fenced blocks with the correct language tag (`sql`, `python`, etc.).
- End with a "Cheat Sheet" section as a tight bullet/table block, then "Further Reading."

## 5. Output 2 — HTML file

- Filename: `chXX_kebab_case_title.html`, self-contained (inline `<style>`, no external
  dependencies except Mermaid.js via CDN for diagrams, loaded from
  `https://cdnjs.cloudflare.com`).
- Visual design: follow the `frontend-design` skill — pick a deliberate palette/type system that
  fits a "staff engineer's technical playbook" subject (not a generic AI-blue gradient template).
  A dark, terminal/editorial technical-book feel suits this content well, but make an intentional
  choice and state it in a one-line design note before building, then stay consistent across all
  chapters so the set feels like one book.
- Structure mirrors the Markdown file's section order exactly, styled as distinct visual
  components:
  - Callout boxes with distinct left-border colors/icons for: FAANG Signal, War Story,
    Anti-Pattern vs Pattern (paired, side-by-side if space allows), Say-this-out-loud lines.
  - Trade-off tables as real styled `<table>` elements, not images.
  - The chapter's key figure(s) rendered as an **interactive diagram**: prefer an inline SVG or
    small HTML/JS widget (hoverable nodes, expandable detail, or step-through states) over a
    static Mermaid render where the content benefits from interaction (e.g. the metadata tree,
    the 4-phase interview timeline, the CDC pipeline). Where the diagram is simple and linear,
    a clean Mermaid render (via mermaid.js in-browser) is acceptable.
  - Code blocks with monospace styling and a visible language label.
  - A dedicated, visually distinct "Cheat Sheet" panel near the end — this is the
    "photograph this before your interview" artifact, so give it strong visual hierarchy
    (e.g. a boxed grid or card layout), since the book explicitly designs it to be screenshotted.
- Responsive down to mobile width; visible focus states on any interactive element; respect
  `prefers-reduced-motion`.
- No login, no external API calls, no tracking — this is a static study document.

---

## 6. Voice and fidelity rules

- Preserve the book's actual interview scripts and quoted lines verbatim (in quotation marks) —
  these are literally "here's what to say," and paraphrasing weakens their interview value.
- Never sanitize or soften a War Story or Anti-Pattern — the specificity (the 38%-of-volume
  merchant, the 8x Hudi storage bloat) is the pedagogical point.
- Do not invent gotchas, numbers, or code that aren't in the books. If something is genuinely
  unclear from extraction, search again rather than guessing, and if still unclear, mark it
  `[verify against source page]` rather than inventing a plausible-sounding number.
- Keep the tone the book uses for its own "what you'll be able to say" lines — confident,
  compressed, staff-engineer register — when reproducing them; keep Claude's own connective
  explanation in plain, clear teaching prose.
- Match content depth to interview prep, not academic completeness: prioritize the parts of each
  chapter the book itself flags as interview signal (FAANG Signal, cheat sheet, transcript) over
  incidental prose.

---

## 7. How to invoke this per chapter

Say any of:
- "Generate Chapter 4 (Storage Engines)."
- "Do the next chapter."
- "Redo Chapter 9's HTML with a different diagram for the metadata tree."
- "Do Case Study 3 from Chapter 16 as its own deliverable."

Each request should produce exactly one Markdown file and one HTML file, following this
instruction set, presented together.
