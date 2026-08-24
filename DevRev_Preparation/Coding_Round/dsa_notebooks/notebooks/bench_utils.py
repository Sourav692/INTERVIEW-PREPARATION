# -*- coding: utf-8 -*-
"""Shared benchmarking helper for the Blind-75 study notebooks.

One tested function, reused by every notebook, so each notebook only has to
declare its `solutions`, its `make_worst_case(n)` input generator, and the
`sizes` to test. Empirically confirms each approach's Big-O via the
doubling-ratio, and can optionally draw a log-log plot.

Standard library only, except the *optional* matplotlib import used only when
`plot=True` (guarded, so notebooks still run without matplotlib installed).
"""
from time import perf_counter

__all__ = ["time_call", "benchmark"]


def time_call(fn, args, repeats=1):
    """Return the best (fastest) run time of ``fn(*args)`` in milliseconds.

    We take the *minimum* over ``repeats`` runs because the fastest run is the
    least polluted by GC pauses / OS scheduling noise.
    """
    best = float("inf")
    for _ in range(repeats):
        start = perf_counter()
        fn(*args)
        best = min(best, perf_counter() - start)
    return best * 1000.0  # milliseconds


def benchmark(solutions, make_worst_case, sizes, repeats=1, plot=False):
    """Time every approach across growing input sizes and print a ratio table.

    Parameters
    ----------
    solutions : dict[str, callable]
        Maps a display label to a solution function. Each function is called as
        ``fn(*make_worst_case(n))``.
    make_worst_case : callable
        ``make_worst_case(n)`` returns a *tuple* of positional args producing a
        worst-case (no early-exit) input of size ``n``.
    sizes : list[int]
        Input sizes to test, ideally doubling (e.g. [1000, 2000, 4000, 8000]).
    repeats : int
        Timing repetitions per size (best time is kept).
    plot : bool
        If True, also draw a log-log plot (requires matplotlib; skipped with a
        message if it is not installed).

    Returns
    -------
    dict[str, list[float]]
        Label -> list of times (ms), aligned with ``sizes``.
    """
    results = {}
    for name, fn in solutions.items():
        print(f"\n{name}")
        print(f"  {'n':>7} | {'time (ms)':>10} | {'ratio vs prev':>13}")
        print(f"  {'-'*7} | {'-'*10} | {'-'*13}")
        times, prev = [], None
        for n in sizes:
            t = time_call(fn, make_worst_case(n), repeats)
            times.append(t)
            ratio = f"{t/prev:>12.2f}x" if prev else f"{'n/a':>13}"
            print(f"  {n:>7} | {t:>10.2f} | {ratio}")
            prev = t
        results[name] = times

    print("\nRatios per doubling: ~1x=>constant/log, ~2x=>linear or n log n, "
          "~4x=>quadratic, ~8x=>cubic.")

    if plot:
        _plot_loglog(results, sizes)
    return results


def _plot_loglog(results, sizes):
    """Draw a log-log runtime plot with O(n) and O(n^2) reference slopes."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[plot skipped] matplotlib not installed - run: pip install matplotlib")
        return

    EPS = 1e-4  # clamp so zero-ms points survive the log axis
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, times in results.items():
        ys = [max(t, EPS) for t in times]
        ax.plot(sizes, ys, marker="o", linewidth=2, label=name)

    # Reference slopes anchored at the first (size, time) point.
    n0 = sizes[0]
    first_times = [t[0] for t in results.values() if t and t[0] > 0]
    base = min(first_times) if first_times else 1.0
    for label, p in (("O(n)", 1), ("O(n^2)", 2)):
        ys = [base * (n / n0) ** p for n in sizes]
        ax.plot(sizes, ys, "--", color="gray", alpha=0.5, linewidth=1)
        ax.annotate(label, (sizes[-1], ys[-1]), color="gray", fontsize=8,
                    va="center", ha="left")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("input size n (log scale)")
    ax.set_ylabel("time in ms (log scale)")
    ax.set_title("Runtime vs input size (log-log)\nslope = complexity exponent")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    plt.show()
