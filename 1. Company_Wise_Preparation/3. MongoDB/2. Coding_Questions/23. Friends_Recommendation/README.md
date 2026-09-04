# Friends Recommendation

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Graphs, Hash Tables · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

In a social network, every user has a list of friends. Given a graph representing the social network (represented as `Map<Integer, List<Integer>>` where key is the user id and value is the list of the user's friends) and a user id, recommend a **"best new friend"** for the given user.

The rules are:

- **Prioritized recommendation:** the user who shares the **most mutual friends** with the given user.
- **Auxiliary recommendation:** If there's a tie, choose the user with the **smaller ID**.
- **Restriction:** don't recommend the given user himself/herself and the given user's current friends.

---

## Study Tools

### Hint 1

Count, for every non-friend of the given user, how many of the given user's friends also have that person as a friend. The answer is the non-friend with the highest count.

### Hint 2

Iterate through the given user's friends, and for each friend, iterate through **their** friends. Skip anyone who is the given user himself or already a friend of the given user. Use a map to accumulate mutual-friend counts.

### Hint 3

After building the count map, scan it once to find the maximum count. Ties are broken by choosing the smaller user ID. If the map is empty, return -1.

---

### Answer

This is a mutual-friend counting problem. For each friend `f` of the target user `u`, every friend of `f` (other than `u`) shares at least one mutual friend with `u`. We tally those non-friends, then pick the one with the highest tally, breaking ties by smallest ID.

```python
from collections import defaultdict
from typing import Dict, List


def recommend_friend(graph: Dict[int, List[int]], user: int) -> int:
    friends = set(graph.get(user, []))

    mutual_counts = defaultdict(int)

    for friend in friends:
        for candidate in graph.get(friend, []):
            if candidate == user or candidate in friends:
                continue
            mutual_counts[candidate] += 1

    if not mutual_counts:
        return -1

    best_candidate = -1
    best_count = -1
    for candidate in sorted(mutual_counts.keys()):
        if mutual_counts[candidate] > best_count:
            best_count = mutual_counts[candidate]
            best_candidate = candidate

    return best_candidate
```

**Time:** O(F + E) — where F is the number of friends of the target user and E is the total number of edges among those friends (each friend's adjacency list is scanned once, and set lookups are O(1) on average).

**Space:** O(F + C) — where C is the number of distinct non-friend candidates encountered, plus the set of the target user's friends.

**Correctness argument:** Every candidate that shares at least one mutual friend with `u` is discovered by scanning the adjacency lists of `u`'s friends. The count map tracks exactly how many of `u`'s friends are connected to each candidate. Since we skip `u` and all existing friends, every entry in `mutual_counts` is a valid recommendation candidate. Scanning the sorted keys guarantees that when counts tie, the smaller ID is selected first and only replaced if a strictly larger count appears.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute-force idea: for every user in the graph who isn't `u` and isn't already a friend of `u`, count how many of `u`'s friends are also friends with that user. That's O(N × F × F) in the worst case if you check all N users and for each one scan all of `u`'s friends and their friends. The bottleneck is checking users who have **zero chance** of being recommended.

Flip it around. Instead of iterating over all users, iterate over `u`'s friends. For each friend `f`, look at `f`'s friends. Any of those who aren't `u` and aren't already a friend of `u` just got one mutual friend. This way you only touch users who actually share at least one mutual friend with `u`. That drops the work to the sum of degrees of `u`'s friends.

Now you have a map of candidate → mutual-friend count. The final step is picking the max count with tie-breaking by smallest ID. Sorting the candidate IDs and doing a single pass handles the tie-break cleanly, but you could also track the best as you build the map if you want to avoid the sort — just be careful to update on `>` only, not `>=`, so the smaller ID wins ties.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Set membership for friends** — converting the friend list to a set makes the skip check O(1) instead of O(F), which matters when friend lists are large.
- **Iterating over `u`'s friends rather than all users** — this is the efficiency win that separates a working answer from an optimal one; you only touch candidates who actually share a mutual friend.
- **Handling the empty case explicitly** — returning -1 when no recommendation exists shows you thought about boundary conditions, and the interviewer will ask about it if you don't mention it first.
- **Tie-breaking mechanics** — sorting keys and using a strict `>` comparison ensures the smallest ID wins ties without extra bookkeeping; state this invariant out loud.
- **Degree of the target user's friends** — if `u` has many friends with huge friend lists, the algorithm scales with that sum, so mentioning the bound O(sum of degrees of `u`'s friends) demonstrates you understand the actual cost.
- **Duplicate edges in the input** — if the graph might contain duplicate friend entries, the count could be inflated; mention that you're assuming clean input or that deduplication would be a one-line fix.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the graph is undirected but stored asymmetrically — how would you handle that?** — Consider normalizing by adding reverse edges or checking both directions when counting.
- **How would you return the top k recommendations instead of just one?** — Use a heap or sort the count map by value descending, then ID ascending.
- **What if the graph is too large to fit in memory?** — Think about distributed processing: map each friend pair to `(candidate, mutual friend)` and reduce by candidate.
- **How would you weight mutual friends by their closeness to the target user?** — Add a weight per friend of `u` and accumulate weighted counts instead of simple increments.
- **Can you do this in a single pass without building the full count map?** — Yes, maintain the best candidate and count as you go, but you need to handle the tie-break carefully since candidates can appear multiple times.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One thing the official answer leaves out

`recommend_friend` never checks whether the *target user exists* in the graph, and never excludes a candidate who is unreachable. Those turn out fine — `graph.get(user, [])` yields an empty friend set, so the count map is empty and it returns `-1`.

But there is a subtler gap: **the algorithm counts a candidate once per shared friend, which is what "mutual friends" means — yet it never verifies the friendship is mutual.** If the adjacency map is asymmetric (`A` lists `B`, but `B` does not list `A`), the count silently reflects a one-way edge. The official answer's own follow-up raises this and the code does not address it.

The notebook implements a `symmetric=True` option that normalises the graph first, and asserts that the two readings genuinely differ on an asymmetric input.
