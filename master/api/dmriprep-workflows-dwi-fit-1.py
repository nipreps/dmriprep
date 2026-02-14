from dmriprep.config.testing import mock_config
from dmriprep.workflows.dwi.fit import init_dwi_fit_wf
with mock_config():
    from dmriprep import config
    wf = init_dwi_fit_wf(
        dwi_file=config.execution.layout.get(
            suffix='dwi', extension='.nii.gz')[0].path,
    )