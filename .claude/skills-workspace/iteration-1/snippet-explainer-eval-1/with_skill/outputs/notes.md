Skill under test: dsa-snippet-explainer

Setup
- Copied (not moved) the original notebook:
  5. Data_Structure and Algorithms\DSA_Deep_Dive\12_Heaps_Priority_Queues\12_heaps_priority_queues.ipynb
  to:
  .claude\skills-workspace\iteration-1\snippet-explainer-eval-1\with_skill\outputs\12_heaps_priority_queues_copy.ipynb
- All edits below were made ONLY on the copy.

Cell targeted
- Considered cell `c40e6003` (the hand-rolled `push`/`pop` demo in section 1, with h = [] built from
  [5, 1, 8, 3, 9, 2, 7], prints, and asserts) as the most literal "heap push/pop" cell, but it already
  has a non-empty explanation cell right after it (`c286ac56`) written in an ASCII-diagram narrative
  style, not the required Step | Action | state table format. Per SKILL.md ("Do not overwrite a
  non-empty explanation without asking"), I did not touch or replace that existing cell.
- Instead targeted cell `f754799f` in section 3 ("Python's heapq (min-heap) and the max-heap trick"),
  which had no existing explanation cell after it. It demonstrates heap push/pop operations three ways
  using Python's heapq, with demo data, prints, and an assert:
    1. h = [] built from [5, 1, 3] -> heapq.heappush/heappop (plain min-heap)
    2. pq = [] with heapq.heappush of (2, "task-B") then (1, "task-A") -> heappop (tuple-keyed priority
       queue)
    3. mx = [] built from negated [5, 1, 3] -> heappop then negate back (max-heap-via-negation trick),
       with assert largest == 5
- Inserted one new markdown cell (id 05a9c81e) immediately after cell f754799f, following the
  Combination Sum walkthrough format from SKILL.md/TEMPLATE.md: a `### Step-by-step` opening, one
  `####` subsection per traced block (h, pq, mx) each with a short numbered algorithm list, the exact
  demo line, and a full markdown table (Step | Action | `<heap>` after) tracing every push/pop against
  the real index/sift-up/sift-down mechanics, tied out to the notebook's printed output and
  `assert largest == 5`, plus a closing `#### Mental model` section.

Verification
- Original file at 5. Data_Structure and Algorithms\DSA_Deep_Dive\12_Heaps_Priority_Queues\
  12_heaps_priority_queues.ipynb still has 13 cells and shows no changes in `git status`/`git diff`
  (clean — confirmed via `git status --porcelain` on that exact path).
- The copy under .claude\skills-workspace\...\outputs\ now has 14 cells (13 original + 1 inserted
  markdown explanation).
- No other files in the repository were modified.
