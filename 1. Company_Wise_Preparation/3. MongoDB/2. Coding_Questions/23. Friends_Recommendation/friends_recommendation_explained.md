# Friends Recommendation — Explained Simply

## The Problem

A social network stored as `{user: [their friends]}`. Given a user, recommend the **best new friend**:

1. Whoever shares the **most mutual friends** with them.
2. Tie? Pick the **smaller ID**.
3. Never recommend the user themselves, or someone they're already friends with.

```
graph = {1: [2, 3],
         2: [1, 4, 5],
         3: [1, 4],
         4: [2, 3, 5],
         5: [2, 4]}

recommend(1) → 4      (shares friends 2 and 3)
```

## The Reframe: A Mutual Friend Is a Two-Step Path

Say it out loud and the algorithm appears:

> `u — f — c` means "`u` knows `f`, and `f` knows `c`".

So *"how many mutual friends do `u` and `c` have?"* is exactly *"how many two-step paths run from `u` to `c`?"*

Which means: **start at `u`, walk two steps, and count where you land.** Every landing is a mutual friend by definition — you got there *via* one of `u`'s friends.

## An Analogy First: Working the Room at a Party

You're at a party and want to meet someone new.

**The slow way:** go around the entire room, and for every single person, ask them to list all their friends and see how many overlap with yours. Exhausting — and most people you ask turn out to share nobody with you at all.

**The fast way:** find the handful of people you *already* know. Ask each of them: *"who else are you here with?"*

Every name you hear is, by definition, someone who shares a friend with you. And if three different friends all name the same person, that person shares **three** mutual friends with you — they're clearly the one to be introduced to.

You never spoke to the 200 strangers who know nobody you know. **You didn't need to** — they could never have been the answer.

## Why That's the Whole Optimisation

| Approach | Cost |
|---|---|
| Check every user | O(N × F) — all N users, each compared against your F friends |
| Walk two steps out | **O(sum of the degrees of your friends)** |

In a real network the difference is enormous. You have 200 friends who each have 200 friends → you touch **40,000** people. Not the three billion in the graph.

And crucially, that number **doesn't grow** when the network adds a million strangers. The benchmark shows it: as the user count doubles from 1,000 to 8,000, the naive version's time doubles each step, while the two-step walk stays flat — **305× faster** at 8,000 users.

## Step-by-Step Example (Narrated)

```
graph = {1: [2, 3],
         2: [1, 4, 5],
         3: [1, 4],
         4: [2, 3, 5],
         5: [2, 4]}
```

Target: **user 1**.

---

**Step 0.** Note who 1 is already friends with: `{2, 3}`.

Store it as a **set**, not a list — we're about to check membership over and over.

---

**Step 1 — via friend 2.** Who does 2 know? `[1, 4, 5]`

- **1** → that's the target themselves. **Skip.**
- **4** → new! `counts = {4: 1}`
- **5** → new! `counts = {4: 1, 5: 1}`

---

**Step 2 — via friend 3.** Who does 3 know? `[1, 4]`

- **1** → skip.
- **4** → **already counted once**, so bump it: `counts = {4: 2, 5: 1}`

> This bump is the entire measurement. Candidate 4 was reached via **two different friends** (2 and 3), so they share two mutual friends with user 1.

---

**Step 3 — pick the winner.**

`{4: 2, 5: 1}` → highest count is 2 → **recommend user 4.** ✅

We never looked at anyone outside 1's immediate neighbourhood.

## Three Details That Matter

### 1. The friend list must be a `set`

```python
friends = set(graph.get(user, []))     # ✅
```

The check `if candidate in friends` runs **once per edge examined**. On a list that's O(F) each time, silently multiplying the whole algorithm by F. On a set it's O(1).

### 2. Skip inside the loop, not afterwards

Filtering out the target and existing friends *as you go* means the count map only ever contains genuine candidates. The final scan has nothing to throw away.

### 3. `>` versus `>=` decides the tie-break

```python
for candidate in sorted(mutual_counts):        # ascending ID
    if mutual_counts[candidate] > best_count:  # STRICTLY greater
        best, best_count = candidate, mutual_counts[candidate]
```

Because IDs are visited in ascending order, the **first** candidate to reach a given count claims it. A strict `>` means a later, larger ID can never displace it on a tie.

Change it to `>=` and the rule silently flips to *largest ID wins*. **One character, opposite behaviour** — and no test catches it unless you write one that actually ties.

## The Gap in the Official Answer

The code counts a candidate whenever *some friend of `u` lists them*. It never checks the friendship is **mutual**.

If `A` lists `B` but `B` doesn't list `A`, that one-way edge still counts. And it fails in **both** directions:

```python
# The raw reading COUNTS an edge it shouldn't:
{1: [2], 2: [1, 9], 9: []}
→ recommends 9, via a friendship 9 doesn't reciprocate

# The raw reading MISSES an edge it should count:
{1: [2], 2: [1], 9: [2]}
→ recommends nobody, because 2 never lists 9
```

Normalising the graph first — adding every reverse edge — makes "friend" mean what the word means.

> **Worth asking about, not assuming.** An asymmetric adjacency map is usually a data bug. But sometimes it's deliberate, because a **follow** is genuinely one-way — and "mutual friends" and "people who follow the same people" are different metrics. The code can't tell you which was meant.

## Counting Isn't Yet Recommending

Here's the idea that turns this from an exercise into a real recommender.

Suppose two people both share 2 mutual friends with you:

- **Candidate A** — via a friend who knows **10,000 people**.
- **Candidate B** — via a friend who knows **12 people**.

Those are not equal evidence. The hyper-connected friend knows *everyone* — their "endorsement" is nearly meaningless. The selective friend knowing both of you is a genuine signal.

The standard fix is **Adamic–Adar**: weight each shared friend by `1 / log(their degree)`.

```python
counts[c] += 1 / math.log(degree(f))     # instead of += 1
```

The notebook tests this with a deliberate hub — a user who knows 100 people — and confirms the weighted score discounts their endorsement.

## The Follow-Ups, Briefly

**Top-k instead of top-1.** Sort by `(-count, id)` — descending count, ascending ID. That's the same tie-break rule expressed as a **sort key**, which is the point: write the rule once, and the top-1 and top-k paths can't drift apart.

**A graph too big for memory.** The two-step walk is a textbook **map-reduce**: map each `(friend, candidate)` pair to `(candidate, 1)`, reduce by summing. It parallelises perfectly, since each friend is processed independently.

The real difficulty isn't the algorithm — it's **skew**. A celebrity with 50 million followers makes one reducer key dwarf every other, and the standard fix is to cap or specially handle very high-degree nodes.

**A single pass with no count map?** Not really. A candidate is encountered multiple times, so you can't know the winner until you've seen every increment. You'd still need the counts — you'd just track the running best alongside them, saving the final sort. O(C) instead of O(C log C), for meaningfully fiddlier tie-break logic.

## Common Mistakes

- **Iterating over every user in the graph.** Anyone with zero mutual friends can never win. Don't look at them.
- **Keeping the friend list as a list.** Turns an O(1) membership check into O(F), multiplying the whole cost.
- **Using `>=` in the tie-break.** Silently inverts the rule to largest-ID-wins.
- **Forgetting to exclude existing friends.** They'll often have the highest mutual counts of anyone.
- **Forgetting to exclude the user themselves.** They appear in every one of their friends' lists.
- **Not handling "no recommendation possible".** Return -1 (or `None`) — and say which.
- **Trusting the graph's shape.** Duplicate edges inflate counts; self-loops recommend the user to themselves; asymmetric edges are counted or missed depending on direction.

## The Takeaway

> Don't search the whole graph and filter. **Search outward from the answer's neighbourhood.** Only people within two hops can possibly share a friend with you — so walk two steps and tally where you land.

That reframing — *"a mutual friend is a path of length 2"* — is what turns a vague social question into a concrete traversal. And the same instinct applies far beyond social graphs: whenever you're about to enumerate everything and discard most of it, ask whether you can start from the small set that could actually qualify.
