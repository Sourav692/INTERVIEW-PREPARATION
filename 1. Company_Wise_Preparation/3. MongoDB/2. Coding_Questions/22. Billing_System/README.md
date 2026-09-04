# Billing System

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Arrays, Math · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

### Problem 1

Design a function to update daily costs in a monthly bill.

- The bill is represented as an array of length 31, where each index corresponds to a day of the month (0-based index).
- Implement an `update` function that takes a specific day (`index`) and a cost (`newCost`) and updates the bill as follows: `bill[index] += newCost`.

### Problem 2

Given a specific day of the month, calculate the **total cost** up to and including that day using the following formula:

```
PlanCost:  Max(MinimumPlanCost, usageCost * percentage)
TotalCost: usageCost + planCost
```

- `MinimumPlanCost` and `percentage` are constants.
- `usageCost` is the total cost in the bill up to the given day.

### Problem 3

Extend the functionality to support **multiple plans** in a month.

- A plan is defined by its range of days and associated constants: `{ start: startDay, end: endDay, MinimumPlanCost, percentage }`.
- Given a day, calculate the total cost for all plans that overlap from the start of the month up to that day.
- Use the formula for each plan within its range, summing up the costs for all applicable plans.

**Example input:**

```json
[
  { "start": 0,  "end": 10, "MinimumPlanCost": v1, "percentage": p1 },
  { "start": 11, "end": 15, "MinimumPlanCost": v2, "percentage": p2 },
  { "start": 16, "end": 30, "MinimumPlanCost": v3, "percentage": p3 }
]
```

For a given day (e.g., 17):

- Calculate the cost for days 0–10 using the first plan.
- Calculate the cost for days 11–15 using the second plan.
- Calculate the cost for days 16–17 using the third plan.
- Return the total cost as the sum of all plan costs.

---

## Study Tools

### Hint 1

The single-plan case is just a **prefix sum** query with a clamped multiplier. Think about what happens when `usageCost * percentage` falls below `MinimumPlanCost` — the plan cost becomes a constant, which changes the shape of the total.

### Hint 2

For multiple plans, each plan contributes **independently** over its own day range. A plan is only active for days between its `start` and `end`, so for a query at day `d` you need the sum of bill entries over the **intersection** of `[0, d]` with each plan's range.

### Hint 3

Precompute prefix sums of the bill array once. Then each plan's contribution is `max(MinimumPlanCost, percentage * usageInRange)` where `usageInRange` is a single prefix-sum difference. Sum these contributions over all plans and add the total usage to get the final answer.

---

### Answer

This is a **prefix-sum** problem with a **piecewise-linear** cost function. The core idea is to precompute `prefix[i] = sum(bill[0..i])` so any range sum is O(1), then for each plan compute its contribution independently based on the usage that falls within that plan's active range.

#### Single-Plan Solution

For Problem 2, the formula is:

```
usageCost = sum(bill[0..day])
planCost  = max(MinimumPlanCost, usageCost * percentage)
totalCost = usageCost + planCost
```

```java
public class BillingSystem {
    private int[] bill;
    private double minimumPlanCost;
    private double percentage;

    public BillingSystem(int[] bill, double minimumPlanCost, double percentage) {
        this.bill = bill;
        this.minimumPlanCost = minimumPlanCost;
        this.percentage = percentage;
    }

    public void update(int day, int newCost) {
        bill[day] += newCost;
    }

    public double getTotalCost(int day) {
        double usageCost = 0;
        for (int i = 0; i <= day; i++) {
            usageCost += bill[i];
        }
        double planCost = Math.max(minimumPlanCost, usageCost * percentage);
        return usageCost + planCost;
    }
}
```

**Time:** O(day) per query due to the linear scan — if queries are frequent, precompute prefix sums. **Space:** O(1) auxiliary space beyond the bill array.

#### Multi-Plan Solution

For Problem 3, each plan has its own `start`, `end`, `MinimumPlanCost`, and `percentage`. A plan contributes to the total only for days within its range. For a query at day `d`:

- The usage attributable to plan `i` is `sum(bill[max(0, start_i) .. min(d, end_i)])`.
- The plan cost is `max(MinimumPlanCost_i, percentage_i * usageInPlanRange)`.
- The total cost is `sum(usageInPlanRange + planCost_i)` over all plans.

Using prefix sums makes each range query O(1):

```java
import java.util.*;

class Plan {
    int start;
    int end;
    double minimumPlanCost;
    double percentage;

    Plan(int start, int end, double minimumPlanCost, double percentage) {
        this.start = start;
        this.end = end;
        this.minimumPlanCost = minimumPlanCost;
        this.percentage = percentage;
    }
}

public class BillingSystem {
    private int[] bill;
    private long[] prefix;
    private List<Plan> plans;

    public BillingSystem(int[] bill, List<Plan> plans) {
        this.bill = bill;
        this.plans = plans;
        buildPrefix();
    }

    private void buildPrefix() {
        prefix = new long[bill.length + 1];
        for (int i = 0; i < bill.length; i++) {
            prefix[i + 1] = prefix[i] + bill[i];
        }
    }

    public void update(int day, int newCost) {
        bill[day] += newCost;
        buildPrefix();   // O(n) rebuild; see note below
    }

    private long rangeSum(int left, int right) {
        if (left > right) return 0;
        return prefix[right + 1] - prefix[left];
    }

    public double getTotalCost(int day) {
        double total = 0;
        for (Plan p : plans) {
            int effectiveStart = Math.max(0, p.start);
            int effectiveEnd = Math.min(day, p.end);
            long usageInPlan = rangeSum(effectiveStart, effectiveEnd);
            double planCost = Math.max(p.minimumPlanCost, p.percentage * usageInPlan);
            total += usageInPlan + planCost;
        }
        return total;
    }
}
```

**Time:** O(p) per query where p is the number of plans, with O(1) per range sum. Updates are O(n) due to prefix rebuild; if updates are frequent, use a Fenwick tree for O(log n) updates and queries. **Space:** O(n) for the prefix array.

#### Correctness Argument

For each plan, the usage within its range is independent of other plans because the bill array entries are disjoint across plan ranges (or if they overlap, the problem statement implies each day is billed under exactly one plan). The `max` operation correctly implements the minimum charge: if `percentage * usage` is below `MinimumPlanCost`, the customer pays the minimum; otherwise they pay the proportional amount. Summing `usageInPlan + planCost` over all plans gives the total bill because every day from 0 to `day` falls into exactly one plan's range (assuming plans partition the month). If plans can overlap, the problem statement's example shows non-overlapping ranges, so this interpretation holds.

#### Edge Cases

- **`day` before any plan starts:** `effectiveEnd < effectiveStart`, `rangeSum` returns 0, plan cost is `max(min, 0) = minimumPlanCost`. The customer pays the minimum even with zero usage — verify with the interviewer whether this matches business logic.
- **`day` beyond the last plan's end:** trailing plans contribute 0 usage but still their minimum cost. Again, confirm whether plans beyond `day` should contribute at all.
- **Negative costs in bill:** the prefix sum handles them arithmetically, but `max` with `MinimumPlanCost` may mask them.
- **Empty plans list:** returns 0.
- **`percentage` as a decimal** (e.g., 0.15 for 15%) **vs. integer** (e.g., 15): clarify with the interviewer. The code assumes decimal.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start by solving Problem 1 — that's just a one-liner: `bill[day] += newCost`. Then Problem 2 asks for the total up to a day. The naive approach is a loop from 0 to `day` summing `bill[i]`, which is O(day) per query. That's fine for a single query, but the moment you realize the interviewer is building toward multiple queries and multiple plans, you know you need prefix sums.

Build `prefix[i] = sum(bill[0..i-1])` so `rangeSum(l, r) = prefix[r+1] - prefix[l]` in O(1). Now Problem 2 becomes trivial: `usage = rangeSum(0, day)`, `planCost = max(min, usage * percentage)`, return `usage + planCost`.

For Problem 3, the key insight is that each plan operates **independently** over its own range. The usage for plan `i` at query day `d` is `rangeSum(max(0, start_i), min(d, end_i))`. The plan cost for that usage is `max(MinimumPlanCost_i, percentage_i * usageInPlan)`. Sum these over all plans and you're done.

The only wrinkle is updates. If updates are frequent, rebuilding the prefix array on every update is O(n). Mention that a **Fenwick tree** (Binary Indexed Tree) would give O(log n) updates and O(log n) range queries, and offer to implement it if the interviewer wants. Most interviewers will be satisfied with the prefix-sum approach and a note about the tradeoff.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Clarify whether plans partition the month or can overlap** — the example shows non-overlapping ranges, but real billing systems sometimes have prorated overlaps. Your range-sum logic handles both, but the total-cost formula changes if a day falls under two plans.
- **Ask about the units of `percentage`** — is 0.15 a 15% rate or is 15 a 15% rate? Getting this wrong silently corrupts every calculation. A quick clarification saves you from a wrong answer.
- **Mention the update/query tradeoff explicitly** — prefix sums give O(1) range queries but O(n) updates. A Fenwick tree gives O(log n) for both. Naming this tradeoff shows you're thinking about the full system lifecycle.
- **Verify the minimum-cost semantics for zero-usage plans** — if a plan covers days 11–15 and the query is on day 5, should that plan contribute its `MinimumPlanCost`? The formula says yes, but a real billing system might only charge for plans that have started. State your interpretation and code to it.
- **Use `long` for prefix sums to avoid overflow** — 31 days of `int` costs could theoretically overflow a 32-bit int if costs are large. Using `long` for the prefix array is a defensive choice that costs nothing.
- **Walk through the example day 17 by hand** — compute each plan's usage and plan cost separately, then sum. This demonstrates you understand the decomposition and gives the interviewer confidence the code matches the spec.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if plans can overlap, and a day's usage is split across multiple plans?** — You'd need an allocation rule (e.g., prorated by day, or sequential consumption) and the total-cost formula changes accordingly.
- **How would you handle updates efficiently if the bill changes frequently?** — Replace the prefix array with a Fenwick tree for O(log n) updates and range queries.
- **What if the month length is not fixed at 31 days?** — Generalize to an arbitrary `daysInMonth` parameter; the prefix array and plan ranges scale naturally.
- **Can you support queries for arbitrary date ranges, not just month-to-date?** — The same prefix-sum logic extends to `rangeSum(l, r)` for any `l` and `r`; plan costs would need a rule for partial-month usage.
- **How would you persist this data if the bill is stored in a database?** — A `daily_charges` table indexed by `(account_id, day)` with a `SUM` query, and a `plans` table with `start_day, end_day, minimum_cost, percentage`; consider materializing prefix sums or caching query results.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same design in Python so every claim is executable and testable; the Java reference above is reproduced unchanged.

## ⚠️ A note on the "plan not yet started" edge case

The official answer flags this and then codes the version that charges anyway:

> *"`day` before any plan starts: … plan cost is `max(min, 0) = minimumPlanCost`. **The customer pays the minimum even with zero usage** — verify with the interviewer whether this matches business logic."*

That is worth taking seriously, because it is not a rounding detail — it changes the bill. Querying on day 3 with the three-plan example charges `v1 + v2 + v3`, billing the customer for two plans that have not begun. Almost no real billing system does that.

The notebook implements **both** policies behind a flag (`charge_unstarted_plans`), asserts the difference, and defaults to the one a billing system would actually want: a plan contributes only once `day >= plan.start`.
