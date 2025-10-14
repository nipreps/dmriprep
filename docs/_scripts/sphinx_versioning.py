"""Compatibility wrapper around :mod:`sphinxcontrib-versioning`."""
from __future__ import annotations

import sys
from typing import Iterable, Sequence

import click


def _ensure_click_os_args(argv: Sequence[str] | None = None) -> None:
    """Provide ``click.get_os_args`` for older Click releases.

    ``sphinxcontrib-versioning`` requires :func:`click.get_os_args`, which was
    introduced in Click 8.1. Older releases do not expose this attribute,
    causing the CLI to fail during imports. When the attribute is missing we
    register a small fallback that mirrors the behaviour introduced in Click
    8.1: return the process arguments without the interpreter path.
    """

    if hasattr(click, "get_os_args"):
        return

    def _get_os_args() -> Iterable[str]:
        if argv is not None:
            return list(argv)
        return list(sys.argv[1:])

    click.get_os_args = _get_os_args  # type: ignore[attr-defined]


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke ``sphinx-versioning`` with Click compatibility shims."""

    _ensure_click_os_args(argv)

    from sphinxcontrib.versioning.__main__ import cli

    kwargs = {"prog_name": "sphinx-versioning", "standalone_mode": False}
    if argv is not None:
        kwargs["args"] = list(argv)

    try:
        return int(cli.main(**kwargs) or 0)
    except SystemExit as exc:  # pragma: no cover - Click uses ``SystemExit``.
        return int(exc.code)


if __name__ == "__main__":
    sys.exit(main())
