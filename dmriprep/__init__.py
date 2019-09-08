"""Top-level package for dmriprep."""
import warnings as _warnings
from .__about__ import (
    __version__,
    __copyright__,
    __credits__,
    __packagename__,
)


__all__ = [
    '__version__',
    '__copyright__',
    '__credits__',
    '__packagename__',
]

# cmp is not used by dmriprep, so ignore nipype-generated warnings
_warnings.filterwarnings('ignore', r'cmp not installed')
_warnings.filterwarnings('ignore', r'This has not been fully tested. Please report any failures.')
_warnings.filterwarnings('ignore', r"can't resolve package from __spec__ or __package__")
_warnings.simplefilter('ignore', DeprecationWarning)
_warnings.simplefilter('ignore', ResourceWarning)
