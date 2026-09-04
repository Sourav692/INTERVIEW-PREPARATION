# Linked Hash Map — Explained Simply

## The Problem

Build a hash map that **remembers what order things were added in**.

```python
m = LinkedHashMap()
m.put("a", 1)
m.put("b", 2)
m.put("c", 3)

list(m)          # -> ["a", "b", "c"]     ← in order, every time
m.get("b")       # -> 2                   ← still O(1)
m.remove("b")
list(m)          # -> ["a", "c"]
```

Everything must stay **O(1)** — you don't get to trade speed for order.

## Why One Structure Isn't Enough

Two different questions, two different structures:

| Question | What answers it |
|---|---|
| "What's the value for key `b`?" | a **hash map** — instant, but knows nothing about order |
| "What order were these added in?" | a **linked list** — knows order, but finding a key means walking it |

Neither can do the other's job. So use **both**, over the same set of node objects.

And the join between them is the one decision that matters:

> **The map stores `key -> Node`, not `key -> value`.**

The map hands you the *actual list node*. That's what lets you unlink it and move it in a couple of pointer writes, instead of walking the list to find it.

## An Analogy First: A Photo Album with an Index

Imagine a photo album where the photos are pasted in **the order you took them**, and there's an index at the front:

```
INDEX                    ALBUM
"beach"  → page 3        page 1: birthday
"party"  → page 1        page 2: hiking
"hiking" → page 2        page 3: beach
```

Two capabilities, kept separate:

- **Flipping through the album front-to-back** gives you chronological order. That's the linked list.
- **Looking up "beach" in the index** takes you straight to page 3 without flipping. That's the hash map.

The index doesn't contain a *copy* of the photo — it tells you **where the photo is**. That's the "store nodes, not values" rule. If the index held copies, then moving a photo to the back of the album would mean flipping through the whole thing to find the original.

## The Question You Must Ask First

Here's what this problem is really testing, and it's easy to miss: **what should happen when you touch a key that's already there?**

There are two standard answers, and Java's `LinkedHashMap` supports both:

|  | `put` on an existing key | `get` on an existing key |
|---|---|---|
| **Insertion order** *(Java's default)* | update the value, **leave it where it is** | **leave it where it is** |
| **Access order** *(`accessOrder=true`)* | update, **move to the end** | **move to the end** |

### Watch the difference

Start with `a, b, c`, then `put("a", 99)`, then `get("b")`:

```
INSERTION ORDER                  ACCESS ORDER
a, b, c                          a, b, c
put(a, 99) → a, b, c             put(a, 99) → b, c, a
get(b)     → a, b, c             get(b)     → c, a, b
```

**Insertion order** is what you want for a config map, a JSON object, or anything where the caller's declaration sequence is meaningful. Reads and updates are *observations* — they don't change history.

**Access order** is what you want when "most recently touched" matters — because that's exactly the recency list an **LRU cache** evicts from.

> Both are correct. **Silently picking one is the mistake.** Say which you're building and why — that's the actual content of this question.

## The Doubly Linked List, and the Sentinel Trick

The order is held in a **doubly linked list** — each node knows the node before *and* after it:

```
head <-> [a] <-> [b] <-> [c] <-> tail
        oldest             newest
```

Why both directions? To pull a node out of the middle, you have to reconnect its neighbours to each other:

```python
node.prev.next = node.next
node.next.prev = node.prev
```

With only forward pointers you couldn't reach `node.prev` without walking from the start — O(n), and the design fails.

### The sentinels

Notice `head` and `tail` in that diagram. They're **permanent dummy nodes** that never hold real data.

Without them, removing a node needs a pile of cases:

```
if it's the only node:   ...
elif it's the first:     ...
elif it's the last:      ...
else:                    ...
```

Four branches, in the function you're most likely to get wrong on a whiteboard.

**With** sentinels, every real node is *guaranteed* to have a neighbour on both sides. So removal is unconditionally two lines, no `if` at all. Two wasted objects delete an entire category of bugs.

## Step-by-Step Example (Narrated)

Insertion-order mode. Start empty:

```
map:  {}
list: head <-> tail
```

---

**`put("a", 1)`**

Not in the map. Make a node, splice it in just before `tail`, record it:

```
map:  {a: node_a}
list: head <-> [a] <-> tail
```

---

**`put("b", 2)`**, **`put("c", 3)`** — same thing, each appended at the newest end:

```
map:  {a, b, c}
list: head <-> [a] <-> [b] <-> [c] <-> tail
```

---

**`put("a", 99)`** — an **update**

`a` **is** in the map. Look it up → we get `node_a` directly.

Change its value to 99. And then... in insertion-order mode, **do nothing else.**

```
list: head <-> [a] <-> [b] <-> [c] <-> tail       ← a stays first
```

Also return the **old** value, `1` — that's what Java's `Map.put` contract specifies.

*(In access-order mode, this is where you'd unlink `a` and re-append it, giving `b, c, a`.)*

---

**`get("b")`** → `2`

One map lookup. In insertion-order mode a read changes nothing.

---

**`remove("b")`**

Pop it from the map, then unlink it from the list:

```
node_b.prev.next = node_b.next      # a.next = c
node_b.next.prev = node_b.prev      # c.prev = a
```

```
map:  {a, c}
list: head <-> [a] <-> [c] <-> tail
```

**Both structures updated.** Forget either one and they drift apart — which is the bug this whole design has to guard against.

## The Payoff: An LRU Cache Is Three More Lines

This is why building the general structure is worth it.

An LRU cache **is** a linked hash map in access order, with a capacity limit:

```python
class LRUCache(LinkedHashMap):
    def __init__(self, capacity):
        super().__init__(access_order=True)     # ← touching refreshes recency
        self.capacity = capacity

    def put(self, key, value):
        old = super().put(key, value)
        if len(self) > self.capacity:
            self.popitem(last=False)            # ← evict the oldest end
        return old
```

That's it. Access order already keeps the most-recently-touched entry at the tail, so the **least** recently used is sitting at the head, ready to evict.

> Recognising that one problem *is* another with a constraint added is exactly what interviewers are listening for.

## Why the Node Stores Its Own Key

It looks redundant — the map is already keyed by it.

But look at `popitem`:

```python
node = self._head.next          # you have a NODE
del self._map[node.key]         # you need its KEY to clean the map
```

Without `node.key` you'd have to search the whole map for the entry whose value is this node — O(n), and the O(1) promise is gone.

> **General rule:** when two containers share objects, **each object carries whatever its peers need to find it.**

## "Why Not Just Use a dict?"

Fair question — Python 3.7+ dicts **do** preserve insertion order.

For insertion-order mode alone, a plain `dict` genuinely is enough.

But a dict **cannot reorder**. There's no "move this key to the end" operation. And that single missing capability is exactly what access-order mode — and therefore every LRU cache — is built on.

That's what the explicit linked list buys you: not the order itself, but **control over it**.

## Why It's Fast

The notebook benchmark runs 20,000 mixed operations against a map whose size doubles:

| Entries | List of pairs | Map + linked list |
|---|---|---|
| 250 | 106 ms | 5.6 ms |
| 500 | 199 ms (1.9×) | 4.8 ms (0.9×) |
| 1,000 | 422 ms (2.1×) | 4.9 ms (1.0×) |
| 2,000 | 842 ms (2.0×) | 5.9 ms (1.2×) |

The list version **doubles** each time — every operation scans everything. The linked hash map is **flat**: one hash lookup plus a fixed number of pointer writes, no matter how big it gets.

At 2,000 entries that's **143× faster**.

## Common Mistakes

- **Storing values in the map instead of nodes.** You'd have to search the list to reorder — O(n), design ruined.
- **Not deciding between insertion order and access order.** They differ by one line and produce completely different structures.
- **Updating only one of the two structures on `remove`.** They drift apart, and every later operation is subtly wrong.
- **Skipping the sentinels.** Four extra branches in your two most error-prone functions.
- **Using a singly linked list.** No `prev` means no O(1) removal from the middle.
- **`put` not returning the old value.** Java's contract specifies it, and it costs one line. (Note the wart: `None` means both "no previous value" and "the previous value was `None`" — the same ambiguity as using `None` for "not found".)
- **Deleting the *next* key while iterating.** Reading `node.next` before yielding makes deleting the *current* key safe, but not the next one. If you need full safety, iterate a snapshot.

## The Takeaway

> When one structure can't answer both questions, **use two and let them share the same objects**. The hash map gives you *identity*; the doubly linked list gives you *order*. Point the map at the list's nodes and both stay O(1).

And build the general version first: a linked hash map with an ordering flag gives you an [LRU cache](../10.%20LRU_Cache/README.md) almost for free.
