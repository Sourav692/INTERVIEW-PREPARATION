# Confluence Page Word Count — Explained Simply

## The Problem

Confluence pages form a tree (a page has child pages). You need `subtreeWordCount(page)`: the total word frequency across a page **and every page below it**.

Example tree:

```
Home ("the cat sat")
├── Child ("the cat")
└── Child2 ("sat sat")
```

Expected: `subtreeWordCount(Home) -> {"the": 2, "cat": 2, "sat": 3}`

## Why the Obvious Way Is Slow

The tempting shortcut: concatenate every descendant's text into one giant string, then tokenize that once per call.

```
def subtree_naive(page):
    all_text = page.content
    for child in page.children:
        all_text += " " + collect_everything_under(child)   # re-walks the whole subtree's text
    return count_words(all_text)
```

This *looks* like "one pass," and for a single call it even costs the same as the good version. The real problem shows up if `subtreeWordCount` is called again from a different ancestor, or repeatedly by a user browsing the tree: every single call re-tokenizes the same raw text from scratch, throwing away all the work a smarter approach could have reused.

## The Simple Trick: Solve Each Child, Then Just Add

Don't think "tokenize the whole subtree." Think: **"my answer = my own words, plus each child's answer, added together."** Each page only ever tokenizes its *own* content, exactly once — the combining step is pure addition of dictionaries.

## An Analogy First: A Company's Total Headcount

Imagine you're the CEO and you want the total employee count for the whole company. You don't personally go count every single employee in every department. Instead, you ask each direct report: "how many people report up through you, total?" Each of them asks *their* direct reports the same question, all the way down to a manager with no reports, who just answers "however many people are directly on my team."

Then the answers bubble back up: each manager adds their own team's count to what their sub-managers reported, and passes the sum upward. By the time it reaches you, you have the total — and nobody ever double-counted or re-walked the org chart twice.

## Step-by-Step Example (Narrated)

Tree: `Home("the cat sat")` → children `Child("the cat")`, `Child2("sat sat")`.

We compute `subtreeWordCount` **bottom-up** (post-order): finish all of a node's children before combining.

---

**Visit `Child` (a leaf — no children of its own)**
Tokenize its own content `"the cat"` → `{"the": 1, "cat": 1}`.
It has no children to add, so this **is** its final subtree answer.
`subtreeWordCount(Child) = {"the": 1, "cat": 1}`

---

**Visit `Child2` (a leaf)**
Tokenize its own content `"sat sat"` → `{"sat": 2}`.
No children. Final answer: `subtreeWordCount(Child2) = {"sat": 2}`

---

**Visit `Home` (now that both children are done)**
Tokenize its own content `"the cat sat"` → `{"the": 1, "cat": 1, "sat": 1}`. This is *Home's own* count — nothing from its children yet.
Now **add** `Child`'s subtree answer: `{"the": 1, "cat": 1}` → running total becomes `{"the": 2, "cat": 2, "sat": 1}`.
Now **add** `Child2`'s subtree answer: `{"sat": 2}` → running total becomes `{"the": 2, "cat": 2, "sat": 3}`.

---

Final: `subtreeWordCount(Home) = {"the": 2, "cat": 2, "sat": 3}` — matches the expected output exactly.

### The one detail that's easy to miss: order doesn't matter, but *completeness* does

You must finish computing **all** of a node's children before you combine them into the parent — that's why this is called "post-order." If you tried to add `Home`'s own words to `Child`'s answer *before* `Child` had finished asking its own children, you'd combine an incomplete number. The recursion naturally enforces this: a function call to `solve(child)` doesn't return until that entire branch is done.

## Plain-English Walkthrough

1. If the page has no children, its answer is just its own word count.
2. Otherwise, start with the page's own word count.
3. For each child, recursively get that child's subtree answer, and add it into the running total (word by word).
4. Once all children are added, that running total is the page's own subtree answer — hand it up to whoever asked.

## Simple Python Code

```python
import re
from collections import Counter

def word_count(page):
    words = re.findall(r"[a-zA-Z0-9]+", page.content.lower())
    return Counter(words)

def subtree_word_count(page):
    total = word_count(page)              # start with this page's own words
    for child in page.children:
        total.update(subtree_word_count(child))   # add the child's subtree answer
    return dict(total)

class Page:
    def __init__(self, content, children=None):
        self.content = content
        self.children = children or []

home = Page("the cat sat", [Page("the cat"), Page("sat sat")])
print(subtree_word_count(home))  # {'the': 2, 'cat': 2, 'sat': 3}
```

## Why `Counter.update()` Instead of a Manual Loop?

`Counter` is a dict built specifically for counting, and `.update(other_counter)` already knows how to add matching keys together (and create new keys for anything it hasn't seen). Writing `for word, count in child.items(): total[word] += count` does the exact same thing, just with more code — `Counter` is the idiomatic shortcut for "merge these two frequency tallies."

## Complexity

- **Time:** O(N·M) — N total pages, each page's content (average length M) tokenized exactly once.
- **Space:** O(N·U) for the aggregated dictionaries (U = unique words per page), plus O(depth) for the recursion stack.

## The Reusable Pattern

This is the **"post-order tree aggregation"** pattern — any time a problem asks "give me a total/sum/count for a subtree," this shape applies:

- Size or height of a tree
- Sum of all values in a subtree
- Lowest Common Ancestor (see *Company Hierarchy*)
- Directory size on a real file system (folder size = its own files + every subfolder's size)

Core idea: `answer(node) = own_contribution(node) + combine(answer(child) for child in node.children)` — never re-derive what a child has already computed.
