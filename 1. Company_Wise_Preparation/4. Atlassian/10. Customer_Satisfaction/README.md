# Customer Satisfaction

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Hash Tables, Sorting · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

**Customer Support Rating System**

Imagine we have a customer support ticketing system. Customers can rate a support agent out of 5.

### Requirements

- Write a function that accepts a rating.
- Write another function that shows all agents and their average rating, ordered highest → lowest.

### Tie Handling

Your current solution does not account for cases where two agents have the same average rating.

- What options exist for handling ties?
- How can we implement them in code?

### Monthly Best Agents

We now want to determine the best agents each month. Update the implementation so this information can be retrieved.

### Export Feature

Write a new function that exports each agent's average ratings per month.

- Export can be in any format (e.g., CSV, JSON, XML).
- It should return:
  - Average ratings (unsorted)
  - Total rating for each agent (not the average)

---

## Study Tools

### Hint 1

The core challenge is maintaining a running total and count for each agent so you can compute the average on demand. Think about what data structure lets you look up an agent's current stats in O(1) time.

### Hint 2

When you need to display agents sorted by average rating, you can't just sort the dictionary keys — you need to sort based on a computed value. For ties, consider what secondary criteria would make the ordering deterministic, like the agent's name or ID.

### Hint 3

For the monthly breakdown, you need a nested structure: one level for the month, another for the agent. When exporting, flatten that structure and include both the average and the total count of ratings, since the total rating alone is ambiguous without knowing how many ratings contributed to it.

---

### Answer

This is a data aggregation problem where the key is choosing the right nested dictionary structure to support O(1) inserts and O(n log n) sorted retrieval. Ratings are stored in a structure keyed by month, then by agent, keeping a running sum and count so averages are always derivable.

The core idea is to store raw aggregates (sum and count) rather than precomputed averages. This lets you update in constant time and compute averages only when needed for display or export. For ties, the cleanest approach is to sort by a tuple of `(-average, agent_id)` so the ordering is deterministic and testable.

```python
from collections import defaultdict
from typing import Dict, Tuple, List

class CustomerSupportRatingSystem:
    def __init__(self):
        # Structure: {month: {agent_id: [total_rating, count]}}
        self._ratings: Dict[str, Dict[str, List[int]]] = defaultdict(
            lambda: defaultdict(lambda: [0, 0])
        )

    def accept_rating(self, agent_id: str, rating: int, month: str) -> None:
        """Record a rating for an agent in a specific month."""
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        agent_stats = self._ratings[month][agent_id]
        agent_stats[0] += rating
        agent_stats[1] += 1

    def get_all_agents_sorted(self, month: str = None) -> List[Tuple[str, float]]:
        """Return agents and their average ratings, sorted highest to lowest.

        Args:
            month: If provided, only consider ratings from that month.
                   If None, aggregate across all months.
        """
        if month:
            months_to_consider = [month]
        else:
            months_to_consider = list(self._ratings.keys())

        # Aggregate stats across the relevant months
        agent_totals: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
        for m in months_to_consider:
            for agent_id, stats in self._ratings[m].items():
                agent_totals[agent_id][0] += stats[0]
                agent_totals[agent_id][1] += stats[1]

        # Compute averages and sort
        results = []
        for agent_id, (total, count) in agent_totals.items():
            avg = total / count if count > 0 else 0.0
            results.append((agent_id, avg))

        # Sort by average descending, then by agent_id ascending for ties
        results.sort(key=lambda x: (-x[1], x[0]))
        return results

    def get_best_agents_by_month(self) -> Dict[str, List[Tuple[str, float]]]:
        """Return the best agents for each month, sorted by average rating."""
        best_by_month = {}
        for month in self._ratings:
            best_by_month[month] = self.get_all_agents_sorted(month=month)
        return best_by_month

    def export_ratings(self, format: str = "csv") -> str:
        """Export each agent's average ratings per month, unsorted.

        Returns:
            A string containing the export data in the specified format.
            Each row includes: month, agent_id, average_rating, total_rating_count
        """
        rows = []
        for month in self._ratings:
            for agent_id, (total, count) in self._ratings[month].items():
                avg = total / count if count > 0 else 0.0
                rows.append((month, agent_id, avg, count))

        if format.lower() == "json":
            import json
            export_data = [
                {
                    "month": month,
                    "agent_id": agent_id,
                    "average_rating": round(avg, 2),
                    "total_rating_count": count
                }
                for month, agent_id, avg, count in rows
            ]
            return json.dumps(export_data, indent=2)
        else:  # Default to CSV
            lines = ["month,agent_id,average_rating,total_rating_count"]
            for month, agent_id, avg, count in rows:
                lines.append(f"{month},{agent_id},{avg:.2f},{count}")
            return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    system = CustomerSupportRatingSystem()

    # Record some ratings
    system.accept_rating("agent_a", 5, "2024-01")
    system.accept_rating("agent_a", 4, "2024-01")
    system.accept_rating("agent_b", 4, "2024-01")
    system.accept_rating("agent_b", 4, "2024-02")
    system.accept_rating("agent_c", 3, "2024-02")

    print("All agents sorted:")
    print(system.get_all_agents_sorted())

    print("\nBest agents by month:")
    print(system.get_best_agents_by_month())

    print("\nExport (CSV):")
    print(system.export_ratings("csv"))
```

**Time:** O(1) for `accept_rating` (dictionary lookups), O(n log n) for `get_all_agents_sorted` where n is the number of agents (sorting dominates), O(m·n log n) for `get_best_agents_by_month` where m is the number of months, O(m·n) for `export_ratings` — where n is the number of agents and m is the number of months.

**Space:** O(m·n) where m is the number of months and n is the number of agents — we store running sum and count for each agent-month combination.

The correctness argument is straightforward: by storing `[total, count]` for each agent-month pair, the average is always `total / count`, which is mathematically the correct arithmetic mean. The sorting with `(-average, agent_id)` ensures a total order: agents are ranked by descending average, and any agents with identical averages are ordered by their ID, making the output deterministic and reproducible.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that could work: a flat list of `(agent_id, rating)` tuples. Each `accept_rating` just appends to the list in O(1). To get sorted averages, you'd iterate through the list, build a dictionary of `{agent_id: [sum, count]}`, compute averages, then sort. That works fine for small datasets, but every query is O(n) just to rebuild the aggregates, and if you're accepting thousands of ratings, you're doing that work repeatedly.

The obvious optimization is to maintain the aggregates incrementally. Instead of storing raw ratings, store a dictionary mapping `agent_id` to a running `[total, count]`. Now `accept_rating` is still O(1) but `get_all_agents_sorted` only needs to compute averages and sort — no rebuilding. The dictionary lookup is the key insight: you're trading a tiny bit of memory for eliminating repeated aggregation work.

When monthly requirements come in, you realize the flat dictionary isn't enough. You need to know not just what an agent's overall average is, but what it was in January versus February. The natural extension is a nested dictionary: `{month: {agent_id: [total, count]}}`. This preserves the O(1) insert and gives you the ability to query by month or aggregate across all months.

The tie-handling question forces you to think about what "sorted" really means. If two agents both have a 4.5 average, what order should they appear in? The interviewer is checking whether you recognize that Python's sort is stable but that stability alone doesn't give you a meaningful order. Sorting by a tuple `(-average, agent_id)` makes the ordering explicit and deterministic — you're saying "highest average first, and if tied, alphabetical by ID." That's testable and defensible.

For the export feature, the key realization is that you need both the average and the count. If you only export the total rating (say, 45), the consumer can't tell if that's 9 ratings of 5 or 45 ratings of 1. Including the count makes the data self-describing and lets downstream systems recompute averages if needed.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Store aggregates, not raw data** — keeping `[sum, count]` instead of individual ratings means your insert is O(1) and your queries never need to rescan history. This is the difference between a solution that scales and one that works for the demo.
- **Make tie-breaking explicit** — sorting with `key=lambda x: (-x[1], x[0])` shows you've thought about determinism. If you just sort by average, the order of tied agents depends on insertion order, which makes your output hard to test and unpredictable for users.
- **Design the data structure for the query patterns** — the nested `{month: {agent: [sum, count]}}` structure directly mirrors the requirements. When the interviewer asks for monthly best agents, you can answer in O(m·n log n) instead of redesigning from scratch.
- **Include the count in exports** — exporting just the average loses information. A 5.0 average from one rating is very different from a 5.0 average from a hundred ratings. Including the count shows you understand data quality and downstream consumption.
- **Validate inputs at the boundary** — checking that ratings are between 1 and 5 catches bad data early. In a real system, you'd also want to validate that `agent_id` is non-empty and that `month` follows a consistent format.
- **Consider rounding and precision** — when exporting, you round averages to 2 decimal places for readability, but internally you keep full precision. This matters when someone imports your CSV and tries to reconcile numbers.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if you need to handle millions of ratings per day and the export is run hourly?** — Think about batching writes, precomputing daily aggregates, and whether the current in-memory structure still works or needs a database.
- **How would you modify this to support weighted ratings, where more recent ratings count more?** — Consider storing a timestamp and applying exponential decay or a sliding window.
- **What if agents can be deactivated and you need to exclude them from the sorted list?** — Add an active flag to the agent data and filter during query, or maintain a separate active-agents set.
- **How would you handle the case where an agent has no ratings in a given month?** — Decide whether to show them with a 0.0 average, exclude them, or show "N/A", and make that consistent across all query methods.
- **If the export needs to be in a specific format for a downstream system (like a data warehouse), how would you structure the code to make adding new formats easy?** — Think about a strategy pattern or a simple `if format == ...` dispatch with a clear extension point.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
