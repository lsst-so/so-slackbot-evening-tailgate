"""Optional memory diagnostics, enabled with TAILGATE_MEMDEBUG_MINUTES.

When enabled, logs every N minutes:
  - process RSS (from /proc/self/status, Linux only),
  - live thread count and names,
  - number of objects tracked by the garbage collector,
  - the top lines whose traced allocations grew since the previous report
    (tracemalloc).

Meant for chasing the slow memory growth seen in production (RSO-1006).
It has a small overhead (tracemalloc), so leave it off in normal operation.
"""
import gc
import logging
import threading
import tracemalloc

logger = logging.getLogger("tailgate_bot.memdebug")


def _rss_mib() -> float:
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return float("nan")


class MemoryReporter:
    def __init__(self, top: int = 10, frames: int = 15):
        self._top = top
        tracemalloc.start(frames)
        self._previous = tracemalloc.take_snapshot()

    def report(self) -> None:
        gc.collect()
        snapshot = tracemalloc.take_snapshot()
        traced, peak = tracemalloc.get_traced_memory()
        threads = threading.enumerate()
        logger.info(
            "MEMDEBUG rss=%.2fMiB traced=%.1fKiB peak=%.1fKiB gc_objects=%d threads=%d [%s]",
            _rss_mib(), traced / 1024, peak / 1024, len(gc.get_objects()),
            len(threads), ", ".join(sorted(t.name for t in threads)),
        )
        for stat in snapshot.compare_to(self._previous, "lineno")[: self._top]:
            if stat.size_diff:
                logger.info("MEMDEBUG   %s", stat)
        self._previous = snapshot


def add_memdebug_job(scheduler, minutes: int) -> None:
    reporter = MemoryReporter()
    scheduler.add_job(reporter.report, "interval", minutes=minutes, id="memdebug", name="memdebug")
    logger.info("Memory diagnostics enabled: reporting every %d min", minutes)
