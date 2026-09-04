# SnapID

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Hash Tables · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Implement a data structure with functionality similar to a hash table. In our custom data structure, **insert & delete operations return a `snapID`**, and we pass on the `snapID` for lookup.

For instance, say `DS` is our custom data structure, here are operations and results:

```
DS.insert(k1, v1)   -> snap1
DS.insert(k2, v2)   -> snap2
DS.delete(k1)       -> snap3
DS.insert(k1, v3)   -> snap4

DS.hasKey(k1, snap1) -> True
DS.hasKey(k1, snap2) -> True
DS.hasKey(k1, snap3) -> False
DS.hasKey(k1, snap4) -> True

DS.getVal(k1, snap1) -> v1
DS.getVal(k1, snap4) -> v3
```

---

## Study Tools

### Hint 1

Each operation creates a new `snapID`, so you need to preserve the state of every key at every point in time. Think about what data structure lets you store multiple values for the same key, each tagged with the `snapID` when it became active.

### Hint 2

For each key, keep a list of `(snapID, value)` pairs in increasing `snapID` order. To answer a query at `snapID s`, you need the latest entry with `snapID <= s` — binary search gives you O(log m) per lookup if the list has m entries.

### Hint 3

Use a `HashMap<K, List<Entry>>` where each `Entry` is `(snapID, value, isDeleted)`. On insert or delete, append to the key's list. On lookup, binary search the list for the greatest `snapID <=` the query `snapID`, then check whether that entry was a delete or an insert.

---

### Answer

This is a **versioned key-value store** using per-key append-only histories with binary search.

Maintain a `HashMap<K, List<Entry>>` where each `Entry` stores `(snapID, value, isDeleted)`. Every insert and delete increments a global counter and appends an entry to the corresponding key's list. Lookups binary search that list for the greatest `snapID <=` the query `snapID`, then return based on whether that entry was an insert or delete.

```java
import java.util.*;

public class SnapIDDS<K, V> {
    private static class Entry<V> {
        int snapID;
        V value;
        boolean isDeleted;

        Entry(int snapID, V value, boolean isDeleted) {
            this.snapID = snapID;
            this.value = value;
            this.isDeleted = isDeleted;
        }
    }

    private final Map<K, List<Entry<V>>> map;
    private int nextSnapID;

    public SnapIDDS() {
        map = new HashMap<>();
        nextSnapID = 1;
    }

    public int insert(K key, V value) {
        int snapID = nextSnapID++;
        map.computeIfAbsent(key, k -> new ArrayList<>())
           .add(new Entry<>(snapID, value, false));
        return snapID;
    }

    public int delete(K key) {
        int snapID = nextSnapID++;
        map.computeIfAbsent(key, k -> new ArrayList<>())
           .add(new Entry<>(snapID, null, true));
        return snapID;
    }

    public boolean hasKey(K key, int snapID) {
        List<Entry<V>> history = map.get(key);
        if (history == null) return false;
        int idx = binarySearch(history, snapID);
        if (idx < 0) return false;
        return !history.get(idx).isDeleted;
    }

    public V getVal(K key, int snapID) {
        List<Entry<V>> history = map.get(key);
        if (history == null) return null;
        int idx = binarySearch(history, snapID);
        if (idx < 0 || history.get(idx).isDeleted) return null;
        return history.get(idx).value;
    }

    // Returns the largest index i such that history.get(i).snapID <= snapID,
    // or -1 if no such index exists.
    private int binarySearch(List<Entry<V>> history, int snapID) {
        int lo = 0, hi = history.size() - 1;
        int result = -1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (history.get(mid).snapID <= snapID) {
                result = mid;
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return result;
    }
}
```

**Time:** O(1) for insert/delete (amortized `ArrayList` append), O(log m) for `hasKey`/`getVal`, where m is the number of operations on that key. **Space:** O(n) where n is the total number of insert/delete operations — every operation appends one `Entry`.

**Correctness:** For any key, the history list is sorted by `snapID` because `nextSnapID` strictly increases. The binary search finds the latest entry at or before the query `snapID`, which is exactly the state of that key at that point in time. If that entry is an insert, the key exists; if it's a delete, it doesn't. Keys never inserted have no history and return `false`/`null`.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

**Step 1: Brute force — snapshot the entire map.** The simplest idea: on every operation, copy the whole map into a list of snapshots. Insert is O(n) per operation (copy everything), and lookup is O(1) by indexing into the snapshot list. Total cost for n operations: O(n²) time and O(n²) space. That's the bottleneck — copying the entire state on every single operation.

**Step 2: Store only what changed.** Instead of copying everything, store only the change. Each operation touches exactly one key, so append `(snapID, value, isDeleted)` to a list for that key. Insert and delete drop to O(1). The tradeoff: lookup now has to search a key's history to figure out its state at a given `snapID`.

**Step 3: Make lookup fast.** Since `snapID`s are assigned in increasing order, each key's history list is sorted by `snapID` automatically. That means we can binary search for the greatest `snapID <=` the query `snapID`. Lookup becomes O(log m) where m is the number of operations on that key, which is typically much smaller than the total operation count.

**Step 4: Handle deletes uniformly.** A delete is just another entry in the history with `isDeleted = true`. The binary search finds the latest entry at or before the query `snapID`, and we check that entry's flag. This unifies insert and delete into one code path — no special cases for "key was deleted then re-inserted."

**Step 5: Edge cases to verify.**

- Query `snapID` before the key's first insert: binary search returns -1, so return `false`/`null`.
- Query `snapID` exactly equal to a delete: the delete entry is the latest `<= snapID`, so return `false`/`null`.
- Delete a key that doesn't exist yet: we still append a delete entry, which is harmless — a subsequent `hasKey` at that `snapID` returns `false`, same as if we'd skipped it. This keeps the code simpler without breaking correctness.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Walk through the example in the prompt with your data structure** — tracing `insert(k1,v1) → snap1`, `delete(k1) → snap3`, then `hasKey(k1, snap2)` shows you understand that `snap2` still sees `k1` as alive because the delete hasn't happened yet. Interviewers watch for this temporal reasoning.
- **State the space complexity precisely** — it's O(n) total entries across all keys, one per operation. Saying O(n) per key is wrong; the total is bounded by the number of operations, which matters if the interviewer pushes on memory.
- **Explain why binary search works** — the history list is sorted by `snapID` because `snapID`s are monotonically increasing. If you just say "binary search" without justifying the sortedness, you leave a gap in the correctness argument.
- **Discuss the delete-a-missing-key case explicitly** — you can choose to append a delete entry anyway or skip it. Appending keeps the code uniform and is still correct because the binary search result is the same. Mentioning this shows you've thought about edge cases before the interviewer asks.
- **Name the amortized cost of `ArrayList` append** — O(1) amortized, not worst-case. If the interviewer asks about worst-case, you can switch to `LinkedList` for O(1) worst-case append at the cost of O(m) binary search (no random access), or use a balanced tree for O(log m) everything.
- **Offer the `getVal` returning `null` ambiguity** — if `null` is a valid stored value, returning `null` for "key absent" is ambiguous. You can point this out and suggest `hasKey` as the disambiguator, or return an `Optional<V>`.
- **Mention the multi-key snapshot extension** — if the interviewer asks for a global snapshot across all keys, your per-key histories still work: just query each key with the same `snapID`. The per-key design composes naturally.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if we need to iterate over all keys present at a given `snapID` efficiently?** — Think about maintaining a global event log plus per-key histories, or a persistent balanced tree keyed by `snapID`.
- **How would you support `getAllVersions(key)` returning every value ever stored for a key, in order?** — This is just iterating the history list; consider whether to include tombstones.
- **What if `snapID`s can be passed out of order** — e.g., a client queries with an old `snapID` after many new operations? — Your binary search already handles this; the question is whether you want to cap memory by pruning old history.
- **How would you compress the history if a key is inserted and deleted many times without ever being queried at intermediate `snapID`s?** — Consider coalescing consecutive operations when a lookup hasn't observed them, or periodic compaction.
- **What's the worst-case time for a single lookup if one key has m operations and you use a `LinkedList` instead of `ArrayList`?** — Binary search needs random access, so `LinkedList` forces O(m) scan; tradeoffs between append cost and lookup cost are the core tension.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same design in Python so every claim is executable and testable; the Java reference above is reproduced unchanged.
