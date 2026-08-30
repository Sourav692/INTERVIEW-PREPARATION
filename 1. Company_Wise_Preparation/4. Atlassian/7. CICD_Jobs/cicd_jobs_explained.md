# CI/CD Jobs — Explained Simply

## The Problem

Given job time intervals, find where **2 or more** jobs overlap.

```
intervals = [(2, 7), (4, 8), (15, 20)]
# Job A runs [2,7), Job B runs [4,8) -- they overlap on [4,7)
# Job C runs [15,20) -- alone, no overlap
```

Expected: `[(4, 7)]`

## Why the Obvious Way Is Slow

The obvious approach: check every unit of time from the earliest start to the latest end, and count how many intervals cover it.

```
for t in range(earliest, latest):
    count how many intervals contain t
```

This is O(n · range) — if timestamps span millions of units (or the intervals are given in fine-grained time like milliseconds), this crawls through huge stretches of time where nothing changes at all, just to notice the overlap count is still the same as the previous instant.

## The Simple Trick: The Overlap Count Only Changes at a Start or an End

Between a job starting and the next job starting or ending, the number of active jobs is **constant** — there's no reason to check anything in between. So instead of walking every instant, just walk the handful of moments where something actually happens: every job's start, and every job's end.

## An Analogy First: Counting People in a Room by the Door, Not the Clock

Imagine you want to know, at every moment during the day, how many people are inside a room. You could stand there checking the room every second — mostly you'd see "still 3 people, still 3 people, still 3 people" over and over, wasting effort.

Instead, just watch the **door**. Every time someone walks in, add 1 to your count. Every time someone walks out, subtract 1. The count only ever changes at a doorway event — checking anything between two doorway events is pointless, because nothing changed.

## Step-by-Step Example (Narrated)

`intervals = [(2, 7), (4, 8), (15, 20)]`

### Step 1 — turn every interval into two "doorway" events

- `(2, 7)` → `(2, +1)` and `(7, -1)`
- `(4, 8)` → `(4, +1)` and `(8, -1)`
- `(15, 20)` → `(15, +1)` and `(20, -1)`

All events: `(2,+1), (7,-1), (4,+1), (8,-1), (15,+1), (20,-1)`

### Step 2 — sort them by time

`(2,+1), (4,+1), (7,-1), (8,-1), (15,+1), (20,-1)`

(Since no two events land at the exact same timestamp here, we don't need to worry about tie-breaking yet — that's covered in the next section.)

### Step 3 — sweep through, tracking the active count

**At t=2, event +1:** active goes from 0 to 1. Was it below 2 and now still below 2? Yes (1 < 2) — no overlap segment starts.

**At t=4, event +1:** active goes from 1 to 2. It just **crossed up to 2** — an overlap segment starts here. Remember `overlap_start = 4`.

**At t=7, event -1:** active goes from 2 to 1. It just **crossed back below 2** — the overlap segment ends here. Record the segment `(overlap_start, 7) = (4, 7)`.

**At t=8, event -1:** active goes from 1 to 0. Still below 2, nothing to report.

**At t=15, event +1:** active goes from 0 to 1. Still below 2.

**At t=20, event -1:** active goes from 1 to 0. Nothing to report.

---

Only one segment was ever recorded: **`[(4, 7)]`** — matches the expected output exactly.

### The one detail that's easy to miss: what happens when two events land at the same instant?

If a job ends at time `t` and a *different* job starts at exactly `t`, do they "overlap" at that instant? This problem's own rule says yes — `(2,5)` and `(5,6)` are considered overlapping. To make that happen, when sorting events with the same timestamp, process the `+1` (start) **before** the `-1` (end) — that way both jobs are briefly counted as active together at `t`, for one instant, before the ending job leaves.

## Plain-English Walkthrough

1. Turn every `(start, end)` interval into two events: `(start, +1)` and `(end, -1)`.
2. Sort all events by time (processing `+1` before `-1` at the same timestamp, so touching intervals count as overlapping).
3. Sweep through the sorted events, keeping a running `active` counter.
4. The instant `active` crosses from below 2 up to 2 or more, remember that time as the start of an overlap segment.
5. The instant `active` drops back below 2, close the segment using the current time as its end.

## Simple Python Code

```python
def intervals_with_two_or_more_jobs(intervals):
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda e: (e[0], -e[1]))   # +1 before -1 at the same timestamp

    result = []
    active = 0
    overlap_start = None
    for time, delta in events:
        if active >= 2 and active + delta < 2:
            result.append((overlap_start, time))
            overlap_start = None
        elif active < 2 and active + delta >= 2:
            overlap_start = time
        active += delta
    return result

print(intervals_with_two_or_more_jobs([(2, 7), (4, 8), (15, 20)]))  # [(4, 7)]
```

## Why Sort by `(time, -delta)` Instead of Just `time`?

If two events share a timestamp, Python's sort needs a tie-break rule or the order is arbitrary. `-delta` puts `+1` (which becomes `-1` when negated) before `-1` (which becomes `+1` when negated) — because `-1 < 1`. That's exactly what forces starts to be processed before ends at the same instant, which is what makes touching intervals count as overlapping, matching this problem's stated rule.

## Complexity

- **Time:** O(n log n) — sorting the `2n` events dominates; the sweep itself is O(n).
- **Space:** O(n) — the events list and the output.

## The Reusable Pattern

This is the **"event / sweep-line"** pattern — any "how many things are active at once" question over intervals reduces to this:
- Meeting Rooms II (minimum rooms needed = the maximum overlap this same sweep finds)
- Car Pooling (capacity-threshold overlap — same idea, generalized threshold)
- Busiest time-of-day analysis (see *Tennis Club* for a resource-assignment variant of this idea)

Core idea: convert intervals into `+1`/`-1` point-events, sort them, and sweep — the active count only ever changes at those events, so there's no reason to examine anything in between.
