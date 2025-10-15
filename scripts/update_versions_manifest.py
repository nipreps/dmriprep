#!/usr/bin/env python3
"""Generate the versions manifest consumed by the docs version switcher."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
from typing import Iterable, List, Sequence

DEFAULT_HEAD_CANDIDATES: Sequence[str] = ("master", "main", "latest", "stable")


def read_git_tags() -> List[str]:
    """Return Git tags ordered from newest to oldest."""
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.split()


def discover_tags(site: pathlib.Path, candidates: Iterable[str]) -> List[str]:
    """Filter tags that have a rendered documentation directory."""
    return [candidate for candidate in candidates if (site / candidate).is_dir()]


def discover_heads(
    site: pathlib.Path,
    ref_name: str | None,
    ref_type: str | None,
    *,
    preferred: Sequence[str] = DEFAULT_HEAD_CANDIDATES,
) -> List[str]:
    """Return an ordered list of head names to expose in the switcher."""
    heads: List[str] = []
    for candidate in preferred:
        candidate_path = site / candidate
        if candidate_path.is_dir() and candidate not in heads:
            heads.append(candidate)

    if ref_type == "branch" and ref_name:
        branch_path = site / ref_name
        if branch_path.is_dir() and ref_name not in heads:
            heads.insert(0, ref_name)

    return heads


def derive_base_url(repository: str | None) -> str:
    """Return the public GitHub Pages base URL for the given repository."""
    if repository:
        try:
            owner, repo_name = repository.split("/", 1)
        except ValueError:
            owner, repo_name = "nipreps", "dmriprep"
    else:
        owner, repo_name = "nipreps", "dmriprep"

    return f"https://{owner}.github.io/{repo_name}/"


def format_entry(identifier: str, base_url: str) -> dict[str, str]:
    return {
        "version": identifier,
        "name": identifier,
        "url": f"{base_url}{identifier}/",
    }


def build_manifest(
    *,
    site: pathlib.Path,
    ref_name: str | None,
    ref_type: str | None,
    repository: str | None,
) -> dict:
    site.mkdir(parents=True, exist_ok=True)

    tags = discover_tags(site, read_git_tags())
    heads = discover_heads(site, ref_name, ref_type)
    base_url = derive_base_url(repository)

    head_entries = [format_entry(head, base_url) for head in heads]
    tag_entries = [format_entry(tag, base_url) for tag in tags]
    head_versions = {entry["version"] for entry in head_entries}

    return {
        "heads": head_entries,
        "tags": tag_entries,
        "versions": head_entries
        + [entry for entry in tag_entries if entry["version"] not in head_versions],
        "downloads": [],
        "subprojects": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        default="site",
        type=pathlib.Path,
        help="Path to the gh-pages worktree.",
    )
    parser.add_argument(
        "--manifest-name",
        default="versions.json",
        help="Name of the manifest file to create in the site directory.",
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="Repository slug (OWNER/REPO) used to derive the base URL.",
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


def main() -> None:
    args = parse_args()
    manifest = build_manifest(
        site=args.site,
        ref_name=args.ref_name,
        ref_type=args.ref_type,
        repository=args.repository,
    )
    manifest_path = args.site / args.manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
