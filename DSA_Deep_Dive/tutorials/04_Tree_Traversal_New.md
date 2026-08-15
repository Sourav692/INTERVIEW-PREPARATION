# Stack & Queue — Python Implementation Reference

## The sample tree

Every trace and code example below (and in `tree-traversal.md`, `bst-delete.md`) uses this same tree, built by inserting `50, 30, 70, 20, 40, 60, 80, 45, 90` into a BST in that order:

```
            50
          /    \
        30      70
       /  \    /  \
     20   40  60   80
            \          \
            45          90
```

```python
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

def insert(root, val):
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    else:
        root.right = insert(root.right, val)
    return root

root = None
for v in [50, 30, 70, 20, 40, 60, 80, 45, 90]:
    root = insert(root, v)
```

## Stack (LIFO) — use a plain `list`

A stack only ever touches **one end**, so Python's built-in `list` is the natural fit: `append()` adds to the end (the "top"), `pop()` removes from the end.

```python
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)   # add to the END → the "top"

    def pop(self):
        return self.items.pop()   # remove from the END → the "top"

    def peek(self):
        return self.items[-1]     # look at the END, don't remove it

    def is_empty(self):
        return len(self.items) == 0
```

Both `append()` and `pop()` (no index) are **O(1) amortized** — Python over-allocates space at the end of a list, so most calls don't need to resize.

## Queue (FIFO) — use `collections.deque`, not a plain `list`

A queue touches **both ends**: add at the back, remove at the front. This is where a plain list breaks down.

```python
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        self.items.append(item)      # add to the BACK (right end)

    def dequeue(self):
        return self.items.popleft()  # remove from the FRONT (left end)

    def peek(self):
        return self.items[0]         # look at the FRONT, don't remove it

    def is_empty(self):
        return len(self.items) == 0
```

`deque` is implemented as a doubly-linked list of fixed-size blocks, so `append()`, `appendleft()`, `pop()`, and `popleft()` are all **O(1)** — no matter which end you touch. This is exactly what `levelorder()` used in the traversal notebook (`from collections import deque`).

## The trap: a plain `list` as a queue

```python
class SlowQueue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)   # O(1) — fine, adds to the back

    def dequeue(self):
        return self.items.pop(0)  # O(n) — shifts every remaining item left!
```

This *works* — it produces the right values in the right order — but `list.pop(0)` is a hidden performance trap. A Python list is one contiguous block of memory. Removing index 0 means every remaining element has to shift one slot to the left to close the gap, which is O(n) per dequeue. Do that n times and a "should be O(n) total" BFS becomes O(n²).

## Quick reference

|                  | Data structure        | Add                              | Remove                        | Why                                                   |
| ---------------- | --------------------- | -------------------------------- | ----------------------------- | ----------------------------------------------------- |
| Stack            | `list`              | `.append(x)` — O(1) amortized | `.pop()` — O(1) amortized  | Only ever touches one end.                            |
| Queue (correct)  | `collections.deque` | `.append(x)` — O(1)           | `.popleft()` — O(1)        | Doubly-linked blocks, O(1) at both ends.              |
| Queue (the trap) | `list`              | `.append(x)` — O(1)           | `.pop(0)` — **O(n)** | Contiguous memory — front removal shifts everything. |

## Interview Notes

- If asked to implement a stack in Python, a plain `list` is the correct, idiomatic answer — no need to reach for anything fancier.
- If asked to implement a queue, the correct answer is `collections.deque`, specifically *because* `list.pop(0)` is O(n). Naming this trade-off out loud is usually exactly what the interviewer is listening for.
- `queue.Queue` (with a capital Q, from the `queue` module) is a different thing — it's a thread-safe queue meant for producer/consumer patterns across threads, with blocking `put()`/`get()`. It's overkill (and the wrong tool) for a plain single-threaded BFS.
- Python lists also support `insert(0, x)` to add at the front, but that's the same O(n) problem in the other direction — same fix applies: use `deque.appendleft()`.

## DFS traversals using the Stack class — iterative (explicit push/pop)

Same `Stack` class as above, used to drive pre/in/post-order without recursion. (Refer back to the tree diagram at the top of this doc while reading these traces.)

**Pre-order** — push right then left (so left pops first), pop and visit immediately:

```python
def preorder_iterative(root):
    if root is None:
        return []
    result = []
    stack = Stack()
    stack.push(root)
    while not stack.is_empty():
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.push(node.right)   # push right FIRST...
        if node.left:
            stack.push(node.left)    # ...then left, so left pops next (LIFO)
    return result
```

Trace: pop 50→visit, push 70,30 · pop 30→visit, push 40,20 · pop 20→visit · pop 40→visit, push 45 · pop 45→visit · pop 70→visit, push 80,60 · pop 60→visit · pop 80→visit, push 90 · pop 90→visit. Result: `50,30,20,40,45,70,60,80,90`.

**In-order** — push while walking left (to remember the way back up), pop to visit and pivot right:

```python
def inorder_iterative(root):
    result = []
    stack = Stack()
    node = root
    while not stack.is_empty() or node is not None:
        while node is not None:
            stack.push(node)      # remember: still owes a visit + right subtree
            node = node.left
        node = stack.pop()        # nothing further left → visit
        result.append(node.val)
        node = node.right
    return result
```

**Post-order** — needs two stacks: the first pops in Root→Right→Left order, pushing everything onto a second stack reverses that into Left→Right→Root:

```python
def postorder_iterative(root):
    if root is None:
        return []
    stack1, stack2 = Stack(), Stack()
    stack1.push(root)
    while not stack1.is_empty():
        node = stack1.pop()
        stack2.push(node)             # stack2 collects Root-Right-Left order
        if node.left:
            stack1.push(node.left)
        if node.right:
            stack1.push(node.right)
    result = []
    while not stack2.is_empty():
        result.append(stack2.pop().val)   # popping stack2 reverses it → Left-Right-Root
    return result
```

## DFS traversals — recursive (implicit push/pop via the call stack)

Recursion doesn't call `.push()`/`.pop()` explicitly — the language runtime pushes a frame on every call and pops it on every return. The three traversals only differ in **where** the `visit()` line sits relative to the two recursive calls.

A useful fact: the **order frames get entered** (pushed) is identical across all three traversals — `50, 30, 20, 40, 45, 70, 60, 80, 90` — because all three recurse into `node.left` before `node.right`. What differs is only *when within that shared recursion* each node's value actually gets recorded. This is the same "walk around the tree, pass every node three times" mental model from the traversal notes: entry = upper-left pass, between children = from-below pass, after both children return = upper-right pass.

**Pre-order** — record on entry, before recursing:

```python
def preorder_recursive(node, result=None):
    if result is None:
        result = []
    if node is None:
        return result
    result.append(node.val)              # visit BEFORE recursing (upper-left pass)
    preorder_recursive(node.left, result)
    preorder_recursive(node.right, result)
    return result
```

| Call (push)  | Visit now | Stack at that moment |
| ------------ | --------- | -------------------- |
| preorder(50) | 50        | [50]                 |
| preorder(30) | 30        | [50, 30]             |
| preorder(20) | 20        | [50, 30, 20]         |
| preorder(40) | 40        | [50, 30, 40]         |
| preorder(45) | 45        | [50, 30, 40, 45]     |
| preorder(70) | 70        | [50, 70]             |
| preorder(60) | 60        | [50, 70, 60]         |
| preorder(80) | 80        | [50, 70, 80]         |
| preorder(90) | 90        | [50, 70, 80, 90]     |

Each frame pops right after both of its own recursive calls return — the exact mirror image of the call order above.

**In-order** — record between the two recursive calls (from-below pass):

```python
def inorder_recursive(node, result=None):
    if result is None:
        result = []
    if node is None:
        return result
    inorder_recursive(node.left, result)
    result.append(node.val)               # visit BETWEEN children (from-below pass)
    inorder_recursive(node.right, result)
    return result
```

| Visit | Stack at that moment |
| ----- | -------------------- |
| 20    | [50, 30, 20]         |
| 30    | [50, 30]             |
| 40    | [50, 30, 40]         |
| 45    | [50, 30, 40, 45]     |
| 50    | [50]                 |
| 60    | [50, 70, 60]         |
| 70    | [50, 70]             |
| 80    | [50, 70, 80]         |
| 90    | [50, 70, 80, 90]     |

**Post-order** — record after both recursive calls return (upper-right pass):

```python
def postorder_recursive(node, result=None):
    if result is None:
        result = []
    if node is None:
        return result
    postorder_recursive(node.left, result)
    postorder_recursive(node.right, result)
    result.append(node.val)               # visit AFTER both children (upper-right pass)
    return result
```

| Visit | Stack at that moment |
| ----- | -------------------- |
| 20    | [50, 30, 20]         |
| 45    | [50, 30, 40, 45]     |
| 40    | [50, 30, 40]         |
| 30    | [50, 30]             |
| 60    | [50, 70, 60]         |
| 90    | [50, 70, 80, 90]     |
| 80    | [50, 70, 80]         |
| 70    | [50, 70]             |
| 50    | [50]                 |

All six functions (3 iterative + 3 recursive) were run against the same sample tree and verified to match the known-correct sequences before writing this up.

## Related deliverable

Interactive HTML explorer (push/pop or enqueue/dequeue by hand across three modes — Stack/list, Queue/deque, Queue/plain-list — with live code-line highlighting, an animated container, and an operation log that calls out the O(n) shift) delivered and saved as a Cowork artifact: "stack-queue-python-explorer".
