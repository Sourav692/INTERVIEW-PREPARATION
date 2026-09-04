# LRU Cache — Explained Simply

## The Problem

Build a cache that holds at most `capacity` items. When it's full and something new arrives, throw away whatever hasn't been used in the longest time — the **least recently used** entry.

```python
c = LRUCache(2)
c.put(1, 1)
c.put(2, 2)
c.get(1)      # -> 1    (using 1 makes it "recent")
c.put(3, 3)   # full! evicts 2, because 1 was just used
c.get(2)      # -> -1   (gone)
```

Both `get` and `put` must be **O(1)**.

## Why LRU?

A cache is small and fast; the thing behind it is big and slow. Being small forces the real question: **when it's full, what do you throw away?**

LRU's bet is **temporal locality** — something you used recently, you'll probably use again soon. It's cheap to maintain and usually right, which is why it's the default nearly everywhere: CPU caches, operating-system page caches, MongoDB's WiredTiger cache, your browser.

## Why One Data Structure Isn't Enough

There are two completely different questions to answer, fast:

| Question | What answers it |
|---|---|
| "What's the value for key K?" | a **hash map** — instant lookup, but no sense of order |
| "Which entry is least recently used?" | an **ordered list** — knows order, but finding a key means scanning |

Neither can do the other's job. A hash map has no order at all. A list has order but no fast lookup.

**So use both.** And here's the crucial part:

> **The map stores `key -> Node`, not `key -> value`.**

The map hands you the *actual list node*, so you can yank it out of its position and move it to the front without searching for it. If the map stored plain values, you'd have to scan the list to find the node — O(n) — and the whole design collapses.

## An Analogy First: The Desk and the Card Index

Picture a small desk that fits exactly 3 folders, and a card index on the wall.

**The desk** is a stack of folders, most recently used on top, least recently used at the bottom. When the desk is full and a new folder arrives, you take the **bottom** one and file it away. You never have to think about which one — it's just the bottom.

**The card index** has one card per folder, and each card says *exactly where that folder is sitting on the desk*. So when someone asks for the "Accounts" folder, you don't rummage through the pile. You read the card, reach straight to that spot, pull the folder out, and put it on top.

Two things make this work:

- **The card points at the folder's position**, not at a copy of its contents. That's what makes "reach straight to it" possible.
- **Each folder has its own label on it.** When you evict the bottom folder, you're holding a *folder* and you need to know which *card* to tear up. Without the label you'd have to search the whole index.

That second point is why every node stores its own key — a detail that looks redundant until you hit eviction.

## The Doubly Linked List, and Why "Doubly"

The desk is a **doubly linked list**: each node knows the node before it **and** after it.

```
head <-> [3] <-> [1] <-> [2] <-> tail
         MRU              LRU
```

Why both pointers? To pull a node out of the middle, you have to reconnect its neighbours to each other:

```
node.prev.next = node.next
node.next.prev = node.prev
```

With only `next` pointers you couldn't find `node.prev` without walking from the head — O(n). The backward pointer is precisely what buys you O(1) removal from the middle.

### Sentinels: two dummy nodes that delete all your bugs

Notice `head` and `tail` in that diagram. They're **fake nodes** that never hold real data. They sit permanently at each end.

Without them, removing a node needs a pile of special cases:

```
if node is the only element:  ...
elif node is first:           ...
elif node is last:            ...
else:                         ...
```

Every one of those is a branch you can get wrong on a whiteboard.

**With** sentinels, every real node is *guaranteed* to have a neighbour on both sides. So removal is unconditionally two lines, with no `if` at all. Two wasted objects buy you a whole category of eliminated bugs.

## Step-by-Step Example (Narrated)

`LRUCache(2)` — capacity 2. Start empty:

```
map:  {}
list: head <-> tail
```

---

**`put(1, "a")`**

Key 1 isn't in the map. Create a node, add it right after `head`, record it in the map.

```
map:  {1: node1}
list: head <-> [1] <-> tail
```

---

**`put(2, "b")`**

New key again. New node, straight to the front.

```
map:  {1: node1, 2: node2}
list: head <-> [2] <-> [1] <-> tail
       MRU ─────────────── LRU
```

Size is 2, capacity is 2. Full, but not over.

---

**`get(1)`** → returns `"a"`

Look up key 1 in the map → we get `node1` **directly**, no searching.

Now **reading counts as using it**, so move it to the front:

1. Unlink it: `node1.prev.next = node1.next` and `node1.next.prev = node1.prev`
2. Re-insert right after `head`

```
list: head <-> [1] <-> [2] <-> tail
       MRU ─────────────── LRU
```

**Key 1 just saved its own life.** Key 2 is now the least recently used.

---

**`put(3, "c")`**

Key 3 is new. Create a node, add at the front, add to the map:

```
map:  {1, 2, 3}          <- size 3, capacity 2. OVER.
list: head <-> [3] <-> [1] <-> [2] <-> tail
```

Now evict. The victim is always **the node just before `tail`** — no searching, no comparing, we just reach for it:

```
evicted = tail.prev        # node2
unlink it
del map[evicted.key]       # <- THIS is why the node stores its own key
```

```
map:  {1: node1, 3: node3}
list: head <-> [3] <-> [1] <-> tail
```

---

**`get(2)`** → `-1`. Key 2 is gone — evicted because it was the one nobody had touched.

Notice the whole outcome hinged on that `get(1)` earlier. Without it, 1 would have been the victim.

## The Two Cases People Get Wrong

### 1. `put` on a key that already exists

```python
c.put(1, "a")
c.put(2, "b")
c.put(1, "A")     # UPDATE - not an insert
```

This must **update the value and move the node to the front** — and **not** change the size.

The bug is to treat it as an insert: you create a *second* node for key 1, so the list now has a duplicate, the count is wrong, and eviction throws away something it shouldn't have. Silent corruption.

### 2. `get` must count as a use

If `get` doesn't move the node to the front, you haven't built an LRU cache — you've built a **FIFO** cache, which evicts by insertion order and ignores usage entirely. Same code shape, completely different (and much worse) behaviour.

## Why Every Node Stores Its Own Key

This looks redundant. The map is *already* keyed by it, so why duplicate it inside the node?

Because of eviction. There, you're holding a **node** and you need to delete the matching **map entry**:

```python
evicted = self._pop_tail()      # you have a node
del self.cache[evicted.key]     # you need its key
```

Without `node.key`, you'd have to search the entire map looking for the entry whose value is this node — O(n), and your O(1) promise is gone.

> **The general rule:** whenever two containers share the same objects, **each object should carry whatever its peers need to find it.**

## Why It's Fast

The notebook benchmark runs 20,000 operations against a cache whose capacity doubles:

| Capacity | List scan | Map + linked list |
|---|---|---|
| 250 | 185 ms | 7.4 ms |
| 500 | 392 ms (2.1×) | 7.1 ms (1.0×) |
| 1,000 | 796 ms (2.0×) | 7.1 ms (1.0×) |
| 2,000 | 1,635 ms (2.1×) | 6.9 ms (1.0×) |

The naive version **doubles** every time — each operation scans the whole cache. The optimal version is **completely flat**: one hash lookup plus a fixed number of pointer writes, regardless of size.

At capacity 2,000 that's **236× faster**, and it keeps widening.

## Shortcut: Python Already Has This

`collections.OrderedDict` **is** a hash map threaded with a doubly linked list — exactly this design, written in C:

```python
self.od.move_to_end(key)         # relink a node to the front
self.od.popitem(last=False)      # pop the least recently used
```

(`functools.lru_cache` is the same machinery wrapped as a decorator.)

**In an interview, don't lead with this.** The question is asking whether you can build the structure. Write it by hand, then mention `OrderedDict` as what you'd actually ship. That ordering shows both capability and judgement.

## A Surprising Thing About Thread Safety

If asked how to make this thread-safe, a single lock around `get` and `put` works, and the critical section is tiny since both are O(1).

But here's the catch worth mentioning:

> **`get` is a *writer*.** It relinks the list.

So you **cannot** use a reader-writer lock and let reads run in parallel — every read mutates shared state. That's a genuinely surprising property of LRU.

High-throughput caches deal with it by **sharding**: 16 independent caches keyed by `hash(key) % 16`, each with its own lock, so unrelated keys never contend. The cost is that eviction becomes per-shard rather than global.

## When LRU Is the Wrong Policy

Worth knowing, because interviewers ask:

LRU's weakness is a **sequential scan**. Read a million rows once each, and every one of them looks "recently used" — so they push your entire genuinely-hot working set out of the cache. The cache ends up full of data nobody will ever ask for again.

Alternatives: **LFU** (least *frequently* used) resists scans but adapts slowly to real change. **LRU-K** looks at the last K accesses instead of just the most recent. **ARC** adaptively balances recency against frequency.

Naming *why* LRU fails on scans shows you understand the policy, not just its implementation.

## Common Mistakes

- **Storing values in the map instead of nodes.** You'd have to search the list to reorder — O(n), design ruined.
- **Treating `put` on an existing key as an insert.** Creates a duplicate node and corrupts the count.
- **Not moving the node on `get`.** You've built FIFO, not LRU.
- **Forgetting `node.key`.** Eviction can't clean up the map in O(1).
- **Skipping the sentinels.** Four extra branches in the two most error-prone functions.
- **Using a singly linked list.** No `prev` pointer means no O(1) removal from the middle.
- **Letting the map and list drift apart.** After every operation, the list must hold exactly the map's keys, in recency order, with length ≤ capacity. Write that sentence down and check each method against it.

## The Takeaway

> When one structure can't answer both questions, **use two and let them share the same objects**. A hash map gives you *identity*; a doubly linked list gives you *order*. Point the map at the list's nodes and both questions become O(1).

That pairing shows up again and again — LFU caches, linked hash maps, timer wheels, schedulers. And an LRU cache is exactly a [linked hash map](../12.%20Linked_Hash_Map/README.md) in access order, with an eviction rule bolted on.
