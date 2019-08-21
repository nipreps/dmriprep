"""
Base module variables
"""
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__packagename__ = 'dmriprep'
__credits__ = ('Contributors: please check the ``.zenodo.json`` file at the'
               'top-level folder of the repository')
__url__ = 'https://github.com/nipy/dmriprep'

DOWNLOAD_URL = (
    'https://github.com/nipy/dmriprep/{name}/archive/{ver}.tar.gz'.format(
        name=__packagename__, ver=__version__
    )
)
