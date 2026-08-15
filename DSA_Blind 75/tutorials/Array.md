# 📊 Array — Concept Tutorial

> A plain-language guide to the ideas behind the Blind 75 **Array** problems, with diagrams.
> Pair this with the interactive pages in `visualizations/Array/` and the runnable `notebooks/Array/`.

---

## 1. What is an Array?

An **array** is a row of boxes, each holding a value, each with a numbered position (its **index**, starting at 0). Because the boxes sit next to each other in memory, you can jump to any index instantly.

```mermaid
flowchart LR
    A["index 0<br/>2"] --- B["index 1<br/>7"] --- C["index 2<br/>11"] --- D["index 3<br/>15"]
```

- **Read/write by index:** `O(1)` (instant).
- **Search for a value:** `O(n)` (you may have to look at everything).
- **The whole game** with array problems is: *avoid the slow nested-loop scan* by using a smarter idea.

---

## 2. The Core Patterns

Almost every Blind 75 array problem is one of five ideas.

### 🧠 Pattern A — Remember What You've Seen (Hash Map / Set)

Instead of comparing every pair (slow, `O(n²)`), walk once and remember what you've passed in a hash map. Then each new element just does an instant lookup.

```mermaid
flowchart TD
    S["For each number x"] --> Q{"Have I seen<br/>its partner<br/>(target − x)?"}
    Q -->|Yes| F["Found the pair! ✅"]
    Q -->|No| R["Remember x, move on"]
    R --> S
```

**The tell:** *"find two things that add up to X"*, *"any duplicates?"*, *"does a value exist?"*
**Turns** `O(n²)` **into** `O(n)`.
**Problems:** Two Sum, Contains Duplicate.

---

### 👉👈 Pattern B — Two Pointers From Both Ends

On a **sorted** array (or a symmetric one), put one finger at each end and move them toward the middle. The order tells you which finger to move.

```mermaid
flowchart LR
    subgraph Sorted Array
      A["2"] --- B["7"] --- C["11"] --- D["15"]
    end
    L(("L")) -.-> A
    R(("R")) -.-> D
```

Decision each step:

```mermaid
flowchart TD
    C{"sum of the two ends<br/>vs target"} -->|too small| ML["move LEFT finger right<br/>(get bigger)"]
    C -->|too big| MR["move RIGHT finger left<br/>(get smaller)"]
    C -->|equal| DONE["found it! ✅"]
```

**The tell:** sorted data, *"a pair/triple"*, *"max area / min·distance"*.
**Cost:** one `O(n)` sweep, `O(1)` memory.
**Problems:** 3Sum, Container With Most Water. (Two Sum too, if sorted.)

---

### 🏃 Pattern C — One Pass, Keep a Running Best

When each element's answer depends only on a running summary of everything before it, keep that summary in a variable — no inner loop.

```mermaid
flowchart LR
    subgraph "walk left → right"
      direction LR
      P1["cheapest so far"] --> P2["best profit so far"]
    end
```

Kadane's algorithm (Maximum Subarray) is the classic:

```mermaid
flowchart TD
    N["new number x"] --> D{"running sum + x<br/>vs x alone"}
    D -->|"extend is better"| E["running += x"]
    D -->|"x alone is better"| R["restart run at x"]
    E --> B["update best"]
    R --> B
```

**The tell:** *"best profit"*, *"largest/smallest run"*, *"max difference where one comes before the other"*.
**Problems:** Best Time to Buy & Sell Stock, Maximum Subarray, Maximum Product Subarray (track **both** max and min because negatives flip them).

---

### ↔️ Pattern D — Build From Both Directions (Prefix / Suffix)

When each answer needs *"everything on one side"*, precompute running results from the left and from the right, then combine.

```mermaid
flowchart LR
    subgraph "nums"
      n1["1"] --- n2["2"] --- n3["3"] --- n4["4"]
    end
    subgraph "prefix (product of everything left)"
      p1["1"] --- p2["1"] --- p3["2"] --- p4["6"]
    end
    subgraph "suffix (product of everything right)"
      s1["24"] --- s2["12"] --- s3["4"] --- s4["1"]
    end
```

Answer[i] = prefix[i] × suffix[i]. No division needed.
**The tell:** *"combine everything except me"*, range sums/products.
**Problems:** Product of Array Except Self.

---

### ✂️ Pattern E — Halve the Search (Binary Search)

If the data is **sorted** — even *sorted-then-rotated* — you can throw away half each step.

```mermaid
flowchart TD
    M["look at the middle"] --> D{"which half<br/>must hold<br/>the answer?"}
    D -->|left| KL["keep left half"]
    D -->|right| KR["keep right half"]
    KL --> M
    KR --> M
```

For a **rotated** array, first work out which half is in proper order, then decide.
**The tell:** *"O(log n)"*, *"sorted"*, *"find pivot / target in rotated array"*.
**Problems:** Find Minimum in Rotated Sorted Array, Search in Rotated Sorted Array.

---

## 3. Which Pattern for Which Problem?

```mermaid
mindmap
  root((Array))
    Hash Map
      Two Sum
      Contains Duplicate
    Two Pointers
      3Sum
      Container With Most Water
    Running Value
      Best Time to Buy Sell
      Maximum Subarray
      Maximum Product Subarray
    Prefix / Suffix
      Product of Array Except Self
    Binary Search
      Find Minimum in Rotated
      Search in Rotated
```

---

## 4. Complexity Cheat Sheet

| Pattern | Time | Space |
|---|---|---|
| Hash map lookup | `O(n)` | `O(n)` |
| Two pointers (sorted) | `O(n)` (+ sort) | `O(1)` |
| Running value (Kadane) | `O(n)` | `O(1)` |
| Prefix / suffix | `O(n)` | `O(1)` extra |
| Binary search | `O(log n)` | `O(1)` |

---

## 5. Interview Playbook

1. **Say the brute force first** — "check every pair, that's O(n²)" — to show you understand the problem.
2. **Look for a tell:** searching for a match → *hash map*; sorted → *two pointers* or *binary search*; best run → *running value*; "everything except me" → *prefix/suffix*.
3. **State the speed** of your better idea and why it's faster.
4. **Test a tiny example by hand** before coding (the interactive pages do exactly this).

> ▶ **Next:** open `visualizations/Array/index.html` to watch each of these run step by step.
