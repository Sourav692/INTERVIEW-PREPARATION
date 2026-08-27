# 271. Encode and Decode Strings — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 3_Other Patterns/encode_and_decode_strings.ipynb`
> **LeetCode:** https://leetcode.com/problems/encode-and-decode-strings/
> **Generated for:** personal study reference (Premium problem)

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Length-prefix encoding | Write each string's length before its content: `"<len>#<content>"`, so decode always knows exactly how far to read |
| Why a plain separator fails | If the data itself contains the separator character, a naive split can't tell data from delimiter |
| Framing / parsing | Decode reads digits up to `#` to get a length, then slices exactly that many characters — content can safely contain *anything*, including `#` or digits |

**Canonical example** (from notebook):

```
["lint","code"] -> encode -> "4#lint4#code" -> decode -> ["lint","code"]
```

Expected outputs (from notebook asserts):

| Input | `decode(encode(...))` |
| ----- | ------------------------ |
| `["lint","code"]` | `["lint","code"]` |
| `["", "", ""]` | `["", "", ""]` |
| `["a#b", "3#weird", "we#ird"]` (contains `#` in the data) | `["a#b", "3#weird", "we#ird"]` |
| `[]` | `[]` |

The notebook also demonstrates the naive approach breaking: `decode_naive(encode_naive(["a#b"])) != ["a#b"]`.

---

## `encode_naive` / `decode_naive` — Join with a Separator (naive — it breaks)

### What it does

Joins the list of strings with `"#"` as a glue character, and decodes by splitting on `"#"`. This is unsafe: if any input string itself contains `#`, the split can't distinguish a real `#` from a separator.

### Code

```python
def encode_naive(strs: List[str]) -> str:
    # Join with a '#'. UNSAFE: breaks if any string itself contains '#'.
    return "#".join(strs)

def decode_naive(s: str) -> List[str]:
    # Splitting on '#' can't tell a real '#' apart from a separator.
    return s.split("#") if s != "" else []
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `"#".join(strs)` | Concatenates all strings, inserting `"#"` between (not before/after) each pair |
| `s.split("#") if s != "" else []` | Splits back on every `"#"` — treats every `#` as a boundary, including ones that were part of the original data |

### Step-by-step trace (notebook's own breaking example `["a#b"]`)

**Encode:**

| Step | Expression | Result |
| ---- | ---------- | ------ |
| 1 | `"#".join(["a#b"])` | `"a#b"` (single-element list — join inserts no separator since there's nothing to join to) |

**Decode:**

| Step | Expression | Result |
| ---- | ---------- | ------ |
| 1 | `"a#b" != ""` → True, so `.split("#")` runs | `"a#b".split("#")` → `["a", "b"]` |

**Final output:** `decode_naive(encode_naive(["a#b"]))` = `["a", "b"]`, which is **not equal** to the original `["a#b"]` ✓ matches the notebook's assertion `broken != ["a#b"]` — the embedded `#` inside the data was misread as a separator, splitting one string into two.

### Mental model

- A delimiter-based scheme silently assumes the delimiter never appears in the data — that assumption is often false in real inputs.
- The failure is *silent*: no exception is raised, you just get corrupted (wrong-length) output.

### Common confusions

- **It "works" on inputs without `#`:** e.g. `["lint","code"]` round-trips fine naively — the bug only shows up on adversarial/real-world data, which is exactly why it's dangerous.
- **Single-element join is a red herring:** `"#".join(["a#b"])` doesn't insert an *extra* `#` (there's only one element), yet decoding still breaks because the `#` was already inside the string.

### Complexity

- **Time:** `O(total length)` — one join, one split
- **Space:** `O(total length)` — the joined string and the resulting list

---

## `encode` / `decode` — Length Prefix (correct)

### What it does

Encodes each string as `"<length>#<content>"` and concatenates all the framed chunks. Decoding reads the digits before each `#` to learn exactly how many characters of content follow, then slices precisely that many characters — so the content can safely contain any character, including digits or `#`.

### Code

```python
def encode(strs: List[str]) -> str:
    parts = []
    for w in strs:
        # Write "<length>#<content>" so the reader knows exactly how far to read.
        parts.append(str(len(w)) + "#" + w)
    return "".join(parts)                  # concatenate all the framed chunks

def decode(s: str) -> List[str]:
    res = []
    i = 0
    while i < len(s):                      # keep reading chunks until the string ends
        j = i
        while s[j] != "#":                 # read digits up to the '#' marker
            j += 1
        length = int(s[i:j])               # those digits are the content length
        start = j + 1                      # content begins right after the '#'
        res.append(s[start:start + length])# take exactly `length` characters (any char is safe)
        i = start + length                 # jump to the start of the next chunk
    return res
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `parts.append(str(len(w)) + "#" + w)` | Frame each string as `"<length>#<content>"` |
| `"".join(parts)` | Concatenate all frames with no extra separator (the length prefix already delimits chunks) |
| `i = 0` | Read cursor into the encoded string |
| `while i < len(s):` | Loop until every chunk has been consumed |
| `j = i; while s[j] != "#": j += 1` | Scan forward from `i` to find the `#` marking the end of the length digits |
| `length = int(s[i:j])` | Parse the digits between `i` and `j` as the content length |
| `start = j + 1` | Content starts right after the `#` |
| `res.append(s[start:start+length])` | Slice out exactly `length` characters — safe no matter what they contain |
| `i = start + length` | Advance the cursor past this chunk to the start of the next one |

### Step-by-step trace (canonical example `["lint","code"]`)

**Encode:**

| Word `w` | `len(w)` | Frame `str(len(w)) + "#" + w` | `parts` after |
| -------- | -------- | -------------------------------- | ---------------- |
| `"lint"` | 4 | `"4#lint"` | `["4#lint"]` |
| `"code"` | 4 | `"4#code"` | `["4#lint", "4#code"]` |

`"".join(parts)` → `"4#lint4#code"` (12 characters total).

**Decode `"4#lint4#code"`** (indices: `4`=0,`#`=1,`l`=2,`i`=3,`n`=4,`t`=5,`4`=6,`#`=7,`c`=8,`o`=9,`d`=10,`e`=11):

| Iteration | `i` (start) | `j` scan finds `#` at | `length = int(s[i:j])` | `start = j+1` | `s[start:start+length]` | `res` after | `i` after (`start+length`) |
| --------- | ----------- | ------------------------ | -------------------------- | ---------------- | --------------------------- | -------------- | ------------------------------- |
| 1 | 0 | 1 | `int("4")=4` | 2 | `s[2:6] = "lint"` | `["lint"]` | 6 |
| 2 | 6 | 7 | `int("4")=4` | 8 | `s[8:12] = "code"` | `["lint","code"]` | 12 |

`i = 12 = len(s)`, loop exits (`12 < 12` is False). **Final output:** `["lint", "code"]` ✓ matches the notebook's assertion `decode(encode(["lint","code"])) == ["lint","code"]`.

### Mental model

- "Say the size first, then the content" removes all ambiguity — the reader never has to *guess* where a chunk ends; it's told explicitly.
- Because the length is read as digits up to a `#`, and then exactly that many raw characters are consumed regardless of their content, embedded `#` characters (or even digits) inside the string can never be misinterpreted as structure.
- This is the same idea used in real network protocols (e.g. HTTP `Content-Length`, length-prefixed framing in binary protocols).

### Common confusions

- **The inner `#` search only looks for the *next* `#`, not the *last*:** this works because the digits of a length never contain `#`, so the first `#` after `i` is guaranteed to be the length/content boundary — no ambiguity even though `#` may also appear later inside the content.
- **Off-by-one on slicing:** `start = j + 1` (skip past the `#` itself), and `s[start:start+length]` (not `s[start:length]`) — a common bug is slicing to `length` as an absolute index instead of a count from `start`.
- **Empty strings still work:** `""` encodes as `"0#"` (length 0, then zero content characters) and decodes back correctly, since `s[start:start+0]` is `""`.

### Complexity

- **Time:** `O(total length)` — encode does one pass building frames; decode does one pass reading digits+slicing, and each character is touched a constant number of times
- **Space:** `O(total length)` — the encoded string, and the output list of decoded strings

---

## Quick reference

| Function pair | Technique | Output on `["lint","code"]` | Time | Space |
| -------------- | --------- | ------------------------------- | ---- | ----- |
| `encode_naive` / `decode_naive` | Join/split on a `"#"` separator | Round-trips OK here, but **breaks** on `["a#b"]` → `["a","b"]` | `O(total length)` | `O(total length)` |
| `encode` / `decode` | Length-prefix framing (`"<len>#<content>"`) | `"4#lint4#code"` → `["lint","code"]` (always correct) | `O(total length)` | `O(total length)` |

## Patterns to remember

- **Length-prefix framing:** state a chunk's size before its content so you can read it back with zero ambiguity — the same idea used in real network protocols.
- **Separators are unsafe alone:** any in-band marker can appear in the data; a length tells you exactly how far to read.
- **Signal words:** "serialize / deserialize", "pack a list into one string", "encode with arbitrary characters".
- **Related problems:** Serialize and Deserialize Binary Tree, string tokenizers, protocol design.
- **Common pitfalls:** (1) using a delimiter the data may contain; (2) off-by-one when slicing after the `#`.
