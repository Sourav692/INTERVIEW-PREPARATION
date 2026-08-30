# Data Engineer Questions — Explained Simply

*This screen has 6 parts (3 SQL, 1 data modeling, 2 Python). This walkthrough focuses on the trickiest one — the Stadium consecutive-IDs SQL query — since it's where the core "aha" insight lives. The other parts are summarized briefly at the end.*

## The Problem (Stadium Consecutive IDs)

Table `Stadium(id, visit_date, people)`, where `id` increases with `visit_date`. Find every row that's part of a run of **3 or more consecutive ids**, all with `people >= 100`.

```
id | people
1  | 10     (< 100)
2  | 109    (>= 100)
3  | 150    (>= 100)
4  | 99     (< 100)
5  | 145    (>= 100)
6  | 1455   (>= 100)
7  | 199    (>= 100)
8  | 188    (>= 100)
```

Expected result: ids **5, 6, 7, 8** (a single run of 4 consecutive qualifying rows). Notice ids 2 and 3 also have `people >= 100`, but they're **not** in the answer — id 4 breaks the run, so 2-3 is only a run of length 2, too short to count.

## Why the Obvious Way Is Slow

The obvious SQL approach: join the table to itself three times, matching `id`, `id+1`, `id+2`, and check all three rows have `people >= 100`.

```sql
SELECT s1.* FROM Stadium s1, Stadium s2, Stadium s3
WHERE s1.id = s2.id - 1 AND s2.id = s3.id - 1
  AND s1.people >= 100 AND s2.people >= 100 AND s3.people >= 100
```

This works for finding runs of *exactly* 3, but it's a triple self-join — conceptually the database is comparing every combination of 3 rows against every other, which is O(n³) in the naive case. It also gets awkward fast if you need to handle runs *longer* than 3 correctly (a run of 5 needs to have every one of its 5 rows show up in the answer, not just triples).

## The Simple Trick: Look at Your Neighbors, Without a Join

A window function like `LAG`/`LEAD` lets a row "peek" at a nearby row's value **without joining anything** — it's computed once per row, in a single pass over the data (sorted by `id`). If you can see "the value 1 and 2 positions before me" and "1 and 2 positions after me," you have everything you need to know whether *you* are part of a qualifying run — without ever comparing yourself to unrelated rows.

## An Analogy First: Checking If You're in a Conga Line of at Least 3

Imagine everyone at a party is standing in a numbered line, and some people are wearing a party hat (`people >= 100`). You want to find every person who's part of an unbroken stretch of **at least 3 hat-wearers in a row**.

Instead of comparing yourself to every other hat-wearer in the whole room (a self-join), you just need to glance at the **two people immediately behind you** and the **two people immediately ahead of you** in line. If you're wearing a hat, and either: (a) the two people behind you both have hats (you're the *end* of a run), or (b) one person on each side has a hat (you're in the *middle* of a run), or (c) the two people ahead of you both have hats (you're the *start* of a run) — you're definitely part of a run of 3 or more. No need to look any further down the line than that.

## Step-by-Step Example (Narrated)

Using `LAG(people, 1)`, `LAG(people, 2)`, `LEAD(people, 1)`, `LEAD(people, 2)` (all ordered by `id`), here's what each row can see about its two neighbors on each side:

```
id | people | prev2 | prev1 | (self) | next1 | next2
5  |  145   |  150  |   99  |  145   | 1455  |  199
6  | 1455   |   99  |  145  | 1455   |  199  |  188
7  |  199   |  145  | 1455  |  199   |  188  |  NULL
```

---

**Row `id=5`, people=145 (>=100 ✓).** Check the three OR-conditions:
- Ends a run? `prev1(99) >= 100`? No → this condition fails.
- Middle of a run? `prev1(99) >= 100`? No → fails.
- Starts a run? `next1(1455) >= 100` **and** `next2(199) >= 100`? **Yes, both true!** → **row 5 qualifies** (it's the *start* of a run: 5, 6, 7).

---

**Row `id=6`, people=1455 (>=100 ✓).**
- Ends a run? `prev1(145)>=100` and `prev2(99)>=100`? prev2 fails → no.
- Middle of a run? `prev1(145)>=100` **and** `next1(199)>=100`? **Yes, both true!** → **row 6 qualifies** (it's in the *middle*: 5, 6, 7).

---

**Row `id=7`, people=199 (>=100 ✓).**
- Ends a run? `prev1(1455)>=100` **and** `prev2(145)>=100`? **Yes, both true!** → **row 7 qualifies** (it's the *end* of the run: 5, 6, 7 — and it also happens to extend further, since row 8 continues it).

---

Compare that against **row `id=3`, people=150 (>=100 ✓)** — one of the ones that should be *rejected*:
- Ends a run? `prev1(109)>=100` **and** `prev2(NULL)>=100`? `prev2` is `NULL` (there's no row before id=1) → this comparison is never true → fails.
- Middle of a run? `prev1(109)>=100` **and** `next1(99)>=100`? `next1` is 99, which is `< 100` → fails.
- Starts a run? `next1(99)>=100` **and** `next2(145)>=100`? `next1` fails again → fails.

All three conditions fail — **row 3 correctly does not qualify**, even though `people=150` on its own looks fine. It's isolated between id=1 (10, too low) and id=4 (99, too low), so its "run" is only length 1.

### The one detail that's easy to miss: the "ends/middle/starts" conditions are deliberately overlapping

Notice row 7 satisfied **both** the "ends" and would-be "middle" conditions (since the run actually continues to row 8). That's fine — the query only needs **at least one** condition to be true (it's an `OR`), so a row in the interior of a long run can trivially satisfy several of them at once. The three conditions together guarantee that *every* row in *any* run of length ≥ 3 gets caught by at least one of them.

## Plain-English Walkthrough

1. For every row, compute what its 2 neighbors on each side look like (`LAG`/`LEAD`), sorted by `id`.
2. Keep only rows where `people >= 100` to begin with.
3. Among those, keep a row if: its 2 predecessors both qualify (it ends a run), OR it has one qualifying neighbor on each side (it's in the middle), OR its 2 successors both qualify (it starts a run).
4. Any row satisfying at least one of those three is part of some run of length ≥ 3.

## Simple SQL

```sql
WITH flagged AS (
  SELECT id, visit_date, people,
    LAG(people, 1) OVER (ORDER BY id) AS prev1,
    LAG(people, 2) OVER (ORDER BY id) AS prev2,
    LEAD(people, 1) OVER (ORDER BY id) AS next1,
    LEAD(people, 2) OVER (ORDER BY id) AS next2
  FROM Stadium
)
SELECT id, visit_date, people
FROM flagged
WHERE people >= 100
  AND ( (prev1 >= 100 AND prev2 >= 100)
     OR (prev1 >= 100 AND next1 >= 100)
     OR (next1 >= 100 AND next2 >= 100) )
ORDER BY visit_date ASC;
```

## Why Does `NULL >= 100` Just Silently Fail Instead of Erroring?

In SQL, comparing anything to `NULL` (an unknown value) produces `NULL`, not `True` or `False` — and `WHERE`/`AND`/`OR` treat `NULL` as "not true," so the row is filtered out rather than crashing. This is exactly what we want at the edges of the table: row 1 has no `prev1`/`prev2` at all, and those comparisons naturally evaluate to "not true" instead of needing a special-case `IS NOT NULL` check everywhere.

## Complexity

- **Time:** roughly O(n log n) — dominated by the sort implied by `ORDER BY id` inside the window function; the actual `LAG`/`LEAD` computation is a single linear pass once sorted.
- The naive triple self-join, by contrast, is conceptually O(n³) before the query planner optimizes it.

## The Reusable Pattern

This is the **"window function replaces self-join"** pattern for comparing a row to its neighbors:
- Any "detect a run/streak of N consecutive qualifying rows" query
- Month-over-month or day-over-day change calculations (`LAG` the previous period's value)
- Ranking within groups (`ROW_NUMBER() OVER (PARTITION BY ...)`)

Core idea: whenever you need to compare a row to nearby rows in a **single pass over sorted data**, a window function computes that comparison once per row — instead of a self-join, which conceptually re-derives the same "who's near me" relationship independently for every candidate pair (or triple).

---

## The Other Parts of This Screen (Brief)

- **Duplicate EmployeeIDs:** `GROUP BY EmpID HAVING COUNT(*) > 1` — the standard "find duplicates" idiom. `HAVING` filters on the *aggregate* (`COUNT(*)`), which `WHERE` can't do, because grouping hasn't happened yet when `WHERE` runs.
- **DAU / MAU:** `COUNT(DISTINCT user_id)` grouped by day (or by month, via a date-truncation function like `DATE_TRUNC`) — counting distinct users per time bucket.
- **Star Schema:** split the flat file into one **fact table** (one row per sale, holding foreign keys + measures like `sale_amt`) and one **dimension table** per real-world entity (customer, product, store, date) — designed around the query patterns you were shown, not the shape of the incoming file.
- **Weekly Aggregation:** the example output implies ISO weeks (Monday start) — `date - timedelta(days=date.weekday())` finds the Monday of any date's week; group by that anchor.
- **Character Frequency:** `collections.Counter(c for c in s if 'a' <= c <= 'z')` — a one-line frequency tally over the lowercase letters.
