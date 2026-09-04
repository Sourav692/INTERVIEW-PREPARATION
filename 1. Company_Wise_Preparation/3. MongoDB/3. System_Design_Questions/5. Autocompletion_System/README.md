# Design an Autocompletion System

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, Caching, Concurrency, Databases, Distributed Systems, Tries · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design an autocompletion system (e.g., for a search box or text editor).

**Requirements:**

- The system should suggest completions as the user types, based on a large corpus of phrases or queries.
- Suggestions should be ranked by relevance (e.g., popularity, frequency, recency, or other signals).
- The system should return suggestions quickly (low latency, typically **under 100ms**).
- The system should handle a high volume of concurrent requests.
- The system should support adding new phrases and updating popularity scores over time.

**Considerations:**

- How would you store the phrases to support fast prefix lookups?
- How would you rank and filter suggestions?
- How would you scale the system to handle millions of phrases and high query throughput?
- How would you handle typos or misspellings?
- How would you personalize suggestions for individual users?

---

## Study Tools

### Hint 1

The core challenge is serving top-k completions for a prefix with sub-100ms latency. A flat table scan over millions of phrases will never work, so think about a data structure that makes the prefix itself the primary key.

### Hint 2

A trie gives you O(prefix length) traversal to reach the node representing everything the user has typed so far. The hard part is what you store at that node to make retrieving the top-k completions fast without walking the entire subtree.

### Hint 3

**Precompute the top-k results at each trie node** and store them there directly. When a phrase's popularity changes, you only need to update the nodes along that phrase's path, which bounds the write cost by the phrase length.

---

### Answer

This is a prefix-lookup problem best solved with a trie that stores **precomputed top-k suggestions at each node**, fronted by a caching layer and backed by an asynchronous popularity pipeline.

#### Core data structure

The primary index is an in-memory trie. Each node represents a prefix and holds:

- `children`: a map from character to child node
- `top_suggestions`: a fixed-size list (size k, typically 5–10) of `(phrase, score)` pairs, sorted by score descending
- `is_terminal`: whether this node ends a complete phrase

Every phrase in the corpus is inserted into the trie once. At insertion time, or during a periodic rebuild, each node's `top_suggestions` is populated with the k highest-scoring phrases in its subtree. **This is the key design decision:** reads become `O(prefix_length + k)` because you traverse the trie to the prefix node and return the precomputed list directly.

#### Data model

The durable source of truth lives in a relational database:

```sql
CREATE TABLE phrases (
    phrase_id         BIGINT PRIMARY KEY,
    phrase_text       VARCHAR(255) NOT NULL,
    popularity_score  BIGINT NOT NULL DEFAULT 0,
    recency_score     BIGINT NOT NULL DEFAULT 0,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL,
    UNIQUE INDEX idx_phrase_text (phrase_text)
);

CREATE TABLE user_personalization (
    user_id             BIGINT NOT NULL,
    phrase_id           BIGINT NOT NULL,
    interaction_count   INT NOT NULL DEFAULT 0,
    last_interacted_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, phrase_id)
);
```

The `popularity_score` combines frequency and recency with a decay function. A simple approach: `score = frequency * exp(-lambda * age_in_days)` plus a recency bonus for interactions in the last 24 hours. The exact formula depends on the product, but you want **a single number per phrase** that the trie can sort on.

#### Request flow

```
Client -> Load Balancer -> API Gateway -> Autocomplete Service -> Trie (in-memory)
                                                    |
                                                    +-> Redis Cache (per-prefix)
```

1. User types a prefix, client sends `GET /autocomplete?q=pref&limit=5`
2. The service normalizes the prefix (lowercase, trim, Unicode canonicalization)
3. Check Redis cache for the exact prefix. On hit, return immediately
4. On miss, traverse the trie to the prefix node and return its `top_suggestions`
5. Populate the cache with a short TTL (30–60 seconds)

#### Scaling and partitioning

For millions of phrases, the entire trie fits in memory on a single machine. A corpus of 10M phrases averaging 20 characters per phrase, with overhead for nodes and edges, lands in the range of **10–30 GB**. That's well within a single large instance's RAM, but you want replication for throughput and fault tolerance.

**Shard the trie by prefix** when the corpus outgrows a single box. A simple scheme: partition by the first one or two characters of the phrase. With first-character sharding on 26 lowercase letters, each shard holds roughly 1/26 of the corpus. The autocomplete service routes requests to the shard owning the prefix's first character. This keeps prefix lookups local to a single shard with **no cross-shard aggregation** for standard queries.

For throughput: a single trie lookup is a handful of pointer-chases and a list copy. Expect 10k–50k QPS per core in a language like Go or Rust, and maybe 2k–5k QPS in Python with a C-optimized trie. With 8–16 cores per machine and 3–5 replicas, you comfortably serve 100k+ QPS. Redis absorbs hot-prefix traffic and reduces trie load substantially.

#### Popularity updates

Updates flow through an async pipeline:

```
User interactions -> Event Stream (Kafka) -> Aggregation Service -> DB + Trie Updater
```

The trie updater consumes aggregated popularity changes and updates the affected trie nodes. For a phrase `p` of length `L`, the update touches exactly `L` nodes — the path from root to the phrase's terminal node. At each node, the updater recomputes `top_suggestions` by checking if the updated phrase's new score changes the top-k ordering. This is **O(L × k) per update**, which is trivial even at thousands of updates per second.

**Batch updates matter more than per-event updates.** Aggregating popularity deltas over a 10–30 second window and applying them in bulk avoids redundant recomputation when a phrase gets multiple interactions in quick succession.

#### Typos and fuzzy matching

The trie handles exact prefix matching. For typo tolerance, add an edit-distance layer:

- **Trie-based fuzzy search:** traverse the trie with a bounded edit distance (typically 1–2). At each step, consider insertions, deletions, and substitutions. This explodes the search space, so cap it at distance 1 for latency-sensitive paths.
- **SymSpell or BK-tree:** a separate index that maps misspellings to correct phrases. When exact prefix lookup returns few or no results, query the fuzzy index for candidates and merge.
- **Character n-gram index:** index phrases by their character trigrams. For a query prefix, find phrases sharing n-grams with the prefix, then rank by overlap and popularity.

The pragmatic approach: **serve exact matches first** (they're fast and usually right), fall back to fuzzy matching only when the exact result set is empty or below a confidence threshold.

#### Personalization

Personalization adds a user-specific ranking layer on top of the global trie:

- Global suggestions come from the trie as described
- User-specific suggestions come from a per-user cache or a secondary index keyed by `(user_id, prefix)` that stores phrases the user has interacted with matching that prefix
- **Blend:** merge the two lists with a weighting function that boosts user-specific scores by a factor like `1 + alpha * interaction_count`

The per-user index can be a Redis hash or a compact in-memory map on the same service. Only active users need personalization data loaded; inactive users get global suggestions. For a user who has never interacted with a phrase, there's no personalization overhead.

#### Capacity numbers

Assume **100M phrases** in the corpus, **10M daily active users**, and **500M queries per day**.

- **Query rate:** 500M queries/day ÷ 86400 seconds ≈ **5,800 QPS average**, 3–5× peak = **17k–29k QPS**
- **Trie memory:** 100M phrases × ~200 bytes per phrase (nodes, edges, top-k lists) ≈ **20 GB**
- **Redis cache:** hot prefixes only (the top 1M prefixes), each entry ~1 KB including the suggestion list = **1 GB**
- **Update rate:** assume 50M interactions per day ≈ **580 updates/sec** average, 3k/sec peak. Trie updates at O(L × k) handle this easily.

#### API surface

```
GET /autocomplete?q=<prefix>&limit=<k>&user_id=<optional>

Response:
{
  "suggestions": [
    {"phrase": "mongodb atlas", "score": 98231},
    {"phrase": "mongodb aggregation", "score": 87120},
    ...
  ]
}
```

`limit` defaults to 5, capped at 20. `user_id` is optional; when provided, the service blends personalized suggestions with global ones.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: store all phrases in a sorted list or a hash map, and on each query scan every phrase, check if it starts with the prefix, and return the top-k by score. That's O(N × L) per query where N is the number of phrases and L is the average phrase length. With 100M phrases, that's seconds per query. Obviously dead on arrival.

Sorting the phrases lexicographically gets you somewhere: binary search finds the range of phrases matching the prefix in O(log N), but you still have to scan the entire range to find the top-k by score. If a prefix like `"a"` matches 5M phrases, that's still way too slow. **The bottleneck is that lexicographic order doesn't align with score order.**

The insight is to **separate the two concerns**. Store phrases in a trie for fast prefix navigation, and at each trie node, precompute the top-k highest-scoring phrases in that node's subtree. Now a query is just: walk the trie following the prefix characters, then return the precomputed list. Traversal is O(prefix_length), and returning the list is O(k). That's microseconds.

The tradeoff is **write amplification**. Every time a phrase's score changes, you must update every node on the path from root to that phrase's terminal node. For a phrase of length 20, that's 20 node updates. Each update requires checking whether the phrase enters or leaves the top-k at that node, which is O(k) comparisons. So a score update is O(L × k), around 100–200 operations. With 3k updates per second at peak, that's 300k–600k operations per second spread across shards and replicas. Totally manageable.

The next scaling question is **memory**. A trie over 100M phrases is large but fits in RAM on a single machine. When it doesn't, shard by the first character or first two characters. This works because prefix queries only ever touch one shard — the shard owning the prefix's first character. No cross-shard aggregation, no scatter-gather.

For latency, add a **Redis cache** in front of the trie keyed by prefix. Hot prefixes like `"mo"` or `"new"` get hammered, and caching them for 30–60 seconds absorbs a large fraction of traffic. The cache stores the serialized suggestion list, so a hit avoids trie traversal entirely.

For typos, the trie alone is insufficient. The standard approach is a **layered fallback**: try exact prefix matching first, and if results are sparse, query a fuzzy index. A bounded edit-distance traversal over the trie works for distance 1, but distance 2 explodes the search space. A separate SymSpell-style index or character n-gram index is more practical for distance 2.

For personalization, the key realization is that **you don't need a personalized trie per user**. You need a small per-user overlay: a map from prefix to that user's recently interacted phrases. Merge this overlay with global suggestions at query time, boosting user-specific scores. The overlay is small (active users interact with maybe hundreds of distinct phrases), so it fits in Redis or even local memory on the autocomplete service.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Precomputed top-k at each trie node** — this is the insight that makes reads O(prefix length) instead of O(subtree size). If you describe a trie but then say you traverse the subtree to find top-k, you've missed the core optimization.
- **Bounded write amplification from score updates** — updating a phrase's score touches only the L nodes on its path, and each node update is O(k). Stating that number explicitly shows you understand the write path, which is where tries usually fall apart.
- **A concrete popularity formula** — saying "score = frequency with recency decay" is hand-waving. Give the actual formula or at least a specific decay function, and explain why you chose it.
- **Sharding by first character with single-shard queries** — this is a specific, correct partitioning scheme for prefix lookups. It demonstrates you understand that prefix queries have locality that generic hash sharding would destroy.
- **Concrete capacity numbers that multiply out** — 500M queries/day → 5,800 QPS average → 17k–29k peak, 100M phrases → ~20 GB trie. Every number should trace back to an assumption you stated.
- **Layered typo handling** — exact match first, fuzzy fallback only when needed. This is the production-realistic approach, and it shows you understand that fuzzy matching has a real latency cost.
- **Personalization as an overlay, not a per-user trie** — building a separate trie per user is a common mistake. The overlay approach keeps memory bounded and avoids duplicating the global index.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle multi-word phrases where the user types a space and starts a new word?** — Extend the trie to include a space character as a valid edge, or maintain a separate index keyed by last-word prefix.
- **How do you evict phrases from the trie when the corpus changes significantly?** — Periodic full rebuilds from the database, or lazy deletion with tombstoning and batch cleanup.
- **How would you support prefix matching in languages with no clear word boundaries, like Chinese or Japanese?** — Character-level tries work, but you may need an IME-aware tokenizer or n-gram index.
- **What happens when a celebrity tweet causes a sudden spike in a phrase's popularity?** — Your async update pipeline needs to handle bursty updates without delaying reads; consider a fast-path in-memory score bump with eventual consistency.
- **How do you measure suggestion quality and A/B test ranking changes?** — Define offline metrics (MRR, precision@k against historical queries) and online metrics (click-through rate on suggestions).

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Three problems with the answer

All three are demonstrated with runnable assertions in [`5. Autocompletion_System.ipynb`](5.%20Autocompletion_System.ipynb).

### 1. The update path is only correct for score *increases* — and the design guarantees decreases

This is the real flaw, and it sits under the answer's headline claim.

> *"At each node, the updater recomputes `top_suggestions` by checking if the updated phrase's new score changes the top-k ordering. This is O(L × k) per update."*

That works when a score goes **up**: compare against the node's current k entries, insert if it beats the weakest, done. Everything you need is already in the node.

It does **not** work when a score goes **down** and the phrase falls out of the top-k. To replace it you need the *(k+1)-th best phrase in that node's subtree* — and the node doesn't store it. Finding it means walking the subtree, which is precisely the O(subtree size) cost the precomputed list exists to avoid. Near the root, that subtree is most of the corpus.

And this isn't a rare edge case. The answer's own scoring formula is

```
score = frequency * exp(-lambda * age_in_days)
```

**Every phrase's score decreases on every tick of the clock.** Decay makes demotion the normal case, not the exception. As written, stale phrases would be pinned in every node's top-k until a full rebuild.

The usual first fix is **slack plus lazy repair**: store top-`2k` at each node, serve the best k still valid, and recompute a node's subtree when its valid count drops below k.

**But that fixes deletion, not decay** — and the notebook measures the difference. The repair trigger fires when entries become *invalid*; decay never invalidates anything, because every stored score stays current and correct. A node can hold 2k perfectly valid entries that have all decayed below a phrase which was never in the list, and nothing signals it.

Measured over 400 decay events:

| Strategy | Prefixes returning the exact top-k |
|---|---|
| Naive, no slack (as written) | 69.6% |
| Slack 2× + lazy repair | 92.8% |
| Slack 4× + lazy repair | 98.6% |
| Monotone scores, decay at read | 92.8% |
| Monotone, slack 4× | 98.6% |

Slack is what buys accuracy, and **none of it reaches 100%**. A precomputed top-k trie under a decaying score fundamentally requires a periodic full rebuild; the design choices only decide whether that runs hourly or weekly.

The genuinely valuable second fix is to **make the stored score monotone**: store raw `frequency` plus a timestamp, and apply decay to the ≤ 2k candidates at *read* time. Ageing then costs **zero writes**, stored scores only ever increase, and the O(L × k) claim becomes true as written. It doesn't beat slack on accuracy at equal slack — what it fixes is the write path.

**The answer to give:** O(L × k) per update, monotone stored scores, decay applied at read, *plus a nightly full rebuild* — and say why the rebuild isn't optional. Claiming O(L × k) with no rebuild is the actual error.

### 2. The two memory estimates disagree by 5–15×

| Section | Corpus | Memory | Implied bytes/phrase |
|---|---|---|---|
| Scaling and partitioning | 10M phrases | 10–30 GB | **1,000–3,000 B** |
| Capacity numbers | 100M phrases | 20 GB | **200 B** |

Ten times the corpus in *less* memory. Both figures are quoted confidently and they cannot both be right.

Both figures are defensible — for *different implementations*. The notebook models three levers and reproduces each stated number almost exactly:

| Layout | Bytes/node | Top-k entry | Nodes carrying a list | Result |
|---|---|---|---|---|
| Naive (object + hash map per node, phrase **strings** in the lists) | 120 | 36 | 100% | **2,100 B/phrase** → 21 GB at 10M |
| Compact (packed child slots, interned phrase **IDs**) | 20 | 8 | **20%** | **196 B/phrase** → 19.6 GB at 100M |

The third column is the lever nobody mentions. At ~7 trie nodes per phrase, a 5-entry list at *every* node is most of the footprint. Deep nodes have tiny subtrees, so their top-k is cheap to compute on the fly — store precomputed lists only where the subtree is big enough to be worth it.

**The layout has to be stated, because it moves the answer by an order of magnitude.**

### 3. First-character sharding is not "roughly 1/26"

> *"With first-character sharding on 26 lowercase letters, each shard holds roughly 1/26 of the corpus."*

English first letters are nowhere near uniform. Using standard dictionary initial-letter frequencies, `s` starts about 11% of words and `x` about 0.1%:

| | Share of corpus | vs. the 1/26 (3.85%) claim |
|---|---|---|
| `s` (largest) | ~11.4% | **3.0×** |
| `x` (smallest) | ~0.1% | 0.03× |
| largest : smallest | | **~110:1** |

So you provision every shard for 3× the claimed size while most sit nearly idle. And query traffic is *more* skewed than the corpus, because popular queries cluster.

Sharding by prefix is still the right idea — it preserves the locality that makes queries single-shard. The fix is **balanced range partitioning**: choose split points from the actual corpus distribution so each shard gets an equal share (`a–c`, `d–f`, … and `s` alone split further into `sa–sm`, `sn–sz`). You keep single-shard prefix queries and get even load. Saying "1/26" without checking the distribution is the mistake.

**See also:** [`20. Smallest_Numbers`](../../2.%20Coding_Questions/20.%20Smallest_Numbers/README.md) covers the top-K heap machinery, and [`10. LRU_Cache`](../../2.%20Coding_Questions/10.%20LRU_Cache/README.md) covers the caching layer in front of the trie.
