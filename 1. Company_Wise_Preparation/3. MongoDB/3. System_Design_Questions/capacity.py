# -*- coding: utf-8 -*-
"""Shared back-of-the-envelope helpers for the MongoDB system-design notebooks.

System design questions do not have an algorithm to benchmark, so the notebooks
in this folder use their code cells for something more useful: a **runnable
capacity model**. Every number the source answer states is recomputed from its
stated assumptions and pinned by an assertion, so you can change an assumption
and watch the whole estimate move.

Standard library only.
"""
from typing import Dict, Iterable, List, Optional, Tuple

__all__ = [
    "SECOND", "MINUTE", "HOUR", "DAY", "YEAR",
    "KB", "MB", "GB", "TB", "PB",
    "human_bytes", "human_rate", "human_count",
    "per_second", "table", "assumption_table", "sensitivity",
]

# ---- time -----------------------------------------------------------------
SECOND = 1
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
YEAR = 365 * DAY

# ---- size (decimal, the convention used for storage capacity) --------------
KB = 1_000
MB = KB * 1_000
GB = MB * 1_000
TB = GB * 1_000
PB = TB * 1_000


def human_bytes(n: float) -> str:
    """1234567890 -> '1.23 GB'."""
    for unit, size in (("PB", PB), ("TB", TB), ("GB", GB), ("MB", MB), ("KB", KB)):
        if abs(n) >= size:
            return f"{n / size:,.2f} {unit}"
    return f"{n:,.0f} B"


def human_count(n: float) -> str:
    """5800 -> '5.80 K'.  25_000_000_000 -> '25.00 B'."""
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:,.2f} {unit}"
    return f"{n:,.0f}"


def human_rate(n: float, unit: str = "/s") -> str:
    return f"{human_count(n)}{unit}"


def per_second(total: float, window: float = DAY) -> float:
    """Convert a per-window total into a per-second rate."""
    return total / window


def table(rows: Iterable[Tuple[str, str]], title: Optional[str] = None,
          note: Optional[str] = None) -> None:
    """Print a two-column aligned table. Used for every estimate in these notebooks."""
    rows = list(rows)
    if not rows:
        return
    width = max(len(str(a)) for a, _ in rows)
    if title:
        print(title)
        print("-" * (width + 26))
    for label, value in rows:
        print(f"  {str(label):<{width}}  {value}")
    if note:
        print(f"\n  {note}")


def assumption_table(assumptions: Dict[str, object]) -> None:
    """Print the inputs an estimate rests on, so they can be challenged."""
    table([(k, str(v)) for k, v in assumptions.items()], title="ASSUMPTIONS")


def sensitivity(fn, base: float, label: str, multipliers=(0.5, 1, 2, 5, 10),
                fmt=human_bytes) -> None:
    """Show how one output moves when one input is scaled.

    The point of a capacity estimate is not the number - it is knowing which
    assumption the number is most sensitive to. This makes that visible.
    """
    rows = []
    for m in multipliers:
        marker = "  <- stated" if m == 1 else ""
        rows.append((f"{label} x {m:g}", f"{fmt(fn(base * m))}{marker}"))
    table(rows, title=f"SENSITIVITY TO {label.upper()}")
