# Data Engineer Questions

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Data Engineering, Databases, SQL · **Difficulty/Frequency:** Common (5/10)

*This is a multi-part screen covering SQL, data modeling, and Python coding tasks.*

---

## Problem Statement

### SQL Part 1 — Stadium Consecutive IDs

**Table: Stadium**

| Column Name | Type |
|---|---|
| id | int |
| visit_date | date |
| people | int |

`visit_date` is the primary key. As `id` increases, `visit_date` increases.

**Goal:** Display records where there are 3 or more consecutive ids, each with `people >= 100`. Return ordered by `visit_date ASC`.

**Example Input**

| id | visit_date | people |
|---|---|---|
| 1 | 2017-01-01 | 10 |
| 2 | 2017-01-02 | 109 |
| 3 | 2017-01-03 | 150 |
| 4 | 2017-01-04 | 99 |
| 5 | 2017-01-05 | 145 |
| 6 | 2017-01-06 | 1455 |
| 7 | 2017-01-07 | 199 |
| 8 | 2017-01-09 | 188 |

**Example Output**

| id | visit_date | people |
|---|---|---|
| 5 | 2017-01-05 | 145 |
| 6 | 2017-01-06 | 1455 |
| 7 | 2017-01-07 | 199 |
| 8 | 2017-01-09 | 188 |

Explanation: Rows 5, 6, 7, 8 have consecutive IDs and all have `people >= 100`.

### SQL Part 2 — Duplicate EmployeeIDs

**Employee Table**

| EmpID | Name | Salary | Department |
|---|---|---|---|
| 101 | Prakash | 1200 | IT |
| 102 | Jackie | 1100 | Sales |
| 102 | Jackie | 1200 | Sales |

Write a query to return all EmployeeIDs that are duplicated.

### SQL Part 3 — DAU / MAU Query

Data fields: `date` (YYYY-MM-DD), `user_id` (int), `activity_type` (login | view | click | logout), `timestamp`.

Write SQL to compute:
- DAU = count of distinct active users per day
- MAU = count of distinct active users per month

### Data Modeling Question

Given flat-file fields: `cust_id`, `cust_name`, `cust_address`, `sale_amt`, `sale_qty`, `product`, `product_family`, `date`, `time_of_transaction`, `mode_of_transaction`, `store_id`, `store_location`.

Example user queries:
- What is the total sales from each store?
- How many distinct customers came to our stores?
- Top grossing product by sales?

**Question:** How would you design database tables to efficiently support these queries?

### Coding Part 1 — Weekly Aggregation

Given a list of sequential timestamps, group them by 7-day windows.

```python
ts = [
    '2019-01-01',
    '2019-01-02',
    '2019-01-08',
    '2019-02-01',
    '2019-02-02',
    '2019-02-05',
]

weekly_aggregation(ts)
# -> [
#     ['2019-01-01', '2019-01-02'],
#     ['2019-01-08'],
#     ['2019-02-01', '2019-02-02'],
#     ['2019-02-05'],
# ]
```

### Coding Part 2 — Character Frequency Counter

Given a string, count character frequency for lowercase a–z.

```python
test_string = "hellowhatisyourname"
# ->
{
    'h': 2, 'e': 2, 'l': 2, 'o': 2, 'w': 1, 'a': 2, 't': 1,
    'i': 1, 's': 1, 'y': 1, 'u': 1, 'r': 1, 'n': 1, 'm': 1
}
```

---

## Study Tools

### Hint 1

For the SQL consecutive-IDs problem, think about comparing each row with its neighbors using window functions like `LAG()` and `LEAD()` — you can check the row before and after in one pass.

### Hint 2

The data modeling question hinges on normalization: separate the transactional grain (one row per sale line item) from dimension tables like customer, product, and store, then link them with foreign keys.

### Hint 3

For weekly aggregation, anchor each timestamp to its week using `date - timedelta(days=date.weekday())` to get the Monday of that week, then group by that anchor while preserving input order.

---

### Answer

This is a multi-part data engineering screen covering SQL window functions, duplicate detection, DAU/MAU computation, star-schema data modeling, and two Python coding tasks.

#### SQL: Consecutive IDs with people >= 100

Use `LAG()` and `LEAD()` to check the previous and next rows ordered by `id`. A row is part of a valid group if it and at least one neighbor (previous or next) both have `people >= 100`. Since the problem guarantees `id` increases with `visit_date`, ordering by `id` and checking `people >= 100` for three consecutive rows is sufficient.

```sql
WITH flagged AS (
  SELECT
    id,
    visit_date,
    people,
    LAG(people, 1) OVER (ORDER BY id) AS prev1_people,
    LAG(people, 2) OVER (ORDER BY id) AS prev2_people,
    LEAD(people, 1) OVER (ORDER BY id) AS next1_people,
    LEAD(people, 2) OVER (ORDER BY id) AS next2_people
  FROM Stadium
)
SELECT id, visit_date, people
FROM flagged
WHERE people >= 100
  AND (
    (prev1_people >= 100 AND prev2_people >= 100)   -- current ends a run of 3
    OR
    (prev1_people >= 100 AND next1_people >= 100)   -- current is middle of a run
    OR
    (next1_people >= 100 AND next2_people >= 100)   -- current starts a run of 3
  )
ORDER BY visit_date ASC;
```

This handles runs longer than 3 correctly: every row in a run of length ≥3 will satisfy at least one of the three conditions. A run of exactly 3 has all three rows matching (first row matches the third condition, middle row matches the second, last row matches the first). A run of 4+ has interior rows matching the middle condition and boundary rows matching the edge conditions.

#### SQL: Duplicate EmployeeIDs

```sql
SELECT EmpID
FROM Employee
GROUP BY EmpID
HAVING COUNT(*) > 1;
```

This returns `102` from the example since it appears twice. If you need all duplicate rows, wrap it in a subquery or use a window function.

#### SQL: DAU / MAU

```sql
-- DAU
SELECT date, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY date
ORDER BY date;

-- MAU
SELECT
  DATE_TRUNC('month', date) AS month,
  COUNT(DISTINCT user_id) AS mau
FROM events
GROUP BY DATE_TRUNC('month', date)
ORDER BY month;
```

`DATE_TRUNC` is PostgreSQL syntax; in MySQL you'd use `DATE_FORMAT(date, '%Y-%m-01')`, and in SQL Server `DATEFROMPARTS(YEAR(date), MONTH(date), 1)`. The key is counting distinct `user_id` per time bucket.

#### Data Modeling

This is a classic star schema. The flat file is at the transaction line-item grain. Split it into a fact table and dimension tables.

```sql
-- Dimension tables
CREATE TABLE dim_customer (
  cust_id INT PRIMARY KEY,
  cust_name VARCHAR(255),
  cust_address VARCHAR(500)
);

CREATE TABLE dim_product (
  product_id INT PRIMARY KEY,
  product_name VARCHAR(255),
  product_family VARCHAR(100)
);

CREATE TABLE dim_store (
  store_id INT PRIMARY KEY,
  store_location VARCHAR(500)
);

CREATE TABLE dim_date (
  date_id INT PRIMARY KEY,
  full_date DATE,
  year INT,
  month INT,
  day INT,
  day_of_week INT
);

-- Fact table
CREATE TABLE fact_sales (
  sale_id INT PRIMARY KEY,
  cust_id INT REFERENCES dim_customer(cust_id),
  product_id INT REFERENCES dim_product(product_id),
  store_id INT REFERENCES dim_store(store_id),
  date_id INT REFERENCES dim_date(date_id),
  sale_amt DECIMAL(12, 2),
  sale_qty INT,
  time_of_transaction TIME,
  mode_of_transaction VARCHAR(50)
);
```

This supports all three queries efficiently:

- Total sales per store: `SELECT store_id, SUM(sale_amt) FROM fact_sales GROUP BY store_id` — joins to `dim_store` if you need location names.
- Distinct customers: `SELECT COUNT(DISTINCT cust_id) FROM fact_sales`
- Top grossing product: `SELECT product_id, SUM(sale_amt) AS total FROM fact_sales GROUP BY product_id ORDER BY total DESC LIMIT 1`

#### Coding: Weekly Aggregation

The question is ambiguous about week boundaries. The most standard interpretation: group by ISO week (Monday as week start), preserving the order of first appearance of each week in the input.

```python
from datetime import datetime, timedelta

def weekly_aggregation(ts):
    """Group timestamps by ISO week (Monday as week start).
    Preserves order of first appearance of each week."""
    dates = [datetime.strptime(t, '%Y-%m-%d') for t in ts]
    groups = {}
    order = []

    for d in dates:
        # Monday of the current week
        week_start = d - timedelta(days=d.weekday())
        key = week_start.strftime('%Y-%m-%d')
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(d.strftime('%Y-%m-%d'))

    return [groups[k] for k in order]
```

**Time:** O(n) — one pass over the timestamps, each `strftime`/`strptime` is O(1). **Space:** O(n) — the `groups` dict stores all timestamps.

This produces the expected output: `'2019-01-01'` and `'2019-01-02'` are in the week starting `'2018-12-31'` (Monday), `'2019-01-08'` is in the week starting `'2019-01-07'`, `'2019-02-01'` and `'2019-02-02'` are in the week starting `'2019-01-28'`, and `'2019-02-05'` is in the week starting `'2019-02-04'`.

#### Coding: Character Frequency Counter

```python
from collections import Counter

def char_frequency(s):
    """Count frequency of lowercase a-z characters."""
    return dict(Counter(c for c in s if 'a' <= c <= 'z'))
```

**Time:** O(n) — single pass over the string. **Space:** O(1) — at most 26 keys in the result dict.

If you want to avoid `Counter` and be explicit:

```python
def char_frequency(s):
    freq = {}
    for c in s:
        if 'a' <= c <= 'z':
            freq[c] = freq.get(c, 0) + 1
    return freq
```

Both produce `{'h': 2, 'e': 2, 'l': 2, 'o': 2, 'w': 1, 'a': 2, 't': 1, 'i': 1, 's': 1, 'y': 1, 'u': 1, 'r': 1, 'n': 1, 'm': 1}` for the example input.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

This is a multi-part screen, so let's work through each piece the way you'd approach it live.

**SQL: Consecutive IDs.** Start with the naive approach: self-join the table three times on `id`, `id+1`, `id+2` and filter where all three have `people >= 100`. That works but is O(n³) with a triple join and gets ugly. The interviewer will ask if you can do better. The insight is that you need to look at each row's neighbors. Window functions let you do this in a single pass. `LAG(people, 1)` gives you the previous row's `people`, `LEAD(people, 1)` the next. A row is part of a valid streak if it and the two rows before it all have `people >= 100`, or it and the two rows after it all have `people >= 100`, or it has one qualifying neighbor on each side. You need `LAG` with offset 2 and `LEAD` with offset 2 to check the "two before" and "two after" conditions. The middle condition only needs offset 1 on each side.

**SQL: Duplicate EmployeeIDs.** `GROUP BY EmpID HAVING COUNT(*) > 1` is the canonical answer. If they ask for all columns of duplicate rows, you'd use `ROW_NUMBER() OVER (PARTITION BY EmpID ORDER BY EmpID)` and filter where `rn > 1`.

**SQL: DAU / MAU.** DAU is straightforward: `GROUP BY date` with `COUNT(DISTINCT user_id)`. MAU needs a month bucket. The trick is knowing your SQL dialect's date truncation function. In PostgreSQL it's `DATE_TRUNC('month', date)`, in MySQL `DATE_FORMAT(date, '%Y-%m-01')`, in SQL Server `DATEFROMPARTS(YEAR(date), MONTH(date), 1)`. Pick one and state it clearly.

**Data Modeling.** Think about what queries need to be fast. All three example queries aggregate by a dimension (store, customer, product), so a star schema with a central fact table and dimension tables is the natural fit. The fact table is at the granularity of one sale line item. `cust_id`, `product_id`, `store_id`, and `date_id` are foreign keys to dimension tables. `sale_amt` and `sale_qty` are measures. The `dim_date` table pre-computes year, month, day for fast grouping without date functions.

**Coding: Weekly Aggregation.** The key decision is how to define a "7-day window." The example output shows `'2019-01-01'` and `'2019-01-02'` grouped together, and `'2019-01-08'` separate. That's consistent with ISO weeks starting on Monday: Jan 1, 2019 is a Tuesday, so its week starts Dec 31, 2018. Jan 8 is a Tuesday, so its week starts Jan 7. The gap of 6 days between Jan 2 and Jan 8 crosses a week boundary. If you instead used a rolling 7-day window anchored at the first timestamp, you'd get `['2019-01-01', '2019-01-02', '2019-01-08']` all in one group since Jan 8 is exactly 7 days after Jan 1. The example output rules that out. So ISO weeks it is. Python's `datetime.weekday()` returns 0 for Monday, so subtracting `timedelta(days=d.weekday())` gives you the Monday of that week. Group by that anchor.

**Coding: Character Frequency.** `Counter` from `collections` is the idiomatic answer. Filter to lowercase a-z with a simple range check. If they ask you to implement it manually, a dict with `get(c, 0) + 1` is the cleanest.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State your SQL dialect assumptions** — `DATE_TRUNC` vs `DATE_FORMAT` vs `DATEFROMPARTS` differs across databases. Saying "in PostgreSQL I'd write..." shows you know the ecosystem, and the interviewer can redirect if their stack differs.
- **Explain why the window function approach is correct for runs longer than 3** — a run of 5 consecutive qualifying rows has its first row matching the "two after" condition, its last row matching the "two before" condition, and the three interior rows matching the "one on each side" condition. Walk through this explicitly.
- **Justify the star schema with query patterns** — the three example queries all aggregate by a single dimension, which is exactly what star schemas optimize for. Mention that a snowflake schema would normalize `product_family` into its own table if the family has attributes beyond a name.
- **Nail the week boundary definition before coding** — the weekly aggregation problem is ambiguous. Ask whether weeks start on Monday or Sunday, and whether the first timestamp anchors a rolling window. The example output implies ISO weeks, so state that assumption and code against it.
- **Use `Counter` but be ready to implement it manually** — `Counter` is the right tool, but the interviewer may ask what it does under the hood. Knowing it's a dict subclass with `__missing__` returning 0 shows depth.
- **For the consecutive IDs SQL, mention the alternative self-join approach** — a triple self-join on `s1.id = s2.id - 1 AND s2.id = s3.id - 1` works but is O(n³). Mentioning it and then improving to O(n) with window functions demonstrates algorithmic thinking in SQL.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you modify the consecutive IDs query to return the start and end of each qualifying streak instead of individual rows?** — Think about using `ROW_NUMBER()` and subtracting from `id` to assign a group ID to each streak.
- **How would you compute DAU/MAU ratio (stickiness) as a single query?** — Join the DAU and MAU subqueries on month and divide.
- **What if the flat file has 10 billion rows and you need to run these queries in under 100ms?** — Consider columnar storage, pre-aggregation, partitioning by date, and materialized views.
- **How would you handle the weekly aggregation if timestamps include time components and span multiple timezones?** — Normalize to UTC first, decide on a timezone for week boundaries, and truncate to date before computing the week anchor.
- **How would you extend the character frequency counter to handle Unicode efficiently?** — Use a dict with `ord(c)` as the key or `collections.Counter` directly, since Unicode has too many code points for a fixed-size array.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
