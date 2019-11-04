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


@pytest.fixture(scope="session")
def dipy_test_data(tmpdir_factory):
    """Create a temporal directory shared across tests to pull data in."""
    from dipy.data.fetcher import _make_fetcher, UW_RW_URL

    datadir = Path(tmpdir_factory.mktemp("data"))
    _make_fetcher(
        "fetch_sherbrooke_3shell",
        str(datadir),
        UW_RW_URL + "1773/38475/",
        ['HARDI193.nii.gz', 'HARDI193.bval', 'HARDI193.bvec'],
        ['HARDI193.nii.gz', 'HARDI193.bval', 'HARDI193.bvec'],
        ['0b735e8f16695a37bfbd66aab136eb66',
         'e9b9bb56252503ea49d31fb30a0ac637',
         '0c83f7e8b917cd677ad58a078658ebb7'],
        doc="Download a 3shell HARDI dataset with 192 gradient direction")()

    return {
        'dwi_file': str(datadir / "HARDI193.nii.gz"),
        'bvecs': str(datadir / "HARDI193.bvec"),
        'bvals': str(datadir / "HARDI193.bval"),
    }
