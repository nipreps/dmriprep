from dmriprep.config.testing import mock_config
from dmriprep import config
from dmriprep.workflows.dwi.base import init_dwi_preproc_wf
with mock_config():
    dwi_file = config.execution.bids_dir / 'sub-THP0005' / 'dwi'                     / 'sub-THP0005_dwi.nii.gz'
    wf = init_dwi_preproc_wf(str(dwi_file))