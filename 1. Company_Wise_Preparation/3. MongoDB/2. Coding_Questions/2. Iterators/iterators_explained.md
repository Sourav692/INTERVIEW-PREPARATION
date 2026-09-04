# Iterators — Explained Simply

## The Problem

You are handed two **iterators**. Each one hands you numbers in increasing order. Build a thing that hands back all of those numbers, still in increasing order — using only a **constant** amount of extra memory.

```
A = 1, 3, 5
B = 2, 3, 8

you must produce:  1, 2, 3, 3, 5, 8
```

And you may **not** dump everything into a list first.

## First: What Is an Iterator?

An iterator is a source you can only ask one thing: **"what's next?"**

```
next(it)   ->  1
next(it)   ->  3
next(it)   ->  5
next(it)   ->  StopIteration    (nothing left)
```

Two properties make this problem what it is:

1. **It's lazy.** Nothing exists until you ask for it. An iterator over a 500 GB log file, or over an infinite sequence, costs almost no memory.
2. **You cannot peek.** There is no "show me the next value but don't take it". Asking *is* taking. Once you call `next()`, that value is out and it's yours to keep track of.

That second point is the whole design constraint.

## Why the Obvious Way Is Wrong

The obvious thing:

```
everything = sorted(list(A) + list(B))
```

It gives the right answer. But it:

- **stores every element** — that's O(m+n) memory, and the problem said constant;
- **does all the work up front** — if either iterator is infinite, this hangs forever;
- **sorts data that was already sorted** — pure wasted work.

## The Simple Trick: Hold One Value From Each

Here is the observation that makes constant space possible:

> Both lists are **already sorted**. So the smallest number you haven't emitted yet is sitting at the **front** of one of them. It can't be hiding in the middle — everything in the middle is bigger.

So you never need to look at more than **two numbers at a time**: the front of A and the front of B. Compare them, emit the smaller, and pull a fresh number from *only* the list you took from.

Since you can't peek, you have to pull those two front values out and **hold them in variables**. Those two variables are your entire memory footprint — two numbers, forever, whether the iterators have 6 elements or 6 billion.

## An Analogy First: Two Queues at One Ticket Window

Picture two lines of people, and in each line everyone is already sorted by age, youngest at the front. You have to admit everybody through one door, youngest first overall.

You do **not** need to know everyone's age. You just look at **the two people at the front** and wave in the younger one. That person leaves, the next person in that line steps forward, and you look again.

You never memorise the crowd. You only ever look at two faces. That's constant space.

And when one line empties out? Stop comparing — just wave the other line through one by one.

## Step-by-Step Example (Narrated)

`A = 1, 3, 5` and `B = 2, 3, 8`.

**Setup.** Pull one value from each and hold it. (You must do this eagerly — there's no peek.)

```
head_A = 1        head_B = 2
```

---

**`next()`** — Compare `1` vs `2`. A is smaller → **emit 1**, and pull a fresh value from **A only**.

```
head_A = 3        head_B = 2        emitted: 1
```

Notice B was untouched. Its `2` is still waiting.

---

**`next()`** — Compare `3` vs `2`. B is smaller → **emit 2**, pull from **B only**.

```
head_A = 3        head_B = 3        emitted: 1, 2
```

---

**`next()`** — Compare `3` vs `3`. A **tie**. We use `<=`, so A wins → **emit 3**, pull from **A only**.

```
head_A = 5        head_B = 3        emitted: 1, 2, 3
```

> The tie rule is arbitrary but must be *fixed*. Using `<=` means "when equal, take from A". This makes the output deterministic, and if the values carry extra data, A's copy consistently comes out first — a **stable** merge.

---

**`next()`** — Compare `5` vs `3`. B is smaller → **emit 3**, pull from **B only**.

```
head_A = 5        head_B = 8        emitted: 1, 2, 3, 3
```

---

**`next()`** — Compare `5` vs `8`. A is smaller → **emit 5**, pull from A. But A is empty now! `next()` raises `StopIteration`, so we flip a flag: **A is dead**.

```
head_A = (dead)   head_B = 8        emitted: 1, 2, 3, 3, 5
```

---

**`next()`** — A is dead, so there's nothing to compare. Just **emit 8** and pull from B — which is now also empty. **B is dead.**

```
emitted: 1, 2, 3, 3, 5, 8   ✅
```

---

**`hasNext()`** — both flags are dead → `False`. Done.

## Why the "Dead" Flags Matter

When an iterator runs dry you need *some* way to remember it. Two tempting shortcuts are both bugs:

- **Use `None` as "empty".** Breaks the moment a real value is `None`, and `None < 5` raises a `TypeError` in Python 3.
- **Use `float('inf')` as "empty".** Feels clever — infinity always loses the comparison. But it silently breaks if your data contains infinity, and it doesn't work at all for strings or objects.

A separate boolean per iterator is unambiguous and works for any value type. And once one flag is dead, the live iterator is simply **drained** with no comparisons at all.

## The Follow-Up: What About *n* Iterators?

Now you have 10, or 1,000, lines at the ticket window.

The same idea still works — hold one head per line, emit the smallest. But "find the smallest of n heads" now means **scanning all n of them, for every single person you admit**. With 1,000 lines and a million people, that's a billion comparisons.

### The fix: a min-heap

A **min-heap** (Python: `heapq`) is a container with one job: *always know which item is smallest*. Looking at the smallest is instant; adding an item or removing the smallest costs about `log n` steps instead of `n`.

The crucial difference is that a heap **remembers**. The linear scan throws away everything it learned and starts over each round. The heap keeps the ordering work it already did.

So instead of n variables, you keep a heap of pairs:

```
heap = [ (value, which_iterator_it_came_from), ... ]
```

Each `next()`:

1. **Pop** the smallest pair — that's your answer.
2. Pull the next value from **that same** iterator and **push** it back in.

```
iterators:  A = 1,3,5      B = 2,3,8      C = 4,6

seed heap:  [(1,A), (2,B), (4,C)]

pop (1,A) -> emit 1, push (3,A)   heap: [(2,B), (3,A), (4,C)]
pop (2,B) -> emit 2, push (3,B)   heap: [(3,A), (3,B), (4,C)]
pop (3,A) -> emit 3, push (5,A)   heap: [(3,B), (4,C), (5,A)]
pop (3,B) -> emit 3, push (8,B)   heap: [(4,C), (5,A), (8,B)]
...
```

The heap **never holds more than one entry per iterator**, because you only push after you pop. That's what keeps memory at O(n) — the number of *streams*, not the number of *elements*.

### Why store the iterator index in the pair?

Two reasons, and both matter:

1. **You need to know which iterator to refill** after popping. The index tells you.
2. **It breaks ties safely.** When two values are equal, Python moves on to compare the second slot of the tuple. If that second slot were the raw data instead of an integer, Python would try `some_object < some_other_object` and could crash with `TypeError`. An integer index always compares cleanly.

## Why It's Fast

| Approach | Space | Per `next()` |
|---|---|---|
| Drain everything and sort | O(m+n) ❌ | O(1) but O((m+n) log(m+n)) up front |
| Two heads (2 iterators) | **O(1)** ✅ | **O(1)** |
| Scan all heads (n iterators) | O(n) | O(n) |
| Min-heap (n iterators) | O(n) | **O(log n)** |

The benchmark in the notebook makes this concrete: as the number of iterators doubles, the scan version's time roughly **doubles**, while the heap version barely moves.

## Common Mistakes

- **Trying to peek.** There's no `peek()` on an iterator. Pull the value out and hold it — that buffered value *is* your peek.
- **Advancing both iterators after a comparison.** You only consumed one value, so you only refill one. Advancing both silently drops elements.
- **Using `<` instead of `<=` and never deciding the tie rule.** Both work, but pick one and say why. `<=` keeps the merge stable.
- **Forgetting the empty-iterator case in the constructor.** If an iterator is empty from the start, that first eager `next()` raises immediately — catch it and mark it dead, don't let it escape.
- **Pushing to the heap before popping.** The heap only stays at size n if you pop first, then push the replacement. Do it in the wrong order and it grows.
- **Calling `hasNext()` on an infinite iterator and expecting it to end.** It won't. That's correct behaviour — the caller has to stop.

## The Takeaway

> When your inputs are already sorted, the answer is always at the **front** of one of them. Buffer one value per input, emit the smallest, and refill only what you consumed. When there are many inputs, let a **min-heap** answer "which front is smallest?" so you stop re-scanning what you already know.

This is the merge step of merge sort, the shape of `heapq.merge`, and exactly how a database merges sorted index scans or an LSM-tree merges its sorted levels.
