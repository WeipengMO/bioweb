"""Generic result file manager for all analysis modules.

Usage in any analysis module::

    from bioweb_analysis.results import ResultsManager

    results = ResultsManager("tcga")   # sub-directory under data/results/
    plot_path = results.next_png("survival_{project}")   # allocate a new file path
    # ... save figure to plot_path ...
    results.clear_module()   # remove old plots before writing new ones

At backend startup::

    from bioweb_analysis.results import cleanup_old_results
    cleanup_old_results(max_age_seconds=86400)   # purge files older than 24 h
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar

RESULTS_ROOT = Path("data/results")


class ResultsManager:
    """Manages plot output files for a single analysis module.

    Parameters
    ----------
    module:
        Sub-directory name under ``data/results/`` (e.g. ``"tcga"``, ``"ora"``).
    max_age_seconds:
        When calling :meth:`cleanup_old`, files older than this many seconds are
        removed.  ``None`` means *no age limit* (remove everything).
    """

    _registry: ClassVar[dict[str, ResultsManager]] = {}

    def __init__(self, module: str, *, max_age_seconds: int | None = None) -> None:
        self.module = module
        self.dir = RESULTS_ROOT / module
        self.dir.mkdir(parents=True, exist_ok=True)
        self.max_age_seconds = max_age_seconds
        ResultsManager._registry[module] = self

    # ------------------------------------------------------------------
    # Path allocation
    # ------------------------------------------------------------------

    def next_png(self, stem: str) -> Path:
        """Return a fresh ``*.png`` path inside the module directory.

        >>> mgr = ResultsManager("tcga")
        >>> mgr.next_png("survival_TCGA-LUAD_TP53")
        PosixPath('data/results/tcga/survival_TCGA-LUAD_TP53_a1b2c3d4e5.png')
        """
        from uuid import uuid4

        return self.dir / f"{stem}_{uuid4().hex[:10]}.png"

    # ------------------------------------------------------------------
    # Cleanup helpers
    # ------------------------------------------------------------------

    def clear_module(self) -> int:
        """Remove **all** ``*.png`` files in this module's directory.

        Returns the number of files removed.
        """
        return _clear_dir(self.dir)

    def clear_all(self) -> int:
        """Remove **all** ``*.png`` files under the entire results root.

        Returns the number of files removed.
        """
        return _clear_dir(RESULTS_ROOT)

    def cleanup_old(self, *, max_age_seconds: int | None = None) -> int:
        """Remove ``*.png`` files older than *max_age_seconds*.

        Falls back to the instance default when called without arguments.
        Returns the number of files removed.
        """
        age = max_age_seconds if max_age_seconds is not None else self.max_age_seconds
        return _cleanup_old(self.dir, max_age_seconds=age)

    # ------------------------------------------------------------------
    # Plot url helper
    # ------------------------------------------------------------------

    def plot_url(self, plot_path: Path) -> str:
        """Convert an absolute path to a relative URL under ``/results/``."""
        return "/results/" + str(plot_path.relative_to(RESULTS_ROOT)).replace("\\", "/")


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------


def get_module(module: str, *, max_age_seconds: int | None = None) -> ResultsManager:
    """Get or create the :class:`ResultsManager` for *module*."""
    if module in ResultsManager._registry:
        return ResultsManager._registry[module]
    return ResultsManager(module, max_age_seconds=max_age_seconds)


def cleanup_old_results(*, max_age_seconds: int = 24 * 60 * 60) -> int:
    """Remove stale ``*.png`` files under the entire results root.

    Called at backend startup to purge files older than 24 hours by default.
    Returns the number of files removed.
    """
    return _cleanup_old(RESULTS_ROOT, max_age_seconds=max_age_seconds)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _clear_dir(directory: Path) -> int:
    removed = 0
    if directory.exists():
        for path in directory.rglob("*.png"):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def _cleanup_old(directory: Path, *, max_age_seconds: int | None = None) -> int:
    if not directory.exists():
        return 0
    if max_age_seconds is None:
        return _clear_dir(directory)
    now = time.time()
    removed = 0
    for path in directory.rglob("*.png"):
        if now - path.stat().st_mtime < max_age_seconds:
            continue
        path.unlink(missing_ok=True)
        removed += 1
    return removed
