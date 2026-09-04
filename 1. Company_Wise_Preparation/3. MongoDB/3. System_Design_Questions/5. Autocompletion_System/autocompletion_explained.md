# Autocompletion System — Explained Simply

## The Problem

100 million phrases. Someone types `"mon"`. Return the 5 most popular completions in under 100 milliseconds, 6,000 times a second, while popularity keeps shifting under you.

## An Analogy First: The Library Index Card

Picture a library with 100 million book titles.

**The naive version:** someone asks for titles starting with "mon". A librarian walks the shelves reading every spine. Correct, hopeless.

**Slightly better:** the shelves are alphabetical. Now they can jump straight to the "mon" section — but the section holds 400,000 titles and the question was *"which five are most borrowed?"*. Alphabetical order tells you nothing about popularity, so they still read all 400,000.

**The real version:** at the end of every aisle, and every sub-aisle, someone has pinned **a card listing the five most-borrowed books down that way.**

Walk to the "mon" aisle. Read the card. Done — three steps and a glance, no matter how many books are behind it.

That's the whole design. And it immediately raises the question the source answer never quite answers: **who updates the cards, and what happens when a book becomes *less* popular?**

## The Real Problem: Two Orderings That Fight

| | Needs data ordered by | |
|---|---|---|
| **Prefix matching** | lexicographically | `mon…` are adjacent |
| **Top-k ranking** | by score | most popular first |

Sort by one and you destroy the other. That's why:

- **Sorted list + binary search:** finds the prefix range in O(log N), then must scan the whole range to rank it. Prefix `"a"` matches 5M phrases.
- **Sorted by score:** top-k is trivial, finding the prefix is a full scan.

**A trie solves navigation. Precomputed top-k lists solve ranking. Neither alone is enough.**

## The Trie, Concretely

Corpus: `mongodb` (900), `monday` (500), `money` (700). k=2.

```
        root                        Each node stores the best 2 BELOW it:
         │
         m   [mongodb 900, money 700]
         │
         o   [mongodb 900, money 700]
         │
         n   [mongodb 900, money 700]
        ╱│╲
       ╱ │ ╲
      d  e  g   d:[monday 500]  e:[money 700]  g:[mongodb 900]
```

Type `"mon"` → three hops → return the card. **The subtree is never walked.** `O(prefix_length + k)`.

The notebook verifies this literally — reading prefix `"mon"` touches exactly 3 nodes, not the 6-phrase subtree.

**The price is write amplification.** A phrase of length L sits in the subtree of exactly L nodes — every prefix of itself — so a score change may touch L lists. You moved ranking from read time to write time.

Is that worth it? 500M queries vs 50M interactions per day:

```
Read:write ratio = 10:1
```

Yes — but note it's **10:1, not the million-to-one** of the access-control problem. The margin is real but not huge, which is exactly why the write path deserves scrutiny.

## The Flaw: Scores Going *Down*

Here's the answer's claim:

> *"At each node, the updater recomputes `top_suggestions` by checking if the updated phrase's new score changes the top-k ordering. **This is O(L × k) per update.**"*

For an **increase**, that's true. `monkey` jumps from 200 to 5,000? Compare against the node's 2 entries, insert if it wins. Everything you need is in the node. The notebook confirms it's correct.

For a **decrease**, it falls apart:

```
DECREASE mongodb 900 -> 100
  Trie says  ['money', 'mongodb']      ← wrong
  Truth is   ['money', 'month']
  Missing    ['month']
```

`month` (650) is genuinely the second-best phrase under `"mon"` now. But node `"mon"` only ever stored 2 entries, and `month` was never one of them. **The correct answer isn't recoverable from what the node holds.** Finding it means walking the subtree — the exact O(subtree) cost the design exists to eliminate.

### And this isn't an edge case — the design guarantees it

Look at the answer's own scoring formula:

```
score = frequency * exp(-lambda * age_in_days)
```

**Every phrase's score decreases with every tick of the clock.** Demotion isn't an exception here; it's the steady state. Stale phrases would sit pinned in every node's list indefinitely.

## Fixing It: Three Attempts, Honestly Measured

### Attempt 1: slack + lazy repair

Store top-`2k`, serve the best k still valid, recompute a node's subtree when its valid count drops below k.

Fixes the single-demotion case. But under *sustained* decay it drifts — and understanding why is the interesting part:

> The repair trigger fires when entries become **invalid**. Decay never invalidates anything — every stored score stays current and correct. A node can hold 2k perfectly valid entries that have all decayed below a phrase that was never in the list, and **nothing signals the problem**.

**Slack fixes deletion. Decay is a different failure and needs a different fix.**

### Attempt 2: make the score monotone

Store raw `frequency` plus a timestamp. Apply decay to the ≤2k candidates **at read time**.

Now stored scores only ever *increase* — precisely the case the O(L × k) update handles correctly. Ageing costs **zero writes**. The notebook ages `mongodb` out of the top-2 without touching the trie at all.

Cost: a sort over ~10 candidates per read. Free next to a network hop.

### Measured, over 400 decay events

| Strategy | Prefixes returning the exact top-k |
|---|---|
| Naive, no slack (as written) | 69.6% |
| Slack 2× + lazy repair | 92.8% |
| Slack 4× + lazy repair | 98.6% |
| Monotone, decay at read | 92.8% |
| Monotone, slack 4× | 98.6% |

Two honest readings of this table:

1. **Slack is what buys accuracy.** At equal slack, monotone scoring *matches* it rather than beating it. What monotone fixes is the write path, not the ranking.
2. **Nothing reaches 100%.** A full rebuild restores it instantly, which tells you what's really going on.

### Attempt 3: admit you need a rebuild

> A precomputed top-k trie under a decaying score **fundamentally requires a periodic full rebuild.** The design choices only decide whether it runs hourly or weekly.

**The answer to give:** "O(L × k) per update, monotone stored scores, decay applied at read, plus a nightly full rebuild — and the rebuild isn't optional."

Claiming O(L × k) with no rebuild is the actual error. The interesting engineering question isn't *whether* you rebuild — it's how much slack and what scoring scheme buy you the longest gap between rebuilds.

## The Memory Numbers Contradict Each Other

| Section | Corpus | Memory | Bytes/phrase |
|---|---|---|---|
| *Scaling and partitioning* | 10M | 10–30 GB | **1,000–3,000** |
| *Capacity numbers* | 100M | 20 GB | **200** |

Ten times the corpus in *less* memory. Both stated confidently.

They're both defensible — for **different implementations**. Modelling three levers reproduces each figure almost exactly:

| Layout | Bytes/node | Per top-k entry | Nodes with a list | Result |
|---|---|---|---|---|
| **Naive** — object + hash map per node, phrase **strings** in the lists | 120 | 36 | 100% | **2,100 B/phrase** → 21 GB at 10M |
| **Compact** — packed child slots, interned phrase **IDs** | 20 | 8 | **20%** | **196 B/phrase** → 19.6 GB at 100M |

That third column is the lever nobody mentions. At ~7 trie nodes per phrase, **a 5-entry list at every node is most of the footprint.** Deep nodes have tiny subtrees — computing their top-k on the fly is cheap. Store precomputed lists only where the subtree is big enough to earn one.

> Layout isn't a detail at this scale. It moves the answer by 10×. Say which one you're building.

## "Roughly 1/26 Per Shard" Is Not True

> *"With first-character sharding on 26 lowercase letters, each shard holds roughly 1/26 of the corpus."*

English first letters are wildly non-uniform:

```
  s   11.35%   2.95x the 1/26 claim
  c    9.70%   2.52x
  p    8.36%   2.17x
  ...
  x    0.10%   0.03x

  Largest : smallest  =  110 : 1
```

You'd provision every shard for **3× the claimed size** and leave most nearly idle. And query traffic is *more* skewed than the corpus, because popular queries cluster.

### The fix keeps the good property

Sharding by prefix is still right — it's what makes every query hit exactly one shard. Just choose the boundaries from the **corpus**, not the alphabet:

```
BALANCED RANGE PARTITIONING (7 SHARDS)
  a-c  (3 letters)  21.78%
  d-f  (3 letters)  14.04%
  g-k  (5 letters)  13.00%
  l-o  (4 letters)  14.34%
  p-r  (3 letters)  13.52%
  s-t  (2 letters)  16.51%
  u-z  (6 letters)   6.81%

  Per-letter shards, imbalance  2.95x
  Balanced ranges, imbalance    1.52x
```

Split `s` further into `sa–sm` / `sn–sz` if it's still hot. A prefix still falls entirely inside one range, so queries stay single-shard.

**And what you must not do:** hash-shard by phrase. It distributes perfectly and destroys prefix locality — every query becomes a scatter-gather across every shard.

## Typos: Layer, Don't Replace

The trie does exact prefix matching. Typo tolerance is a *fallback*, not a redesign:

1. **Try exact first.** Fast, and usually right.
2. **If results are sparse**, query a fuzzy index — bounded edit-distance traversal (distance 1 only; distance 2 explodes), SymSpell, or a character n-gram index.

Running fuzzy matching on every query buys nothing and costs latency on the 95% of queries that were spelled fine.

## Personalization: An Overlay, Not a Per-User Trie

The common mistake is building a trie per user. 10M DAU × a trie is not a plan.

You need a **small per-user overlay** — a map of phrases that user has interacted with — merged with global suggestions at query time, boosting user-specific scores by something like `1 + alpha * interaction_count`.

Active users touch maybe hundreds of distinct phrases. That fits in Redis, or even local memory.

**Notice the shape:** a small hot map layered over a big cold index. The same shape answers the celebrity-spike follow-up — a small in-memory delta map of score bumps, applied at read time, folded into the trie later by the normal pipeline. **When one shape answers two follow-ups, it's probably the right shape.**

## Common Mistakes

- **Describing a trie, then walking the subtree for top-k.** That's missing the entire optimization.
- **Claiming O(L × k) updates with no rebuild cadence.** Only true for increases; decay makes decreases universal.
- **Assuming slack fixes decay.** It fixes deletion. Different failure.
- **Writing decayed scores into the index.** Store frequency, decay at read, and ageing costs nothing.
- **Quoting a memory number without a layout.** 200 B and 3,000 B/phrase are both honest for the same structure.
- **A top-k list at every node.** At 100M phrases that's most of your RAM, for subtrees small enough to scan.
- **"1/26 per letter."** Off by 3× at the top and 100× across the range.
- **Hash-sharding by phrase.** Perfect balance, zero prefix locality, scatter-gather forever.
- **Fuzzy matching on every query.** Latency cost on the queries that didn't need it.
- **A trie per user.** The overlay is the answer.

## The Takeaway

> Prefix needs lexicographic order; top-k needs score order. A trie gives you the first, and a pre-pinned card at every node gives you the second — without either destroying the other.

Three ideas carry it: **precompute at the node, not the answer** (turns O(subtree) into O(k)), **ask what happens when the value goes down** (increases and decreases are not symmetric, and most complexity claims are quietly about increases only), and **shard so a query stays local** (range partitioning preserves the locality that hash partitioning throws away).

And the habit worth stealing: when a design says "O(L × k) per update," **run a decrease through it.** The read path was fine. The write path was only half-specified, and the scoring formula in the same document guaranteed the missing half would fire constantly.
