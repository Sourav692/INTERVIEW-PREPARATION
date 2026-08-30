# Generic (M-ary) Trees — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use generic trees (2 — Confluence Page Word Count, 8 — Company Hierarchy).

**Corresponds to README.md sections:**
- §2 — vocabulary (quick skim)
- §3 — children-list representation only (skip the `{id, parent_id}` and first-child/next-sibling parts)
- §4 — DFS pre/post-order (skip BFS)
- §5 — the everyday operations / solve-subtree-then-combine pattern
- ~~§1, §6~~ — not needed here — see the full tutorial if you want them

> ⚠️ **Do not read `04_Tree_Traversal`** for these problems — that tutorial is binary-tree-specific (in-order traversal, tree reconstruction, Morris traversal). Both Atlassian tree problems use **generic M-ary trees** with no left/right distinction, so none of it applies. Everything you need is right here.

---

- **Representation:** a node holds a value plus a `children` **list** (any number of children) — exactly the `Page`/`Node` classes in both problems.
- **The one traversal that matters here: post-order DFS.** Process every child before combining their results into the current node's own answer.
  ```python
  def solve(node):
      result = own_contribution(node)
      for child in node.children:
          result = combine(result, solve(child))
      return result
  ```
- This "solve each subtree, then combine" shape **is** the entire algorithm behind both `subtreeWordCount` (Confluence Word Count) and `lowest_common_manager` (Company Hierarchy) — everything else in those problems is bookkeeping around this one pattern.
- You do not need BFS on a generic tree, the `{id, parent_id}` flat-reconstruction technique, or the first-child/next-sibling representation for either problem.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for BFS, the `{id, parent_id}` reconstruction, and real-world examples.
