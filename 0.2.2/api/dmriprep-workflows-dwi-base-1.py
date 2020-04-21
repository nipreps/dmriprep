from dmriprep.config.testing import mock_config
from dmriprep import config
from dmriprep.workflows.dwi.base import init_early_b0ref_wf
with mock_config():
    wf = init_early_b0ref_wf()