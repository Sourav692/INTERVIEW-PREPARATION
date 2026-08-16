# 🚀 6-Week Data Engineering & DSA Master Interview Preparation Roadmap

> **Target Roles:** Senior / Staff Data Engineer, Lead Analytics Engineer, Distributed Systems Engineer.  
> **Commitment:** 2–3 Hours / Day (~15–20 Hours / Week) over 6 Weeks.

---

## 🎯 High-Level Structure & Core Pillars

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           6-WEEK MASTER PREP MATRIX                             │
├───────────────┬──────────────────────┬────────────────────────┬─────────────────┤
│   Pillar 1    │       Pillar 2       │        Pillar 3        │    Pillar 4     │
│   DSA & ALGO  │  CORE DATA ENG/SPARK │   DE SYSTEM DESIGN     │  OOP / SE / AI  │
├───────────────┼──────────────────────┼────────────────────────┼─────────────────┤
│ Blind 75+     │ Spark Catalyst, AQE, │ Lambda vs Kappa, CDC,  │ Design Patterns,│
│ Patterns,     │ Skew, Shuffling,     │ Lakehouse (Delta/Ice), │ Resilient APIs, │
│ Time & Space  │ Delta Lake, Tuning,  │ Streaming (Kafka/Flink)│ LLM Tool-calling│
│ Complexity    │ Advanced SQL         │ Data Modeling          │ (DevRev focus)  │
└───────────────┴──────────────────────┴────────────────────────┴─────────────────┘
```

---

## 📅 Week 1: Foundations, Two Pointers, Advanced SQL & Ingestion Architectures

### 🧠 Core Goals
1. Master Arrays, Hashing, Two Pointers, and Sliding Window techniques.
2. Master Advanced SQL: Window Functions, CTEs, Gaps & Islands, Execution plans.
3. System Design: Ingestion fundamentals (Push vs Pull, Batch vs Streaming, Backpressure).
4. Software Engineering: OOP principles, Creational Design Patterns (Singleton, Factory, Builder).

---

### 📋 Daily Breakdown

#### **Day 1: Arrays & Hashing Fundamentals**
- **DSA Practice:**
  - [Two Sum](https://leetcode.com/problems/two-sum/) (Easy) — Hash Map lookup `O(N)`
  - [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) (Easy) — Set lookup `O(N)`
  - [Valid Anagram](https://leetcode.com/problems/valid-anagram/) (Easy) — Frequency array / Hash Map
- **Data Engineering:**
  - SQL Window Functions: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE()`.
  - Case Study: Finding the top 3 salaries per department without subquery joins.
- **SE / System Design:**
  - Principles: SOLID principles with real-world Python examples.

#### **Day 2: Two Pointers & Two-Sum Variants**
- **DSA Practice:**
  - [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) (Easy) — Inward two-pointer
  - [3Sum](https://leetcode.com/problems/3sum/) (Medium) — Sorting + Two Pointers `O(N^2)`
  - [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) (Medium) — Greedy inward pointers
- **Data Engineering:**
  - SQL Analytic Functions: `LEAD()`, `LAG()`, `FIRST_VALUE()`, `LAST_VALUE()`.
  - Frame specification: `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` vs `RANGE`.
- **System Design:**
  - Ingestion Architectures: Webhook/Push vs Polling/Pull, Rate limiting, Message Queues as buffers.

#### **Day 3: Sliding Window (Fixed & Dynamic)**
- **DSA Practice:**
  - [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) (Easy) — Single pass state tracking
  - [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) (Medium) — Dynamic sliding window with set/map
  - [Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) (Medium) — Max frequency in window
- **Data Engineering:**
  - Complex SQL: Gaps & Islands problem (identifying contiguous active session ranges).
- **SE / OOP:**
  - Creational Patterns: **Factory Method** & **Abstract Factory** for pluggable database connectors.

#### **Day 4: Sliding Window Hard & Prefix Sum**
- **DSA Practice:**
  - [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) (Hard) — Window with character frequency target counter
  - [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) (Medium) — Prefix Sum + Hash Map
- **Data Engineering:**
  - SQL Query Optimization: Index types (B-Tree, Hash, Bitmap), Query Execution Plan reading (`EXPLAIN ANALYZE`).
- **System Design:**
  - Batch Ingestion at scale: File chunking, SFTP/S3 bulk ingestion, retry strategies, dead-letter queues.

#### **Day 5: Strings & Matrix Manipulation**
- **DSA Practice:**
  - [Group Anagrams](https://leetcode.com/problems/group-anagrams/) (Medium) — Tuple of character counts as hash key
  - [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) (Medium) — Bucket Sort `O(N)` or Min-Heap `O(N log K)`
  - [Rotate Image](https://leetcode.com/problems/rotate-image/) (Medium) — Transpose + Reverse rows
- **Data Engineering:**
  - Data Validation: Null handling, schema drift, idempotency in SQL ELT pipelines.
- **SE / AI:**
  - Design Pattern: **Singleton** (Thread-safe connection pool) and **Builder** (Query builder pattern).

#### **Day 6: Deep-Dive Integration & Review**
- **DSA Practice:**
  - [Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/) (Medium) — Left and right product passes `O(N)`
  - [Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) (Medium) — Hash Set range starter detection
- **System Design Blueprint:**
  - Case Study: Design an API rate limiter & ingestion gateway for 50k events/sec.

#### **Day 7: Mock Interview Drill #1 & Self-Assessment**
- Complete **Weekly Mock Drill 1** (see Rubrics below).
- Review all failed/stumbled problems and document lessons in `DSA_Deep_Dive`.

---

## 📅 Week 2: Linked Lists, Stacks, Spark Internals & CDC Pipelines

### 🧠 Core Goals
1. Master Linked Lists, Stacks, Monotonic Stacks, and Binary Search.
2. Apache Spark Internals: Driver/Executor architecture, Catalyst Optimizer, Tungsten Execution Engine, RDD vs DataFrame vs Dataset.
3. System Design: Change Data Capture (CDC), Debezium, Kafka log compaction, transactional outbox pattern.
4. Software Engineering: Structural Design Patterns (Adapter, Decorator, Facade).

---

### 📋 Daily Breakdown

#### **Day 8: Linked List Manipulations**
- **DSA Practice:**
  - [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/) (Easy) — Iterative & Recursive
  - [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/) (Easy) — Sentinel dummy node
  - [Reorder List](https://leetcode.com/problems/reorder-list/) (Medium) — Find middle + Reverse 2nd half + Interleave
- **Spark Internals:**
  - Architecture: Driver, Cluster Manager (YARN/K8s/Standalone), Executors, Slots, Tasks, Stages, Jobs.
  - Transformation vs Action, Narrow vs Wide dependencies (Lineage Graph / DAG).

#### **Day 9: Fast & Slow Pointers and Advanced Linked Lists**
- **DSA Practice:**
  - [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/) (Easy) — Floyd's Tortoise and Hare
  - [Remove Nth Node From End of List](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) (Medium) — Two-pointer offset
  - [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) (Hard) — Min-Heap `O(N log K)` or Divide & Conquer
- **Spark Internals:**
  - Catalyst Optimizer 4 phases: Analysis (Catalog) -> Logical Optimization -> Physical Planning -> Cost Model / Code Generation.
  - Tungsten Engine: Off-heap memory management (sun.misc.Unsafe), Whole-Stage Code Generation, Cache-aware computation.

#### **Day 10: Stacks & Monotonic Stacks**
- **DSA Practice:**
  - [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) (Easy) — Stack with matching hashmap
  - [Min Stack](https://leetcode.com/problems/min-stack/) (Medium) — Auxiliary stack or pair storage
  - [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/) (Medium) — Monotonic Decreasing Stack
- **System Design (CDC):**
  - Change Data Capture (CDC) mechanics: WAL parsing (Postgres `pgoutput`, MySQL `binlog`).
  - Debezium + Kafka Connect + Transactional Outbox pattern.

#### **Day 11: Monotonic Stack Hard & Binary Search Basics**
- **DSA Practice:**
  - [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) (Hard) — Monotonic Stack boundary tracking
  - [Binary Search](https://leetcode.com/problems/binary-search/) (Easy) — Standard template `left <= right`
  - [Search a 2D Matrix](https://leetcode.com/problems/search-a-2d-matrix/) (Medium) — Coordinate transformation `mid // cols`, `mid % cols`
- **Spark Core:**
  - PySpark DataFrame API: `withColumn`, `groupBy`, `agg`, `selectExpr`, window specifications in PySpark.

#### **Day 12: Binary Search in Rotated Arrays & Search Space Reduction**
- **DSA Practice:**
  - [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) (Medium) — Unsorted half boundary check
  - [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) (Medium) — Determine which side is strictly sorted
  - [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) (Medium) — Binary Search on Answer space `[1, max(piles)]`
- **SE / Design Patterns:**
  - Structural Patterns: **Adapter** (standardizing heterogeneous data sources) and **Decorator** (telemetry / retry wrappers).

#### **Day 13: End-to-End Spark & CDC Integration**
- **DSA Practice:**
  - [Evaluate Reverse Polish Notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/) (Medium) — Stack evaluation
  - [Car Fleet](https://leetcode.com/problems/car-fleet/) (Medium) — Time-to-destination monotonic stack
- **System Design Blueprint:**
  - Case Study: Design an End-to-End CDC ingestion pipeline from MySQL to Data Lakehouse with deduplication.

#### **Day 14: Mock Interview Drill #2 & Self-Assessment**
- Complete **Weekly Mock Drill 2**.
- Deep review on Spark catalyst physical plan diagnosis (`df.explain(True)`).

---

## 📅 Week 3: Trees, Spark Optimization, Delta Lake & Lakehouse

### 🧠 Core Goals
1. Master Binary Trees, Binary Search Trees (BST), Tree Traversals (BFS, DFS, In-order, Post-order, Pre-order), Tries.
2. Spark Performance Tuning: Shuffling, Spill to Disk, Data Skew mitigation, Adaptive Query Execution (AQE), Broadcast Joins.
3. System Design: Modern Lakehouse Architectures (Delta Lake, Apache Iceberg, Apache Hudi), ACID on Object Storage, Time Travel, Medallion Architecture.
4. Software Engineering: Behavioral Design Patterns (Strategy, Observer, Command).

---

### 📋 Daily Breakdown

#### **Day 15: Binary Tree Traversals & Properties**
- **DSA Practice:**
  - [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) (Easy) — DFS / BFS
  - [Same Tree](https://leetcode.com/problems/same-tree/) (Easy) — Simultaneous traversal
  - [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) (Easy) — Post-order / Pre-order swap
- **Spark Performance:**
  - Shuffling mechanics: Hash Partitioning, Range Partitioning, Shuffle Read/Write bottlenecks.
  - Shuffle Spill (Memory vs Disk): Root causes (high memory pressure, skewed partition size) and fixes.

#### **Day 16: Tree BFS & Level Order Processing**
- **DSA Practice:**
  - [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) (Medium) — Queue BFS with level size tracking
  - [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) (Medium) — BFS rightmost element or DFS right-first
  - [Subtree of Another Tree](https://leetcode.com/problems/subtree-of-another-tree/) (Easy) — Tree comparison sub-routine
- **Spark Performance Tuning:**
  - Data Skew handling techniques: Salting (adding random prefix + broadcast join), Custom partitioners, AQE skew join optimization.
  - Broadcast Hash Join (`broadcast(df)`): Thresholds (`spark.sql.autoBroadcastJoinThreshold`), limitations (driver OOM).

#### **Day 17: Binary Search Tree (BST) & Validation**
- **DSA Practice:**
  - [Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/) (Medium) — Min/Max bound propagation or In-order traversal
  - [Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/) (Medium) — In-order iterative stack
  - [Lowest Common Ancestor of a BST](https://leetcode.com/problems/lowest-common-ancestor-of-a-bst/) (Medium) — Split condition logic
- **Lakehouse Deep Dive:**
  - Delta Lake Architecture: `_delta_log` JSON commits + Parquet checkpoints, ACID transactions, Optimistic Concurrency Control (OCC).
  - Delta operations: `MERGE INTO`, `OPTIMIZE` (Bin-packing / Compaction), `Z-ORDER BY`, `VACUUM` (Retention limits).

#### **Day 18: Tree Construction & Path Sums (DFS Hard)**
- **DSA Practice:**
  - [Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/) (Medium) — Hash Map of indices + recursive split
  - [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) (Hard) — Global max with single branch return
  - [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) (Hard) — Pre-order traversal with sentinel `null`
- **Lakehouse & Medallion Architecture:**
  - Bronze (Raw / Append-only) -> Silver (Enriched, Cleaned, Conformed, SCD Type 2) -> Gold (Aggregated, Star Schema, BI-ready).
  - Iceberg vs Delta comparison: Metadata tree (Snapshots -> Manifest Lists -> Manifest Files) vs Transaction log.

#### **Day 19: Prefix Trees (Tries)**
- **DSA Practice:**
  - [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/) (Medium) — TrieNode with `children` dict and `is_end` flag
  - [Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/) (Medium) — Trie with DFS dot wildcard
  - [Word Search II](https://leetcode.com/problems/word-search-ii/) (Hard) — Backtracking on 2D Board + Trie pruning
- **SE / Design Patterns:**
  - Behavioral Patterns: **Strategy** (Swappable ingestion parsers/sinks) and **Observer** (Event-driven pipeline triggers).

#### **Day 20: Advanced Spark Memory Management & AQE**
- **DSA Practice:**
  - [Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) (Medium) — General tree post-order traversal
- **Spark AQE (Adaptive Query Execution):**
  - Dynamically coalescing shuffle partitions (`spark.sql.adaptive.coalescePartitions.enabled`).
  - Dynamically switching join strategies (SortMergeJoin -> BroadcastHashJoin at runtime).
  - Dynamically optimizing skew joins.

#### **Day 21: Mock Interview Drill #3 & Self-Assessment**
- Complete **Weekly Mock Drill 3**.
- Review Delta Lake OCC conflict resolution scenarios.

---

## 📅 Week 4: Heaps, Backtracking, Streaming & Real-Time Architectures

### 🧠 Core Goals
1. Master Heaps / Priority Queues, Intervals, and Backtracking algorithms.
2. Structured Streaming & Databricks: Triggers, Watermarking, Exactly-once processing, Checkpointing, Delta Live Tables (DLT).
3. System Design: Streaming architectures with Apache Kafka & Apache Flink (Stateful stream processing, Windowing: Tumbling, Sliding, Session).
4. Software Engineering: Resilient API Design, Idempotency keys, Circuit Breakers, Rate Limiters.

---

### 📋 Daily Breakdown

#### **Day 22: Priority Queues / Heaps**
- **DSA Practice:**
  - [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/) (Medium) — Min-Heap of size K `O(N log K)` or Quickselect `O(N)`
  - [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) (Medium) — Max-Heap of size K
  - [Task Scheduler](https://leetcode.com/problems/task-scheduler/) (Medium) — Max-Heap / Greedy frequency counting
- **Spark Structured Streaming:**
  - Processing model: Micro-batch vs Continuous Processing.
  - Streaming Sources & Sinks (Kafka, Delta, S3, Memory). Output Modes: `append`, `update`, `complete`.

#### **Day 23: Two Heaps & Hard Priority Queue**
- **DSA Practice:**
  - [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) (Hard) — Max-Heap (lower half) + Min-Heap (upper half)
  - [Merge Intervals](https://leetcode.com/problems/merge-intervals/) (Medium) — Sort by start time + Greedy merge
  - [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) (Medium) — Greedy interval scheduling (sort by end time)
- **Streaming Internals:**
  - Watermarking (`withWatermark("timestamp", "10 minutes")`): Handling late data, dropping outdated state.
  - Streaming Joins: Stream-Static Join vs Stream-Stream Join (State store size management).

#### **Day 24: Interval Management & Insertions**
- **DSA Practice:**
  - [Insert Interval](https://leetcode.com/problems/insert-interval/) (Medium) — Left unmerged + Merge overlap + Right unmerged
  - [Meeting Rooms](https://leetcode.com/problems/meeting-rooms/) (Easy) / [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/) (Medium) — Min-Heap for room allocation
- **Kafka Architecture:**
  - Brokers, Topics, Partitions, Consumer Groups, Offsets, Log retention, Replication factor, ISR (In-Sync Replicas).
  - Producer semantics: `acks=0`, `acks=1`, `acks=all`, `idempotence=true`.

#### **Day 25: Backtracking Core**
- **DSA Practice:**
  - [Subsets](https://leetcode.com/problems/subsets/) (Medium) — Choice tree / Bit manipulation
  - [Combination Sum](https://leetcode.com/problems/combination-sum/) (Medium) — Reusable elements backtracking with index branch
  - [Permutations](https://leetcode.com/problems/permutations/) (Medium) — Visited array / swap in-place
- **Flink & Stream Processing Concepts:**
  - Exactly-Once semantics via Chandy-Lamport distributed snapshotting (Checkpoints & Savepoints).
  - Windowing types: Tumbling (fixed non-overlapping), Sliding (overlapping), Session (inactivity gap).

#### **Day 26: Advanced Backtracking & Grid Search**
- **DSA Practice:**
  - [Word Search](https://leetcode.com/problems/word-search/) (Medium) — 2D Backtracking with in-place character masking
  - [Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/) (Medium) — Backtracking + DP palindrome verification
  - [Letter Combinations of a Phone Number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/) (Medium) — Recursive phone map expansion
- **Databricks Platform & DLT:**
  - Delta Live Tables (DLT): Expectations (`@dlt.expect`, `@dlt.expect_or_drop`, `@dlt.expect_or_fail`), Auto Loader (`cloudFiles`).
  - Unity Catalog: Three-level namespace (`catalog.schema.table`), Data lineage, Fine-grained access control (Row/Column filters).

#### **Day 27: Resilient API Design & Integration**
- **DSA Practice:**
  - [N-Queens](https://leetcode.com/problems/n-queens/) (Hard) — Column, diag1, diag2 bitmasks / sets
- **SE / Resilient Systems:**
  - Idempotency keys implementation (Distributed lock via Redis + Token deduplication).
  - Circuit Breaker pattern (Closed -> Open -> Half-Open) and Exponential Backoff with Jitter.

#### **Day 28: Mock Interview Drill #4 & Self-Assessment**
- Complete **Weekly Mock Drill 4**.
- Diagram a low-latency real-time streaming pipeline end-to-end.

---

## 📅 Week 5: Graphs, Data Warehousing & Modern AI Tool Calling

### 🧠 Core Goals
1. Master Graphs: BFS, DFS, Topological Sort (Kahn's algorithm), Union-Find (Disjoint Set Union), Shortest Path (Dijkstra).
2. Data Warehousing & Modeling: Star Schema vs Snowflake, Slowly Changing Dimensions (SCD Type 1, 2, 3, 4, 6), Partitioning vs Sharding.
3. System Design: Clickstream analytics, large-scale metrics aggregation platform.
4. Software Engineering & AI: LLM Tool Calling, Agentic Pipeline Architecture, Schema generation, DevRev integration patterns.

---

### 📋 Daily Breakdown

#### **Day 29: Graph BFS / DFS & Connected Components**
- **DSA Practice:**
  - [Number of Islands](https://leetcode.com/problems/number-of-islands/) (Medium) — 2D Grid DFS / BFS
  - [Clone Graph](https://leetcode.com/problems/clone-graph/) (Medium) — Hash Map mapping old node -> new node + DFS/BFS
  - [Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/) (Medium) — Multi-source BFS/DFS from ocean borders
- **Data Warehousing:**
  - Dimensional Modeling (Kimball Methodology): Fact tables (Transactional, Periodic Snapshot, Accumulating Snapshot), Dimension tables, Conformed Dimensions, Surrogate Keys.

#### **Day 30: Topological Sort & Cycle Detection**
- **DSA Practice:**
  - [Course Schedule](https://leetcode.com/problems/course-schedule/) (Medium) — Kahn's Algorithm (In-degree array + Queue) or DFS 3-color state
  - [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) (Medium) — Topological ordering output
  - [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) (Hard) — Graph construction from adjacent word diffs + Topo sort
- **Data Warehousing:**
  - Slowly Changing Dimensions (SCD):
    - Type 1: Overwrite
    - Type 2: Add new row with `is_current`, `valid_from`, `valid_to`
    - Type 3: Add previous value column
    - Type 6: Hybrid (1 + 2 + 3)

#### **Day 31: Union-Find (Disjoint Set Union)**
- **DSA Practice:**
  - [Number of Connected Components in an Undirected Graph](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/) (Medium) — Union by rank with path compression
  - [Redundant Connection](https://leetcode.com/problems/redundant-connection/) (Medium) — Detect edge connecting already unified nodes
  - [Graph Valid Tree](https://leetcode.com/problems/graph-valid-tree/) (Medium) — `E == V - 1` and single connected component
- **Data Engineering Storage:**
  - Partitioning vs Sharding vs Bucketing/Clustering: Range partitioning, Hash partitioning, Columnar formats (Parquet vs ORC: Dictionary encoding, RLE, Snappy/ZSTD compression).

#### **Day 32: Advanced Graph & Word Ladder**
- **DSA Practice:**
  - [Word Ladder](https://leetcode.com/problems/word-ladder/) (Hard) — Bidirectional BFS on intermediate wildcards
  - [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) (Medium) — Multi-source BFS with minute counter
  - [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) (Medium) — Bellman-Ford / Modified Dijkstra
- **System Design Blueprint:**
  - Case Study: Design a Real-Time Clickstream Analytics platform processing 100M events/day with 1-second dashboard latency.

#### **Day 33: LLM Tool Calling & Agentic Pipeline Architecture**
- **DSA Practice:**
  - [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) (Medium) — Boundary DFS un-flipping
  - [Accounts Merge](https://leetcode.com/problems/accounts-merge/) (Medium) — Union-Find on email addresses
- **Modern AI & Agentic Systems (DevRev Focus):**
  - Function / Tool Calling Architecture: JSON Schema definition, System Prompts, Tool dispatch loop, Error recovery & fallback.
  - Multi-agent orchestration, Structured Output enforcement (Pydantic / Instructor), Vector databases & Hybrid Search (BM25 + Dense Embeddings).

#### **Day 34: System Design Case Study: Metrics Aggregator**
- **DSA Practice:**
  - Graph review and timed contest simulation (3 Mediums in 60 mins).
- **System Design Blueprint:**
  - Case Study: Design a distributed Timeseries Metrics Store & Alerting System (e.g. Datadog / Prometheus scale).

#### **Day 35: Mock Interview Drill #5 & Self-Assessment**
- Complete **Weekly Mock Drill 5**.
- Evaluate graph problem time complexity proofs and Kimball modeling trade-offs.

---

## 📅 Week 6: Dynamic Programming, Cost Optimization & Full Mock Simulation

### 🧠 Core Goals
1. Master 1D and 2D Dynamic Programming (Memoization & Tabulation), Interval DP, and Subsequence patterns.
2. Production Operations: Pipeline Monitoring, Data Quality Frameworks (Great Expectations, Soda), Cost Optimization & FinOps, Governance.
3. System Design: Complex multi-tier architectures (Real-Time Fraud Detection, Financial Double-entry Ledger).
4. Full Interview Simulations: Technical Coding, DE Deep Dive, System Design & Behavioral Leadership.

---

### 📋 Daily Breakdown

#### **Day 36: 1D Dynamic Programming Foundations**
- **DSA Practice:**
  - [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) (Easy) — Fibonacci state `O(1)` space
  - [Min Cost Climbing Stairs](https://leetcode.com/problems/min-cost-climbing-stairs/) (Easy) — Single-state transition
  - [House Robber](https://leetcode.com/problems/house-robber/) (Medium) — `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`
  - [House Robber II](https://leetcode.com/problems/house-robber-ii/) (Medium) — Two passes `nums[1:]` and `nums[:-1]`
- **Production Operations:**
  - Pipeline monitoring: Data SLAs, Alert fatigue mitigation, Dead Letter Queues (DLQ), Circuit breakers in ETL.

#### **Day 37: 1D DP Classic Optimization Problems**
- **DSA Practice:**
  - [Coin Change](https://leetcode.com/problems/coin-change/) (Medium) — Unbounded knapsack `dp[i] = min(dp[i], dp[i - c] + 1)`
  - [Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/) (Medium) — `O(N^2)` DP or `O(N log N)` with Binary Search Patience Sorting
  - [Word Break](https://leetcode.com/problems/word-break/) (Medium) — `dp[i]` matched prefixes
- **FinOps & Cost Optimization:**
  - Spark/Databricks Cost Tuning: Spot instances vs On-demand, Graviton/ARM instances, Autoscaling policies, Cluster idle termination, Parquet file sizing (128MB–1GB sweet spot).

#### **Day 38: 2D Dynamic Programming & Grid Paths**
- **DSA Practice:**
  - [Unique Paths](https://leetcode.com/problems/unique-paths/) (Medium) — 2D grid DP / 1D rolling array
  - [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) (Medium) — Matrix DP matching characters
  - [Best Time to Buy and Sell Stock with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/) (Medium) — State machine DP (Hold, Sold, Rest)
- **Data Quality & Governance:**
  - Data Quality: Great Expectations / Deequ / SodaCL validations.
  - Governance: Data cataloging, column-level lineage, GDPR/CCPA compliance (Right to be forgotten in Delta Lake / Iceberg).

#### **Day 39: 2D DP Hard & Knapsack Variations**
- **DSA Practice:**
  - [Edit Distance](https://leetcode.com/problems/edit-distance/) (Medium) — Insert, Delete, Replace transitions
  - [Target Sum](https://leetcode.com/problems/target-sum/) (Medium) — Subset sum knapsack variation
  - [Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/) (Hard) — 2D String matching DP
- **System Design Blueprint:**
  - Case Study: Design a Real-Time Financial Ledger & Fraud Detection System with strict consistency and Exactly-Once processing.

#### **Day 40: High-Impact Pattern Synthesis & Quick Revision**
- **DSA Practice:**
  - [Decode Ways](https://leetcode.com/problems/decode-ways/) (Medium) — String parsing DP with 0 validation
  - [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) (Medium) — Kadane's Algorithm
  - [Jump Game](https://leetcode.com/problems/jump-game/) (Medium) & [Jump Game II](https://leetcode.com/problems/jump-game-ii/) (Medium) — Greedy reachability
- **Behavioral & Project Defense:**
  - STAR Method structuring: Biggest data pipeline failure & how you fixed it, resolving team technical disagreements, scaling bottlenecks.

#### **Day 41: Full-Length Mock Simulation #1 (DSA + Spark Deep-Dive)**
- **Round 1 (60 mins):** Timed 2-problem DSA session (1 Medium + 1 Hard).
- **Round 2 (60 mins):** Spark architecture, memory troubleshooting, and SQL tuning drill.

#### **Day 42: Full-Length Mock Simulation #2 (System Design & AI Tools)**
- **Round 3 (60 mins):** Large-scale Data Platform System Design (Clickstream / Lakehouse / Real-time alerts).
- **Round 4 (45 mins):** LLM Tool Calling, Agentic pipeline integration, and Behavioral review.

---

## 🏆 Weekly Mock Interview Drill Sets & Evaluation Rubrics

### 📝 Mock Drill 1 (End of Week 1)
1. **DSA Coding (45m):** [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) (Hard) or [3Sum](https://leetcode.com/problems/3sum/) (Medium).
2. **SQL Deep Dive (30m):** Write a query to find consecutive active user streaks across multiple regions, handling missing days and ties.
3. **Trap Question:** *"Why is `SELECT DISTINCT` often a code smell in data pipelines, and what are the performance implications during shuffle?"*
4. **Evaluation Rubric:**
   - [ ] Stated time/space complexity before coding.
   - [ ] Handled edge cases (empty strings, all duplicates, negative numbers).
   - [ ] Explained SQL execution order: `FROM` -> `WHERE` -> `GROUP BY` -> `HAVING` -> `SELECT` -> `WINDOW` -> `ORDER BY` -> `LIMIT`.

---

### 📝 Mock Drill 2 (End of Week 2)
1. **DSA Coding (45m):** [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) (Hard) or [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) (Medium).
2. **Spark Architecture (30m):** Explain step-by-step what happens physically inside a cluster when you execute:  
   `df.groupBy("user_id").agg(count("*")).filter("count > 5")`.
3. **Trap Question:** *"What causes a Spark driver OOM vs an executor OOM, and how do you fix each?"*
4. **Evaluation Rubric:**
   - [ ] Accurately detailed Exchange (Shuffle), Sort/Hash Aggregate, and Predicate Pushdown.
   - [ ] Driver OOM: `collect()`, `broadcast()` too large, driver memory undersized.
   - [ ] Executor OOM: Skew, high concurrency per core, insufficient off-heap/execution memory.

---

### 📝 Mock Drill 3 (End of Week 3)
1. **DSA Coding (45m):** [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) (Hard) or [Implement Trie](https://leetcode.com/problems/implement-trie-prefix-tree/) (Medium).
2. **Lakehouse Architecture (30m):** How does Delta Lake ensure ACID transactions over S3/GCS without a centralized database? How does it handle concurrent writes?
3. **Trap Question:** *"If a Spark job with 200 tasks has 199 tasks finish in 5 seconds and 1 task takes 45 minutes, how do you diagnose and fix it?"*
4. **Evaluation Rubric:**
   - [ ] Diagnosed Data Skew / Spill to disk via Spark UI Task Metrics.
   - [ ] Proposed: Salting key, Adaptive Query Execution (`spark.sql.adaptive.skewJoin.enabled`), Broadcast join, or Repartitioning by high-cardinality composite key.
   - [ ] Explained Delta Lake OCC and atomic log commits.

---

### 📝 Mock Drill 4 (End of Week 4)
1. **DSA Coding (45m):** [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) (Hard) or [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/) (Medium).
2. **Streaming System Design (30m):** Design a real-time alerting engine that triggers an anomaly event if a user logs in from two distinct countries within 10 minutes.
3. **Trap Question:** *"How does Kafka guarantee message ordering, and what happens to ordering if a partition has multiple consumers or if retries are enabled?"*
4. **Evaluation Rubric:**
   - [ ] Partition-level ordering guarantees explained.
   - [ ] In-flight requests (`max.in.flight.requests.per.connection=1` or idempotence) for retry safety.
   - [ ] Stateful streaming window with watermarking and late event handling.

---

### 📝 Mock Drill 5 (End of Week 5)
1. **DSA Coding (45m):** [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) (Medium) or [Word Ladder](https://leetcode.com/problems/word-ladder/) (Hard).
2. **Data Modeling & System Design (30m):** Design the complete dimensional model and ingestion architecture for an E-commerce marketplace with real-time order tracking and daily financial reconciliations.
3. **Trap Question:** *"When should you choose a Star Schema over a wide denormalized table in modern columnar query engines like Snowflake or BigQuery?"*
4. **Evaluation Rubric:**
   - [ ] Star Schema vs One Big Table (OBT) trade-offs (storage, maintenance, flexibility vs join cost).
   - [ ] Designed Fact and Dimension tables with proper surrogate keys and SCD Type 2 handling.
   - [ ] Outlined LLM Tool Calling schema validation and fallback strategies.

---

### 📝 Mock Drill 6 (End of Week 6 - Comprehensive Capstone)
1. **DSA Coding (45m):** [Edit Distance](https://leetcode.com/problems/edit-distance/) (Hard) or [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) (Hard).
2. **Full System Design (45m):** Design a multi-tenant Data Platform capable of ingesting 1 Billion events/day from mobile apps, supporting real-time ML feature store lookups (<10ms) and ad-hoc analytical queries.
3. **Evaluation Rubric:**
   - [ ] Ingestion Layer (Kafka / Event Hub) with partitioning strategy.
   - [ ] Speed Layer (Flink / Spark Streaming) writing to Key-Value Feature Store (Redis / DynamoDB / Bigtable).
   - [ ] Batch / Lakehouse Layer (Delta Lake / Iceberg on S3/GCS) with Medallion architecture.
   - [ ] Query Serving Layer (Trino / BigQuery / Databricks SQL) with caching and access control.
   - [ ] End-to-end monitoring, SLA tracking, and cost optimization calculations.

---

## 🛠️ Workspace Quick Navigation & Resources
- **DSA Blind 75 Tracker:** [Blind75_Tracker.md](file:///d:/INTERVIEW%20PREPARATION/DSA_Blind%2075/Blind75_Tracker.md)
- **Data Engineering System Design:** [Data Engineering System Design Index](file:///d:/INTERVIEW%20PREPARATION/Data%20Engineering%20System%20Design/index.html)
- **DevRev Technical Preparation:** [DevRev Index](file:///d:/INTERVIEW%20PREPARATION/DevRev_Preparation/INDEX.html)
- **Agent Tool Calling Demo:** [Agent Tool Calling](file:///d:/INTERVIEW%20PREPARATION/DevRev_Preparation/agent_tool_calling_demo/)
- **Interactive Prep Tracker Dashboard:** [MASTER_ROADMAP_TRACKER.html](file:///d:/INTERVIEW%20PREPARATION/MASTER_ROADMAP_TRACKER.html)
