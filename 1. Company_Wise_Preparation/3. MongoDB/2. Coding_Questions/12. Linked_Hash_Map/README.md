# Linked Hash Map

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Hash Tables, Linked List · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Implement a linked Hash Map.

---

## Study Tools

### Hint 1

A hash map gives you O(1) lookups by key, but it loses insertion order. Think about what extra pointer each entry needs to carry so you can still traverse the entries in the order they were added.

### Hint 2

You need a doubly linked list threaded through the same nodes the hash table buckets point to. Keeping head and tail sentinels makes the splice-out and append operations branch-free.

### Hint 3

On `put`, if the key exists you update the value and move its node to the tail; otherwise you create a node, append it to the tail, and hash it into the bucket. On `get`, move the touched node to the tail too if you want access-order semantics like an LRU.

---

### Answer

This is a hash map augmented with a doubly linked list through the entries. A plain Python `dict` handles the hashing and collision resolution; the linked list gives you stable iteration order and O(1) reordering. I'll implement the standard interpretation of a Java-style `LinkedHashMap` with insertion-order iteration.

```python
class _Node:
    __slots__ = ('key', 'value', 'prev', 'next')

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LinkedHashMap:
    def __init__(self):
        self._map = {}          # key -> _Node
        self._head = _Node()    # sentinel, least recently inserted
        self._tail = _Node()    # sentinel, most recently inserted
        self._head.next = self._tail
        self._tail.prev = self._head

    def _append_to_tail(self, node):
        last = self._tail.prev
        last.next = node
        node.prev = last
        node.next = self._tail
        self._tail.prev = node

    def _unlink(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None

    def put(self, key, value):
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._unlink(node)
            self._append_to_tail(node)
        else:
            node = _Node(key, value)
            self._map[key] = node
            self._append_to_tail(node)

    def get(self, key):
        node = self._map.get(key)
        if node is None:
            return None
        return node.value

    def remove(self, key):
        node = self._map.pop(key, None)
        if node is None:
            return None
        self._unlink(node)
        return node.value

    def __contains__(self, key):
        return key in self._map

    def __len__(self):
        return len(self._map)

    def __iter__(self):
        cur = self._head.next
        while cur is not self._tail:
            yield cur.key
            cur = cur.next

    def items(self):
        cur = self._head.next
        while cur is not self._tail:
            yield (cur.key, cur.value)
            cur = cur.next
```

**Time:** O(1) average for `put`, `get`, `remove`, and `__contains__` — all hash-table operations are O(1) average and the linked-list splice/append is constant time.
**Space:** O(n) — one `_Node` per entry plus the dict overhead.

**Correctness:** The invariant is that the doubly linked list order always matches insertion order. On first `put` of a key, `_append_to_tail` places the node after the current tail sentinel's predecessor, so it becomes the last entry. On re-`put`, `_unlink` detaches the node and `_append_to_tail` reattaches it at the end, preserving the property that the most recently written key is last. `remove` deletes from both structures, so a key can never appear in the list but not the map or vice versa. Iteration walks the list, which by the invariant yields insertion order.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive baseline: a list of `(key, value)` pairs. `get` and `put` are O(n) because you scan the list, and `remove` is O(n). That's the thing you're trying to beat.

The first upgrade is a plain `dict`, which gives O(1) `get`, `put`, and `remove`. But now iteration order is arbitrary in older Python versions and insertion-ordered in 3.7+, but you can't *reorder* entries. The bottleneck is that a bare hash table has no notion of sequence.

The key decision is to make the hash table store **node references** instead of raw values. Each node has `prev` and `next` pointers, so the same object lives in both the bucket chain and the linked list. Now `put` on a new key is O(1): create the node, append to tail, hash it. `put` on an existing key is O(1): update the value, unlink from the list, re-append to tail. You're paying one extra pointer hop per operation, which is negligible.

Why sentinel nodes for head and tail? Without them, `_append_to_tail` needs three branches: empty list, one element, many elements. With sentinels, the list is never empty from the perspective of the splice code, so `_append_to_tail` and `_unlink` are each four pointer assignments with no conditionals. That's the kind of simplification that prevents off-by-one bugs when you're coding under pressure.

If the interviewer asks for **access-order** instead of insertion-order, the only change is that `get` also unlinks and re-appends the node to the tail. That turns this into the core of an LRU cache, which is probably where the conversation goes next.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Name the data structure combination up front** — saying "hash table plus doubly linked list through the same nodes" in the first minute tells the interviewer you see the whole design before you write a line.
- **Use sentinel nodes** — head and tail as empty `_Node` objects eliminate the empty-list special case from both `_append_to_tail` and `_unlink`, which is where most implementations of this question pick up bugs.
- **Store nodes in the map, not just values** — the moment you say `self._map[key]` returns a `_Node`, the O(1) reordering on `put` becomes obvious, and the interviewer knows you understand the memory layout.
- **Be explicit about re-`put` semantics** — updating an existing key's value and moving it to the tail is the behavior a Java `LinkedHashMap` gives you by default, and saying so shows you've thought about the contract rather than just the happy path.
- **Mention the access-order variant** — pointing out that moving a node on `get` gives you an LRU cache signals you've seen this pattern before and can adapt it when the follow-up lands.
- **Trace the `_unlink` pointer assignments carefully** — `node.prev.next = node.next` and `node.next.prev = node.prev` *before* clearing `node.prev` and `node.next` is the exact sequence that prevents dangling references, and walking through it out loud catches mistakes early.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Change the iteration order to access-order** — move the touched node to the tail inside `get` as well as `put`. Think about how this changes the `get` method and what data structure you've just built.
- **Implement an LRU cache with a capacity limit on top of this** — evict the head node when `len` exceeds capacity. You already have the `_unlink` and `_append_to_tail` primitives; the eviction is one line.
- **Make `put` return the previous value associated with the key, or `None` if there was none.** — You need to capture the old value before overwriting it in the existing-key branch.
- **Add an `__eq__` method that compares two `LinkedHashMap` instances by their iteration order and values.** — Walk both lists in lockstep and compare key-value pairs.
- **What's the worst-case time complexity of `put` and `get`?** — Hash collisions can degrade to O(n) in the pathological case; mention how Python's dict handles collisions with open addressing and why average case is the relevant bound.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One correction to the official answer

The official `put` **moves an existing key's node to the tail** on update. That is *not* what Java's `LinkedHashMap` does in its default (insertion-order) mode, and the answer's own correctness paragraph asserts "the list order always matches insertion order" — the two claims contradict each other.

Java's `LinkedHashMap`:

- **insertion-order mode (default):** re-putting an existing key updates the value and **leaves its position alone**.
- **access-order mode** (`accessOrder=true`, the LRU building block): both `get` *and* `put` move the entry to the end.

The notebook implements both modes explicitly and asserts the difference, since choosing between them — and saying which you chose — is the actual content of this question. See also [`10. LRU_Cache`](../10.%20LRU_Cache/README.md), which is this structure in access order with an eviction rule.
