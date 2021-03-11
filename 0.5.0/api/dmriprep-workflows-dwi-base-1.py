from dmriprep.config.testing import mock_config
from dmriprep import config
from dmriprep.workflows.dwi.base import init_dwi_preproc_wf
with mock_config():
    wf = init_dwi_preproc_wf(
        f"{config.execution.layout.root}/"
        "sub-THP0005/dwi/sub-THP0005_dwi.nii.gz"
    )