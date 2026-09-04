---
name: dsa-snippet-explainer
description: Insert a step-by-step markdown study cell immediately after a Jupyter code snippet, tracing every operation as a full markdown table (Step | Action | state columns) matching notebook asserts — the same format used for the Combination Sum / Combination Sum II trace. Works for any DSA (heaps, hash tables, sorting, graphs, trees, two pointers, tries, backtracking, etc.). Use when the user asks to explain a notebook cell, code snippet, or algorithm step by step, "in the same format" as a prior walkthrough, or to add a markdown cell after selected code.
---

# DSA Snippet Explainer

Turn **one code cell** into a **markdown cell right below it** so the reader can follow every mutation without leaving the notebook. Canonical example: the Combination Sum / Combination Sum II trace in `DSA_Deep_Dive/21_Backtracking/21_backtracking.ipynb` (the cell after `combine`/`combination_sum`/`combination_sum2`) — **every explanation this skill produces uses that cell's table format**, not ASCII-block format from older versions of this skill.

Do **not** write a separate `_explained.md` file (that is `tree-notebook-explainer`). Do **not** rewrite the code cell.

## When to use

- User points at a notebook cell / attached selection and asks to explain it step by step.
- User wants “the same format as [the heap walkthrough / the combination sum walkthrough / a prior trace]” for another DSA snippet.
- User asks to add a markdown explanation cell after existing code.

## Workflow

Copy this checklist:

```
- [ ] 1. Identify the exact code cell and its demo input / asserts / printed output
- [ ] 2. Simulate every step; every claimed state must match a real execution of the code
- [ ] 3. Insert one markdown cell immediately after that code cell, using the table format below
- [ ] 4. Remove an empty placeholder cell if one sits in that slot
```

There is no depth/format question anymore — **always** produce the full step-by-step markdown-table
trace described below. Do not ask the user to pick a depth or a diagram style; the only thing worth
asking (and only if genuinely ambiguous) is *which* function(s) in the cell to trace.

### 1. Identify the snippet

Read the notebook around the selection. Use:

- The cell’s own demo data (`h = []`, `for x in [...]`, test arrays).
- `assert` / `print` lines as the **source of truth** for the final state.
- Neighboring README only to name invariants (heap property, `hash % capacity`) — **trace the notebook’s numbers**, not a different tutorial example.

If the cell has several functions (e.g. `combine`, `combination_sum`, `combination_sum2`), explain **all of them** in one markdown cell, each as its own `####` subsection, in the order the demo runs — unless the user explicitly named only a subset.

### 2. Simulate, then write

Hand-simulate (or mentally execute) the Python **every step of the way** — every recursive call, choose/include, prune/break, un-choose/exclude, record. If an index, swap, or branch is wrong, the cell is useless. Do not compress or skip steps with `...` — write one table row per step, all the way through, exactly like the Combination Sum reference trace.

Insert with the notebook editor (`edit_mode: "insert"`, `cell_id` = the target code cell's id, `cell_type: "markdown"`). If the next cell is an empty code/markdown stub, **replace or delete it** so the explanation sits directly above the next real heading.

Do not overwrite a non-empty explanation without asking.

See [TEMPLATE.md](TEMPLATE.md) for a fill-in-the-blanks version of the shape below.

## Required cell shape (always this format)

Heading levels:

- `### Step-by-step: what this cell actually does` — top of the new cell (the notebook section is already `##`).
- `####` for each function traced, and **Mental model** at the end.

### Opening (2–4 sentences)

Under the `###` heading: state the shared shape/invariant across the function(s) in plain words (e.g. “both share one recursion, `backtrack(start, remaining)` …”), name exactly what differs between them (one or two lines of code, not a redesign), and note the demo input(s)/expected result(s) the trace will hit.

### Per-function sections (`#### functionName(...)  — short tagline`)

For **each** function the demo calls, in this exact order:

1. A short numbered algorithm list (2–5 steps: sort / base case / loop-and-prune / choose / recurse / un-choose). This replaces the old separate “primer” section — fold any “why this formula/invariant” explanation into these numbered steps or into one sentence directly above the table, not into ASCII art.
2. One line naming the demo input exactly as the notebook calls it (`Demo: candidates = [2, 3, 6, 7] (already sorted), target = 7.`).
3. **A markdown table**, one row per step, columns = `Step` + `Action` + one column per piece of mutable state the function tracks (typically `path`/`out`/`res` after, plus whatever drives the recursion: `remaining`, `i`, `start`, pointers, etc.). Match the reference table shape:

   ```
   | Step | Action | `path` after | `remaining` after | `res` after |
   |---|---|---|---|---|
   | 1 | `backtrack(0, 7)` entered | `[]` | 7 | `[]` |
   | 2 | `i=0`: CHOOSE `2` | `[2]` | 5 | `[]` |
   ...
   ```

   - `Action` cells name the concrete operation and its outcome inline: `CHOOSE`, `INCLUDE`, `EXCLUDE`, `BREAK`, `SKIP`, `RECORD`, `UN-CHOOSE` in bold/caps, plus the comparison or index that drove it (`i=2: 6 > 3 → **BREAK**`).
   - Every row must reflect a real step of a real execution — no invented shortcuts, no `...` ellipsis rows. If the true trace has 50 rows, write 50 rows.
   - Do not add ASCII/mermaid diagrams inside a step; the table row *is* the picture. (An array-with-indices line is fine only in the opening/algorithm-list prose if the topic genuinely needs an index map, e.g. `index: 0 1 2 3 → value: 1 1 2 5`, but never as a per-step fenced block.)

4. Immediately after the table: one sentence tying the final row to the notebook’s `assert`/printed output (`Final res = [[2, 2, 3], [7]] — matches assert cs == [[2, 2, 3], [7]]`), plus, if genuinely useful, one line on *why* a particular row mattered (the row where a dedup-skip or prune changed the outcome).

### Close

- `#### Mental model` — 3–5 bullets: the “why” behind what changed between the traced functions (which line/guard changes semantics, what the loop variable really represents, what the prune buys), not a restatement of the loop.

## Style

- Complete sentences. No filler. No jargon without a five-word gloss the first time.
- Do not import leftovers from other chats (CSV `escape_field`, unrelated lambdas).
- Complexity notes belong **after** the table for that function, in the closing tie-out sentence — not as a separate section.
- Match the notebook exactly: variable names (`path` vs `out` vs `res`), 0-based indices, Python `//`, whatever the actual code calls things.
- If the user asks for a translation/localization of an existing trace cell (e.g. “same thing but in Bengali”), keep this exact table structure and translate the prose/Action text; keep code identifiers, values, and table syntax (`|`, backticks) untouched.

## Quality checklist

- [ ] Markdown cell is the next cell after the target code.
- [ ] Every function the demo calls has its own `####` subsection with a numbered algorithm list, a demo line, and a full markdown table.
- [ ] Every table row matches a real step of a real execution of that cell — no skipped/compressed steps.
- [ ] Final table row(s) match `assert` / printed output for every traced function.
- [ ] Mental model is present at the end.
- [ ] No ASCII-art/fenced per-step diagrams were used in place of table rows.
- [ ] Empty stub cell under the new markdown is gone.