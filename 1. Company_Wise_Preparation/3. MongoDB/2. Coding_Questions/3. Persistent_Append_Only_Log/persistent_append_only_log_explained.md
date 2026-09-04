# Persistent Append-Only Log — Explained Simply

## The Problem

Build a file that stores records. You can only ever **add to the end** — never overwrite, never delete in place.

```
append(b"hi")     -> 0     (this record starts at byte 0)
append(b"abc")    -> 6     (this one starts at byte 6)
read(6)           -> b"abc"
scan(0)           -> b"hi", b"abc"
flush()                    (now it survives a power cut)
```

Three rules:
- Every record is stored as **a 4-byte length, then that many bytes of payload**.
- `append` must be O(1).
- Anything you `flush()`ed must still be there after a crash.

## Why "Append-Only" Is a Feature, Not a Limitation

At first this sounds restrictive. It's actually where all the power comes from:

- **Writes are sequential.** Disks (and SSDs) are dramatically faster at writing one continuous stream than at hopping around.
- **Nothing ever moves.** Byte position 6 will still hold that same record tomorrow. So a byte position becomes a **permanent address** you can hand out and store.
- **There is no half-updated state.** You can't corrupt an existing record by partially overwriting it, because you never overwrite anything.

That second point is the whole trick. `append` hands you back an **offset**, and later `read(offset)` jumps straight there. No searching.

## The First Problem: A File Is Just Bytes

Write `hi` and then `abc` to a file and you get:

```
h i a b c
```

Now read it back. Where does the first record end? Is it `hi`? `hia`? `hiabc`? **The bytes don't say.** A file has no built-in idea of "records".

### The fix: say how long each record is, before the record

```
[00 00 00 02] h i        <- "the next 2 bytes are one record"
[00 00 00 03] a b c      <- "the next 3 bytes are one record"
```

Now the file **explains itself**. To read a record: grab 4 bytes, decode them as a number, then grab exactly that many more bytes. Done — no separate index file needed.

This is called **framing**, and it's the same problem network protocols solve when they send a length before each message.

> **Why 4 bytes, big-endian?** Four bytes hold numbers up to ~4 billion, so records up to ~4 GB. "Big-endian" means the most significant byte comes first — the standard portable ordering, so a log written on one machine reads correctly on another.

## An Analogy First: A Roll of Receipt Paper

Think of a shop's till roll. It only ever prints forward — you cannot go back and edit a line halfway up the roll.

- **Appending** = printing a new line at the bottom. Fast, and never disturbs anything above it.
- **The offset** = "how many centimetres from the start of the roll". Once printed, that measurement is permanent.
- **The length prefix** = the till printing "ITEM: 12 chars" before each entry, so anyone reading the roll knows where one entry stops and the next begins.
- **Changing a price** = you don't scratch out the old line. You print a **new** line further down. The old line is still on the roll, just stale.
- **Compaction** = at closing time, copying only the still-relevant lines onto a fresh roll and throwing the old one away.

Every log-structured database works exactly like this till roll.

## Step-by-Step Example (Narrated)

Start with an empty file. Keep one number in memory: `size = 0`.

---

**`append(b"hi")`**

The record will start at the current end of the file, so the answer is `offset = 0`.

Build the bytes to write — length **and** payload together in one chunk:

```
00 00 00 02   h  i
└─ length=2 ─┘ └payload┘
```

Write those 6 bytes at position 0. Then update the counter: `size = 0 + 4 + 2 = 6`.

**Returns `0`.**

---

**`append(b"abc")`**

`offset = size = 6`. Build `[00 00 00 03] a b c` — 7 bytes — write at position 6. `size = 6 + 4 + 3 = 13`.

**Returns `6`.**

The file now looks like:

```
byte:  0  1  2  3  4  5   6  7  8  9  10 11 12
      [00 00 00 02] h  i [00 00 00 03] a  b  c
```

---

**`read(6)`**

1. Read 4 bytes starting at byte 6 → `00 00 00 03` → the number **3**.
2. Read 3 bytes starting at byte 10 → `a b c`.

**Returns `b"abc"`.** ✅

Notice we jumped straight to byte 6. We did **not** read the first record. That's the O(1).

---

**`scan(0)`** — walk the whole file:

- At byte 0: length 2 → read `b"hi"` → move forward by `4 + 2 = 6`.
- At byte 6: length 3 → read `b"abc"` → move forward by `4 + 3 = 7` → now at byte 13.
- Byte 13 = `size` → stop.

It yields one record at a time, so a 100 GB log costs one record's worth of memory.

## The Sneaky Part: "Written" Doesn't Mean "Saved"

This is the bit that separates a correct answer from a great one.

When you call `write()` and it returns successfully, your data is usually **still in RAM** — in an operating-system buffer called the page cache. The OS writes it to the actual disk later, whenever convenient.

| Failure | Survives? |
|---|---|
| Your program crashes | ✅ Yes — the OS still holds the data and will write it out |
| The power goes out | ❌ **No** — RAM is gone, the data was never on the disk |

To *actually* get bytes onto the physical disk, you must call **`fsync`** (Java: `channel.force(false)`). It blocks until the hardware confirms.

**And it's slow** — often several milliseconds, because it waits on real hardware. That's why `flush()` is a separate method the caller chooses to call, rather than something `append` does every time. Real databases batch this: 500 appends, then one `fsync`, and all 500 callers are told "durable" together. That's called **group commit**.

> The `false` in Java's `force(false)` means "flush the file *contents*, don't bother syncing the *metadata* (size, timestamps) too". Metadata sync is a second, extra disk operation you don't need here.

## Two Bugs Worth Avoiding

### 1. Writing the length and the payload separately

```
write(length)     <-- crash right here
write(payload)
```

Now the file ends with a header claiming "3 more bytes coming" — and there are none. The file is **structurally broken**: any reader walking forward will run off the end and can't tell where the next record starts.

**The fix:** build `length + payload` into **one** chunk and issue **one** write. There's no longer a moment in between.

### 2. Trusting a length you read from disk

```
length = read_4_bytes(offset)     # a corrupted 4 bytes might decode to 2,000,000,000
buffer = allocate(length)         # ...and now you've tried to allocate 2 GB
```

**The fix:** before allocating anything, check the length is sane against something you already trust:

```
if offset + 4 + length > size:  raise "corrupt record"
```

Any number that came *from* the data is untrusted. Bound-check it first.

## Building a Key-Value Store On Top

This is the classic follow-up, and it's only a few lines once the log exists.

The log gives you **durability and order**. A plain dictionary in memory gives you **fast lookup**. Combine them:

```
index = {}          # key -> the byte offset of that key's newest record
```

- **`put("a", b"1")`** → append a record containing both the key and the value; store the returned offset: `index["a"] = 0`.
- **`get("a")`** → `index["a"]` gives you `0`; `read(0)` gives you the record. Two O(1) steps.
- **`put("a", b"3")`** (overwrite) → append a *new* record at, say, offset 12, and point the index there: `index["a"] = 12`. The record at offset 0 is still in the file, but nothing points at it any more. It's **garbage**.
- **`delete("a")`** → you can't erase from an append-only file, so you append a special "this key is gone" record called a **tombstone**, and drop the key from the index.

### Crash recovery is beautifully simple

On restart, the `index` dictionary is empty — it only ever lived in RAM. So: **replay the log from the beginning**.

```
for each record in scan(0):
    if it's a tombstone:  remove the key from the index
    else:                 index[key] = this record's offset
```

Because records are in the order they were written, **the last record for a key wins** — and that's exactly the state the store was in when it crashed. The log *is* the source of truth; the index is just a cache of where things are.

## Compaction: Taking Out the Garbage

Overwrite the same key 200 times and the file holds 200 records, 199 of them dead. The file grows forever.

**Compaction** fixes it:

1. Make a **new, empty** file.
2. For each key still in the index, read its live record and append it to the new file — noting its **new** offset.
3. `os.replace(new_file, old_file)` — an **atomic** rename.
4. Swap in the new index.

Two things make this safe:

- **The rename is atomic.** At every single instant, anyone opening the path sees either the complete old file or the complete new one — never a half-written mess. If you crash mid-rewrite, the original is untouched and you just try again later.
- **You rebuild the index as you go.** This is the answer to "what happens to the offsets after compaction?" — they all change, so you record the new ones while writing and swap the whole index in at the end.

## Why It's Fast

| Operation | Naive (read by record number) | This design (read by offset) |
|---|---|---|
| `append` | O(1) + a size syscall | **O(1)** |
| `read` | **O(k)** — walk from byte 0 | **O(1)** — jump straight there |
| `scan` | O(n) | O(n), lazily |
| memory | O(1) | O(1) |

The notebook's benchmark shows it plainly: double the log size and the "read by record number" version takes twice as long, while "read by offset" doesn't move at all.

## Common Mistakes

- **Calling `os.path.getsize()` on every append.** That's a syscall each time. Read the size once when you open the file and keep a counter — the file only grows, so the counter can never go stale.
- **Using length `0` as an end-of-file marker.** An empty record is legitimate. Use the known file size as the boundary instead.
- **Loading all records into a list inside `scan`.** Defeats the whole point. Yield them one at a time.
- **Thinking `f.flush()` is durability.** In Python that only pushes *Python's* buffer into the OS. `os.fsync` is the one that reaches the disk.
- **Forgetting that reopening must work.** Read the existing file size in the constructor, and appending to a pre-existing log just continues from the end.

## The Takeaway

> Promise never to overwrite, and a byte position becomes a permanent address. Prefix every record with its length, and the file explains its own structure. Call `fsync` and you know it's really saved. Everything else — key-value stores, write-ahead logs, replication, compaction — is built on those three ideas.

This is the shape of Kafka's partitions, of a database's write-ahead log, of Bitcask, and of the LSM-trees inside MongoDB's WiredTiger storage engine.
