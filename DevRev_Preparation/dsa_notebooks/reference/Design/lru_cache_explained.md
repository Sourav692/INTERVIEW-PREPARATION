# LRU Cache — Explained Simply

## The Problem

Design a cache that holds a fixed number of items (`capacity`). It needs two operations, and **both must be instant (O(1))**, no matter how big the cache is:

- `get(key)` — return the value, or `-1` if it's not there. This also counts as "using" that key.
- `put(key, value)` — insert or update a value. If the cache is full, kick out the **Least Recently Used (LRU)** item first.

Example:

```
cache = LRUCache(capacity = 2)
cache.put(1, 1)
cache.put(2, 2)
cache.get(1)        # -> 1   (using key 1 makes it "most recently used")
cache.put(3, 3)      # cache is full -> evicts key 2 (it's the least recently used)
cache.get(2)        # -> -1  (key 2 was evicted)
```

## Why the Obvious Way Is Slow

The obvious way: keep a dictionary of values, plus a plain list tracking the order keys were used (oldest at the front, newest at the back).

```
on get/put: find the key in the order list, remove it, and append it to the end
on overflow: remove the very first item in the order list
```

The problem: removing an item from the *middle* of a Python list (or from the front) requires shifting every element after it — that's `O(n)` per operation. If you do `n` operations, that's `O(n²)` total. Too slow for a cache meant to be fast.

## The Simple Trick: Combine a Dictionary with a Doubly Linked List

You need two things to both be fast:
1. **Find a value by key instantly** → a **dictionary** does this in O(1).
2. **Know what's least-recently-used, and reorder things instantly** → a **doubly linked list** does this in O(1), because you can unlink and re-insert any node without shifting anything else.

Neither one alone solves the whole problem — together, they do:

- The dictionary maps `key → node` (so you can jump straight to any entry).
- The doubly linked list keeps entries ordered by recency: the front is "just used," the back is "least recently used."
- Every time a key is touched (`get` or `put`), unlink its node and stick it back at the **front**.
- When the cache overflows, just chop off the node sitting at the **back** — that's guaranteed to be the least-recently-used one.

Two dummy "sentinel" nodes (a fake `head` and fake `tail`) sit at the very ends of the list so you never have to special-case "is this the first/last real node?"

## Step-by-Step Example

```
capacity = 2
```

| Action | List (front = most recent → back = least recent) | Notes |
|--------|-----------------------------------------------------|-------|
| put(1,1) | [1] | |
| put(2,2) | [2, 1] | |
| get(1) → 1 | [1, 2] | touching 1 moves it to the front |
| put(3,3) | [3, 1] | cache full → evict the back (key 2) |
| get(2) → -1 | [3, 1] | key 2 no longer exists |

## Plain-English Walkthrough

1. Keep a dictionary from `key` to a "node" object holding the value.
2. Keep those nodes threaded together in a doubly linked list, ordered by how recently they were used (most-recent at the front).
3. On `get(key)`: look up the node in the dictionary (instant). If found, unlink it from wherever it is and re-insert it at the front (now it's "most recent"). Return its value.
4. On `put(key, value)`: if the key already exists, unlink its old node. Create/update the node and insert it at the front. If the cache now has more items than capacity, remove the node sitting at the very back (the least-recently-used one) and delete it from the dictionary too.

## Simple Python Code

```python
class Node:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}                    # key -> Node
        self.head = Node()               # dummy front (most-recent side)
        self.tail = Node()               # dummy back (least-recent side)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_front(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        if key not in self.map:
            return -1
        node = self.map[key]
        self._remove(node)
        self._add_front(node)            # touching it -> move to front
        return node.val

    def put(self, key, value):
        if key in self.map:
            self._remove(self.map[key])
        node = Node(key, value)
        self.map[key] = node
        self._add_front(node)
        if len(self.map) > self.cap:     # over capacity -> evict the least-recently-used
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
```

## Why Dummy Head/Tail Nodes?

Without them, inserting into an empty list or removing the only node in the list requires special-case code ("is this the first node? is this the last node?"). By always keeping a fake `head` and `tail` at the two ends, every real node always has a `prev` and a `next` — insert and remove logic never needs to check for edge cases.

## Complexity

- **Time:** O(1) for both `get` and `put` — dictionary lookup is instant, and linked-list insert/remove doesn't shift anything.
- **Space:** O(capacity) — one node per cached item.

## The Reusable Pattern

This is the **"hash map + doubly linked list"** pattern — the standard way to get O(1) lookup *and* O(1) reordering/eviction at the same time. Use it whenever you see:
- "O(1) get and set, with eviction"
- "Least/most recently used"
- "Bounded cache with a fixed size"

Related: LFU Cache (evicts by frequency instead of recency), Design a browser history, session/response caching for APIs.
