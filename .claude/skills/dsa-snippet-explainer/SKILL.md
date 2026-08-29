---
name: dsa-snippet-explainer
description: Insert a step-by-step markdown study cell immediately after a Jupyter code snippet, tracing every operation with ASCII diagrams and matching notebook asserts. Works for any DSA (heaps, hash tables, sorting, graphs, trees, two pointers, tries, etc.). Use when the user asks to explain a notebook cell, code snippet, or algorithm "in the same format" as the heap push/pop walkthrough, or to add a markdown cell after selected code.
---

# DSA Snippet Explainer

Turn **one code cell** into a **markdown cell right below it** so the reader can follow every mutation without leaving the notebook. Canonical example: `DSA_Deep_Dive/12_Heaps_Priority_Queues/12_heaps_priority_queues.ipynb` (the cell after `push`/`pop`).

Do **not** write a separate `_explained.md` file (that is `tree-notebook-explainer`). Do **not** rewrite the code cell.

## When to use

- User points at a notebook cell / attached selection and asks to explain it step by step.
- User wants “the same format as the heap walkthrough” for another DSA snippet.
- User asks to add a markdown explanation cell after existing code.

## Workflow

Copy this checklist:

```
- [ ] 1. Identify the exact code cell and its demo input / asserts / printed output
- [ ] 2. Ask depth + primer questions unless the user already answered
- [ ] 3. Simulate every step; every claimed array/tree/map must match the code
- [ ] 4. Insert one markdown cell immediately after that code cell
- [ ] 5. Remove an empty placeholder cell if one sits in that slot
```

### 1. Identify the snippet

Read the notebook around the selection. Use:

- The cell’s own demo data (`h = []`, `for x in [...]`, test arrays).
- `assert` / `print` lines as the **source of truth** for the final state.
- Neighboring README only to name invariants (heap property, `hash % capacity`) — **trace the notebook’s numbers**, not a different tutorial example.

If the cell has several functions (`push` and `pop`), explain **all of them** in one markdown cell, in the order the demo runs.

### 2. Ask before writing (required unless already specified)

Use a structured question tool when available. Ask only what changes the cell:

**Depth** (pick one):

| Option | Meaning |
|--------|---------|
| Full | Every mutating operation (every push/pop/insert/swap/pointer move) with state **after each one** |
| First-class ops + one unwind | Full trace of the “build” loop; only the first “undo” op (e.g. first `pop`) in detail, then “repeat → …” |
| Compact | One table row per operation; ASCII snapshot only at the **end** of the build |

**Primer** (pick one):

- **Yes** — short “why these formulas / invariants” section **before** the trace (default, matching the heap cell).
- **No** — skip; the code cell or a heading above already covers it.

If the user already said “same as the heap cell”, take **Full** + **Yes** without asking.

Do **not** write the markdown until those two answers exist.

### 3. Simulate, then write

Hand-simulate (or mentally execute) the Python. If a swap or index is wrong, the cell is useless.

Insert with the notebook editor (`is_new_cell: true`, index = code cell index + 1, language markdown). If the next cell is an empty code/markdown stub, **replace or delete it** so the explanation sits directly above the next real heading.

Do not overwrite a non-empty explanation without asking.

## Required cell shape

Follow [TEMPLATE.md](TEMPLATE.md) in this order. Heading levels:

- `### Step-by-step: what this cell actually does` — top of the new cell (the notebook section is already `##`).
- `####` for the primer, each algorithm (`push`, `pop`, …), and **Mental model**.

### Opening (2–4 sentences)

State the **invariant** in plain words, how the structure is stored, and the **exact** printed/asserted results the demo will hit.

### Primer (`#### …`) — if they asked for it

Topic-specific, not generic CS:

- Table of index formulas / pointer moves / hash reduction / sort keys.
- One ASCII (or array) picture of the **post-build** structure with indices labeled.
- One or two worked index lookups (“parent of value at i=4 is …”).
- One sentence on what `i` / `lo` / `bucket` **means** in this snippet (current hole, not a full-array scan).

### Per-operation traces

For each function the demo calls:

1. Numbered list of the algorithm (append then sift up; save root then sift down; etc.).
2. The demo input in one line.
3. **One block per operation**:
   - Bold title: `**1. push 5**` or `**pop → 1.**`
   - Prose: indices compared, whether a swap happened, resulting array/map **after this step**.
   - Fenced ASCII: `array:` / `buckets:` / pointers on the same snapshot as the prose.

Do not skip steps with `...` unless the user chose Compact, or you have shown ≥3 identical steps and the rest are the same pattern.

### Close

- Tie the last state to the notebook `assert` / print.
- One complexity line if it is already implied by the tutorial (`O(log n)` per push).
- `#### Mental model` — 3–5 bullets: the “why”, not a restatement of the loop.

## Diagrams by DSA

Prefer **ASCII over mermaid** (renders in notebooks). Pick the picture that matches the structure:

| Topic | Show after each step |
|-------|----------------------|
| Heap / complete tree in an array | Array line + tree with `/ \` |
| Binary / BST / generic tree | ASCII tree; mark visited node |
| Hash map / set | `index = hash % cap` then buckets (lists or slots) |
| Array two-pointers / sliding window | Array with `L`/`R`/`i` carets |
| Sort (in-place) | Array after each swap/partition |
| Graph BFS/DFS | Queue/stack + visited set; optional adjacency sketch |
| Trie | Path of nodes for the current key |
| Sweep-line | Time + running counter after each event |

Label **indices** when the code uses arithmetic (`2*i+1`). Bold the value that just moved.

## Style

- Complete sentences. No filler. No jargon without a five-word gloss the first time.
- Do not import leftovers from other chats (CSV `escape_field`, unrelated lambdas).
- Complexity and “this is heapsort” belong **after** the last traced op, not in the primer.
- Match the notebook: min-heap vs max-heap, 0-based indices, Python `//`.

## Quality checklist

- [ ] Markdown cell is the next cell after the target code.
- [ ] Every intermediate array/tree matches a real execution of that cell.
- [ ] Final state matches `assert` / printed output.
- [ ] Primer (if requested) uses the **same** demo data as the trace.
- [ ] Mental model is present.
- [ ] Empty stub cell under the new markdown is gone.