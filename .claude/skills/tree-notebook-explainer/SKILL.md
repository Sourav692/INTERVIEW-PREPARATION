---
name: tree-notebook-explainer
description: Generate detailed step-by-step markdown reference docs from DSA_Deep_Dive tree notebooks (generic tree, binary tree, BST, tree traversal). For each code function it produces line-by-line explanations, ASCII tree diagrams, and full iteration traces showing stack/queue/result state after every step — the same teaching style used in chat walkthroughs. Invoke when the user asks to "explain the notebook", "create reference notes", "step-by-step trace", or wants markdown study notes for tree notebook code.
---

# Tree Notebook Explainer

Turn runnable tree notebooks into **personal reference markdown** — one file per notebook, one section per meaningful code block. The reader should be able to follow every line and every loop iteration without opening the notebook.

## When to use

- User asks to explain a tree notebook, create reference notes, or document notebook code step-by-step.
- User names a notebook (`04_tree_traversal`, `03_binary_search_tree`, etc.) or says "all tree notebooks".
- User wants the chat-style walkthrough format (line tables + iteration traces with stack/result) saved to disk.

## Scope — tree notebooks

### DSA Deep Dive (`DSA_Deep_Dive/notebooks/`)

| Notebook | Path |
|----------|------|
| Generic tree | `01_generic_tree.ipynb` |
| Binary tree | `02_binary_tree.ipynb` |
| Binary search tree | `03_binary_search_tree.ipynb` |
| Tree traversal | `04_tree_traversal.ipynb` |

Output: `DSA_Deep_Dive/reference/<basename>_explained.md`

### Blind 75 (`DSA_Blind 75/notebooks/Tree/`)

All 14 tree-topic problem notebooks (max depth, same tree, invert, subtree, level order, construct tree, validate BST, kth smallest, LCA BST, max path sum, serialize, add/search word, implement trie, word search II).

Output: `DSA_Blind 75/reference/Tree/<basename>_explained.md`

If the user names a different notebook under either project, apply the same format unless they say otherwise.

## Output location & naming

- **Deep Dive:** `DSA_Deep_Dive/reference/<notebook_basename>_explained.md`
- **Blind 75:** `DSA_Blind 75/reference/Tree/<notebook_basename>_explained.md`
  - Example: `maximum_depth_of_binary_tree.ipynb` → `DSA_Blind 75/reference/Tree/maximum_depth_of_binary_tree_explained.md`
- Create `DSA_Deep_Dive/reference/` if missing.
- Do **not** overwrite an existing file without asking.
- After writing, tell the user the file path and which functions were documented.

## Workflow

1. **Read** the target notebook top-to-bottom. Also skim the matching tutorial in `DSA_Deep_Dive/tutorials/` for the canonical tree diagram and expected outputs.
2. **Identify** every code cell worth explaining: class definitions (brief), each function/algorithm, and rebuild/utility helpers. Skip pure `assert`/`print` test-only cells unless they teach something.
3. **Use the sample tree from the notebook** for all traces. If the notebook has multiple trees, pick the one the asserts use. Draw it as ASCII before tracing.
4. **Write one markdown file** following [TEMPLATE.md](TEMPLATE.md). One `##` section per function.
5. **Verify** every claimed output matches the notebook's `assert` lines or printed expected values.

## Required section format (every function)

Use this order inside each `## Function Name` section:

### 1. One-sentence purpose
What the function does and when you'd use it.

### 2. The tree / input used for the trace
ASCII diagram of the exact tree or input data. Label the root and note BST vs generic vs binary.

### 3. Full code block
Copy the function verbatim from the notebook (clean formatting, keep comments).

### 4. Line-by-line table

| Line / code | What it does |
|-------------|--------------|
| ... | Plain English, no jargon without definition |

### 5. Step-by-step execution trace
**Mandatory for:** loops, recursion call order, stack/queue operations, two-pointer moves, rebuild splits.

After **every iteration** (or every recursive visit for small trees), show state in a table:

| Iter | Action | `stack` / `queue` / pointers | `result` / return so far |
|------|--------|------------------------------|--------------------------|

Conventions:
- **Stack:** `[bottom ... top]` — mark which end is popped.
- **Queue:** `[front ... back]` — mark `popleft` end.
- **Recursion:** show call order and when `visit` happens (pre/in/post).
- Bold the **visited / popped** value each step.

### 6. Final output
State the final result and confirm it matches the notebook assert.

### 7. Mental model
1–3 bullets or one paragraph — the "why", not the "what".

### 8. Common confusions (when applicable)
Call out traps the user has asked about before:
- In-order is sorted **only on a BST**, not every binary tree.
- Iterative pre-order: push **right then left** so left pops first (LIFO).
- Post-order with two stacks: stack1 = Root→Right→Left, stack2 reverses.
- `height` base case `-1` vs `0` depending on edge vs node counting.
- Orphan / forest handling in flat-list → tree builders.

## Trace depth rules

| Algorithm type | How deep to trace |
|----------------|-------------------|
| DFS recursive on ≤7 nodes | Trace every visit in order |
| Iterative with stack/queue | Trace **every** loop iteration until empty |
| Simple O(1) helpers (`size`, `find`) | Walk one example call tree; show recursive unwind for 2–3 nodes |
| Tree rebuild from traversals | Trace first 2–3 recursive `build()` calls with split indices |
| BFS level-order | Show queue after each dequeue + enqueue batch |

Do not skip iterations with "..." unless the pattern is identical and you've shown at least 3 consecutive identical steps.

## Style rules

- Write for self-study reference — complete sentences, skimmable tables.
- Use the **same tree** across related functions in one file when possible (e.g. BST `50/30/70/...` for traversal notebook if the tutorial uses it; generic `A/B/C/...` tree for notebook 01).
- Prefer ASCII trees over mermaid (renders everywhere).
- No filler. Every table row must teach something.
- Complexity: one line at the end of each section (`Time O(...)`, `Space O(...)`) with a short justification.

## Multi-notebook batch

If the user asks for all tree notebooks:
- Generate four files, one per notebook.
- Reuse consistent terminology across files.
- Do not merge into one giant file unless asked.

## Quality checklist

Before finishing, confirm:

- [ ] Every function in the notebook that implements an algorithm has its own section.
- [ ] Every loop-based algorithm has a full iteration table.
- [ ] Outputs match notebook `assert` values.
- [ ] ASCII tree appears before the first trace in each section.
- [ ] Common confusions included where relevant.
- [ ] File saved under `DSA_Deep_Dive/reference/`.

## Additional resources

- Output structure template: [TEMPLATE.md](TEMPLATE.md)
