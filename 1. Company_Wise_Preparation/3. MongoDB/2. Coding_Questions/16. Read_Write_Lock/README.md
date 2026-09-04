# Read/Write Lock

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Concurrency · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Implement a Read/Write Lock.

---

## Study Tools

### Hint 1

The core tension is allowing **multiple readers at once** while giving writers **exclusive** access, so think about what state you need to track beyond just a boolean flag. You'll need to know **how many** readers are currently inside the critical section.

### Hint 2

A `Condition` variable (or two) lets you block writers while readers are present, and block readers while a writer holds the lock. The tricky part is deciding when a **waiting writer gets priority** over new readers to avoid writer starvation.

### Hint 3

Track `readers` (count of active readers) and `writer` (boolean for active writer). Readers acquire by incrementing `readers` if no writer is active; writers set `writer = True` and wait until `readers == 0`. Use a single lock plus condition variables to make the wait/notify logic atomic.

---

### Answer

This is a classic concurrency problem where you implement a readers-writer lock with mutual exclusion for writers and shared access for readers. The standard approach uses a mutex, a reader count, a writer flag, and condition variables to coordinate the transitions between states.

#### The Core Idea

You need to maintain two pieces of state:

- `readers`: how many threads are currently reading
- `writer`: whether a thread is currently writing

All state transitions happen under a single mutex. Readers wait if a writer is active **or waiting** (to prevent writer starvation). Writers wait if any readers are active or another writer is active.

#### Implementation

```python
import threading


class ReadWriteLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._readers = 0
        self._writer = False
        self._readers_cond = threading.Condition(self._lock)
        self._writers_cond = threading.Condition(self._lock)
        self._waiting_writers = 0

    def acquire_read(self):
        with self._lock:
            # Wait while a writer is active or waiting (writer priority)
            while self._writer or self._waiting_writers > 0:
                self._readers_cond.wait()
            self._readers += 1

    def release_read(self):
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._writers_cond.notify_all()

    def acquire_write(self):
        with self._lock:
            self._waiting_writers += 1
            try:
                while self._writer or self._readers > 0:
                    self._writers_cond.wait()
                self._writer = True
            finally:
                self._waiting_writers -= 1

    def release_write(self):
        with self._lock:
            self._writer = False
            # Wake up all waiting readers and one waiting writer
            self._readers_cond.notify_all()
            self._writers_cond.notify_all()
```

**Time:** O(1) for all operations — each lock/unlock is constant-time state manipulation under a mutex. **Space:** O(1) — only a few integer and boolean fields.

#### Correctness Argument

The invariant is: at any moment, either `readers > 0` and `writer == False`, or `readers == 0` and `writer == True`, or `readers == 0` and `writer == False` (unlocked). All state changes happen while holding `self._lock`, so the invariant is preserved across every transition. Readers can only increment `readers` when `writer == False`, and writers can only set `writer = True` when `readers == 0` and no other writer is active. The `_waiting_writers` counter ensures that once a writer is waiting, new readers block, preventing writer starvation.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest version: just a boolean `writer` flag and a reader count, with no waiting logic. Readers check if `writer` is false and increment `readers`; writers check if `readers == 0` and set `writer = True`. This fails because the check-then-act isn't atomic — two readers could both see `writer == False` and both proceed, or a reader and writer could race.

Add a mutex to make the check-then-act atomic. Now you have basic correctness, but threads that can't acquire the lock just spin or fail. You need a way to block and wake up threads. This is where condition variables come in.

The naive condition variable approach: readers wait on `writer == False`, writers wait on `readers == 0`. This works but can **starve writers** — if readers keep arriving, a writer might wait forever. The fix is to track `_waiting_writers` and make readers check `_waiting_writers == 0` before acquiring. Now a writer that's waiting gets priority over newly arriving readers.

The last subtlety is the release logic. When the last reader releases, you need to wake up writers. When a writer releases, you need to wake up all readers (they can all proceed) and one writer (if any are waiting). Using `notify_all()` for both conditions is simpler and correct, though slightly less efficient than targeted wakeups.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Mention writer starvation explicitly** — the interviewer is listening for whether you know that naive reader-preference implementations can starve writers indefinitely. Tracking `_waiting_writers` and giving them priority is the key differentiator.
- **Explain the invariant** — state clearly that the lock is always in exactly one of three states: readers-active, writer-active, or unlocked. This shows you're thinking about correctness, not just code.
- **Use condition variables correctly** — the `while` loop (not `if`) around `wait()` matters because spurious wakeups and multiple waiters can cause the condition to change between wakeup and re-check.
- **Consider the fairness tradeoff** — this implementation gives writers priority, but you could mention that a reader-preference version would have higher throughput for read-heavy workloads at the cost of potential writer starvation.
- **Discuss the release wakeup strategy** — releasing a writer should notify both readers and writers; you can optimize by checking which conditions changed, but `notify_all()` on both is simpler and correct.
- **Think about reentrancy** — if the interviewer asks, note that this lock is **not** reentrant; a thread holding a read lock that tries to acquire a write lock will deadlock. Reentrant versions need to track owner thread IDs.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you make this lock reentrant?** — Track which threads hold read locks and prevent a reader from upgrading to a writer unless it's the only reader.
- **What if you wanted to support upgrading from read to write lock without releasing first?** — This requires a careful protocol to avoid deadlock when multiple readers try to upgrade simultaneously.
- **How would you implement this as a distributed lock across multiple machines?** — Think about consensus protocols, leases, and how to handle node failures.
- **What's the performance difference between this and just using a mutex for everything?** — Consider read-heavy workloads and the cost of contention on the single mutex.
- **How would you add a timeout to the acquire methods?** — Use `condition.wait(timeout)` and handle the return value to distinguish timeout from notification.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Note on the official answer

The implementation above is correct, and the notebook verifies it under real thread contention. Two things it leaves implicit, both covered in the notebook:

1. **Writer priority starves *readers*, not just the other way round.** The answer names reader-preference starvation but not its mirror image: with a continuous stream of writers, `_waiting_writers > 0` is permanently true and readers never run. Fairness is a *choice between* two starvation modes, and the honest third option is a FIFO/fair lock where whoever waited longest goes next.
2. **`notify_all()` on both conditions makes the two `Condition` objects redundant.** Since both share `self._lock` and both are woken on every release, a single `Condition` behaves identically. Two conditions only pay off with *targeted* wakeups (`notify()` on writers when the last reader leaves, `notify_all()` on readers when a writer leaves) — the notebook implements that version and measures it.
