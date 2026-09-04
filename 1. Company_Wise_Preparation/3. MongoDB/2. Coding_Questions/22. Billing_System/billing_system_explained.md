# Billing System — Explained Simply

## The Problem

A monthly bill is an array of 31 daily costs. Three tasks, building on each other:

1. **`update(day, cost)`** — add a charge to a day.
2. **Total up to a day**, where the total isn't just the usage:
   ```
   plan_cost = max(MinimumPlanCost, usage × percentage)
   total     = usage + plan_cost
   ```
3. **Several plans in one month**, each covering a range of days with its own minimum and rate.

## Two Ideas, Both Simple

**Prefix sums** — so summing a range of days is instant.

**A clamped rate** — `max(minimum, rate × usage)`, which is just "you pay at least this much" written as arithmetic.

Everything else is careful reading of the spec.

## Prefix Sums: Sum a Range Without Summing It

To find the total cost of days 5 through 12, the obvious approach adds up eight numbers. Do that for every query and every plan and you're re-walking the array constantly.

Instead, precompute the **running total**:

```
bill    =    [10, 20, 30, 40, 50]
prefix  = [0, 10, 30, 60, 100, 150]
          ↑
   a leading zero
```

`prefix[i]` = the sum of everything *before* index `i`.

Now any range is a **single subtraction**:

```
sum(bill[1..3]) = prefix[4] - prefix[1] = 100 - 10 = 90
                                          (20 + 30 + 40 ✓)
```

### That leading zero matters

`prefix` has `n + 1` entries, starting with `0` for "the empty range".

Without it, `rangeSum(0, r)` needs a special case (`if l == 0: return prefix[r]`), and that's a branch people get wrong. With it, the same formula works for every range including those starting at 0.

It's the same trick as the half-open interval in binary search: one extra slot removes a whole class of edge case.

## An Analogy First: The Milometer

Your car's odometer doesn't record "how far did I drive on Tuesday". It records **total distance ever**.

But that's enough. To find Tuesday's mileage:

```
reading Tuesday night − reading Monday night
```

One subtraction, no matter how many days you're asking about. And the odometer costs nothing to maintain — it just counts up as you drive.

That's a prefix sum. `prefix[i]` is the odometer reading at the end of day `i-1`, and any range is the difference between two readings.

## The Clamped Rate

```
plan_cost = max(MinimumPlanCost, usage × percentage)
```

This is a **piecewise-linear** cost — the shape of every phone tariff and cloud bill:

```
cost
  │           ╱  ← rate × usage (proportional)
  │         ╱
  │───────╱      ← minimum (flat)
  │      ↑
  └──────┴──────────── usage
     break-even
```

Below the **break-even point** you pay the flat minimum. Above it you pay the rate.

And the break-even point is exactly `minimum / rate`. With `minimum = 5.0` and `rate = 0.1`, that's `50` units of usage.

> **That number tells you your test cases:** below it, exactly on it, and above it. The "exactly on it" case is where a `<` vs `<=` mistake would hide.

## Step-by-Step Example (Narrated)

`bill = [10] × 31`. Three plans, each with `minimum = 5.0`, `rate = 0.1`:

```
plan A: days 0–10       plan B: days 11–15       plan C: days 16–30
```

**Query: day 17.**

Each plan sees only the days in the **intersection** of its range with `[0, 17]`:

---

**Plan A** — range 0–10, all elapsed.

```
effective range = [max(0, 0), min(17, 10)] = [0, 10]     → 11 days
usage = 11 × 10 = 110
rate × usage = 11.0    vs.    minimum = 5.0
plan cost = max(5.0, 11.0) = 11.0        ← above break-even, the rate wins
```

---

**Plan B** — range 11–15, all elapsed.

```
effective range = [11, min(17, 15)] = [11, 15]           → 5 days
usage = 5 × 10 = 50
rate × usage = 5.0     vs.    minimum = 5.0
plan cost = max(5.0, 5.0) = 5.0          ← EXACTLY at break-even
```

> `50 × 0.1 = 5.0`, which is precisely `minimum / rate`. Both branches of the `max` agree. This is the boundary case worth having a test for.

---

**Plan C** — range 16–30, but the month has only reached day 17.

```
effective range = [16, min(17, 30)] = [16, 17]           → 2 days  ← CLAMPED
usage = 2 × 10 = 20
rate × usage = 2.0     vs.    minimum = 5.0
plan cost = max(5.0, 2.0) = 5.0          ← below break-even, the minimum bites
```

---

**Total:**

```
usage:      110 + 50 + 20 = 180
plan costs:  11 +  5 +  5 =  21
                    total = 201
```

The clamping — `min(day, plan.end)` — is the entire multi-plan logic. Everything else is the same formula three times.

## The Spec Problem Worth Raising

The official answer flags this and then codes past it:

> *"`day` before any plan starts: plan cost is `max(min, 0) = minimumPlanCost`. **The customer pays the minimum even with zero usage.**"*

Take it seriously. Query on **day 3**:

- Plan A (days 0–10): 4 days of usage → a real charge. ✅
- Plan B (days 11–15): **hasn't started**. Usage 0 → charged the minimum. ❌
- Plan C (days 16–30): **hasn't started**. Usage 0 → charged the minimum. ❌

You've billed the customer for two plans that don't begin for another week.

**No real billing system does that.** And it's not a rounding detail — it's a different bill.

The fix is one line:

```python
if day < plan.start:
    continue        # this plan hasn't begun
```

The notebook implements **both** behind a flag and asserts they differ, because the right move in an interview is to *notice the ambiguity, name it, and say which you chose*.

> **In a money spec, ambiguity is the first thing to raise, not the last.**

## Two Small Things That Prevent Real Bugs

### Empty ranges must yield zero, not a negative

```python
if lo > hi:
    return 0.0
```

When a plan hasn't started, `min(day, end) < max(0, start)` — the intersection is empty. Without this guard, the subtraction `prefix[hi+1] - prefix[lo]` runs backwards and returns a **negative** number.

In a billing system, a negative charge is a refund nobody authorised.

### The prefix cache must be invalidated

```python
def update(self, day, cost):
    self.bill[day] += cost
    self._prefix = None      # ← the whole prefix is now stale
```

Forget that line and every query after an update silently reports the old total. The notebook has a test for exactly this.

## The Update/Query Trade-Off

Prefix sums give O(1) queries — but any update invalidates the whole array, costing O(n) to rebuild.

| Structure | Query | Update |
|---|---|---|
| Plain array (re-sum each time) | O(n) | O(1) |
| **Prefix sums** | **O(1)** | O(n) |
| **Fenwick tree** | O(log n) | O(log n) |

A **Fenwick tree** (binary indexed tree) balances both: each slot stores the sum of a block sized by the lowest set bit of its index, so a prefix sum assembles from `log n` blocks and an update touches `log n` of them.

**But for a 31-day month, none of this matters.** `log 31 ≈ 5` versus `n = 31` — the constant factors probably favour the plain array.

The benchmark bears it out: the Fenwick version is actually **slower** than plain prefix sums here, because O(log n) beats O(1) at nothing.

> **Knowing when *not* to reach for the clever structure is as much of the answer as knowing how to build it.** It earns its place when the range is a year of minutes, or millions of accounts.

## The Question to Ask Before Coding

**Is `percentage` 0.15 or 15?**

If you assume decimal and they meant "15 percent", every number you produce is 100× wrong — and it's arithmetically silent, so nothing crashes.

One sentence of clarification saves the entire answer.

## The Thing This Design Gets Wrong for Production

Everything here uses **floating point** — and you should never bill in floating point.

```python
0.1 + 0.2 == 0.3     # False
```

A billing system that's a hundredth of a penny out will eventually be a hundredth of a penny out **in someone's favour**, over and over, and someone will notice.

Real systems store **integer minor units** (pence, cents) or use `decimal.Decimal`, and define rounding explicitly at the point of charge.

*(The notebook's tests use `1e-9` tolerances — which is itself the argument.)*

## Common Mistakes

- **Sizing `prefix` at `n` instead of `n+1`.** Forces a special case for ranges starting at 0.
- **Not guarding `lo > hi`.** A reversed subtraction gives a negative charge.
- **Forgetting to invalidate the prefix cache after an update.** Silently stale totals.
- **Charging plans that haven't started.** Arithmetically faithful, commercially wrong.
- **Not asking about the units of `percentage`.** 100× errors, silently.
- **Reaching for a Fenwick tree on a 31-element array.** More code, slower.
- **Billing in floats.** Accumulating rounding errors in money.
- **Assuming plans never overlap without checking.** If day 12 is under two plans, its usage gets counted twice and the invoice stops adding up.

## The Takeaway

> **Precompute the running total once**, and every range sum becomes a single subtraction. Then the multi-plan logic is nothing more than clamping each plan's range to the part of the month that has actually elapsed.

The harder half isn't the algorithm — it's the **reading**. "Plans that haven't started still pay their minimum" is faithful to the formula and absurd as a bill. When the spec is about money, the ambiguities are the first thing to surface.
