"""py.test configuration."""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nb
import pytest


@pytest.fixture(autouse=True)
def doctest_autoimport(doctest_namespace):
    """Make available some fundamental modules to doctest modules."""
    doctest_namespace['np'] = np
    doctest_namespace['nb'] = nb
    doctest_namespace['os'] = os
    doctest_namespace['Path'] = Path
    doctest_namespace['data_dir'] = Path(__file__).parent / 'data' / 'tests'
    tmpdir = tempfile.TemporaryDirectory()
    doctest_namespace['tmpdir'] = tmpdir.name
    yield
    tmpdir.cleanup()
