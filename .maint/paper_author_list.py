#!/usr/bin/env python3
"""Generate an author list for a new paper or abstract."""
import sys
from pathlib import Path
import json
from update_zenodo import get_git_lines, sort_contributors


# These authors should go last
AUTHORS_LAST = ["Rokem, Ariel", "Esteban, Oscar"]


def _aslist(inlist):
    if not isinstance(inlist, list):
        return [inlist]
    return inlist


if __name__ == "__main__":
    devs = json.loads(Path(".maint/developers.json").read_text())
    contribs = json.loads(Path(".maint/contributors.json").read_text())

    hits, misses = sort_contributors(
        devs + contribs,
        get_git_lines(),
        exclude=json.loads(Path(".maint/former.json").read_text()),
        last=AUTHORS_LAST,
    )
    # Remove position
    affiliations = []
    for item in hits:
        del item["position"]
        for a in _aslist(item.get("affiliation", "Unaffiliated")):
            if a not in affiliations:
                affiliations.append(a)

    aff_indexes = [
        ", ".join(
            [
                f"{affiliations.index(a) + 1}"
                for a in _aslist(author.get("affiliation", "Unaffiliated"))
            ]
        )
        for author in hits
    ]

    if misses:
        print(
            "Some people made commits, but are missing in .maint/ "
            f"files: {', '.join(misses)}",
            file=sys.stderr,
        )

    print(f"Authors ({len(hits)}):")
    authors = "; ".join(
        f"{i['name']} \\ :sup:`{idx}`\\ " for i, idx in zip(hits, aff_indexes)
    )
    print(f"{authors}.")

    lines = '\n'.join(f'{i + 1: >2}. {a}' for i, a in enumerate(affiliations))
    print(f'\n\nAffiliations:\n{lines}')
