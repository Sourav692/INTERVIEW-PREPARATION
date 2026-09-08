Two Sum notebook - test run notes

Files written (all inside this outputs/ folder only):
- two_sum.ipynb
- bench_utils.py
- notes.md (this file)

No files were written to, or modified in, the real "DSA_Blind 75" or
"5. Data_Structure and Algorithms" directories, or anywhere else in the
repository. This was verified by only ever targeting paths under
".claude/skills-workspace/iteration-1/leetcode-notebook-eval-0/with_skill/outputs/"
for all Write/Bash file operations in this run.

Approaches included in two_sum.ipynb (worst -> best, per the skill's required
3-approach progression):
1. Brute Force - nested loop over all pairs, O(n^2) time / O(1) space.
2. Better - sort (value, original_index) pairs then two-pointer scan inward,
   O(n log n) time / O(n) space.
3. Optimal - single-pass hash map (value -> index) storing seen values and
   checking for the complement, O(n) time / O(n) space.

Also included per the skill's required structure: title cell, Concepts cell
with first-principles "What is it?" primers for Hash Map and Two Pointers,
problem statement with examples/constraints, one markdown+code pair per
approach, a correctness test/verification cell (5 cases, all passed), an
empirical complexity benchmark cell using the shared bench_utils.benchmark
helper (doubling sizes [500, 1000, 2000, 4000], repeats=3, plot=True), and a
closing "Patterns Learned" cell.

Verification performed: extracted all code cells from the notebook and ran
them as a standalone script from within the outputs/ folder. All 5 test
cases passed for all 3 approaches, and the benchmark's measured ratios
tracked the claimed complexities (brute ~4-5x per doubling => quadratic,
optimal ~2-2.2x per doubling => linear, better ~2-3x with more variance at
small n, consistent with O(n log n) plus timing noise at these input sizes).
matplotlib was not installed in this environment, so the plot step printed
its guarded skip message ("[plot skipped: matplotlib not installed]") and
the notebook did not fail - this is the expected fallback behavior described
in bench_utils.py.

Deviation from the skill's stated output location (as instructed for this
test): the notebook and bench_utils.py were saved together in this outputs/
folder instead of under "DSA_Blind 75/notebooks/Array/two_sum.ipynb" and a
shared "DSA_Blind 75/notebooks/bench_utils.py". The notebook's bootstrap cell
was NOT simplified - it still walks up from os.getcwd() looking for
bench_utils.py exactly as the skill specifies, so the same bootstrap code
would work unmodified in the real repo location. It happens to find
bench_utils.py immediately in this test because the two files are colocated
in the same outputs/ folder.
