---
name: dsa-snippet-explainer-bn
description: Insert a Bengali (বাংলা) step-by-step markdown study cell after a Jupyter code snippet, using the exact same full markdown-table trace format as the dsa-snippet-explainer skill (Step | Action | state columns), with prose translated to Bengali and code/values/table syntax kept as-is. Use when the user asks for a snippet/cell explained "in Bengali" / "বাংলায়", or asks to translate an existing trace cell into Bengali.
---

# DSA Snippet Explainer (Bengali)

Same job as [`dsa-snippet-explainer`](../dsa-snippet-explainer/SKILL.md), same required table format —
only the language of the prose changes. Canonical example: the Bengali trace cell inserted after the
English Combination Sum / Combination Sum II trace in
`DSA_Deep_Dive/21_Backtracking/21_backtracking.ipynb`.

Do **not** invent a different structure for the Bengali version. Do **not** write a separate `.md` file.
Do **not** rewrite the code cell.

## When to use

- User asks to explain a code cell / snippet **in Bengali** (বাংলায়), or asks for "the same explanation
  but in Bengali."
- User points at an existing English trace cell (made by `dsa-snippet-explainer`) and asks for a Bengali
  version of it.
- User asks to translate an existing markdown explanation cell into Bengali.

## Workflow

```
- [ ] 1. Get an English-quality trace first — either read an existing English trace cell for this code,
        or build one mentally/on paper following dsa-snippet-explainer's rules (identify snippet, demo
        data, simulate every step)
- [ ] 2. Translate structure-for-structure into Bengali: headings, algorithm-list prose, Action-column
        prose, tie-out sentences, Mental model bullets
- [ ] 3. Insert one new markdown cell — right after the English trace cell if one exists in this slot,
        otherwise right after the target code cell
- [ ] 4. Remove an empty placeholder cell if one sits in the insertion slot
```

### 1. Get the trace right before translating

Read the target code cell and its demo/`assert`/print output exactly as `dsa-snippet-explainer` would.
If an English trace cell already exists directly below the code (the common case — this skill is usually
invoked right after `dsa-snippet-explainer` or on a notebook that already has one), use **that cell's
content** as the source of truth for the steps, table rows, and final state — translate it, do not
re-derive it from scratch and risk drifting from what's already been verified. If no English trace exists
yet, hand-simulate the code yourself first (same rigor as `dsa-snippet-explainer`: every recursive
call/mutation, matching the notebook's `assert`).

### 2. Translate, don't redesign

Keep **exactly** the same shape as the English format:

- `### ধাপে ধাপে ব্যাখ্যা (বাংলায়): এই সেলটা আসলে কী করছে` as the top heading (or an equivalent
  natural Bengali phrasing of "Step-by-step: what this cell actually does" — keep it consistent within
  one notebook).
- One `####` subsection per function, in the same order, with the same tagline pattern translated
  (e.g. `#### \`combination_sum(...)\` — বারবার reuse করা যায়`).
- The same numbered algorithm list, translated line by line.
- The same demo line, translated (`Demo:` → `Demo:` is fine, or `ডেমো:`), keeping the exact call/values
  in code font untouched.
- **The exact same markdown table** — same number of rows, same columns, same `Step` numbers, same
  code/number values in every cell. Only the `Action` column's descriptive words move to Bengali; keywords
  like CHOOSE / INCLUDE / EXCLUDE / BREAK / SKIP / RECORD / UN-CHOOSE stay in English caps (they're
  algorithm vocabulary, not prose) — translate the surrounding words only, e.g.
  `i=2: 6 > 3 → **BREAK**` stays `i=2: 6 > 3 → **BREAK**`, but a sentence like "loop ends" around it
  becomes Bengali.
- The same tie-out sentence after each table, translated, still naming the exact `assert`/result values
  in code font (never translate the values themselves — `[2, 2, 3]` stays `[2, 2, 3]`).
- `#### মানসিক মডেল (Mental model)` closing with the same number of bullets, same meaning, translated.

Never translate: variable/function names, code snippets, table pipes/backticks, numbers, or the literal
Python values shown in state columns. Keep an English gloss in parentheses for any Bengali technical term
that isn't obvious on first read (as `dsa-snippet-explainer-bn`'s own examples do, e.g. "মানসিক মডেল
(Mental model)").

### 3. Insert

Insert with the notebook editor (`edit_mode: "insert"`). If an English trace cell exists in this slot,
insert **after that cell** (`cell_id` = the English trace cell's id) so English and Bengali sit side by
side, English first. If none exists, insert directly after the code cell like `dsa-snippet-explainer`
would, and produce the full trace (in Bengali) yourself per section 1.

Do not overwrite a non-empty explanation (English or Bengali) without asking.

## Quality checklist

- [ ] Same number of table rows and same values as the English (or hand-simulated) source trace — nothing
      dropped, compressed, or invented in translation.
- [ ] Every function traced in English is also traced in Bengali, same order.
- [ ] Algorithm keywords (CHOOSE/INCLUDE/EXCLUDE/BREAK/SKIP/RECORD/UN-CHOOSE) stayed in English caps.
- [ ] Code identifiers, values, and table syntax are byte-identical to the source — only prose moved to
      Bengali.
- [ ] Mental model section present, same number of bullets as the source.
- [ ] New cell placed correctly (after the English trace if one exists, else after the code cell); no
      leftover empty stub cell.
