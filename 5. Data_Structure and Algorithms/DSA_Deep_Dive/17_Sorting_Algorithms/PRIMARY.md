# Sorting Algorithms — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use sorting (1, 4, 6, 7, 10).

**Corresponds to README.md sections:**
- §5 — Python's `sorted()`
- §6 — Stability in action (multi-key sorting)
- ~~§1~~ — the O(n log n) lower bound: CS depth, not needed here
- ~~§2–§4~~ — hand-written insertion/merge/quicksort: not needed here — see the full tutorial if you want them

---

- **Just use `sorted()` / `.sort()`** with a `key=` function and `reverse=True/False`. You never hand-roll a sort in any of these problems.
- **The one property that matters: stability.** Python's sort never reorders elements that compare equal.
- **The multi-key sort trick** (used in Jira CSV Exporter, Ballot Processing, Customer Satisfaction): to sort by several columns with **independent, possibly-mixed** directions, sort once per column — **least significant column first, most significant column last**. Stability carries each earlier pass's ordering through as the tiebreak under the final sort.
  ```python
  step1 = sorted(issues, key=lambda i: i["assignee"], reverse=True)   # least significant, first
  result = sorted(step1, key=lambda i: i["status"])                    # most significant, last
  ```

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for the comparison-sort lower bound and hand-written sort implementations.
