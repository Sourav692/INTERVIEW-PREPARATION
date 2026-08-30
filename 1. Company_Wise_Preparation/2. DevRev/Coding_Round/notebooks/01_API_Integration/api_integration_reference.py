# -*- coding: utf-8 -*-
"""API Integration — runnable reference for the DevRev technical round.

Covers: cursor & offset pagination, retry-with-backoff (+ full jitter),
token-bucket rate limiting, idempotent webhook handling, and a client that
composes rate-limiting + retries around a paginated fetch.

Run:  python api_integration_reference.py
"""
import time, random, functools, threading


# =====================================================================
# 1. PAGINATION
# =====================================================================
def fetch_all_pages(fetch_page, start_cursor=None, max_pages=10_000):
    """Loop until there is no next cursor.
    fetch_page(cursor) -> {"items": [...], "next_cursor": "abc" or None}
    """
    results = []
    cursor = start_cursor
    pages = 0
    while True:
        page = fetch_page(cursor)              # one API call for one page
        results.extend(page["items"])          # collect this page's records
        cursor = page.get("next_cursor")       # advance to the next page
        pages += 1
        if not cursor:                         # None / "" / missing -> done
            break
        if pages >= max_pages:                 # safety cap: never loop forever
            raise RuntimeError("pagination exceeded max_pages (possible cursor loop)")
    return results


def fetch_all_offset(fetch_page, page_size=100, max_pages=10_000):
    """fetch_page(offset, limit) -> a plain list (possibly short on the last page)."""
    results = []
    offset = 0
    for _ in range(max_pages):
        items = fetch_page(offset, page_size)  # ask for page_size rows starting at offset
        if not items:                          # empty page -> no more data
            break
        results.extend(items)
        if len(items) < page_size:             # short page = the last page
            break
        offset += page_size
    return results


def extract_next_cursor(page):
    """Normalize the many places APIs hide the 'next' token."""
    for path in (("next_cursor",), ("paging", "next"), ("meta", "next_cursor")):
        node = page
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if node:
            return node
    return None


# =====================================================================
# 2. RETRIES & BACKOFF
# =====================================================================
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class HTTPError(Exception):
    def __init__(self, status, message=""):
        super().__init__(f"HTTP {status} {message}")
        self.status = status


def retry_with_backoff(max_retries=5, base=0.5, cap=30.0, timeout_budget=60.0, sleep=time.sleep):
    """Retry transient HTTP errors with exponential backoff + full jitter."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)          # success -> return
                except HTTPError as e:
                    if e.status not in RETRYABLE_STATUS or attempt >= max_retries:
                        raise                            # fatal, or out of attempts
                    ceiling = min(cap, base * (2 ** attempt))
                    delay = random.uniform(0, ceiling)   # FULL JITTER
                    if time.monotonic() - start + delay > timeout_budget:
                        raise                            # would blow the total budget
                    sleep(delay)
                    attempt += 1
        return wrapper
    return decorator


class IdempotentProcessor:
    """Apply each event at most once; never let a stale event overwrite a newer one."""
    def __init__(self):
        self.applied = {}                       # entity_id -> highest version applied

    def process(self, event):
        eid, version = event["id"], event["version"]
        if eid in self.applied and self.applied[eid] >= version:
            return "skipped"                    # duplicate or out-of-order (stale)
        self.applied[eid] = version
        return "applied"


# =====================================================================
# 3. RATE LIMITING
# =====================================================================
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate                        # tokens per second (the average limit)
        self.capacity = capacity                # max tokens = max burst
        self.tokens = float(capacity)           # start full
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = now

    def try_acquire(self, n=1):
        with self.lock:
            self._refill()
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False

    def acquire(self, n=1):
        while True:
            with self.lock:
                self._refill()
                if self.tokens >= n:
                    self.tokens -= n
                    return
                missing = n - self.tokens
                wait = missing / self.rate
            time.sleep(wait)                     # sleep outside the lock


class RateLimitedClient:
    """Every request waits for a token and retries transient failures."""
    def __init__(self, requests_per_minute, burst=None, transport=None):
        rate = requests_per_minute / 60.0
        capacity = burst or requests_per_minute
        self.bucket = TokenBucket(rate=rate, capacity=capacity)
        self._transport = transport

    @retry_with_backoff(max_retries=5, base=0.2, cap=5.0, timeout_budget=30.0)
    def request(self, *args, **kwargs):
        self.bucket.acquire()                    # 1) rate limit
        return self._transport(*args, **kwargs)  # 2) the actual call

    def fetch_all(self, path):
        def fetch_page(cursor):
            return self.request(path, cursor=cursor)
        return fetch_all_pages(fetch_page)


# =====================================================================
# DEMO / SELF-TEST
# =====================================================================
if __name__ == "__main__":
    print("=== 1. Pagination (cursor) ===")
    DATA = list(range(1, 24))                    # 23 records to page through
    def cursor_page(cursor):
        start = cursor or 0
        chunk = DATA[start:start + 10]           # pages of 10
        nxt = start + 10 if start + 10 < len(DATA) else None
        return {"items": chunk, "next_cursor": nxt}
    got = fetch_all_pages(cursor_page)
    print("  fetched", len(got), "records:", got)
    assert got == DATA

    print("  empty set ->", fetch_all_pages(lambda c: {"items": [], "next_cursor": None}))

    print("\n=== 1b. Pagination (offset) ===")
    def offset_page(offset, limit):
        return DATA[offset:offset + limit]
    got2 = fetch_all_offset(offset_page, page_size=10)
    print("  fetched", len(got2), "records"); assert got2 == DATA

    print("\n=== 2. Retry with backoff (force 429s, then succeed) ===")
    calls = {"n": 0}
    @retry_with_backoff(max_retries=5, base=0.01, cap=0.05, sleep=lambda d: None)  # no real sleeping
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:                       # fail twice with a retryable error
            raise HTTPError(429, "slow down")
        return "ok"
    print("  result:", flaky(), "after", calls["n"], "attempts"); assert calls["n"] == 3

    # a fatal 404 should NOT be retried
    calls404 = {"n": 0}
    @retry_with_backoff(sleep=lambda d: None)
    def fatal():
        calls404["n"] += 1
        raise HTTPError(404, "not found")
    try:
        fatal()
    except HTTPError as e:
        print("  404 raised immediately, attempts =", calls404["n"]); assert calls404["n"] == 1

    print("\n=== 2b. Idempotent webhook processing ===")
    proc = IdempotentProcessor()
    print("  id42 v2 ->", proc.process({"id": 42, "version": 2}))   # applied
    print("  id42 v1 ->", proc.process({"id": 42, "version": 1}))   # skipped (stale/out-of-order)
    print("  id42 v2 ->", proc.process({"id": 42, "version": 2}))   # skipped (duplicate)
    assert proc.applied[42] == 2

    print("\n=== 3. Token bucket enforces the rate ===")
    # rate=20/s, capacity=5 burst: 5 instant, then throttled to ~20/s.
    tb = TokenBucket(rate=20, capacity=5)
    t0 = time.monotonic()
    for _ in range(15):                          # 5 burst + 10 more at 20/s ~= 0.5s
        tb.acquire()
    elapsed = time.monotonic() - t0
    print(f"  15 requests (burst 5) took {elapsed:.2f}s (expected ~0.5s)")
    assert 0.35 <= elapsed <= 0.9

    print("\n=== 4. RateLimitedClient.fetch_all (rate-limited + retried + paginated) ===")
    hits = {"n": 0}
    def transport(path, cursor=None):
        hits["n"] += 1
        if hits["n"] == 2:                       # one transient hiccup mid-scan
            raise HTTPError(503, "try again")
        start = cursor or 0
        chunk = DATA[start:start + 8]
        nxt = start + 8 if start + 8 < len(DATA) else None
        return {"items": chunk, "next_cursor": nxt}
    client = RateLimitedClient(requests_per_minute=600, burst=100, transport=transport)
    result = client.fetch_all("/items")
    print("  fetched", len(result), "records through a rate-limited, retrying client")
    assert result == DATA

    print("\nALL CHECKS PASSED")
