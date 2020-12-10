# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous utilities."""


def check_deps(workflow):
    """Make sure dependencies are present in this system."""
    from nipype.utils.filemanip import which

    return sorted(
        (node.interface.__class__.__name__, node.interface._cmd)
        for node in workflow._get_all_nodes()
        if (
            hasattr(node.interface, "_cmd")
            and which(node.interface._cmd.split()[0]) is None
        )
    )


def sub_prefix(subid):
    """
    Make sure the subject ID has the sub- prefix.

    Examples
    --------
    >>> sub_prefix("sub-01")
    'sub-01'

    >>> sub_prefix("01")
    'sub-01'

    """
    return f"sub-{subid.replace('sub-', '')}"
