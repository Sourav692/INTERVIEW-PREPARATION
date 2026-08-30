# CI/CD Jobs

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Arrays, Sorting · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

**Job Timeframe Processing**

### Problem 1 — Merge Overlapping Intervals

Given a list of timeframes (start, end) representing jobs in a CI/CD platform, return the list of times where one or more jobs occur. If intervals overlap, merge them.

Example:

```
[(2, 7), (4, 8), (15, 20)]
```

should return:

```
[(2, 8), (15, 20)]
```

Note: Intervals like (2,5) and (5,6) count as overlapping.

### Problem 2 — Intervals With ≥2 Jobs Running

Return only the time intervals where two or more jobs are occurring at the same time.

Example:

```
[(2, 7), (4, 8), (15, 20)]
```

should return:

```
[(4, 7)]
```

because two jobs overlap in that range.

### Problem 3 — Busiest Interval

Return the single interval where the maximum number of jobs overlap.

Example:

```
[(2, 7), (4, 8), (15, 20)]
```

returns:

```
(4, 7)
```

because this is the period where the most jobs (2) occur simultaneously.

---

## Study Tools

### Hint 1

Think about sorting the events first. Each start adds a job, each end removes one — the state changes only at these points.

### Hint 2

For Problem 2, track how many jobs are active as you sweep through sorted events. An overlap interval starts when the count rises to 2 and ends when it drops below 2.

### Hint 3

For Problem 3, sweep through events and track the maximum active count. The busiest interval is the longest stretch where the active count equals that maximum.

---

### Answer

This is a classic interval sweep problem. Sort all start and end events by time, then process them in order while maintaining the number of active jobs.

#### Problem 1 — Merge Overlapping Intervals

Sort intervals by start time. Iterate through them, merging the current interval with the last merged interval if they overlap (i.e., `current.start <= last.end`).

```python
def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [list(intervals[0])]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [tuple(x) for x in merged]
```

**Time:** O(n log n) — sorting dominates; merging is O(n). **Space:** O(n) — for the output list.

**Correctness:** By induction, after processing the first k intervals, `merged` contains the merged representation of those intervals. When adding interval k+1, it either overlaps with the last merged interval (in which case we extend it) or it starts after it (in which case we start a new merged interval). Since intervals are sorted by start, no interval can overlap with an earlier merged interval without also overlapping the last one.

#### Problem 2 — Intervals With ≥2 Jobs Running

Create events: `(time, +1)` for each start, `(time, -1)` for each end. Sort by time; for ties, process `+1` before `-1` so that intervals like (2,5) and (5,6) correctly produce an overlap. Sweep through events, tracking the active count. When the count rises to 2, record the start of an overlap; when it drops below 2, record the end.

```python
def intervals_with_two_or_more_jobs(intervals):
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda x: (x[0], -x[1]))  # +1 before -1 at same time

    result = []
    active = 0
    overlap_start = None

    for time, delta in events:
        if active >= 2 and active + delta < 2:
            # Overlap ends here
            result.append((overlap_start, time))
            overlap_start = None
        elif active < 2 and active + delta >= 2:
            # Overlap starts here
            overlap_start = time
        active += delta

    return result
```

**Time:** O(n log n) — sorting 2n events. **Space:** O(n) — for the events list and output.

**Correctness:** The active count changes only at event times. An overlap interval starts when the count transitions from below 2 to at least 2, and ends when it transitions from at least 2 to below 2. Processing `+1` before `-1` at the same timestamp ensures that a job ending at time t and another starting at t are considered overlapping at that instant, matching the problem's definition.

#### Problem 3 — Busiest Interval

Same sweep as Problem 2, but track the maximum active count and the interval(s) where that maximum occurs. When the active count reaches a new maximum, start a new interval; when it drops below the maximum, close the current interval. If there are multiple intervals with the same maximum count, return the longest one.

```python
def busiest_interval(intervals):
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda x: (x[0], -x[1]))  # +1 before -1 at same time

    active = 0
    max_active = 0
    best_start = None
    best_end = None
    best_length = -1
    current_start = None

    for time, delta in events:
        if delta == 1:
            active += 1
            if active > max_active:
                max_active = active
                current_start = time
                best_start = time
                best_end = None
                best_length = -1
            elif active == max_active:
                current_start = time
        else:
            if active == max_active:
                # Close the current max interval
                length = time - current_start
                if length > best_length:
                    best_length = length
                    best_start = current_start
                    best_end = time
            active -= 1

    # If the maximum extends to the very end
    if best_end is None and best_start is not None:
        best_end = events[-1][0]

    return (best_start, best_end)
```

**Time:** O(n log n) — sorting 2n events. **Space:** O(n) — for the events list.

**Correctness:** The sweep processes events in chronological order. The active count after processing all events at time t equals the number of jobs running at t. When the count reaches a new maximum, we begin tracking a candidate interval; when it drops from the maximum, we close the current candidate. By tracking the longest interval at the maximum count, we return the single busiest interval.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: for each unit of time, count how many jobs are active. That's O(n·m) where m is the time range, which is terrible for large timestamps. The key insight is that the active count only changes at start and end times.

For Problem 1, sort by start time and merge greedily. The sorted order means we only need to compare each interval with the last merged one — if `start <= last_end`, they overlap. This is O(n log n) for the sort plus O(n) for the merge.

For Problems 2 and 3, switch to an event-based sweep. Convert each interval into two events: `(start, +1)` and `(end, -1)`. Sort events by time. The tricky part is handling ties at the same timestamp — you want to process starts before ends so that a job ending at t and another starting at t count as overlapping. This means sorting by `(time, -delta)` so `+1` comes before `-1`.

For Problem 2, track when the active count crosses the threshold of 2. The overlap starts when active goes from 1 to 2, and ends when it goes from 2 to 1. For Problem 3, you do the same sweep but track the maximum active count and the interval(s) where that maximum is achieved. If multiple intervals tie for the maximum, pick the longest one.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Sort by `(time, -delta)` to handle ties correctly** — this ensures that a job ending at t and another starting at t are considered overlapping, which matches the problem's explicit note about intervals like (2,5) and (5,6).
- **Use an event sweep rather than checking every time unit** — the active count only changes at start and end times, so sweeping events is O(n log n) instead of O(n·m) where m is the time range, which can be enormous.
- **Track the transition points, not just the counts** — for Problem 2, the overlap starts when active crosses from 1 to 2 and ends when it crosses from 2 to 1. Stating this invariant makes the code much cleaner and easier to verify.
- **Handle the tie-breaking for Problem 3 explicitly** — if multiple intervals have the same maximum active count, you need to decide which one to return. The problem says "single interval," so picking the longest one is a reasonable interpretation; say this out loud.
- **Walk through the example [(2,5), (5,6)] for Problem 2** — with start-before-end tie-breaking, the events are (2,+1), (5,+1), (5,-1), (6,-1), producing the overlap (5,5). This demonstrates you understand the edge case.
- **Consider the empty input case** — returning an empty list for Problems 1 and 2, and `None` or an empty tuple for Problem 3, shows you've thought about boundary conditions.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if intervals are given as `(start, duration)` instead of `(start, end)`?** — Convert to `(start, start + duration)` first, then apply the same logic.
- **How would you handle streaming intervals that arrive over time?** — Maintain a min-heap of end times and process each new interval as it arrives.
- **What if you need to return all intervals where exactly k jobs overlap, for arbitrary k?** — Generalize the threshold logic from Problem 2 to track crossings of k.
- **Can you solve Problem 1 in-place with O(1) extra space?** — Sort in place and merge using a read/write pointer.
- **How would you handle intervals with open endpoints, like (2, 5) vs [2, 5]?** — Adjust the tie-breaking and overlap condition to account for inclusivity.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
