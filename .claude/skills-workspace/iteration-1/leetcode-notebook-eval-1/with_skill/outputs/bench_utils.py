"""
Shared benchmarking helper for LeetCode study notebooks.

Provides:
    time_call(fn, args, repeats=1) -> float
        Times a single callable invocation (best-of-`repeats`, in milliseconds).

    benchmark(solutions, make_worst_case, sizes, repeats=1, plot=False)
        Runs every solution against worst-case inputs of growing size,
        prints an ASCII table of n | time (ms) | ratio vs prev per approach,
        and (optionally) draws a log-log runtime chart with O(n)/O(n^2)
        reference slopes. The matplotlib import is guarded so the notebook
        never hard-depends on a third-party library.

This file is the single source of truth for notebook benchmark cells —
notebooks should import it rather than re-implementing the timing loop.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Sequence, Tuple


def time_call(fn: Callable, args: Tuple, repeats: int = 1) -> float:
    """Return the best (minimum) wall-clock time in milliseconds across `repeats` runs."""
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn(*args)
        elapsed = time.perf_counter() - start
        if elapsed < best:
            best = elapsed
    return best * 1000.0  # ms


def benchmark(
    solutions: Dict[str, Callable],
    make_worst_case: Callable[[int], Tuple],
    sizes: Sequence[int],
    repeats: int = 1,
    plot: bool = False,
) -> Dict[str, List[float]]:
    """
    Time each solution in `solutions` (label -> callable) against inputs produced
    by `make_worst_case(n)` for every n in `sizes` (expected to double each step).

    Prints a table per approach:
        n | time (ms) | ratio vs prev

    A ratio near 1x suggests O(1)/O(log n); near 2x suggests O(n)/O(n log n);
    near 4x suggests O(n^2); near 8x suggests O(n^3), when n doubles each row.

    Returns a dict of label -> list of times (ms), one per size, for further
    inspection or custom plotting.
    """
    results: Dict[str, List[float]] = {label: [] for label in solutions}

    for label, fn in solutions.items():
        print(f"\n=== {label} ===")
        print(f"{'n':>10} | {'time (ms)':>12} | {'ratio vs prev':>14}")
        print("-" * 42)
        prev_time = None
        for n in sizes:
            args = make_worst_case(n)
            t = time_call(fn, args, repeats=repeats)
            results[label].append(t)
            ratio_str = "-" if prev_time is None or prev_time == 0 else f"{t / prev_time:.2f}x"
            print(f"{n:>10} | {t:>12.4f} | {ratio_str:>14}")
            prev_time = t

    if plot:
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(6, 4))
            for label, times in results.items():
                plt.plot(sizes, times, marker="o", label=label)

            # Reference slopes anchored to the first data point of the first solution
            first_label = next(iter(results))
            base_time = results[first_label][0] if results[first_label][0] > 0 else 1e-6
            base_n = sizes[0]
            ref_n = list(sizes)
            ref_linear = [base_time * (n / base_n) for n in ref_n]
            ref_quad = [base_time * (n / base_n) ** 2 for n in ref_n]
            plt.plot(ref_n, ref_linear, "--", color="gray", alpha=0.5, label="O(n) reference")
            plt.plot(ref_n, ref_quad, ":", color="gray", alpha=0.5, label="O(n^2) reference")

            plt.xscale("log")
            plt.yscale("log")
            plt.xlabel("n")
            plt.ylabel("time (ms)")
            plt.title("Empirical runtime (log-log)")
            plt.legend(fontsize=8)
            plt.tight_layout()
            plt.show()
        except ImportError:
            print("\n[plot skipped: matplotlib not installed]")

    return results
