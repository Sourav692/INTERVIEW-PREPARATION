# Ballot Processing — Explained Simply

## The Problem

Each ballot ranks up to 3 candidates: 1st choice = 3 points, 2nd = 2, 3rd = 1. Rank all candidates by total points, descending. On a tie, use the **"first to reach the winning score"** rule: whoever's running total hit their own final score earliest (by ballot number) wins the tie.

```
ballots = [["A", "B"], ["B", "A"], ["C"]]
# A: 3 (ballot 0) + 2 (ballot 1) = 5
# B: 2 (ballot 0) + 3 (ballot 1) = 5
# C: 3 (ballot 2) = 3
```

A and B are tied at 5 points — we need to know *when* each of them first reached 5, not just that they both got there eventually.

## Why the Obvious Way Is Slow (Actually — Why It Gives the Wrong Answer)

The obvious first attempt: track each candidate's points, and remember the ballot index the **first time you see their name** at all.

```
first_seen = {}
for i, ballot in enumerate(ballots):
    for candidate in ballot:
        if candidate not in first_seen:
            first_seen[candidate] = i
```

This is wrong, not just slow. "First appearance" and "first time you reached your *final* score" are completely different things. A candidate could appear early with just 1 point, then slowly climb to 5 points over many later ballots — while another candidate jumps straight to 5 points on their very first appearance. The first candidate would incorrectly look like they "won" the tiebreak just because their *name* showed up first, even though they didn't actually *reach 5* until much later.

## The Simple Trick: You Can't Know "First to Reach the Final Score" Until You Know the Final Score

This is the whole puzzle in one sentence: you need to know each candidate's **final** total before you can meaningfully ask "when did their running total first equal that." So — don't try to do it in one pass. Do it in two: first tally everyone's final score, *then* go back through the ballots a second time and watch for the moment each candidate's running total actually matches their now-known final score.

## An Analogy First: Grading a Race You Only Have Video Of

Imagine you have a video of several racers running around a track, and you want to know who reached **their own final resting position** first — not who's fastest, but literally: at what timestamp did each racer arrive at the exact spot where the video ends showing them?

You can't answer that by watching the video just once, in order — you don't know where anyone ends up until the video is over! So you watch it once all the way through just to note everyone's *final* position. Only then do you rewind and watch it a **second time**, now specifically checking: "at what timestamp does Racer A first appear at position X (their known final spot)?" That's the moment you record.

## Step-by-Step Example (Narrated)

`ballots = [["A", "B"], ["B", "A"], ["C"]]`

### Pass 1 — tally final scores (one pass, left to right)

**Ballot 0, `["A", "B"]`:** A is 1st choice → +3. B is 2nd choice → +2.
Running totals so far: `A=3, B=2`.

**Ballot 1, `["B", "A"]`:** B is 1st choice → +3. A is 2nd choice → +2.
Running totals so far: `A=5, B=5`.

**Ballot 2, `["C"]`:** C is 1st choice → +3.
Running totals so far: `A=5, B=5, C=3`.

Pass 1 is done. **Final scores: `A=5, B=5, C=3`.**

### Pass 2 — replay, watching for "running total == final total"

Now that we know the targets (A needs to reach 5, B needs to reach 5, C needs to reach 3), we replay the *same* ballots from scratch with a **new** running total, checking after every vote.

**Ballot 0, `["A", "B"]`:** A's running total becomes 3. Is that A's final score (5)? No. B's running total becomes 2. Is that B's final score (5)? No. Nobody recorded yet.

**Ballot 1, `["B", "A"]`:** B's running total becomes 3+2=5. Is that B's final score (5)? **Yes!** → `first_reached[B] = 1`. A's running total becomes 3+2=5. Is that A's final score (5)? **Yes!** → `first_reached[A] = 1`.

**Ballot 2, `["C"]`:** C's running total becomes 3. Is that C's final score (3)? **Yes!** → `first_reached[C] = 2`.

Result: `first_reached = {A: 1, B: 1, C: 2}`.

### Final sort: `(-points, first_reached, name)`

- A → `(-5, 1, "A")`
- B → `(-5, 1, "B")`
- C → `(-3, 2, "C")`

A and B tie on both points *and* first-reached-ballot (both hit 5 on ballot 1 — a genuine simultaneous tie in this example) — the name field breaks it alphabetically: **A before B**. Final order: **`[A, B, C]`**.

### The one detail that's easy to miss: "first to reach" checks the *running* total against the *final* total, at every single vote — not just once at the end

If a candidate's running total happened to pass through their final number early, then went higher, and only came back down to that number later, only the **first** time it equals the final value counts — later matches are ignored (`and candidate not in first_reached` in the code guards this).

## Plain-English Walkthrough

1. **Pass 1:** walk every ballot once, adding `3 - position` points to each candidate. This gives you everyone's final score.
2. **Pass 2:** walk the ballots again from a fresh running total. After adding each vote, check: does this candidate's running total now equal their (now-known) final score, and have we not already recorded them? If so, record this ballot's index as their "first reached" moment.
3. Sort candidates by `(-final_score, first_reached_index, name)` — highest score first, earliest-reached breaks ties, name breaks any remaining tie.

## Simple Python Code

```python
def process_ballots(ballots):
    # Pass 1: final scores
    points = {}
    for ballot in ballots:
        for pos, candidate in enumerate(ballot):
            points[candidate] = points.get(candidate, 0) + (3 - pos)

    # Pass 2: first ballot where the running total hits the final score
    first_reached = {}
    running = {c: 0 for c in points}
    for i, ballot in enumerate(ballots):
        for pos, candidate in enumerate(ballot):
            running[candidate] += 3 - pos
            if running[candidate] == points[candidate] and candidate not in first_reached:
                first_reached[candidate] = i

    return sorted(points.keys(), key=lambda c: (-points[c], first_reached[c], c))

ballots = [["A", "B"], ["B", "A"], ["C"]]
print(process_ballots(ballots))   # ['A', 'B', 'C']
```

## Why Not Just Use Whatever Order `dict` Happens to Give You?

Relying on "whatever order candidates were first inserted into the dict" isn't a *rule* — it's an accident of iteration order that has nothing to do with the actual tiebreak the problem asked for. Two people implementing "the obvious thing" differently could get different, both-defensible-looking answers. Making the tiebreak explicit (first-reached, then name) means the output is deterministic and testable, no matter how the code happens to be written.

## Complexity

- **Time:** O(V) for each pass (V = total votes across all ballots), plus O(m log m) to sort m candidates.
- **Space:** O(m) for the points, running-total, and first-reached dictionaries.

## The Reusable Pattern

This is the **"two-pass, because the end determines the middle"** pattern:
- Any "first index where a running value matches a target only known at the end" question
- Computing percentile ranks (need the full distribution before you can rank any single value)
- Normalizing data against a total that isn't known until you've seen everything (e.g. "each item's share of the grand total")

Core idea: if answering a question about *when* something happened requires knowing a fact that's only available *after* everything has happened, don't fight it — compute the fact first (pass 1), then go find the moment it became true (pass 2).
