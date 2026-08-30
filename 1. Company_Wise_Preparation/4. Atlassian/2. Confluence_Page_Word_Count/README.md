# Confluence Page Word Count

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Hash Tables, Strings, Trees · **Difficulty/Frequency:** Very Common (7/10)

---

## Problem Statement

You are building an analytics feature for Confluence that counts words across a page hierarchy.

A Confluence space is represented as a tree. Each node has:

```python
class Page:
    def __init__(self, page_id: str, title: str, content: str, children: List['Page']):
        ...
```

### Word counting rules

- Words are sequences of alphanumeric characters (split on spaces, punctuation, and newlines).
- Counting is case-insensitive ("Hello" and "hello" are the same word).

### Part 1: Single Page Word Count

Implement `wordCount(page: Page) -> dict`

Return a dictionary mapping each word to its frequency within that page's content only.

### Part 2: Subtree Word Count

Implement `subtreeWordCount(page: Page) -> dict`

Return the aggregated word count across the given page and all its descendants.

### Part 3: Top Words in Subtree

Implement `topWords(page: Page, k: int, exclude: List[str]) -> List[str]`

Return the top k most frequent words in the subtree rooted at page, excluding any words in the exclude list. Return words sorted by frequency descending; break ties alphabetically.

### Example

```python
root = Page("p1", "Home", "the cat sat", [
    Page("p2", "Child", "the cat", []),
    Page("p3", "Child2", "sat sat", [])
])

subtreeWordCount(root)
# -> {"the": 2, "cat": 2, "sat": 3}

topWords(root, k=2, exclude=["the"])
# -> ["sat", "cat"]
```

### Follow-up (as posed with the problem)

If pages are very large and the tree has thousands of nodes, how would you make `subtreeWordCount` more efficient using memoization or lazy evaluation?

---

## Study Tools

### Hint 1

The core operation is tokenizing content into lowercase alphanumeric words. Python's `re` module can split on non-alphanumeric boundaries in one pass, which is much cleaner than manual character scanning.

### Hint 2

For the subtree aggregation, don't re-tokenize descendant pages repeatedly. Each page's own word count can be computed once, and the subtree result is the sum of the page's own count plus the subtree counts of its children.

### Hint 3

For `topWords`, you don't need to sort all words when k is small. Use a heap of size k keyed by `(-freq, word)` to keep only the top candidates, or sort once with a custom tuple key.

---

### Answer

This is a tree aggregation problem where the key insight is to compute each page's own word count once, then build subtree counts bottom-up by merging child dictionaries. For the top-k part, use a heap or sorted tuples to handle frequency and alphabetical tie-breaking efficiently.

#### Tokenization

Words are sequences of alphanumeric characters, case-insensitive. The cleanest approach is `re.findall(r'[a-zA-Z0-9]+', content.lower())` which extracts all alphanumeric runs directly and handles spaces, punctuation, and newlines uniformly.

```python
import re
from collections import Counter
from typing import List, Dict
import heapq

class Page:
    def __init__(self, page_id: str, title: str, content: str, children: List['Page']):
        self.page_id = page_id
        self.title = title
        self.content = content
        self.children = children

def wordCount(page: Page) -> Dict[str, int]:
    """Count words in a single page's content."""
    words = re.findall(r'[a-zA-Z0-9]+', page.content.lower())
    return dict(Counter(words))

def subtreeWordCount(page: Page) -> Dict[str, int]:
    """Aggregate word counts across the page and all descendants."""
    result = Counter(wordCount(page))
    for child in page.children:
        child_counts = subtreeWordCount(child)
        for word, count in child_counts.items():
            result[word] += count
    return dict(result)

def topWords(page: Page, k: int, exclude: List[str]) -> List[str]:
    """Return top k most frequent words in subtree, excluding given words."""
    counts = subtreeWordCount(page)
    exclude_set = set(exclude)

    # Build list of (-freq, word) tuples for sorting
    candidates = [(-count, word) for word, count in counts.items() if word not in exclude_set]

    # Sort by (-freq, word): highest frequency first, then alphabetical
    candidates.sort()

    return [word for _, word in candidates[:k]]
```

**Time:** O(N·M) where N is total nodes and M is average content length — each page's content is tokenized once, and dictionary merges are proportional to unique words per page. **Space:** O(N·U) where U is unique words per page — the recursion stack plus aggregated dictionaries.

**Correctness:** The tokenization regex correctly extracts alphanumeric sequences, and `.lower()` ensures case-insensitivity. For subtree aggregation, the recursive structure guarantees each page is visited exactly once, and the merge operation is associative and commutative, so the order of children doesn't matter. For `topWords`, sorting by `(-count, word)` ensures descending frequency with alphabetical tie-breaking, and slicing `[:k]` returns exactly the top k words (or fewer if not enough candidates exist).

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that works: tokenize one page's content. You'd probably write a loop that splits on spaces, strips punctuation, and lowercases — but that's error-prone with edge cases like multiple spaces, tabs, or punctuation adjacent to words. The regex `re.findall(r'[a-zA-Z0-9]+', content.lower())` handles all of that in one line and is the standard idiom.

For the single-page count, `Counter` is the obvious choice — it's built for exactly this frequency-tallying job. `Counter(words)` gives you the dict directly.

Now for the subtree. The naive approach would be to concatenate all content in the subtree and tokenize once, but that's wasteful — you'd re-tokenize the same descendant content every time you call `subtreeWordCount` from a different ancestor. Instead, think recursively: each page's subtree count is its own count plus the subtree counts of its children. This is a classic bottom-up tree aggregation. The key decision is whether to mutate dictionaries in place or create new ones. Creating new `Counter` objects and merging is cleaner and avoids side effects, but if you're worried about performance with very large trees, you could pass the parent's counter down and have children accumulate into it.

For `topWords`, you have the full frequency dict from `subtreeWordCount`. The straightforward approach is to filter out excluded words, then sort. The sort key needs to be a tuple `(-count, word)` because you want descending frequency but ascending alphabetical order — negating the count lets one sort call handle both. If k is small relative to the number of unique words, a heap of size k would be more efficient, but for interview purposes, sorting is usually acceptable and clearer. Mention the heap optimization as a follow-up if asked.

The time complexity is dominated by tokenization — each character in each page's content is scanned once by the regex. The dictionary merges add overhead proportional to unique words, but that's typically much smaller than content size. Space is proportional to the total unique vocabulary across the subtree.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Regex tokenization** — using `re.findall` with a character class shows you know the standard library and avoids a dozen edge cases with punctuation and whitespace. Mention that `\w+` would also work but explicitly listing `[a-zA-Z0-9]+` is safer if the input might contain Unicode.
- **`Counter` vs plain dict** — `Counter` is the idiomatic choice for frequency counting, and its `update` method makes merging child counts clean. Interviewers want to see you reach for the right tool rather than reinventing it.
- **Recursive aggregation pattern** — the bottom-up tree traversal where each node returns its aggregated result is the core algorithmic insight. State the recurrence explicitly: `subtree(node) = own_count(node) + sum(subtree(child) for child in node.children)`.
- **Sort key tuple** — using `(-count, word)` as the sort key handles both frequency and alphabetical tie-breaking in one pass. This is a common idiom that shows you understand Python's sorting semantics.
- **Filtering before sorting** — applying the exclude filter before sorting reduces the candidate set and avoids having to check exclusion during the sort comparison. It also makes the code cleaner.
- **Edge cases** — empty content, empty children list, k larger than the number of unique words, and case differences like "Hello" vs "hello" all need to be handled correctly. The regex and `Counter` approach naturally handles most of these.
- **Memoization potential** — if this were called repeatedly on the same tree, you could cache each node's subtree count. The follow-up question is hinting at this, so mentioning it proactively shows you're thinking about real-world performance.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Add memoization to `subtreeWordCount`** so repeated calls on the same tree don't recompute — store the result on each `Page` object or use a `functools.lru_cache` keyed by `page_id`.
- **What if k is very large relative to unique words?** — consider using `heapq.nlargest` with a custom key, or `Counter.most_common` which uses a heap internally.
- **How would you handle streaming or very large content that doesn't fit in memory?** — process content in chunks, use a disk-backed counter, or consider a MapReduce approach.
- **What if the tree is very deep and you hit Python's recursion limit?** — convert to an iterative post-order traversal using an explicit stack.
- **How would you support incremental updates when a page's content changes?** — invalidate cached subtree counts along the path from the changed node to the root.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
