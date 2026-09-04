# Regex Checking — Explained Simply

## The Problem

Does a string match a pattern? The pattern can contain `+`, meaning **"the character before me, one or more times"**.

```
s = "google",  p = "go+gle"   →  True     (o+ swallows both o's)
s = "gogle",   p = "go+gle"   →  True     (o+ swallows one)
s = "ggle",    p = "go+gle"   →  False    (+ needs at LEAST one o)
```

The match must cover the **whole** string — not just a prefix.

## The Difficulty in One Sentence

> **You can't tell how many characters the `+` should swallow by looking at it.**

Given `s = "aaa"` and `p = "a+"`, the `+` should take all three. But given `s = "aaa"` and `p = "a+aa"`, it should take only **one** — the other two are needed by the rest of the pattern.

The `+` has no idea what comes after it. So you can't be greedy ("take everything"), and you can't be lazy ("take one"). **You have to try both and see which works.**

## An Analogy First: Packing a Suitcase

You're packing a suitcase with a list: *"some socks, then a jumper, then shoes."*

How many socks? The list says "some" — at least one, but it doesn't say how many.

If you stuff in as many socks as possible, there may be no room left for the jumper and shoes. If you pack just one, you might have wasted space.

**You can't decide locally.** The right number of socks depends on what still has to fit afterwards.

So you try: pack one sock, then ask *"can the rest of the list fit in what's left?"* If yes, done. If no, back up, pack **two** socks, and ask again.

That "try, and if it fails back up and try differently" is exactly what the recursion does. It's called **backtracking**.

## The Transitions

Everything is captured by a state `(i, j)` — how far into the string, how far into the pattern:

| Situation | What to do |
|---|---|
| Pattern is finished (`j == len(p)`) | Match **only if** the string is finished too |
| Next pattern char is `+`, and `s[i]` matches `p[j]` | Consume one, then **branch**: `(i+1, j)` take another, **or** `(i+1, j+2)` move on |
| Next pattern char is `+`, but `s[i]` doesn't match | **Fail** — `+` needs at least one |
| Plain character, matches | `(i+1, j+1)` |
| Plain character, doesn't match | **Fail** |

Note the `+` case is the *only* one that branches. Everything else is forced.

### Why `j + 2` and not `j + 1`?

Because a `+` group occupies **two** characters of the pattern: the character and the `+`. To move past `o+` entirely you skip both.

And to *stay* on the group — to take another copy — you leave `j` exactly where it is, so the next iteration sees the same `o+` again.

## Step-by-Step Example (Narrated)

`s = "google"` (`g o o g l e`), `p = "go+gle"`.

---

**`(0,0)`** — `s[0]='g'`, `p[0]='g'`. Is `p[1]` a `+`? No, it's `'o'`. Plain match → **`(1,1)`**

---

**`(1,1)`** — `s[1]='o'`, `p[1]='o'`. Is `p[2]` a `+`? **Yes.**

`s[1]` matches `p[1]`, so consume one `o` and **branch two ways**:

- **Branch A:** `(2,1)` — stay on the `o+`, try to take another
- **Branch B:** `(2,3)` — move past the `o+`, next pattern char is `p[3]='g'`

---

**Try Branch A first: `(2,1)`**

`s[2]='o'`, `p[1]='o'`, `p[2]` is `+`. Match again → branch:

- `(3,1)` — take a third `o`
- `(3,3)` — move on

---

**`(3,1)`** — `s[3]='g'`, `p[1]='o'`. **No match.** `+` fails here. ❌ Back up.

---

**`(3,3)`** — `s[3]='g'`, `p[3]='g'`, `p[4]='l'` isn't `+`. Plain match → `(4,4)`

`(4,4)` — `'l'` vs `'l'` → `(5,5)`
`(5,5)` — `'e'` vs `'e'` → `(6,6)`

`j == len(p)` **and** `i == len(s)`. ✅ **MATCH.**

---

Notice Branch B (`(2,3)`) would have compared `s[2]='o'` against `p[3]='g'` and failed. **The branch that works isn't the first one you'd guess** — which is exactly why you must try both.

## The Two Off-by-Ones

### 1. Check bounds before peeking at `p[j+1]`

```python
if j + 1 < len(p) and p[j + 1] == '+':
```

Without the bounds check, a pattern ending in a plain character indexes off the end.

### 2. The base case needs **both** pointers finished

```python
if j == len(p):
    return i == len(s)       # ✅ both
```

- Checking only `i == len(s)` would accept `"go"` against `"google"` — string done, pattern isn't.
- Checking only `j == len(p)` would accept `"googlexyz"` against `"google"` — pattern done, string isn't.

## The Big One: This Recursion Is Exponential

Here's a genuine error in the official answer. It claims:

> *"O(n × m) worst case — each (i, j) pair is visited once with memoization, **or the recursion tree has at most n × m distinct states without it**."*

...and then shows code with **no memoization**.

The number of distinct *states* is n × m. But without caching, what matters is the number of **paths** through those states — and every `+` doubles the paths.

Consider `"a"*22` against `"a+a+a+a+a+a+a+a+b"`. Every `+` branches two ways, all the branches reach the same states by different routes, and nothing prunes because the trailing `b` never matches.

The notebook measures it:

```
un-memoised: 1,200,739 calls,  409.1 ms
memoised:          171 calls,    0.4 ms   (state space is only 414)
```

**A million calls to compute 171 distinct answers.**

> **Counting states is not the same as counting paths.**

## The Fix Is One Line

```python
@lru_cache(maxsize=None)          # ← that's it
def dfs(i, j):
    ...
```

Why is caching *valid* here? Because of a property worth naming:

> **The answer at `(i, j)` depends only on `i` and `j` — never on how you got there.**

That's the condition for memoization. If the answer also depended on "how many copies have I taken so far", the state would need a third component and a two-element cache key would be wrong.

Once the state fully determines the answer, and the same states recur, you have **dynamic programming**. This is the textbook signature.

## The Same Thing, Bottom-Up

The recursion always calls states with a **larger `i`**. So you can fill a table from `i = n` downward, and every dependency is already computed:

```python
dp[i][j] = "does s[i:] match p[j:]?"
```

Two advantages:

1. **No recursion limit.**
2. **Row `i` depends only on row `i+1`** — so you never need the whole table. Keep one row and roll it forward: **O(m) space** instead of O(n × m).

That rolling array is the answer to the "can you optimise the space?" follow-up.

## The Greedy Trap

Worth testing explicitly, because it's the case that breaks naive implementations:

```
s = "aaa",  p = "a+aa"    →  True
```

A greedy `+` swallows all three `a`s, leaving nothing for `aa`, and reports **False**. The correct answer takes **one** `a` and leaves two behind.

The randomised tests in the notebook check thousands of these against Python's own `re.fullmatch` — free, exhaustive coverage of exactly the cases you wouldn't have thought to write.

## Adding `*` and `?`

The follow-up asks about other operators. Each is just a different pair of transitions:

| Operator | Meaning | Transitions |
|---|---|---|
| `c+` | one **or more** | must match once: `(i+1, j)` or `(i+1, j+2)` |
| `c*` | **zero** or more | **skip entirely**: `(i, j+2)`; or if matching: `(i+1, j)` |
| `?` | any **single** char | `(i+1, j+1)`, no comparison at all |

The one structural difference: `*` can match **zero** characters, so it has a transition that **doesn't consume any of `s`**. The recursion is no longer strictly decreasing in `i`, so you must be sure `j` strictly increases on that branch — otherwise you loop forever.

(And note that `a+` is exactly `a` followed by `a*`, which is a nice observation to offer.)

## A Real-World Footnote: ReDoS

This exponential blow-up isn't academic.

**Backtracking** regex engines — Perl, Java, JavaScript, Python's `re` — do exactly what the un-memoised version does. Feed one a pattern like `(a+)+b` and a string of `a`s, and it hangs. That's a genuine denial-of-service class called **ReDoS**, and it has taken down production systems.

**Automaton** engines — RE2, Go's `regexp` — compile the pattern to a state machine and simulate all states simultaneously, guaranteeing O(n × m). The price is giving up backreferences.

Being able to name that trade-off is a strong signal in an interview.

## Common Mistakes

- **Being greedy or lazy instead of branching.** `"aaa"` vs `"a+aa"` catches it immediately.
- **Reading `p[j+1]` without a bounds check.** Index error on any pattern ending in a plain character.
- **Base case checking only one pointer.** Accepts prefixes or leftovers.
- **`j+1` instead of `j+2` when leaving a `+` group.** A `+` group is two pattern characters.
- **Claiming O(n × m) for un-memoised branching recursion.** States ≠ paths.
- **Forgetting to clear the cache between calls.** An `lru_cache` on a closure captures `s` and `p`, so it's fine — but a module-level cache keyed only on `(i, j)` would return answers from a previous input.

## The Takeaway

> When a rule says "one **or more**", you can't decide locally — the right number depends on what comes after. **Branch, and let the search find out.** Then notice that the branches keep landing on the same states, and cache them.

That two-step — *write the branching recursion, then memoize it* — is how essentially every dynamic programming problem gets solved. The first step gets you correctness; the second turns exponential into polynomial with one decorator.
