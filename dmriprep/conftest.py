"""py.test configuration."""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nb
import pytest
from bids.layout import BIDSLayout
from dipy.data.fetcher import _make_fetcher, UW_RW_URL

_dipy_datadir_root = os.getenv('DMRIPREP_TESTS_DATA') or Path.home()
dipy_datadir = Path(_dipy_datadir_root) / '.cache' / 'data'
dipy_datadir.mkdir(parents=True, exist_ok=True)

_make_fetcher(
    "fetch_sherbrooke_3shell",
    str(dipy_datadir),
    UW_RW_URL + "1773/38475/",
    ['HARDI193.nii.gz', 'HARDI193.bval', 'HARDI193.bvec'],
    ['HARDI193.nii.gz', 'HARDI193.bval', 'HARDI193.bvec'],
    ['0b735e8f16695a37bfbd66aab136eb66',
     'e9b9bb56252503ea49d31fb30a0ac637',
     '0c83f7e8b917cd677ad58a078658ebb7'],
    doc="Download a 3shell HARDI dataset with 192 gradient direction")()

_sherbrooke_data = {
    'dwi_file': dipy_datadir / "HARDI193.nii.gz",
    'bvecs': np.loadtxt(dipy_datadir / "HARDI193.bvec").T,
    'bvals': np.loadtxt(dipy_datadir / "HARDI193.bval"),
}

test_data_env = os.getenv('TEST_DATA_HOME', '/tmp/data')
test_output_dir = os.getenv('TEST_OUTPUT_DIR')
test_workdir = os.getenv('TEST_WORK_DIR')

layouts = {p.name: BIDSLayout(str(p), validate=False, derivatives=True)
           for p in Path(test_data_env).glob('*') if p.is_dir()}


def pytest_report_header(config):
    msg = "Datasets found: %s" % ', '.join([v.root for v in layouts.values()])
    if test_output_dir is not None:
        msg += '\nOutput folder: %s' % Path(test_output_dir).resolve()
    return msg


@pytest.fixture(autouse=True)
def doctest_autoimport(doctest_namespace):
    """Make available some fundamental modules to doctest modules."""
    doctest_namespace['np'] = np
    doctest_namespace['nb'] = nb
    doctest_namespace['os'] = os
    doctest_namespace['Path'] = Path
    doctest_namespace['data_dir'] = Path(__file__).parent / 'data' / 'tests'
    doctest_namespace['dipy_datadir'] = dipy_datadir
    tmpdir = tempfile.TemporaryDirectory()
    doctest_namespace['tmpdir'] = tmpdir.name
    yield
    tmpdir.cleanup()


@pytest.fixture()
def dipy_test_data(scope='session'):
    """Create a temporal directory shared across tests to pull data in."""
    return _sherbrooke_data


@pytest.fixture
def workdir():
    return None if test_workdir is None else Path(test_workdir)


@pytest.fixture
def output_path():
    return None if test_output_dir is None else Path(test_output_dir)


@pytest.fixture
def bids_layouts():
    return layouts
