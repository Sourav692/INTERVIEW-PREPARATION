# Random Dice Roll

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Simulation, Strings · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

### Problem 1

Write a function that simulates rolling a dice with a given number of sides. The function should:

- Take an integer `n` as input, representing the number of sides on the dice.
- Randomly return an integer between 1 and `n` (inclusive).

**Follow-up:** Handle invalid inputs by implementing appropriate error handling using try-except.

### Problem 2

Extend the dice rolling function to support multi-rolls with a specific format.

The input will be a string in the format `xDy`, where:

- `x` is the number of dice to roll.
- `y` is the number of sides on each dice.

The function should return the **sum** of all rolls. For example:

```
Input: "2D6" -> Roll two dice with six sides each and return the sum.
Input: "3D7" -> Roll three dice with seven sides each and return the sum.
```

**Follow-up:** Handle invalid inputs by addressing the following cases:

- The input string does not contain the letter `"D"`.
- Expected numbers (`x` or `y`) are missing or not provided in a valid format.

### Problem 3

Write a function to maintain a **history** of dice roll inputs and their corresponding outputs.

---

## Study Tools

### Hint 1

For Problem 2, split the string on `"D"` and validate that you got exactly two parts that both parse as positive integers.

### Hint 2

The history problem is a natural fit for a class or closure: one method performs the roll (and validates input), another returns a bounded or unbounded list of past results.

### Hint 3

Use `random.randint(1, sides)` for each die roll, and for the history, store each result as a tuple of the input string and the summed output so you can return both together.

---

### Answer

This is three small functions that build on each other: a single-die roller with validation, a parser for `"xDy"` strings that sums multiple rolls, and a stateful history wrapper.

#### Problem 1: single die

```python
import random


def roll_die(n: int) -> int:
    """Roll a single n-sided die. Returns an integer in [1, n]."""
    if not isinstance(n, int):
        raise TypeError(f"n must be an integer, got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    return random.randint(1, n)
```

The try-except follow-up is about the **caller** wrapping this in error handling, not about the function swallowing its own errors:

```python
try:
    result = roll_die(0)
except ValueError as e:
    print(f"Bad input: {e}")
```

**Time:** O(1) — `random.randint` is constant time. **Space:** O(1) — no auxiliary storage.

#### Problem 2: multi-roll with `xDy` format

```python
import random


def roll_multi(spec: str) -> int:
    """Parse an 'xDy' string and return the sum of x rolls of a y-sided die."""
    if not isinstance(spec, str):
        raise TypeError(f"spec must be a string, got {type(spec).__name__}")
    if "D" not in spec:
        raise ValueError(f"spec must contain 'D', got {spec!r}")

    parts = spec.split("D")
    if len(parts) != 2:
        raise ValueError(f"spec must have exactly one 'D', got {spec!r}")

    x_str, y_str = parts
    if not x_str.strip() or not y_str.strip():
        raise ValueError(f"spec must have numbers on both sides of 'D', got {spec!r}")

    try:
        x = int(x_str)
        y = int(y_str)
    except ValueError:
        raise ValueError(f"x and y must be valid integers, got {spec!r}")

    if x < 1:
        raise ValueError(f"x must be at least 1, got {x}")
    if y < 1:
        raise ValueError(f"y must be at least 1, got {y}")

    return sum(random.randint(1, y) for _ in range(x))
```

**Time:** O(x) — one `randint` call per die. **Space:** O(1) — the generator in `sum` doesn't materialize a list.

#### Problem 3: history

```python
import random


class DiceRoller:
    def __init__(self, max_history: int | None = None):
        self._history: list[tuple[str, int]] = []
        self._max_history = max_history

    def roll(self, spec: str) -> int:
        result = roll_multi(spec)
        self._history.append((spec, result))
        if self._max_history is not None and len(self._history) > self._max_history:
            self._history.pop(0)
        return result

    def history(self) -> list[tuple[str, int]]:
        return list(self._history)
```

The history stores `(input_string, summed_output)` pairs so callers can see both the original request and what it produced. `max_history=None` means unbounded; pass an integer to cap it and avoid unbounded memory growth in long-running sessions.

**Time:** O(1) amortized per roll for appending; O(1) per pop from the front when capped (CPython's `list.pop(0)` is O(n) in the worst case, so if you expect large capped histories, use a `collections.deque` instead). **Space:** O(h) where h is the number of history entries retained.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with Problem 1 in the simplest possible form: `random.randint(1, n)` and done. The follow-up asks for error handling, which means deciding what counts as invalid. `n = 0` and negative `n` are invalid because a die must have at least one side. Non-integer input is also invalid. Raise `TypeError` for wrong types and `ValueError` for wrong values — that's the Python convention, and it lets callers catch specific error classes.

For Problem 2, the naive approach is to manually scan the string for `"D"`, extract substrings, call `int()` on each, and hope for the best. That breaks on `"2D"`, `"D6"`, `"2D6D4"`, and `"abcD6"` in ways that are annoying to debug. The cleaner approach is to split on `"D"` and check the **structure** before parsing: exactly two parts, both non-empty, both parseable as integers, both positive. Then the sum is a generator expression over `range(x)`.

One design decision worth calling out: should `roll_multi` catch its own exceptions and return something like `-1` or `None`? **No** — raise the exception and let the caller decide how to handle it. The try-except from Problem 1's follow-up is the caller's responsibility, and mixing error signaling via return values with exceptions makes the API inconsistent.

For Problem 3, the question is vague about what "maintain a history" means, so pick the most standard interpretation: a class that wraps the roll function, appends each `(input, output)` pair to an internal list, and exposes a `history()` accessor. A class is the right call here because you need state that persists across calls. A closure would also work, but a class is more readable and easier to extend (e.g., adding a `clear_history()` method later).

The bounded-history option is worth mentioning even if the question doesn't ask for it, because unbounded growth in a long-running process is a real bug. `deque` with `maxlen` is the idiomatic fix if you want a capped history with O(1) eviction.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Validate before you roll** — checking `n < 1` and type before calling `random.randint` means your error messages are specific and the random call never runs on bad input.
- **Raise the right exception type** — `TypeError` for wrong types and `ValueError` for wrong values is the Python convention. Using the wrong one makes caller-side `except` blocks fragile.
- **Parse structurally, not char-by-char** — `split("D")` with a length check handles missing numbers, extra `D`s, and empty strings in one clean pass, which is much easier to reason about than index arithmetic.
- **Keep error signaling consistent** — `roll_multi` raises on bad input; it never returns a sentinel. Mixing exceptions and sentinel returns forces callers to check both paths.
- **Return a copy from `history()`** — returning `self._history` directly lets callers mutate your internal state. A shallow copy is cheap and prevents that class of bug.
- **Mention the bounded-history tradeoff** — if you store every roll forever, memory grows without bound. Capping it or using `deque(maxlen=...)` shows you're thinking about production behavior, not just passing a test.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Support modifiers like `"2D6+3"`** — think about extending the parser to handle arithmetic suffixes, and how precedence interacts with the sum.
- **Support advantage/disadvantage rolls (`"2D20k1"` keeps the highest of 2 rolls)** — consider how the parse format generalizes and what the output means.
- **Make `DiceRoller` thread-safe** — think about whether a simple `threading.Lock` around `roll` is sufficient, and what happens to history ordering under concurrency.
- **Add a `roll_many` that takes a list of specs and returns a list of sums** — consider whether to validate all inputs before rolling any dice, or roll as you go.
- **Persist the history to disk** — think about the serialization format (JSON lines vs. SQLite) and what happens on restart.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One correction to the official answer

`isinstance(n, int)` returns `True` for **booleans**, because `bool` is a subclass of `int` in Python. So the official `roll_die` accepts `roll_die(True)` and rolls a 1-sided die, and `roll_die(False)` slips past the type check only to fail the `n < 1` check with a confusing message about `False`.

The notebook adds `isinstance(n, bool)` as an explicit rejection before the `int` check, and asserts it.
