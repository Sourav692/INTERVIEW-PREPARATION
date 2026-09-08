"""
Shared benchmarking helper for LeetCode study notebooks.

Provides:
    time_call(fn, args, repeats=1) -> float   # median time in seconds
    benchmark(solutions, make_worst_case, sizes, repeats=1, plot=False)

`benchmark` times each labeled solution against inputs of increasing size
(produced by `make_worst_case(n)`), prints an ASCII table of
n | time (ms) | ratio vs previous size, and optionally draws a log-log
runtime chart (matplotlib import is guarded so the notebook never hard
depends on a third-party library).
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Sequence, Tuple


def time_call(fn: Callable, args: Tuple, repeats: int = 1) -> float:
    """Return the median wall-clock time (seconds) of calling fn(*args)."""
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn(*args)
        samples.append(time.perf_counter() - start)
    samples.sort()
    return samples[len(samples) // 2]


def benchmark(
    solutions: Dict[str, Callable],
    make_worst_case: Callable[[int], Tuple],
    sizes: Sequence[int],
    repeats: int = 1,
    plot: bool = False,
) -> Dict[str, List[float]]:
    """
    Time each solution across growing input sizes and print a ratio table.

    solutions: {label: callable} — each callable is invoked as fn(*args)
               where args = make_worst_case(n).
    make_worst_case: n -> tuple of args producing a worst-case input of size n.
    sizes: increasing (ideally doubling) input sizes, e.g. [1000, 2000, 4000, 8000].
    repeats: number of timing samples per (solution, size) — median is used.
    plot: if True, draw a log-log runtime chart (skipped gracefully if
          matplotlib is unavailable).

    Returns {label: [time_ms, ...]} aligned with `sizes`, for optional reuse.
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
            t_ms = t * 1000.0
            results[label].append(t_ms)
            ratio_str = "-" if prev_time is None or prev_time == 0 else f"{t_ms / prev_time:.2f}x"
            print(f"{n:>10} | {t_ms:>12.4f} | {ratio_str:>14}")
            prev_time = t_ms

    if plot:
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(6, 4))
            for label, times in results.items():
                plt.plot(sizes, times, marker="o", label=label)

            # Reference slopes for O(n) and O(n^2), anchored to the first solution's
            # first data point so they're visually comparable on the log-log plot.
            first_label = next(iter(results))
            base_n = sizes[0]
            base_t = results[first_label][0] if results[first_label][0] > 0 else 1e-6
            ref_n = [base_n, sizes[-1]]
            ref_linear = [base_t, base_t * (sizes[-1] / base_n)]
            ref_quad = [base_t, base_t * (sizes[-1] / base_n) ** 2]
            plt.plot(ref_n, ref_linear, "--", color="gray", alpha=0.5, label="O(n) ref")
            plt.plot(ref_n, ref_quad, ":", color="gray", alpha=0.5, label="O(n^2) ref")

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
