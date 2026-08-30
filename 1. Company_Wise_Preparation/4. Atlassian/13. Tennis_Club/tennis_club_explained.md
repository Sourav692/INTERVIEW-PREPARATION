# Tennis Club — Explained Simply

## The Problem

Assign each booking `(start, finish)` to a court, using the **fewest courts possible**, with unlimited courts available. No court can be double-booked.

```
bookings = [(1, 0, 10), (2, 5, 15), (3, 10, 20), (4, 20, 30)]
# booking 1: [0,10) and booking 2: [5,15) overlap on [5,10) -> need 2 courts at that moment
# booking 3 starts at 10, exactly when booking 1 ends -> can reuse booking 1's court
```

## Why the Obvious Way Is Slow

The obvious approach: try every possible way of assigning bookings to courts, and pick the assignment that uses the fewest courts.

```
try every combination of (booking -> court) assignments
keep the one using the fewest distinct courts
```

The number of ways to assign n bookings to c possible courts explodes combinatorially — this is exponential and completely impractical for any real number of bookings.

## The Simple Trick: Always Reuse Whichever Court Frees Up Soonest

Process bookings in the order they **start**. For each one, ask: "is any existing court already free by the time this booking needs to start?" If yes, put this booking on the court that becomes free **earliest** (not just any free court) — that leaves every other court's later availability untouched for future bookings. If no court is free yet, only then open a brand-new one.

## An Analogy First: A Barbershop With a Smart Receptionist

Imagine a barbershop where new customers keep arriving (in the order they walk in) and the receptionist assigns each one to a chair. Instead of remembering all the chairs and scanning them one by one, the receptionist keeps a small sorted list of "which chair frees up next, and when" — like a ticket dispenser sorted by time.

When a new customer arrives, the receptionist peeks at the very front of that list: "the soonest-available chair frees up at 2:15." If the customer arrived at 2:20 (after 2:15), great — reuse that chair, update its new "next free" time, and re-sort it back into the list. If the customer arrived *before* 2:15, no chair is ready yet — open a brand-new chair. The receptionist never checks chairs that aren't the current soonest — that's the whole trick.

## Step-by-Step Example (Narrated)

`bookings = [(1, 0, 10), (2, 5, 15), (3, 10, 20), (4, 20, 30)]`, already sorted by start time.

We keep a **min-heap** of `(available_time, court_id)` — the court that frees up soonest is always instantly visible at the front.

---

**Booking 1: `(0, 10)`.** Heap is empty → no court is free yet. Open court 0. Push `(10, court 0)` — this court will be available again at time 10.
Heap: `{(10, court 0)}`.

---

**Booking 2: `(5, 15)`.** Peek the heap's front: `(10, court 0)`. Is court 0 available by time 5 (this booking's start)? Is `10 <= 5`? **No** — court 0 is still busy until 10, and this booking needs to start at 5. So we can't reuse it → open a new court, court 1. Push `(15, court 1)`.
Heap: `{(10, court 0), (15, court 1)}`. **Two courts are now in use — this is genuinely necessary, since bookings 1 and 2 overlap on `[5, 10)`.**

---

**Booking 3: `(10, 20)`.** Peek the front: `(10, court 0)` (still the soonest). Is `10 <= 10` (this booking's start)? **Yes!** — court 0 is free by exactly the moment this booking needs it (back-to-back is allowed). Pop it, reuse court 0, push `(20, court 0)` as its new availability.
Heap: `{(15, court 1), (20, court 0)}`.

---

**Booking 4: `(20, 30)`.** Peek the front: `(15, court 1)`. Is `15 <= 20`? **Yes!** — reuse court 1, push `(30, court 1)`.
Heap: `{(20, court 0), (30, court 1)}`.

---

Every booking is assigned, and only **2 distinct courts** were ever opened — matching the maximum number of bookings that were ever simultaneously overlapping (bookings 1 and 2, briefly, on `[5, 10)`).

### The one detail that's easy to miss: `<=`, not `<`, when checking availability

Booking 3 starts at exactly `10`, the same instant court 0 frees up. The check `heap[0][0] <= booking.start` uses `<=` specifically so back-to-back bookings (one ending exactly when another begins) can share a court. Using `<` instead would incorrectly force a brand-new court to be opened for every touching-but-not-overlapping booking.

## Plain-English Walkthrough

1. Sort all bookings by start time.
2. Keep a min-heap of `(available_time, court_id)` for every court currently in use.
3. For each booking, peek the heap's smallest `available_time`. If it's `<=` this booking's start, pop that court, reuse it, and push its new availability (this booking's finish time).
4. Otherwise, no court is free yet — open a brand-new court and push its availability.
5. The number of distinct courts ever opened is the minimum possible, and is also assigned optimally.

## Simple Python Code

```python
import heapq

def assign_courts(bookings):
    bookings = sorted(bookings, key=lambda b: b[1])   # sort by start time
    heap = []           # (available_time, court_id)
    assignments = []
    next_court = 0

    for booking_id, start, finish in bookings:
        if heap and heap[0][0] <= start:
            _, court_id = heapq.heappop(heap)
        else:
            court_id = next_court
            next_court += 1
        heapq.heappush(heap, (finish, court_id))
        assignments.append((booking_id, court_id))

    return assignments

result = assign_courts([(1, 0, 10), (2, 5, 15), (3, 10, 20), (4, 20, 30)])
print(result)
print("courts used:", len(set(court for _, court in result)))   # 2
```

## Why Always Pick the *Earliest*-Freeing Court, Not Just Any Free Court?

This is what's called an exchange argument: suppose an "optimal" solution assigned some booking to a court that frees up *later* than the earliest-available one. You could always swap that assignment to use the earliest-available court instead, without making anything worse — the earliest-available court is free at least as soon as the one that was chosen. Since that swap never hurts, always picking the earliest-available court is guaranteed to be at least as good as any other strategy, which is exactly what "provably optimal" means here.

## Complexity

- **Time:** O(n log n) — sorting the bookings once, then O(log n) heap work for each of the n bookings.
- **Space:** O(n) — the heap holds at most one entry per court ever opened, bounded by the number of bookings.

## The Reusable Pattern

This is the **"interval partitioning via greedy + min-heap"** pattern:
- Meeting Rooms II (minimum meeting rooms needed — identical shape)
- CPU/task scheduling across multiple identical machines
- Any "assign requests to the minimum number of workers/resources, none can double-book" problem

Core idea: the minimum number of resources needed always equals the **maximum number of things overlapping at any single instant** — and greedily reusing whichever resource frees up soonest is provably enough to hit that minimum, no cleverer algorithm can do better.
