# Random Dice Roll — Explained Simply

## The Problem

Three small pieces that build on each other:

1. **Roll one die.** Given `n` sides, return a random number from 1 to `n`.
2. **Roll several.** Given a string like `"2D6"`, roll two six-sided dice and return the **sum**.
3. **Remember.** Keep a history of what was rolled and what came out.

Plus, at every stage: **handle bad input properly.**

## What This Question Is Actually Testing

There's essentially no algorithm here. `random.randint(1, n)` is the whole of part 1.

This is a **code quality** question wearing a dice costume. It's graded on the things production code is graded on:

- Do you reject bad input **clearly**?
- Do you use the language's **conventions**?
- Can a caller **misuse** your code by accident?

Which means the interesting parts are all in the edges.

## Part 1: One Die

```python
def roll_die(n):
    if isinstance(n, bool):
        raise TypeError("n must be an integer, got bool")
    if not isinstance(n, int):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    return random.randint(1, n)
```

Three things worth pulling out.

### `randint` is inclusive at *both* ends

```python
random.randint(1, 6)     # can return 1, 2, 3, 4, 5, or 6   ✅
random.randrange(1, 6)   # can return 1, 2, 3, 4, or 5      ❌ never 6
```

Using `randrange` here is the classic off-by-one, and it's invisible in casual testing — you just never roll a six. The notebook tests catch it by asserting that **both extremes** actually appear over many rolls.

### `TypeError` vs `ValueError` isn't arbitrary

Python's convention:

| Exception | Means |
|---|---|
| `TypeError` | wrong **kind** of thing — a string where an int was expected |
| `ValueError` | right kind, wrong **value** — an int, but zero sides |

Callers write `except ValueError:` to catch one and not the other. Pick the wrong one and their error handling silently stops working.

### The `bool` trap

Here's the genuinely surprising one:

```python
isinstance(True, int)    # True  (!)
True == 1                # True
```

**In Python, `bool` is a subclass of `int`.** So a naive type check happily accepts:

```python
roll_die(True)     # rolls a 1-sided die - always returns 1
roll_die(False)    # passes the int check, then fails with "n must be at least 1, got False"
```

Neither is what anyone meant. If booleans should be rejected — and they should, since `True` isn't a meaningful number of sides — you have to check for `bool` **explicitly, and before** the `int` check.

## The Follow-Up Everyone Gets Backwards

The problem says: *"Handle invalid inputs by implementing appropriate error handling using try-except."*

The tempting reading is: wrap the function body in `try/except` and return `None` when something goes wrong.

**That's the wrong lesson.**

If `roll_multi("2D")` returns `None` instead of raising, that `None` flows into somebody's arithmetic and explodes a hundred lines away, with a stack trace pointing at innocent code. You've turned a loud, findable bug into a silent, mysterious one.

> **Raise at the point of the mistake. Catch at the boundary where you can actually do something about it.**

The `try/except` belongs to the **caller**:

```python
try:
    result = roll_die(user_input)
except ValueError as e:
    print(f"Bad input: {e}")     # here you can re-prompt, log, or skip
```

## An Analogy First: The Bouncer and the Bar

Think of input validation as a bouncer at the door.

**A good bouncer** checks IDs at the entrance and turns people away *there*, saying exactly why: "this ID is expired", "you're not on the list". The problem is caught at the door, and the person knows what to fix.

**A bad bouncer** lets everyone in and hopes for the best. Problems surface in the middle of the bar an hour later, far from the cause, and nobody can work out how the person got in.

**A worse bouncer** turns people away silently — no reason given. They wander off confused, and so does everyone watching.

That's the three options: validate up front with clear messages (good), let bad input through (bad), or fail silently by returning `None` (worse).

## Part 2: Parsing `"2D6"`

The naive approach hunts for the `"D"` and slices around it:

```python
i = spec.find("D")
x = int(spec[:i])
y = int(spec[i+1:])
```

Works on good input. Watch it on bad input:

| Input | What happens |
|---|---|
| `"2D6D4"` | `x = 2`, `y = int("6D4")` → error blaming `'6D4'`, not the extra `D` |
| `"abcD6"` | `int("abc")` → error about `'abc'`, no mention of the format |
| `"2D"` | `int("")` → "invalid literal for int()" — technically true, unhelpful |

The failures are **late** and the messages point at symptoms rather than causes.

### The fix: check the *shape* first

```python
parts = spec.upper().split("D")
if len(parts) != 2:
    raise ValueError(f"spec must be of the form 'xDy', got {spec!r}")
```

One `split` catches almost everything:

| Input | Split result | Caught because |
|---|---|---|
| `"2D6"` | `["2", "6"]` | ✅ valid |
| `"26"` | `["26"]` | not 2 parts (no `D`) |
| `"2D6D4"` | `["2", "6", "4"]` | not 2 parts (too many `D`s) |
| `"2D"` | `["2", ""]` | empty part |
| `"D6"` | `["", "6"]` | empty part |
| `"abcD6"` | `["abc", "6"]` | `int("abc")` fails |

Then parse. Then range-check. Each stage produces an error about **that stage**, so the exception message tells the caller what was actually wrong.

### One small thing: use a generator

```python
sum(random.randint(1, y) for _ in range(x))     # ✅ generator - O(1) space
sum([random.randint(1, y) for _ in range(x)])   # ❌ list - allocates x integers
```

Same speed. But the list version builds an `x`-element list purely to add it up and throw it away. With `x = 10,000,000` that matters. It's free to get right — just drop the brackets.

## Part 3: History

State that persists across calls means a class. Two details carry the marks.

### Return a copy

```python
def history(self):
    return list(self._history)     # ✅ a copy
    # return self._history         # ❌ hands out your internals
```

Without the copy, a caller can do `roller.history().clear()` and silently wipe your state. One word closes the hole.

### Use a `deque` for a bounded history

The obvious cap:

```python
self._history.append(entry)
if len(self._history) > self._max:
    self._history.pop(0)          # ❌ O(n) - shifts every element
```

`list.pop(0)` removes from the front, which means shifting everything else down one slot — O(n) per eviction.

```python
self._history = deque(maxlen=max_history)
self._history.append(entry)        # ✅ O(1), evicts automatically
```

`maxlen` does the capping for you, and eviction is O(1). No length check needed at all.

> And *why* cap it? Unbounded growth in a long-running process is a real memory leak. Offering the option unprompted shows you're thinking past the test case.

### Record only on success

```python
def roll(self, spec):
    result = roll_multi(spec)          # raises before we get here
    self._history.append((spec, result))
    return result
```

Because `roll_multi` raises before the append line runs, a rejected spec never enters the history. That ordering is deliberate, and worth pointing at.

## Step-by-Step Example (Narrated)

`roll_multi("2D6")`:

---

**1. Type check.** Is it a string? Yes.

---

**2. Split.** `"2D6".upper().split("D")` → `["2", "6"]`

Exactly two parts. ✅

---

**3. Emptiness check.** `"2"` and `"6"` are both non-empty. ✅

*(This is what catches `"2D"` → `["2", ""]` and `"D6"` → `["", "6"]`.)*

---

**4. Parse.** `int("2") = 2`, `int("6") = 6`. ✅

*(This is what catches `"abcD6"`.)*

---

**5. Range check.** Both ≥ 1. ✅

*(This catches `"0D6"` and `"2D0"`.)*

---

**6. Roll.** `random.randint(1, 6)` twice — say 4 and 3.

**Return 7.**

Five checks before any dice are thrown, each with its own specific error message.

## Bonus: Real Dice Notation

Tabletop games use a richer format worth knowing:

- **`2D6+3`** — roll two d6, add 3.
- **`2D20k1`** — roll two d20, **keep the highest 1**. This is *advantage* in D&D 5e.

The keep clause forces one genuine change: you need the **individual rolls**, not just their sum, so you have to materialise the list before reducing it:

```python
rolls = [random.randint(1, y) for _ in range(x)]
if keep:
    rolls = sorted(rolls, reverse=True)[:keep]    # advantage = take the best
return sum(rolls) + modifier
```

The notebook verifies the statistics too: rolling `2D20k1` (best of two) averages **higher** than a single `1D20`, which is exactly what "advantage" is supposed to mean.

## How Do You Test Something Random?

You can't assert an exact value. You assert the **invariants**:

1. **Bounds always hold.** `1 <= result <= n`, every time, over thousands of rolls.
2. **Both extremes are reachable.** Over enough rolls you must see both `1` and `n`. *This is what catches the `randint` vs `randrange` off-by-one* — with `randrange` you'd never see `n`.
3. **The distribution is roughly flat.** 60,000 rolls of a d6 should give each face about 10,000 times, within a tolerance.
4. **Every bad input raises the right exception type.** This part is fully deterministic, and it's where most of the real bugs live.

And when you need exact reproducibility, **seed the generator** (`random.seed(53)`) or inject it as a dependency.

## Common Mistakes

- **`randrange` instead of `randint`.** Silently never rolls the maximum.
- **Trusting `isinstance(n, int)` to exclude booleans.** It doesn't.
- **Catching your own exceptions and returning `None`.** Turns loud bugs into silent ones.
- **Mixing exceptions and sentinel returns.** Now every caller has to check both paths, and forgets one.
- **Parsing before validating the shape.** Late failures with misleading messages.
- **Returning the internal history list.** Callers can corrupt your state.
- **`list.pop(0)` for a bounded queue.** O(n) per eviction; use `deque(maxlen=...)`.
- **Recording a roll before it succeeded.** Failed specs pollute the history.
- **`sum([...])` instead of `sum(...)`.** Allocates a list you immediately discard.

## The Takeaway

> When there's no algorithm to show off, the interview is about **judgement**: validate the shape before the pieces, raise the exception the language's conventions expect, let the caller decide how to recover, and never hand out a reference to your own state.

And the specific Python fact worth carrying away: **`bool` is a subclass of `int`**, so any type check that must exclude booleans has to say so explicitly — and first.
