#!/usr/bin/env python3
"""Utilities for working with documentation version slugs."""
from __future__ import annotations

import os
import pathlib
import re
from typing import Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "RELEASE_SLUG_PATTERN",
    "slug_from_tag",
    "is_release_slug",
    "parse_release_slug",
    "sort_release_slugs",
    "iter_release_slugs",
]

RELEASE_SLUG_PATTERN = re.compile(r"^\d+(?:\.\d+){1,}$")
TAG_VERSION_PATTERN = re.compile(r"(?P<version>\d+(?:\.\d+){1,})$")


def slug_from_tag(tag: str | None) -> Optional[str]:
    """Derive the release slug from a Git tag name."""
    if not tag:
        return None
    candidate = tag.strip()
    if not candidate:
        return None
    match = TAG_VERSION_PATTERN.search(candidate)
    if not match:
        return None
    version = match.group("version")
    if not is_release_slug(version):
        return None
    return version


def is_release_slug(slug: str | os.PathLike[str] | None) -> bool:
    """Return ``True`` if *slug* represents a released documentation version."""
    if slug is None:
        return False
    string_value = str(slug).strip()
    if not string_value:
        return False
    return bool(RELEASE_SLUG_PATTERN.match(string_value))


def parse_release_slug(slug: str | os.PathLike[str]) -> Optional[Tuple[int, ...]]:
    """Parse *slug* into a tuple of integers for ordering comparisons."""
    if not is_release_slug(slug):
        return None
    parts = str(slug).strip().split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def sort_release_slugs(slugs: Iterable[str]) -> List[str]:
    """Return release slugs ordered from oldest to newest."""
    sortable: List[Tuple[Tuple[int, ...], str]] = []
    seen: set[str] = set()
    for slug in slugs:
        if slug in seen:
            continue
        parsed = parse_release_slug(slug)
        if not parsed:
            continue
        sortable.append((parsed, slug))
        seen.add(slug)
    sortable.sort()
    return [slug for _, slug in sortable]


def iter_release_slugs(paths: Iterable[pathlib.Path]) -> Sequence[str]:
    """Extract release slugs from *paths* in definition order."""
    slugs: List[str] = []
    seen: set[str] = set()
    for path in paths:
        name = path.name
        if name in {"latest", "master"}:
            continue
        if not is_release_slug(name):
            continue
        if name in seen:
            continue
        slugs.append(name)
        seen.add(name)
    return slugs
