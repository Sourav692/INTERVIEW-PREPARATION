# Retry Strategy — Explained Simply

## The Problem

Build a job runner that retries failures — with the **wait time between attempts** decided by a pluggable policy:

| Strategy | Delays (attempts 1–5) |
|---|---|
| **Linear** | 1, 1, 1, 1, 1 |
| **Fibonacci** | 1, 1, 2, 3, 5 |
| **Exponential** | 1, 2, 4, 8, 16 |

You should be able to swap the policy without touching the retry loop.

## First: Why Wait At All?

Why not just retry immediately?

Because of *why* things usually fail. A failed call almost always means the other end is **overloaded or briefly unavailable**. Retrying instantly adds more load to something that's already struggling.

Do that from a thousand clients in a tight loop and you don't recover from a blip — **you turn a blip into an outage.**

Backing off gives the far end room to breathe.

## An Analogy First: Knocking on a Door

You knock. No answer.

**No backoff:** you hammer on the door continuously. If they were in the shower, they now can't even get to the door — and you're making it worse.

**Linear backoff:** knock every 10 seconds. Polite, but if they've gone out for the afternoon you'll knock 360 times.

**Exponential backoff:** knock, wait 10s, 20s, 40s, 80s… Quick if they're just slow to answer, and it stops pestering an empty house.

**Fibonacci:** 10s, 10s, 20s, 30s, 50s. Between the two — backs off faster than linear, but doesn't give up as violently as exponential.

And the crucial extra: **if a hundred people are all knocking on the same door and they all back off by exactly the same amount, they all knock again at the same instant.** That's why real systems add randomness — more on that below.

## The Design: Separate What Varies

Start with the obvious version — the policy inside the loop:

```python
def run(job, mode):
    for attempt in 1..max:
        try: job(); return True
        except:
            if mode == "linear":      delay = 1
            elif mode == "exponential": delay = 2 ** (attempt-1)
            elif mode == "fibonacci":  delay = fib(attempt)
            sleep(delay)
```

It works. And it shows exactly what's wrong: **every new policy means editing the scheduler.** The delay logic is tangled with the retry logic, and you can't test a curve without actually running a job.

### The fix

Notice all three strategies answer the *same question*:

> **"How long should I wait before attempt number n?"**

That's a function from an integer to a float. So put it behind a one-method interface:

```python
class RetryStrategy:
    def next_delay(self, attempt: int) -> float: ...
```

Now the scheduler owns the **loop** — call the job, catch the failure, count attempts, sleep, give up — and never learns which policy it has. Add a new strategy and the scheduler doesn't change by a single character.

That's the **strategy pattern**, and this is its textbook case.

## The Bit the Official Answer Gets Wrong

Hint 1 says:

> *"Think of each retry strategy as a **pure function** from the attempt number to a delay."*

Linear and exponential obviously are. But the official answer makes Fibonacci **stateful**:

```python
class FibonacciRetry:
    def __init__(self):
        self.prev, self.curr = 0, 1      # ← remembered between calls

    def next_delay(self, attempt):
        nxt = self.prev + self.curr
        self.prev, self.curr = self.curr, nxt
        return nxt
```

It produces the right sequence — *if* you call it with `attempt = 1, 2, 3, …` in strict order, on an instance used by exactly one job.

Three ways that breaks:

1. **Call it out of order** or twice for the same attempt → wrong answers.
2. **Reuse the instance for a second job** → resumes mid-sequence.
3. **Two threads share it** → their `prev`/`curr` updates interleave and **both** get garbage. And a job scheduler is precisely where that happens.

### But `fib(n)` doesn't need state

The nth Fibonacci number depends only on `n`:

```python
def next_delay(self, attempt):
    a, b = 0, 1
    for _ in range(attempt):
        a, b = b, a + b
    return self.initial * a
```

Now the object holds **nothing mutable**. It's reusable, thread-safe, and testable without running a job.

**"But that's O(n) per call instead of O(1)!"** True. And `n` is a *retry count* — single digits. The notebook benchmarks both: at 1,000 attempts the stateless version takes 27 ms and the stateful one 0.2 ms. At a realistic 5 attempts, both are microseconds.

> **Paying a theoretically-worse inner loop to get a genuinely pure interface is the right trade here** — and being able to say *why* is the point.

## Step-by-Step Example (Narrated)

A job that fails twice then succeeds. Exponential backoff, `max_attempts = 4`.

---

**Attempt 1.** Call the job → raises `ConnectionError`.

Not the last attempt, so ask the strategy: `next_delay(1)` = `1 × 2⁰` = **1 second**. Sleep.

---

**Attempt 2.** Call the job → fails again.

`next_delay(2)` = `1 × 2¹` = **2 seconds**. Sleep.

---

**Attempt 3.** Call the job → **succeeds.** Return `True` immediately.

---

**Total: 3 calls, 2 sleeps.**

Note that: **three attempts, but only two delays.** The successful attempt never waits, and — more importantly — see the next section.

## The Off-by-One That Everyone Hits

What if the job *never* succeeds?

```
attempt 1: fail → sleep 1s
attempt 2: fail → sleep 2s
attempt 3: fail → sleep 4s   ← WRONG
return False
```

That final sleep is pure waste. There's **no attempt 4** to wait for. You just made the caller wait 4 seconds to be told something you already knew.

```python
if attempt == self.max_attempts:
    return False          # give up WITHOUT sleeping
sleep(strategy.next_delay(attempt))
```

> **`max_attempts` attempts means `max_attempts - 1` sleeps.**

## Testing Without Actually Waiting

Here's a small trick that makes this whole thing testable.

If the scheduler calls `time.sleep` directly, testing exponential backoff over 5 attempts means your test suite **actually waits 31 seconds**. Nobody writes that test.

So **inject the sleep function**:

```python
def run(self, job, strategy, sleep=time.sleep):
    ...
    sleep(strategy.next_delay(attempt))
```

Production passes nothing and gets `time.sleep`. Tests pass a recorder:

```python
class Recorder:
    def __init__(self): self.delays = []
    def __call__(self, seconds): self.delays.append(seconds)
```

Now the test runs instantly **and** asserts the exact delays:

```python
assert rec.delays == [1, 2, 4]
```

> **General rule:** anything your code waits on, randomises with, or reads the clock from should be injectable.

## Jitter: The Production Detail That Actually Matters

Picture 10,000 clients. A deploy causes them all to fail at the same instant. They all back off by exactly 2 seconds.

**They all retry at the same instant.** A synchronised stampede that re-kills the service just as it was recovering. This is called a **thundering herd**, and it's a genuine cause of outages.

The fix: randomise each delay a bit.

```python
delay = base * (1 - 0.5 * random())     # somewhere in [0.5·base, base]
```

Now those 10,000 retries spread across a window instead of arriving together.

### Where to put it

**Not inside each strategy.** Wrap them instead:

```python
JitteredRetry(ExponentialRetry(), factor=0.5)
```

Two reasons this placement is better:

- The underlying curve stays **deterministic and testable**.
- **Any** strategy — including ones you write later — gets jitter for free.

## Don't Retry Bugs

The official answer catches bare `Exception`. That means a `TypeError` from a mis-called job gets retried three times with backoff.

That's not a transient failure — it's a **bug**. Retrying it just delays the inevitable and buries the original stack trace.

```python
ResilientScheduler(retry_on=(ConnectionError, TimeoutError))
```

**The rule of thumb:**

| Retry these | Never retry these |
|---|---|
| Timeouts | Bad arguments (`TypeError`, `ValueError`) |
| Connection resets | Authentication failures |
| HTTP 429, 503 | HTTP 400, 404 |

Transient means "might work next time". Deterministic means "will fail identically forever".

## The Thing Retries Can't Fix

This is the strongest point you can make in an interview, because it's the failure that reaches production.

> **A retry assumes the failed attempt had no effect.**

Suppose the job is "charge the customer £50" and it fails with a **timeout**.

Did the charge go through? **You don't know.** A timeout means you didn't get a response — not that nothing happened. The charge may well have succeeded and only the reply got lost.

Retry it, and you've charged them twice.

No retry loop can fix this, no matter how clever the backoff. The fix lives in the **job**: it must carry an **idempotency key** so the server recognises the duplicate and discards it.

Raising this unprompted is worth more than any amount of backoff-curve detail.

## Why the Design Is Good

The benchmark comparing stateless vs stateful Fibonacci:

| Attempts | Stateless (pure) | Stateful |
|---|---|---|
| 125 | 0.31 ms | 0.03 ms |
| 250 | 1.32 ms (4.2×) | 0.05 ms (1.8×) |
| 500 | 5.97 ms (4.5×) | 0.10 ms (2.2×) |
| 1,000 | 27.2 ms (4.6×) | 0.20 ms (2.0×) |

The stateless version is quadratic overall, exactly as predicted. **And it doesn't matter** — at any realistic retry count both are microseconds, and the stateless version is the one you can safely share between threads.

*(A fun aside the benchmark turned up: `fib(2000)` is about 4×10⁴¹⁷. Python integers handle that fine, but `float` tops out around 1.8×10³⁰⁸, so multiplying it by the delay raises `OverflowError`. Another argument for capping the delay inside the strategy.)*

## Common Mistakes

- **Sleeping after the final failure.** No attempt follows it.
- **Making Fibonacci stateful.** Breaks on reuse, out-of-order calls, and concurrency.
- **Calling `time.sleep` directly.** Makes the code untestable without real waiting.
- **`except Exception`.** Retries bugs as if they were network blips.
- **Backoff with no jitter.** Synchronised herds re-kill a recovering service.
- **Uncapped exponential.** By attempt 11 you're waiting 17 minutes.
- **Putting the cap in the scheduler.** It's part of the curve — it belongs in the strategy.
- **Retrying a non-idempotent operation.** The retry loop can't help; the job needs an idempotency key.

## The Takeaway

> **Separate what varies from what doesn't.** The loop — call, catch, count, sleep, give up — never changes. Only the delay curve does. Put the curve behind a one-method interface and the loop never needs touching again.

And two things worth carrying beyond this problem: **prefer a pure function to remembered state** (Fibonacci looked like it needed memory, and didn't), and **inject anything that waits or randomises**, so you can test it in microseconds instead of minutes.
