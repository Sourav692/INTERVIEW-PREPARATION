# Ballot Processing

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Arrays, Hash Tables, Sorting · **Difficulty/Frequency:** Common (6/10)

---

## Problem Statement

**Process Ballots and Rank Candidates**

Process a list of ballots and return all candidates sorted in descending order by their total number of points.

### Rules

- Each ballot contains up to 3 different candidates.
- The order of votes matters:
  - 1st vote → 3 points
  - 2nd vote → 2 points
  - 3rd vote → 1 point
- The function should return a list of candidate names, sorted by total points (descending).
- Candidate names are extracted dynamically from ballots as they are processed.

### Follow-Up: Handling Ties

If two or more candidates end up with the same number of points, apply one of the following strategies (based on input selection):

**1st Strategy — First to Reach the Winning Point**

If candidates A and B have equal points, the winner is the one who reached that total first during ballot processing.

**2nd Strategy — Positional Vote Comparison**

Compare candidates by the number of votes received at each position: first compare votes at index 0 (3-point votes); if still tied, compare votes at index 1 (2-point votes); if still tied, compare votes at index 2 (1-point votes).

---

## Study Tools

### Hint 1

You need to track both point totals and how candidates reach them. A dictionary mapping candidate names to their scores lets you tally in a single pass, but for tiebreaking you'll need to record additional state about their scoring pattern.

### Hint 2

For the 'first-to-reach' strategy, track the ballot index where each candidate hits their final score — not just when they first appear. You'll need to know their final total before you can record when they reach it, so a two-pass or delayed-update approach works: tally everything first, then walk through ballots again to find the earliest ballot where each candidate's cumulative score equals their final score.

### Hint 3

In a two-pass solution: first pass tallies all points and builds the final score for each candidate; second pass replays the ballots and records the ballot index at which each candidate's running total hits their final score. For positional tiebreaking, count votes per position during the first pass. Then sort by points (descending), breaking ties according to your chosen strategy.

---

### Answer

Process ballots in two passes: first tally all points and count votes per position, then replay the ballots to record the earliest ballot index at which each candidate reached their final score. Sort by points (descending), then break ties either by first-to-reach index or by positional vote counts, depending on the strategy.

```python
from typing import List

def process_ballots(ballots: List[List[str]], tie_strategy: str = "first") -> List[str]:
    """
    ballots: list of ballots, each ballot is a list of up to 3 candidate names
             in order of preference (index 0 = 1st vote, 3 pts; index 1
             = 2 pts; index 2 = 1 pt)
    tie_strategy: "first" for first-to-reach-winning-point,
                  "positional" for positional vote comparison
    """
    if not ballots:
        return []

    # Pass 1: Tally all points and count votes per position
    points = {}       # candidate -> total points
    positional = {}   # candidate -> [count_at_0, count_at_1, count_at_2]

    for ballot in ballots:
        for pos, candidate in enumerate(ballot):
            if candidate not in points:
                points[candidate] = 0
                positional[candidate] = [0, 0, 0]

            # Award points: pos 0 -> 3, pos 1 -> 2, pos 2 -> 1
            vote_value = 3 - pos
            points[candidate] += vote_value
            positional[candidate][pos] += 1

    # Pass 2: For "first" strategy, find earliest ballot where each candidate reaches final score
    first_reached = {}  # candidate -> ballot index

    if tie_strategy == "first":
        running_points = {c: 0 for c in points}
        for ballot_idx, ballot in enumerate(ballots):
            for pos, candidate in enumerate(ballot):
                vote_value = 3 - pos
                running_points[candidate] += vote_value
                # Record the ballot index where candidate reaches their final score
                if running_points[candidate] == points[candidate] and candidate not in first_reached:
                    first_reached[candidate] = ballot_idx

    # Sort based on strategy
    if tie_strategy == "positional":
        sorted_candidates = sorted(
            points.keys(),
            key=lambda c: (
                -points[c],
                -positional[c][0],
                -positional[c][1],
                -positional[c][2],
                c,
            ),
        )
    else:  # "first"
        sorted_candidates = sorted(
            points.keys(),
            key=lambda c: (-points[c], first_reached[c], c),
        )

    return sorted_candidates
```

**Time:** O(n + m log m) where n is the total number of votes across all ballots and m is the number of distinct candidates. Two passes over n votes to tally and replay, then O(m log m) to sort.

**Space:** O(m) — one dict per candidate for `points`, `positional`, and `first_reached` (or subset thereof).

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start by thinking about what you need to output: candidates sorted by points (descending), with ties broken by either first-to-reach or positional vote counts. The naive approach — build the score dict, then sort — works for the basic case but misses the tiebreaker information.

For total points, a single pass is enough: iterate through ballots, and for each vote at position `pos`, add `3 - pos` points to that candidate's total. After one pass you have `points[c]` for every candidate. Sorting by points descending is O(m log m) and that's unavoidable.

But now consider tiebreaking. The 'positional' strategy is straightforward: during the same pass, count how many votes each candidate received at each position (index 0, 1, 2). Store this in `positional[c] = [count_0, count_1, count_2]`. Then the sort key is `(-points[c], -positional[c][0], -positional[c][1], -positional[c][2], c)`. That works in one pass.

The 'first' strategy is trickier. You need to know the ballot index at which each candidate first reached their final score. The catch: you don't know the final score until you've seen all ballots. So you need two passes. After pass 1 (tallying), you have `points[c]` for each candidate. In pass 2, replay the ballots and track running totals. When a candidate's running total equals their final total for the first time, record that ballot index in `first_reached[c]`. Now sort by `(-points[c], first_reached[c], c)`, and the candidate who hit their final score first wins the tiebreak.

Why does this work? Consider two candidates A and B both ending with 5 points. A reaches 5 on ballot 3, B on ballot 7. In pass 2, when we process ballot 3, A's running total jumps to 5 (their final score) and we set `first_reached[A] = 3`. When we process ballot 7, B's running total hits 5 and we set `first_reached[B] = 7`. The sort key `(-points, first_reached)` then favors A because `first_reached[A] < first_reached[B]`. The candidate name `c` is a final deterministic tiebreaker in case two candidates somehow have the same points and the same first-reached index (possible if they both first appear on the same ballot and never score again, but alphabetical order stabilizes the output).

Handle the empty case naturally: if `ballots` is empty, both dicts stay empty, `sorted([])` returns `[]`, and you're done.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Two-pass solution for first-to-reach** — you can't know when a candidate reaches their final score until you know their final score. A single pass won't work; you need to tally first, then replay to record the earliest ballot where each candidate's running total hits their final value.
- **Replay logic correctness** — in pass 2, check `if running_points[candidate] == points[candidate] and candidate not in first_reached`, so you record only the first ballot where the candidate reaches their final total, never overwriting it.
- **Vote value calculation** — use `3 - pos` to map position 0 to 3 points, position 1 to 2, position 2 to 1. This is cleaner and less error-prone than separate `if pos == 0` branches.
- **Sort key order and signs** — negate `points[c]` to sort descending; negate all positional counts to prefer higher counts; leave the candidate name positive for ascending alphabetical tiebreak. Tuple sort in Python applies comparisons left-to-right, so the order of fields in the key matters.
- **Why not track first_reached on first update** — if you only record the ballot index when a candidate first appears (not when they reach their final score), tiebreaks fail. For example, candidate A could appear early with 1 point, then accumulate to 5 points later; candidate B might jump directly to 5 points on their first appearance. Without replaying, you'd incorrectly favor A.
- **Deterministic output with name tiebreak** — if two candidates somehow tie on both points and first-reached index, the name tiebreak ensures reproducible output and makes testing easier. Always add a final tiebreaker to avoid nondeterminism.
- **Handling edge cases** — empty ballots list returns an empty list naturally; candidates only in the dicts if they appear on at least one ballot (correct, since candidates are extracted dynamically); the code assumes each ballot contains distinct candidates, as the problem states.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if ballots can contain more than 3 candidates?** — Generalize the point value to `len(ballot) - pos` or parameterize a list of weights, and extend `positional` to a list of length `len(ballot)` per candidate.
- **What if you need to return just the top k candidates?** — After building the sort key, take only the first k elements: `return sorted_candidates[:k]`.
- **What if ballots arrive as a stream and you need to output the ranking after each new ballot, without reprocessing all previous ones?** — Maintain `points` and `positional` incrementally, but for "first" strategy you'd need to either re-run pass 2 each time (simpler but slower) or use a smarter data structure like a balanced BST keyed by `(-points, first_reached)` to insert/update in O(log m).
- **What if a candidate's name is unknown until ballots are processed, but you later learn aliases (e.g., "Bob" and "Robert" are the same person)?** — Build a union-find or name-to-canonical-name map, then merge their score dicts after tallying.
- **What if you want to handle invalid ballots (e.g., duplicate candidates within a ballot) gracefully?** — Pre-process each ballot to deduplicate, or track seen candidates per ballot and skip duplicates.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
