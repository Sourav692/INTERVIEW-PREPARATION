# LRU Cache

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Caching, Hash Tables, Linked List · **Difficulty/Frequency:** Common (5/10)

---

## Problem Statement

Implement an LRU cache.

---

## Study Tools

### Hint 1

You need O(1) access to values by key and O(1) ability to move an item to the front when it's touched. A single data structure won't give you both.

### Hint 2

Combine a hash map for fast lookup with a doubly linked list where the head is most-recently-used and the tail is least-recently-used. The map should store **pointers to list nodes**, not just values.

### Hint 3

On `get`, move the node to the head. On `put`, if the key exists, update its value and move it to the head; if it's new, add it at the head and evict the tail node if you're over capacity.

---

### Answer

This is a classic combination of a hash map and a doubly linked list. The map gives you O(1) lookup by key, and the list maintains recency order with O(1) insertions and deletions at both ends. The map stores keys mapped directly to list nodes so you can unlink and re-link a node in constant time when it's accessed.

```python
class Node:
    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}          # key -> Node
        self.head = Node()       # sentinel, most recent side
        self.tail = Node()       # sentinel, least recent side
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node) -> None:
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _add_to_head(self, node: Node) -> None:
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _move_to_head(self, node: Node) -> None:
        self._remove(node)
        self._add_to_head(node)

    def _pop_tail(self) -> Node:
        node = self.tail.prev
        self._remove(node)
        return node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._move_to_head(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._move_to_head(node)
        else:
            node = Node(key, value)
            self.cache[key] = node
            self._add_to_head(node)
            if len(self.cache) > self.capacity:
                evicted = self._pop_tail()
                del self.cache[evicted.key]
```

**Time:** O(1) for both `get` and `put` — hash map lookup, list unlink, and list insert are all constant-time operations.
**Space:** O(capacity) — the hash map holds at most `capacity` entries, and the list holds exactly the same nodes.

**Correctness argument:** The invariant is that the doubly linked list always contains exactly the keys in the cache, ordered from most-recently-used at the head to least-recently-used at the tail, and `len(cache) <= capacity`. Initially the list is empty and the map is empty, so the invariant holds. On `get`, if the key exists, moving its node to the head preserves the ordering invariant. On `put` for an existing key, updating the value and moving to head preserves both the ordering and the size bound. On `put` for a new key, adding to head may temporarily make `len(cache) == capacity + 1`, at which point evicting the tail restores the size bound. Since the tail is always the least-recently-used node by the ordering invariant, eviction removes the correct key.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive version: a plain list where `get` scans for the key and `put` appends. `get` is O(n) and `put` is O(n) because you need to scan to check for duplicates and evict. The bottleneck is finding and removing elements from the middle of a sequence.

A hash map alone fixes lookup to O(1), but you still need some way to track recency. You could store timestamps in the map and scan all entries to find the oldest on eviction — that's O(n) for `put`. The insight is that recency is naturally modeled as an ordering, and the operations you need on that ordering are: insert at the front, remove from the back, and move an arbitrary element to the front. A doubly linked list does all three in O(1) **if you already have a pointer to the node**.

So the key decision is what the map stores. If the map stores values, you'd need to search the list to find the node to move — O(n) again. If the map stores pointers to nodes, you can unlink and re-link in constant time. That's the whole trick.

Finally, handle the sentinel nodes. Using dummy head and tail nodes eliminates all the null-checking branches when inserting at the head or removing the tail. Without them, every `_remove` and `_add_to_head` needs special cases for `node.prev is None` and `node.next is None`. The sentinels make the code shorter and less error-prone.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Store nodes in the map, not values** — the whole O(1) guarantee collapses if you have to search the list to find a node to move; the interviewer is listening for this specific design choice.
- **Walk through an eviction with a concrete example** — trace `put` when the cache is full and show that the tail node gets unlinked and its key removed from the map; this proves you understand both data structures stay in sync.
- **Use sentinel head and tail nodes** — they eliminate four branches of null-checking in `_remove` and `_add_to_head`, which makes the code dramatically cleaner and easier to verify on the whiteboard.
- **Handle the `put` on an existing key explicitly** — this is a subtle case where you update the value and move to head *without* changing the size; forgetting it causes duplicate keys in the list.
- **State the space complexity precisely** — the map and the list share the same nodes, so it's O(capacity), not O(2 × capacity); recognizing shared ownership shows you understand the memory model.
- **Mention thread safety if asked** — a simple `Lock` around `get` and `put` serializes access; the real-world version of this structure (like `functools.lru_cache`) handles concurrency, and acknowledging that shows production awareness.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What changes if we need O(1) eviction by TTL (time-to-live) instead of by recency?** — Think about a min-heap keyed by expiration time combined with lazy deletion from the map.
- **How would you implement this in a multithreaded environment?** — Consider a reader-writer lock or sharding the cache by key range to reduce contention.
- **What if the cache needs to support `get` returning the value without updating recency (a "peek" operation)?** — This breaks the pure LRU semantics; discuss whether reads should count as uses.
- **How would you persist this cache to disk or make it survive restarts?** — Think about a write-ahead log of operations or periodic snapshots of the map and list order.
- **Can you implement LRU with a single data structure instead of two?** — Consider a `collections.OrderedDict` in Python, which combines a hash map and a doubly linked list internally; discuss the tradeoffs of using it.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**See also:** [`12. Linked_Hash_Map`](../12.%20Linked_Hash_Map/README.md) is the same hash-map-plus-doubly-linked-list structure with *insertion*-order semantics instead of *access*-order, and no capacity bound. Study the two together — an LRU cache is a linked hash map in access order with an eviction rule.
