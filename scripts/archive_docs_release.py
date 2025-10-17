#!/usr/bin/env python3
"""Archive a tagged documentation build into the gh-pages site."""
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import sys
from typing import List

from versions import iter_release_slugs, slug_from_tag, sort_release_slugs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        default="site",
        type=pathlib.Path,
        help="Path to the gh-pages worktree.",
    )
    parser.add_argument(
        "--build",
        default=pathlib.Path("docs/_build/html"),
        type=pathlib.Path,
        help="Path to the built documentation to archive.",
    )
    parser.add_argument(
        "--ref-name",
        default=os.environ.get("REF_NAME"),
        help="Current Git reference name.",
    )
    parser.add_argument(
        "--ref-type",
        default=os.environ.get("REF_TYPE"),
        help="Current Git reference type (branch or tag).",
    )
    return parser.parse_args()


def ensure_directory(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_build(build: pathlib.Path, destination: pathlib.Path) -> None:
    if not build.is_dir():
        raise SystemExit(f"Build directory '{build}' does not exist")
    if destination.exists():
        raise SystemExit(f"Destination '{destination}' already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build, destination)


def collect_release_slugs(site: pathlib.Path) -> List[str]:
    if not site.exists():
        return []
    return list(iter_release_slugs(site.iterdir()))


def ensure_latest_alias(site: pathlib.Path, latest_slug: str | None) -> None:
    latest_path = site / "latest"
    if latest_slug is None:
        if latest_path.is_symlink() or latest_path.exists():
            if latest_path.is_dir() and not latest_path.is_symlink():
                shutil.rmtree(latest_path)
            else:
                latest_path.unlink()
        return

    target = site / latest_slug
    if not target.exists():
        raise SystemExit(f"Cannot create latest alias to missing target '{latest_slug}'")

    relative_target = os.path.relpath(target, start=site)

    if latest_path.is_symlink() or latest_path.exists():
        if latest_path.is_dir() and not latest_path.is_symlink():
            shutil.rmtree(latest_path)
        else:
            latest_path.unlink()
    latest_path.symlink_to(relative_target, target_is_directory=True)


def main() -> None:
    args = parse_args()

    if args.ref_type != "tag":
        print("archive_docs_release: current ref is not a tag; nothing to do")
        return

    slug = slug_from_tag(args.ref_name)
    if not slug:
        print(
            f"archive_docs_release: '{args.ref_name}' is not a release tag; skipping",
            file=sys.stderr,
        )
        return

    ensure_directory(args.site)

    destination = args.site / slug
    copy_build(args.build, destination)

    known_slugs = collect_release_slugs(args.site)
    if slug not in known_slugs:
        known_slugs.append(slug)

    ordered_slugs = sort_release_slugs(known_slugs)
    if not ordered_slugs:
        ensure_latest_alias(args.site, None)
        return

    latest_slug = ordered_slugs[-1]
    ensure_latest_alias(args.site, latest_slug)


if __name__ == "__main__":
    main()
