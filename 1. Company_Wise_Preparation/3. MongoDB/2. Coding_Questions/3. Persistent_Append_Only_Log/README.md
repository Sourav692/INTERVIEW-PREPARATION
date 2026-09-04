# Persistent Append-Only Log

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Databases, Operating Systems · **Difficulty/Frequency:** Very Common (8/10)

---

## Problem Statement

Design and implement an `AppendOnlyLog` that stores records durably and supports sequential reads.

```java
class AppendOnlyLog {
    // Open or create a log at the given file path.
    public AppendOnlyLog(String filePath) throws IOException {}

    // Append a record and return its offset (byte position in the file).
    public long append(byte[] record) throws IOException {}

    // Read the record at the given offset.
    public byte[] read(long offset) throws IOException {}

    // Return an iterator over all records from startOffset to end.
    public Iterator<byte[]> scan(long startOffset) {}

    // Ensure all appended records are flushed to disk.
    public void flush() throws IOException {}

    public void close() throws IOException {}
}
```

**Requirements:**

- Each record is prefixed with its length (4-byte big-endian int) so boundaries can be recovered.
- `append` should be O(1) amortized.
- After a crash and restart, all records that were `flush()`ed must be recoverable.

### Follow-up (as posed with the problem)

How would you implement log compaction to reclaim space? How would you use this log as the backbone of a simple key-value store using a hash index of offsets?

---

## Study Tools

### Hint 1

The core of this problem is a binary on-disk format you define yourself: a 4-byte length prefix followed by that many payload bytes. Durability has to be explicit, so think about which `FileChannel` operations actually guarantee bytes hit disk.

### Hint 2

`FileChannel.write` is thread-safe and lets you append to a file without managing a file pointer yourself. For durability, you need `force(false)` — the `false` matters because you only care about the file contents, not the metadata.

### Hint 3

Use a `FileChannel` opened with `CREATE` and `WRITE`, keep a running size counter in memory, and write `[4-byte length][payload]` in a single `ByteBuffer` per append. `read` seeks to the offset, reads the 4-byte length, then reads the payload. `scan` just walks forward from the start offset, reading length-prefixed records until it hits the end.

---

### Answer

This is a classic length-prefixed append-only log with explicit durability semantics. The file format is self-describing: every record is a 4-byte big-endian length followed by exactly that many payload bytes. You keep a `FileChannel` open, track the current end offset in memory, and write each record as a single contiguous `ByteBuffer` so the length and payload are atomic. Durability comes from `FileChannel.force(false)` — it flushes file contents to disk without forcing metadata, which is all you need for crash recovery of flushed records.

#### File format

```
[4-byte big-endian length][payload bytes]
[4-byte big-endian length][payload bytes]
...
```

Every record starts at a known offset (returned by `append`), and the length prefix lets you recover boundaries even if you don't have an in-memory index. A length of 0 is valid (empty payload), so don't use it as a sentinel.

#### Implementation

```java
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Iterator;
import java.util.NoSuchElementException;

class AppendOnlyLog {
    private final FileChannel channel;
    private long size;
    private boolean closed;

    public AppendOnlyLog(String filePath) throws IOException {
        this.channel = FileChannel.open(
            Path.of(filePath),
            StandardOpenOption.CREATE,
            StandardOpenOption.WRITE,
            StandardOpenOption.READ
        );
        this.size = channel.size();
        this.closed = false;
    }

    public long append(byte[] record) throws IOException {
        ensureOpen();
        long offset = size;
        ByteBuffer buf = ByteBuffer.allocate(4 + record.length);
        buf.putInt(record.length);
        buf.put(record);
        buf.flip();
        while (buf.hasRemaining()) {
            channel.write(buf);
        }
        size += 4 + record.length;
        return offset;
    }

    public byte[] read(long offset) throws IOException {
        ensureOpen();
        if (offset < 0 || offset >= size) {
            throw new IllegalArgumentException("Offset out of range: " + offset);
        }

        ByteBuffer lenBuf = ByteBuffer.allocate(4);
        readFully(offset, lenBuf);
        int len = lenBuf.getInt(0);
        if (len < 0 || offset + 4 + len > size) {
            throw new IOException("Corrupt record at offset " + offset);
        }

        ByteBuffer payload = ByteBuffer.allocate(len);
        readFully(offset + 4, payload);
        return payload.array();
    }

    public Iterator<byte[]> scan(long startOffset) {
        return new Iterator<byte[]>() {
            private long cursor = startOffset;

            @Override
            public boolean hasNext() {
                return cursor < size;
            }

            @Override
            public byte[] next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                try {
                    byte[] rec = read(cursor);
                    cursor += 4 + rec.length;
                    return rec;
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            }
        };
    }

    public void flush() throws IOException {
        ensureOpen();
        channel.force(false);
    }

    public void close() throws IOException {
        if (closed) {
            return;
        }
        closed = true;
        channel.close();
    }

    private void readFully(long position, ByteBuffer buf) throws IOException {
        long pos = position;
        while (buf.hasRemaining()) {
            int n = channel.read(buf, pos);
            if (n == -1) {
                throw new IOException("Unexpected EOF at position " + pos);
            }
            pos += n;
        }
        buf.flip();
    }

    private void ensureOpen() {
        if (closed) {
            throw new IllegalStateException("Log is closed");
        }
    }
}
```

**Time:** O(1) amortized for `append` (one write call per record, no seeking since `FileChannel` maintains its own position for non-positional writes), O(1) for `flush`, O(1) for `read` (fixed-size length prefix + one payload read), O(n) for `scan` where n is the number of records scanned.

**Space:** O(record.length) for `append` and `read` (the `ByteBuffer` allocated per call), O(1) otherwise. The log itself is on disk, not in memory.

#### Correctness argument

**Crash recovery invariant:** After `flush()` returns, every byte written by prior `append` calls is on stable storage. `FileChannel.force(false)` guarantees this — it blocks until all buffered writes to the file's data blocks are physically written. The `false` argument skips metadata (file size, mtime), which is fine because the file already exists and its size doesn't need to change atomically for the data to be readable after a crash.

**Record boundary invariant:** Every `append` writes `[len][payload]` as a contiguous region. Since `FileChannel` writes from a single `ByteBuffer` and the file is append-only, no interleaving or partial record can occur within a single `append` call. After a crash, a partially-written record at the tail is possible, but it's beyond the last `flush()`ed offset, so it's simply not considered durable.

The `size` counter is reconstructed from `channel.size()` on open, which is correct because the file only grows. On a clean shutdown, `close()` without `flush()` may lose buffered data, but that's expected — the contract says only `flush()`ed records survive a crash.

#### Edge cases

- **Empty record:** `len = 0` is valid. `read` returns a zero-length array.
- **Reading past the end:** `read` validates the offset and the length prefix against `size`, so a corrupt or truncated tail throws `IOException` rather than returning garbage.
- **Concurrent appends:** `FileChannel.write` is thread-safe, and the `size` update is not atomic, so this class is **not** thread-safe for concurrent `append` calls. If you need that, wrap `append` in a lock.
- **Reopening a log:** The constructor reads `channel.size()`, so you can append to an existing log and scan from any offset.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that works: a `FileOutputStream` and a `DataOutputStream` wrapper. You'd write an int length followed by the bytes, and `read` would seek and read back. That technically satisfies the format, but `DataOutputStream` doesn't give you a flush that forces to disk — `FileOutputStream.flush()` is a no-op. You'd need to get at the underlying `FileDescriptor` and call `sync()`, which works but is clunky and doesn't give you positional reads without reopening the file.

The bottleneck is the API surface. You need three things from the file abstraction: append writes, positional reads, and a force-to-disk operation. `FileChannel` gives you all three. Open it with `CREATE` and `WRITE` plus `READ` (you need read access for `read` and `scan`), and you're set.

For `append`, the naive approach is two writes: one for the length, one for the payload. That works, but it doubles syscalls and creates a window where a crash leaves a length prefix with no payload. Instead, allocate a `ByteBuffer` of `4 + record.length`, put both the length and payload into it, and write it in one go. `FileChannel.write` without a position argument appends at the current channel position, so you don't manage a file pointer. The amortized O(1) comes from the fact that you're doing one write call per record and the OS buffers the actual disk I/O.

For `read`, you need positional reads because the caller gives you an arbitrary offset. `FileChannel.read(buf, position)` handles this directly. Read the 4-byte length first, validate it, then read exactly that many payload bytes. The validation matters: if the file is corrupt or you're reading from a bad offset, you want to throw rather than silently return wrong data.

For `scan`, the iterator just wraps `read` in a loop that advances the cursor by `4 + payload.length` each time. It's lazy, so you don't load the whole log into memory. The `hasNext` check is `cursor < size`, which works because every valid record occupies at least 4 bytes.

`flush` is where durability actually happens. `channel.force(false)` is the key call. The `false` argument tells the OS to flush file contents but not metadata. If you passed `true`, it would also force the file's metadata (size, timestamps) to disk, which is an extra fsync-like operation you don't need for correctness here. The file already exists and its size is implied by the data blocks that were just written.

One design decision worth calling out: you track `size` in memory rather than calling `channel.size()` on every append. `channel.size()` is a syscall that can be surprisingly expensive in a hot path. The in-memory counter starts at `channel.size()` in the constructor and increments by exactly `4 + record.length` per append. Since the file only grows, this never goes stale.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Single-write atomicity** — Writing length and payload in one `ByteBuffer` means a crash can never leave a valid-looking length prefix with missing payload. If you wrote them separately, a crash between the two writes would corrupt the log's structure.
- **`force(false)` vs `force(true)`** — Most people don't know the difference. `force(false)` flushes data blocks, which is all you need for crash recovery of file contents. `force(true)` also flushes metadata like file size and mtime, which costs an extra disk sync. Knowing to pass `false` shows you understand what durability actually requires.
- **Length validation in `read`** — Checking that `len >= 0` and `offset + 4 + len <= size` before allocating the payload buffer prevents garbage reads and potential `OutOfMemoryError` from a corrupt length prefix. The interviewer is watching for this.
- **Lazy `scan` iterator** — Implementing `scan` as a real `Iterator` that reads one record at a time keeps memory usage at O(record size) even for a multi-gigabyte log. Eagerly loading all records into a `List` would be a red flag.
- **In-memory `size` counter** — Avoiding `channel.size()` syscalls on every append is a small optimization that matters for a log that might see millions of appends. It also makes `append` truly O(1) in the amortized sense, since you never scan the file to find the end.
- **Crash recovery semantics** — The constructor reading `channel.size()` means you can reopen a log after a crash and immediately scan from any offset. A partially-written record at the tail is simply ignored because it's beyond the last flushed offset — that's the correct behavior, not a bug.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you implement log compaction to reclaim space?** — Think about rewriting only live records to a new file, then atomically swapping. You need a way to know which offsets are still live, so a hash index or bitmap of valid offsets becomes part of the compaction input.
- **How would you use this log as the backbone of a simple key-value store using a hash index of offsets?** — Maintain an in-memory `HashMap<String, Long>` mapping keys to offsets. On `put`, append the record and update the map. On `get`, look up the offset and read. On restart, rebuild the map by scanning the log.
- **What happens to the hash index after compaction?** — Offsets change, so you either rebuild the index by scanning the compacted file or maintain a translation table from old offsets to new offsets.
- **How would you handle concurrent readers and writers?** — The `FileChannel` itself is thread-safe for positional reads and writes, but the `size` counter and the append operation need a lock. Alternatively, use a single writer thread and lock-free reads.
- **What if records are larger than `Integer.MAX_VALUE`?** — The 4-byte length prefix caps records at ~2GB. You could use an 8-byte length or a varint encoding, but that changes the on-disk format and complicates boundary recovery.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same design in Python (`open(..., "r+b")` / `os.fsync` in place of `FileChannel` / `force`) so every claim is executable and testable; the Java reference above is reproduced unchanged.
