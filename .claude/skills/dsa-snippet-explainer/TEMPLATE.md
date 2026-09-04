# Markdown cell template

Paste this structure into the new notebook cell. Replace the combination-sum-specific lines with the
snippet's DSA. The filled example is the Combination Sum / Combination Sum II trace in
`DSA_Deep_Dive/21_Backtracking/21_backtracking.ipynb` (the cell right after `combine` / `combination_sum` /
`combination_sum2`). This is the **only** format this skill produces — always the full table trace below,
never a depth choice, never per-step ASCII/fenced blocks.

```markdown
### Step-by-step: what this cell actually does

<Shared shape/invariant across the function(s) in one or two sentences>. <What exactly differs between
them — the one or two lines of code that change, not a redesign>. <Demo input(s) and the exact
result(s)/assert(s) the trace will hit>.

#### `<fn_a>(<demo args>)` — <short tagline, e.g. "reuse allowed">

1. <algorithm step 1 — e.g. sort / base case>
2. <algorithm step 2 — e.g. loop + prune condition>
3. <algorithm step 3 — e.g. choose/recurse/un-choose, naming exactly which index the recursive call uses>

Demo: `<the exact demo call as the notebook writes it>`.

| Step | Action | `<state col 1>` after | `<state col 2>` after | `<out/res>` after |
|---|---|---|---|---|
| 1 | `<call>` entered | `<value>` | `<value>` | `<value>` |
| 2 | `i=<i>`: CHOOSE `<val>` | `<value>` | `<value>` | `<value>` |
| 3 | … one row per real step, no skipped/compressed rows … | | | |

Final `<out/res> = <value>` — matches `assert <...>`. <One tie-out sentence — why a particular row
mattered, e.g. the row where a prune or dedup-skip changed the outcome.>

#### `<fn_b>(<demo args>)` — <short tagline, e.g. "each slot once, duplicates skipped">

(same shape: numbered algorithm list, demo line, full table, tie-out sentence)

#### Mental model

- <what changes between fn_a and fn_b — the specific line/guard, not a restatement of the loop>
- <what the recursion's shrinking/loop variable actually represents>
- <why the prune/guard is safe — what property of the input makes it correct>
- <one general lesson that transfers to the next problem of this shape>
```

## Table columns

Always `Step` + `Action` + one column per piece of mutable state the function threads through recursion
(commonly `path`/`out`/`res`, plus whatever drives the recursion: `remaining`, `i`, `start`, two pointers,
a visited set size, etc.). Bold or all-caps the operation keyword inside `Action` (`CHOOSE`, `INCLUDE`,
`EXCLUDE`, `BREAK`, `SKIP`, `RECORD`, `UN-CHOOSE`) and include the concrete comparison that drove it, e.g.:

```
| 5 | `backtrack(0, 1)` → `i=0`: `2 > 1` → **BREAK** | `[2, 2, 2]` | 1 | `[]` |
```

Never collapse a run of steps into `...` and never drop into a fenced ASCII block per step — every
mutation gets its own row, all the way to the end of the demo call.
