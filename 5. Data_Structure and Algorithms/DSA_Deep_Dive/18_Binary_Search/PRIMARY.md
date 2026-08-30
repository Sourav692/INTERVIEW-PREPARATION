# Binary Search — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problem that uses binary search (4 — Highest Price).

**Corresponds to README.md sections:**
- §3 — `bisect_left` vs `bisect_right` (the only section you need)
- ~~§1~~ — the halving idea — not needed here
- ~~§2~~ — the manual `lo`/`hi`/`mid` implementation — not needed here
- ~~§4~~ — binary search on the answer — not needed here — see the full tutorial if you want it

---

- You only need Python's **`bisect`** module — never the manual `lo`/`hi`/`mid` loop.
- **`bisect_right(a, x) - 1`** = the pattern for "find the latest entry `<= x`" in a sorted list — this is exactly the checkpoint-query trick in *Highest Price*.
  ```python
  idx = bisect.bisect_right(checkpoints, target) - 1
  ```

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for the manual implementation and binary-search-on-the-answer generalization.
