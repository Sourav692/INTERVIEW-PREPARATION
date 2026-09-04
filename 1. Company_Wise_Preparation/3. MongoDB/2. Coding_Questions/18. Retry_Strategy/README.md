# Retry Strategy

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Concurrency, Math, OOP & Design Patterns · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design and implement a **Job Scheduler with a configurable retry strategy**. The scheduler should allow different retry strategies to be passed in, and it should execute retries based on the provided strategy. The supported retry strategies are:

- **Linear Retry:** Retry after a fixed interval.
- **Exponential Retry:** Retry with exponentially increasing intervals.
- **Fibonacci Retry:** Retry with intervals based on the Fibonacci sequence.

---

## Study Tools

### Hint 1

Think of each retry strategy as a **pure function from the attempt number to a delay**. The scheduler itself doesn't need to know which strategy is active; it just asks for the next delay and waits.

### Hint 2

Implement each strategy as a class with a method like `next_delay(attempt)` that returns the wait time before that attempt. For Fibonacci, you'll need to track the previous two values across calls, so a small amount of state lives inside the strategy object.

### Hint 3

The scheduler runs a loop: execute the job, and on failure, compute the delay for the next attempt by calling the strategy with the current attempt count. Sleep for that many seconds, increment the attempt counter, and repeat until success or max attempts.

---

### Answer

This is a **strategy pattern** problem: the scheduler owns the retry loop, while each retry policy encapsulates only the delay calculation. The cleanest version models a strategy as an object with a `next_delay(attempt)` method, where `attempt` is the 1-based retry number (so attempt 1 is the first retry after the initial failure). The scheduler takes a job, a strategy, and a max attempt count, then loops until the job succeeds or attempts are exhausted.

```python
import time
from abc import ABC, abstractmethod


class RetryStrategy(ABC):
    @abstractmethod
    def next_delay(self, attempt: int) -> float:
        """Return delay in seconds before the given attempt (1-based)."""
        pass


class LinearRetry(RetryStrategy):
    def __init__(self, interval: float = 1.0):
        self.interval = interval

    def next_delay(self, attempt: int) -> float:
        return self.interval


class ExponentialRetry(RetryStrategy):
    def __init__(self, base: float = 2.0, initial: float = 1.0):
        self.base = base
        self.initial = initial

    def next_delay(self, attempt: int) -> float:
        return self.initial * (self.base ** (attempt - 1))


class FibonacciRetry(RetryStrategy):
    def __init__(self, initial: float = 1.0):
        self.initial = initial
        self.prev = 0
        self.curr = 1

    def next_delay(self, attempt: int) -> float:
        if attempt == 1:
            self.prev = 0
            self.curr = 1
            return self.initial
        nxt = self.prev + self.curr
        self.prev = self.curr
        self.curr = nxt
        return self.initial * self.curr


class JobScheduler:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def run(self, job, strategy: RetryStrategy) -> bool:
        """Run job with retries. Returns True if the job eventually succeeded."""
        for attempt in range(1, self.max_attempts + 1):
            try:
                job()
                return True
            except Exception:
                if attempt == self.max_attempts:
                    return False
                delay = strategy.next_delay(attempt)
                time.sleep(delay)
        return False
```

**Time:** O(m) where m is `max_attempts` — the scheduler loops at most m times, and each strategy's `next_delay` is O(1).

**Space:** O(1) — the scheduler holds only the attempt counter, and each strategy stores a constant number of fields.

The correctness argument is a simple loop invariant: before iteration `attempt`, the job has failed exactly `attempt - 1` times, and the strategy has been asked for delays `attempt - 1` times. If the job succeeds, we return `True` immediately. If it fails and `attempt < max_attempts`, we compute the correct delay for that attempt and sleep. When the loop exits without success, we've made exactly `max_attempts` total calls and return `False`. The Fibonacci strategy's state evolves correctly because `prev` and `curr` hold the (n-1)th and nth Fibonacci numbers after the nth call, so the next call produces the (n+1)th.

One design note worth stating out loud: the scheduler here treats the first call as attempt 1, so `max_attempts` **includes** the initial execution. If you want `max_retries` instead (excluding the first call), shift the loop bounds by one. Either convention is fine as long as you state it.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the dumbest thing that works: a scheduler with a hardcoded `time.sleep(1)` before each retry. That handles the linear case but obviously can't express exponential or Fibonacci backoff without a pile of `if` statements inside the loop. The smell is that the **delay calculation is coupled to the retry loop**.

The fix is to notice that all three strategies answer the same question: *"How long should I wait before retry number n?"* That's a function from an integer to a float. Linear ignores `n` and returns a constant. Exponential returns `base^(n-1)`. Fibonacci returns the nth Fibonacci number. So the natural refactor is a strategy object with a method that takes the attempt number and returns the delay.

Linear and exponential are **stateless** — you can compute the delay directly from `n`. Fibonacci is the only one that needs state, because the nth Fibonacci number depends on the previous two. You could compute it recursively each time, but that's O(2^n) for naive recursion or O(n) for a loop, and you'd be recomputing the whole sequence on every call. Keeping `prev` and `curr` as instance variables makes each call O(1) and amortizes the work across retries.

Now decide who owns the loop. The **scheduler** should own the loop because the job execution, exception handling, and attempt counting are the same regardless of strategy. The strategy just answers the delay question. This gives you a clean separation: swap in a different strategy class and the scheduler code doesn't change. That's the whole point of the strategy pattern, and it's exactly what the interviewer wants to hear.

Finally, think about edge cases: what happens if `max_attempts` is 0 or negative? The loop simply doesn't execute and `run` returns `False`. What if the strategy returns a negative delay? `time.sleep` raises a `ValueError`. You can mention you'd validate inputs in a production version, but for the interview, the loop bounds and the return value on exhaustion are the important parts.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the convention for `attempt`** — say explicitly whether attempt 1 is the first execution or the first retry. It changes the loop bounds and the delay formula, and the interviewer can't tell if you've thought about it unless you say it out loud.
- **Make Fibonacci O(1) per call with instance state** — storing `prev` and `curr` as fields and updating them on each call avoids recomputing the sequence from scratch on every retry. This is the one place where a naive implementation silently degrades.
- **Separate the retry loop from the delay policy** — the scheduler should own the loop, exception handling, and attempt counting; the strategy should only answer how long to wait. This is the core design decision, and it's what makes the code extensible to new strategies.
- **Handle the exhaustion case explicitly** — the code should return `False` (or raise) after `max_attempts` failures, and you should trace through that path. Interviewers look for whether you handle the final failure differently from an intermediate one.
- **Think about what `job()` returning vs. raising means** — the code assumes failure is signaled by an exception. If the job returns a status code or `False` instead, the scheduler's contract changes. Mentioning this shows you understand the boundary between the scheduler and the job.
- **Discuss production concerns briefly** — jitter to avoid thundering herd, a maximum backoff cap for exponential, and whether `time.sleep` blocks the calling thread. You don't need to implement these, but naming them signals you've shipped retry logic before.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Add jitter to the delay calculation** to prevent synchronized retries from multiple workers — think about where the randomness should live so the strategy stays deterministic for testing.
- **Cap the exponential backoff at a maximum delay** — decide whether the cap belongs in the strategy or the scheduler.
- **Make the scheduler non-blocking using `asyncio.sleep` instead of `time.sleep`** — what changes in the scheduler's interface and the strategy's return type?
- **Add a callback that fires on each failure** with the attempt number and the exception — where does it hook into the loop, and how do you keep it from coupling the scheduler to logging code?
- **Support a strategy that gives up early based on the exception type** (e.g., retry on `TimeoutError` but not on `ValueError`) — this pushes you toward a `should_retry(attempt, exception)` method alongside `next_delay`.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two notes on the official answer

**1. `FibonacciRetry` is stateful, and that makes it single-use.** It reproduces the correct sequence (1, 1, 2, 3, 5, 8…), but only if `next_delay` is called with `attempt = 1, 2, 3, …` in strict order, on an instance used by exactly one job at a time. Reusing one instance for a second job resumes mid-sequence unless `attempt == 1` happens to reset it, and two threads sharing an instance interleave their `prev`/`curr` updates and corrupt both. The notebook shows a **stateless** version — closed-form Fibonacci from the attempt number — which is reusable, thread-safe, and makes `next_delay` a genuinely pure function, exactly as Hint 1 describes.

**2. `except Exception` will retry bugs, not just failures.** A `TypeError` from a mis-called job is not transient, and retrying it three times with backoff just delays the inevitable while hiding the stack trace. Production retry loops take a `retry_on=(TimeoutError, ConnectionError)` tuple. The notebook implements this as the `should_retry` extension the last follow-up asks for.
