s

## DFS Traversals via Explicit Push/Pop

Recursion secretly uses a stack (the call stack). If you strip the recursion away and manage that stack yourself, you get the iterative versions — and now the push/pop calls are visible instead of implicit. Reusing the same `Stack` class from the earlier explorer:

```python
class Stack:
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        return self.items.pop()
    def is_empty(self):
        return len(self.items) == 0
```

### Pre-order (Root → Left → Right)

```python
def preorder_iterative(root):
    if root is None:
        return []
    result = []
    stack = Stack()
    stack.push(root)                  # seed with the root
    while not stack.is_empty():
        node = stack.pop()            # pop → this is the node we visit
        result.append(node.val)
        if node.right:
            stack.push(node.right)    # push right FIRST...
        if node.left:
            stack.push(node.left)     # ...then push left, so left pops next (LIFO)
    return result
```

The trick is entirely in the push order: since a stack is LIFO, whatever you push *last* comes back out *first*. Pushing right before left means left is on top, so it gets popped — and visited — before right.

Trace on the usual tree (`50` root, `30/70` children, etc.):

| Step | Pop → visit | Push   | Stack after  |
| ---- | ------------ | ------ | ------------ |
| 1    | 50           | 70, 30 | [70, 30]     |
| 2    | 30           | 40, 20 | [70, 40, 20] |
| 3    | 20           | —     | [70, 40]     |
| 4    | 40           | 45     | [70, 45]     |
| 5    | 45           | —     | [70]         |
| 6    | 70           | 80, 60 | [80, 60]     |
| 7    | 60           | —     | [80]         |
| 8    | 80           | 90     | [90]         |
| 9    | 90           | —     | []           |

Result: `50, 30, 20, 40, 45, 70, 60, 80, 90` ✓

### In-order (Left → Root → Right)

Pre-order's trick doesn't work here — you can't just look at a node and decide whether to visit it immediately, because you first have to fully finish its *entire* left subtree. So the pattern changes: push while walking left (that's how you remember the path back up), and pop when you're ready to actually visit and move right.

```python
def inorder_iterative(root):
    result = []
    stack = Stack()
    node = root
    while not stack.is_empty() or node is not None:
        while node is not None:
            stack.push(node)          # remember this node — still owes us a visit + its right subtree
            node = node.left
        node = stack.pop()            # nothing further left → visit the most recent unfinished node
        result.append(node.val)
        node = node.right             # now go explore its right subtree the same way
    return result
```

Notice pushing and popping are no longer paired one-to-one per node the way they were in pre-order — you push a whole chain of left-children before popping any of them. For node `50`: push `50 → 30 → 20` (all the way left), then pop `20` (visit), pop `30` (visit, then go right into `40`), push `40 → 45`... and so on. Result: `20, 30, 40, 45, 50, 60, 70, 80, 90` — sorted, as expected for a BST.

### Post-order (Left → Right → Root)

Post-order is the awkward one with a single stack, because by the time you pop a node you may not have finished its children yet. The clean workaround: use **two** stacks. The first one pops nodes in a Root → Right → Left order (a mirror image of pre-order); pushing everything it pops onto a second stack automatically reverses that into Left → Right → Root.

```python
def postorder_iterative(root):
    if root is None:
        return []
    stack1 = Stack()
    stack2 = Stack()
    stack1.push(root)
    while not stack1.is_empty():
        node = stack1.pop()
        stack2.push(node)             # stack2 collects nodes in Root-Right-Left order
        if node.left:
            stack1.push(node.left)
        if node.right:
            stack1.push(node.right)
    result = []
    while not stack2.is_empty():
        result.append(stack2.pop().val)   # popping stack2 reverses it → Left-Right-Root
    return result
```

Trace of `stack1` (building Root-Right-Left into `stack2`):

| Step | Pop from stack1 → push to stack2 | Push onto stack1 |
| ---- | --------------------------------- | ---------------- |
| 1    | 50                                | 30, 70           |
| 2    | 70                                | 60, 80           |
| 3    | 80                                | 90               |
| 4    | 90                                | —               |
| 5    | 60                                | —               |
| 6    | 30                                | 20, 40           |
| 7    | 40                                | 45               |
| 8    | 45                                | —               |
| 9    | 20                                | —               |

`stack2` now holds, bottom-to-top: `50, 70, 80, 90, 60, 30, 40, 45, 20`. Popping it off (LIFO reverses it) gives: `20, 45, 40, 30, 60, 90, 80, 70, 50` ✓ — matches the correct post-order.

### The pattern across all three

- **Pre-order**: push order controls everything — push right, then left, pop and visit immediately.
- **In-order**: push while descending left (to remember the way back), pop to visit and pivot right.
- **Post-order**: one pop-and-push cycle isn't enough for a single stack to get the order right, so a second stack does the reversal for you.

I ran all three against the same sample tree and confirmed they match the known-correct sequences (`50,30,20,40,45,70,60,80,90` / `20,30,40,45,50,60,70,80,90` / `20,45,40,30,60,90,80,70,50`) before writing this up. Since this connects directly to the Stack class from the last explorer, I'll fold this push/pop code into your `stack-queue-python.md` project notes as a short addition rather than a new file.
