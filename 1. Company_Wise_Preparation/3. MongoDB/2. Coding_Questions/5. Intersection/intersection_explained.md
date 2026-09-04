# Intersection of Two Arrays — Explained Simply

## The Problem

Given two lists of numbers, return the values that appear in **both** — each one listed only **once**, in any order.

```
nums1 = [1, 2, 2, 1]
nums2 = [2, 2]
answer = [2]                 # not [2, 2] - each value once

nums1 = [4, 9, 5]
nums2 = [9, 4, 9, 8, 4]
answer = [9, 4]              # or [4, 9] - order doesn't matter
```

## Why the Obvious Way Is Slow

The obvious approach reads exactly like the problem statement: for each number in the first list, look through the second list to see if it's there.

```
for v in nums1:
    for w in nums2:
        if v == w:
            ...
```

It works. But look at what it's doing: it reads **all** of `nums2`, from the beginning, **for every single element** of `nums1` — even though `nums2` never changes between passes.

With 1,000 elements in each list, that's up to **1,000,000 comparisons**. Double the lists to 2,000 each and it becomes 4,000,000 — **four times** the work for twice the data. That's what "quadratic" means, and it's why this approach dies on real data.

## The Simple Trick: Read One List Once, Then Never Again

The wasted work is re-reading `nums2` over and over. So don't. Read it **once** and store it in a form that answers "is this value in here?" instantly.

That form is a **set**.

```
seen = set(nums1)            # one pass. now membership is instant

for v in nums2:              # one pass
    if v in seen:            # instant - no scanning
        result.add(v)
```

Two passes total instead of a thousand. The work went from `n × m` to `n + m`.

## What Is a Set, and Why Is It Instant?

A **list** stores things in a row. To find something, you have to walk along and compare — that's the scanning.

A **set** doesn't search. It runs the value through a **hash function** — a bit of arithmetic that turns the value into a number — and that number *is* the address where the value lives. So checking "is 9 in here?" means: compute the address for 9, look at that one spot, done. It never touches anything else.

Two more properties matter here:

- **A set holds no duplicates.** Adding `2` to a set that already contains `2` does nothing. That's the "each element must be unique" requirement, handled for free.
- **It's *average* O(1), not guaranteed.** If many values hashed to the same address you'd be back to scanning. This effectively never happens with ordinary integers, but saying it aloud in an interview shows you understand the structure rather than just its API.

## An Analogy First: The Guest List

You're on the door at a party. 1,000 people are on the guest list. 1,000 people show up.

**The slow way:** for each person who arrives, start at the top of a paper list and read down until you find their name or reach the bottom. A million lines of reading over the night, and the queue stretches around the block.

**The fast way:** before anyone arrives, spend a few minutes writing every name onto index cards filed alphabetically in a box. Now each arrival costs one flip to their letter. A thousand quick lookups.

Two things worth noticing:

- You did **extra work up front** (building the box) to make every later question cheap. That's the space-for-time trade, and it only pays off because you ask the question many times.
- You'd naturally build the box from the **shorter** of the two lists. Same result either way, but a smaller box is less to carry.

## Step-by-Step Example (Narrated)

`nums1 = [4, 9, 5]`, `nums2 = [9, 4, 9, 8, 4]`.

**Setup.** `nums1` is shorter, so build the set from it:

```
seen = {4, 5, 9}
result = {}          (empty set)
```

Now walk `nums2` **once**, left to right.

---

**See `9`** — is 9 in `seen`? Yes. Add it to the result.
`result = {9}`

---

**See `4`** — is 4 in `seen`? Yes. Add it.
`result = {9, 4}`

---

**See `9` again** — yes, it's in `seen`. Add it... but `9` is **already in `result`**, and a set silently absorbs the repeat.
`result = {9, 4}` — unchanged. ✅

*This is the uniqueness requirement being handled by the data structure, with no extra code.*

---

**See `8`** — is 8 in `seen`? No. Skip.
`result = {9, 4}`

---

**See `4` again** — yes, but already recorded. Absorbed.
`result = {9, 4}`

---

**Done.** Convert to a list: **`[9, 4]`** ✅

Total work: 3 insertions to build the set, then 5 lookups. **Eight steps** instead of fifteen comparisons — and unlike the naive version, doubling the input only doubles this.

## The Other Good Answer: Two Pointers

There's a second approach worth knowing, because it's **better** in one specific situation.

If both lists are **sorted**, you can walk one finger along each:

```
a = [4, 5, 9]           b = [4, 4, 8, 9, 9]
    ^                       ^
```

At each step, compare the two values your fingers are on:

- **Equal?** It's a match — record it, then slide both fingers past every copy of that value.
- **Left is smaller?** It can never match anything ahead (everything ahead in `b` is bigger), so move the left finger forward.
- **Right is smaller?** Move the right finger forward.

Each finger only ever moves forward, so the whole walk takes `n + m` steps.

**Why bother, if the set is just as fast?** Because this uses **no extra memory at all**. The set approach needs room for up to 1,000 values; two pointers needs room for two numbers.

So the rule is:

| Situation | Best approach |
|---|---|
| Unsorted input | **Hash set** — O(n+m) time, O(n) space |
| Already sorted | **Two pointers** — O(n+m) time, **O(1) space** |
| Too big for memory | **Two pointers**, streaming from disk |

If you have to sort the data yourself first, sorting costs O(n log n) — slower than the set. So two pointers wins only when sortedness is *given* to you, or when memory is the binding constraint.

## The Common Follow-Up: What If Duplicates Should Count?

A very common variant: `[1, 1, 1]` and `[1, 1]` should return `[1, 1]` — two copies, because that's the **smaller** of the two counts.

A set can't do this. The moment you build a set, you've **thrown the counts away** — `{1}` doesn't remember there were three.

The fix is a **counter** (a dictionary of value → how many times it appears):

```
counts = Counter([1, 1, 1])       # {1: 3}

for v in [1, 1]:
    if counts[v] > 0:
        result.append(v)
        counts[v] -= 1            # spend one from the budget
```

Think of `counts` as a **budget**. `nums1` had three 1s, so you may report a 1 up to three times. `nums2` only offers two, so you spend two and stop.

> **The rule of thumb:** if the question says *"which values"*, use a set. If it says *"how many"*, use a counter. Spotting which one is being asked is half the problem.

## Why It's Fast

The notebook benchmark, with both arrays doubling in size:

| n | Nested scan | Two pointers | Hash set |
|---|---|---|---|
| 500 | 4.8 ms | 0.18 ms | 0.03 ms |
| 1,000 | 19.5 ms | 0.38 ms | 0.07 ms |
| 2,000 | 79.3 ms | 0.85 ms | 0.13 ms |
| 4,000 | 319.9 ms | 1.69 ms | 0.27 ms |

Look at the *ratios*, not the absolute numbers. The nested scan multiplies by **4** each time (quadratic). The other two multiply by **2** (linear). By n = 4,000 the hash set is over a thousand times faster, and the gap keeps widening.

## Common Mistakes

- **Collecting into a list and deduplicating afterwards.** Works, but it's extra code doing a job the set already does. Worse, `if v in result` on a *list* is itself a linear scan — you've quietly reintroduced the slowness you were trying to remove.
- **Returning a set instead of a list.** The problem asks for an array. Convert it.
- **Sorting when you didn't need to.** Sorting costs O(n log n), which is *worse* than the hash set's O(n + m). Only reach for two pointers when the input is already sorted or memory is tight.
- **Building the set from the bigger array.** Same speed, but needlessly more memory. Check the lengths first — one line.
- **Mutating the caller's input.** If you sort, sort a **copy**. Silently reordering someone's list is a nasty surprise.
- **Using a set when the question wanted counts.** Re-read the spec: "unique" → set; "minimum occurrence count" → `Counter`.

## The Takeaway

> When you find yourself scanning the same collection over and over, **preprocess it once** into a structure that answers the question instantly. A hash set turns "is X in here?" from a walk into a single lookup — and, as a bonus, enforces uniqueness for you.

The same move shows up everywhere: two-sum, finding duplicates, detecting cycles, and the posting lists inside a search index.
