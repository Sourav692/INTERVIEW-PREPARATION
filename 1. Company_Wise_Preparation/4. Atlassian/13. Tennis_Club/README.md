# Tennis Club

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Greedy, Heaps, Sorting · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

### Part 1

Task: Implement a function that, given a list of tennis court bookings with start and finish times, returns a plan assigning each booking to a specific court.

- Ensure each court is used by only one booking at a time.
- Use the minimum number of courts.
- Assume an unlimited number of courts available.

**Booking Record Example:**

```python
class BookingRecord:
    Id: int  # ID of the booking
    Start_time: int
    Finish_time: int
```

**Function Signature:**

```python
def assignCourts(bookingRecords: List[BookingRecord]) -> List:
    pass
```

### Part 2

After each booking, a fixed amount of time X is needed to maintain the court before it can be rented again.

### Part 3

A court only needs maintenance after X amount of usage, rather than after every booking.

---

## Study Tools

### Hint 1

Think of this as a scheduling problem where you can process bookings in chronological order. If you sort by start time, you can figure out when a court becomes free again.

### Hint 2

Use a min-heap to track the finish times of courts currently in use. When a new booking starts, you can check if the earliest-finishing court is free.

### Hint 3

For Part 2, just add X to the finish time before putting it in the heap. For Part 3, track usage count per court and only add X when that count reaches the threshold.

---

### Answer

This is a classic interval partitioning problem that maps directly to finding the maximum overlap of intervals. The minimum number of courts equals the maximum number of bookings happening simultaneously, and a greedy assignment using a min-heap achieves this optimal bound.

#### Part 1: Basic Court Assignment

The key insight: sort bookings by start time, then greedily assign each booking to the court that frees up earliest. If no court is free, open a new one.

```python
import heapq
from typing import List

class BookingRecord:
    def __init__(self, id: int, start_time: int, finish_time: int):
        self.Id = id
        self.Start_time = start_time
        self.Finish_time = finish_time

def assignCourts(bookingRecords: List[BookingRecord]) -> List:
    # Sort bookings by start time
    bookings = sorted(bookingRecords, key=lambda b: b.Start_time)

    # Min-heap of (finish_time, court_id)
    heap = []
    court_assignments = []  # List of (booking_id, court_id)
    next_court_id = 0

    for booking in bookings:
        if heap and heap[0][0] <= booking.Start_time:
            # Earliest-finishing court is free
            finish_time, court_id = heapq.heappop(heap)
            heapq.heappush(heap, (booking.Finish_time, court_id))
            court_assignments.append((booking.Id, court_id))
        else:
            # Need a new court
            court_id = next_court_id
            next_court_id += 1
            heapq.heappush(heap, (booking.Finish_time, court_id))
            court_assignments.append((booking.Id, court_id))

    return court_assignments
```

**Time:** O(n log n) — sorting takes O(n log n), and each heap operation is O(log n) with n bookings total.

**Space:** O(n) — the heap can grow to size n in the worst case, and we store n assignments.

**Correctness:** The greedy approach works because sorting by start time ensures we never miss an opportunity to reuse a court. When we process booking i, any court with `finish_time <= start_time_i` is available. Choosing the earliest-finishing court maximizes the remaining availability of other courts for future bookings. This is an exchange argument: any optimal solution can be transformed into our greedy solution without increasing the number of courts.

#### Part 2: Maintenance After Every Booking

Add a fixed maintenance time X after each booking. A court isn't free until `finish_time + X`.

```python
def assignCourtsWithMaintenance(bookingRecords: List[BookingRecord], X: int) -> List:
    bookings = sorted(bookingRecords, key=lambda b: b.Start_time)

    heap = []  # (available_time, court_id)
    court_assignments = []
    next_court_id = 0

    for booking in bookings:
        if heap and heap[0][0] <= booking.Start_time:
            available_time, court_id = heapq.heappop(heap)
            heapq.heappush(heap, (booking.Finish_time + X, court_id))
            court_assignments.append((booking.Id, court_id))
        else:
            court_id = next_court_id
            next_court_id += 1
            heapq.heappush(heap, (booking.Finish_time + X, court_id))
            court_assignments.append((booking.Id, court_id))

    return court_assignments
```

**Time:** O(n log n) — same as Part 1.

**Space:** O(n) — same as Part 1.

#### Part 3: Maintenance After Threshold Usage

Maintenance is needed only after K bookings on the same court. Track usage count per court and only add X when the count reaches K.

```python
def assignCourtsWithThresholdMaintenance(bookingRecords: List[BookingRecord], X: int, K: int) -> List:
    bookings = sorted(bookingRecords, key=lambda b: b.Start_time)

    heap = []  # (available_time, court_id)
    court_usage = {}  # court_id -> number of bookings since last maintenance
    court_assignments = []
    next_court_id = 0

    for booking in bookings:
        if heap and heap[0][0] <= booking.Start_time:
            available_time, court_id = heapq.heappop(heap)

            # Increment usage count
            court_usage[court_id] = court_usage.get(court_id, 0) + 1

            # Check if maintenance is needed
            if court_usage[court_id] >= K:
                available_time = booking.Finish_time + X
                court_usage[court_id] = 0  # Reset after maintenance
            else:
                available_time = booking.Finish_time

            heapq.heappush(heap, (available_time, court_id))
            court_assignments.append((booking.Id, court_id))
        else:
            court_id = next_court_id
            next_court_id += 1
            court_usage[court_id] = 1

            if court_usage[court_id] >= K:
                available_time = booking.Finish_time + X
                court_usage[court_id] = 0
            else:
                available_time = booking.Finish_time

            heapq.heappush(heap, (available_time, court_id))
            court_assignments.append((booking.Id, court_id))

    return court_assignments
```

**Time:** O(n log n) — same heap operations, plus O(1) dictionary lookups.

**Space:** O(n) — heap and usage dictionary both bounded by n.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: try every possible assignment of bookings to courts and check if it's valid. That's exponential — O(c^n) where c is the number of courts and n is the number of bookings. Clearly unusable for any realistic input.

Next, think about what determines the minimum number of courts. If you draw the intervals on a timeline, the answer jumps out: the maximum number of overlapping intervals at any point in time. You can compute this by sorting all events (starts and finishes) and sweeping through, but that only gives you the count, not the actual assignment.

For the assignment, sort by start time and process bookings in order. When a booking starts, you need a court that's free. The greedy choice is to pick the court that frees up earliest — this preserves later-finishing courts for future bookings. A min-heap gives you O(log n) access to the earliest finish time.

The heap stores `(finish_time, court_id)` pairs. When a new booking arrives, peek at the heap root. If `finish_time <= start_time`, pop it and reuse that court with the new finish time. Otherwise, allocate a new court. This runs in O(n log n) and is provably optimal.

For Part 2, the only change is what you push onto the heap: `finish_time + X` instead of `finish_time`. The court isn't available until maintenance completes.

For Part 3, you need per-court state. A dictionary mapping `court_id` to usage count works. When a court reaches K uses, add X to the finish time and reset the counter. The heap still works the same way — you just compute the availability time differently based on whether maintenance is triggered.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the interval partitioning connection immediately** — naming the problem as maximum overlap shows you recognize the pattern, and you can prove the lower bound by noting that any point with k overlapping intervals requires at least k courts.
- **Walk through the greedy exchange argument** — when you pick the earliest-finishing court, you can always swap it with whatever court an optimal solution uses without increasing the court count. This proves optimality in under a minute.
- **Handle the heap comparison carefully** — the condition is `heap[0][0] <= booking.Start_time`, where `<=` allows back-to-back bookings on the same court. If you write `<` instead, you'll open unnecessary extra courts.
- **Return the assignment, not just the count** — the problem asks for a plan mapping bookings to courts, so your return value should be pairs of `(booking_id, court_id)`. You can derive the count from the assignment, but not vice versa.
- **Discuss the X and K parameters as part of the state** — for Part 3, the usage count resets after maintenance, which means the same court can have different availability times depending on its history. Your heap entries must reflect this computed availability, not just the raw finish time.
- **Mention the lower bound proof** — the minimum number of courts equals the maximum overlap, and your greedy algorithm achieves exactly this bound. You can compute the overlap with a sweep line in O(n log n) as a sanity check.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if bookings have different priorities, and higher-priority bookings must be assigned to courts with better amenities?** — Think about sorting by priority within each time slot.
- **How would you handle cancellations? A booking might be removed after the initial assignment.** — Consider lazy deletion in the heap or rebuilding the schedule.
- **What if the number of courts is fixed and you need to reject some bookings to maximize revenue?** — This becomes a weighted interval scheduling problem on multiple machines, which is NP-hard in general.
- **Can you do this in O(n) if the time values are bounded?** — Consider bucket sort or counting sort for the time values.
- **How would you handle recurring bookings (e.g., weekly tennis lessons)?** — Think about expanding recurrences into individual bookings or modeling them as periodic intervals.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
