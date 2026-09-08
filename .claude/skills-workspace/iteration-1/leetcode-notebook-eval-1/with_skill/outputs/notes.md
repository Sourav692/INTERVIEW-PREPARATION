Coin Change study notebook - test run notes
=============================================

Scope confirmation
-------------------
No files were written outside this test outputs folder:
  .claude/skills-workspace/iteration-1/leetcode-notebook-eval-1/with_skill/outputs/

Specifically:
- coin_change.ipynb and bench_utils.py were both written ONLY into this outputs folder
  (not into the real "DSA_Blind 75/notebooks/..." path the skill normally specifies,
  and not into "5. Data_Structure and Algorithms" or any other repo directory).
- No files in "DSA_Blind 75" or "5. Data_Structure and Algorithms" were created, edited,
  or deleted.
- `git status` shows pre-existing, unrelated modifications to AGENTS.md, pyproject.toml,
  and uv.lock (a databricks-connect version pin/lock change) that were already present
  before this task and were NOT made by this notebook-generation work; they were left
  untouched.
- A helper script used to generate the notebook JSON, and a scratch execution-test copy
  of the notebook's code cells used only to verify the notebook runs top-to-bottom, were
  both written to the session scratchpad directory (outside the repo) and/or deleted
  after use, not left in the repo.

Bootstrap deviation from the skill (documented, not hidden)
-------------------------------------------------------------
The skill normally expects one shared `bench_utils.py` living once at
`DSA_Blind 75/notebooks/` and every problem notebook's bootstrap cell walks up from
`os.getcwd()` to find it there. For this test run, `bench_utils.py` was instead placed
directly alongside `coin_change.ipynb` in this outputs/ folder (a "topic folder of one").
The notebook's bootstrap cell still walks up from `os.getcwd()` looking for
`bench_utils.py` (same mechanism as the real skill), so it transparently finds the
test-local copy one directory level closer instead of at a real notebooks/ root -- no
other simplification was made to the bootstrap logic. This is called out again inline in
the benchmark markdown/code cells of the notebook itself.

Approaches included in the notebook (worst -> best, per the skill's required order)
---------------------------------------------------------------------------------
1. Approach 1 - Brute Force: plain recursion with no caching, branching over every coin
   at every remaining amount. O(n^amount)-ish exponential time, O(amount) recursion-stack
   space.
2. Approach 2 - Better: memoized (top-down) recursion -- identical recursion, but caches
   each distinct remaining-amount result in a dict. O(amount * num_coins) time,
   O(amount) space (memo table + call stack).
3. Approach 3 - Optimal: bottom-up tabulation -- fills a 1-D dp array from amount 0 up to
   the target. Same O(amount * num_coins) time as Approach 2, O(amount) space, but no
   recursion overhead or Python recursion-depth risk.

Other required sections present: title cell; Concepts cell with first-principles "What
is it?" primers for Recursion, Memoization (Top-Down DP), and Dynamic Programming
(Bottom-Up / Tabulation); problem statement with 3 example I/O pairs and constraints;
one markdown+code pair per approach; a test/verification cell (asserts across 6 cases,
including an unreachable amount and amount=0); an empirical complexity benchmark cell
using the shared bench_utils.benchmark helper (two separate worst-case generators were
used deliberately: coins=[1] for the two DP approaches to maximize sub-problem count,
and coins=[1,3,4,5] with smaller sizes for the brute-force approach, since coins=[1]
alone has no real branching and would not demonstrate its exponential behavior); and a
final "Patterns Learned" cell.

Verification performed
-----------------------
All code cells were extracted and executed end-to-end outside the notebook (concatenated
into a throwaway script) to confirm: all assertions pass, and the benchmark's doubling
ratios roughly track the claimed complexities (~2x per doubling for the DP approaches,
~10-18x per step for the uncached brute force, confirming non-polynomial growth).
