from dmriprep.config.testing import mock_config
from dmriprep.workflows.base import init_dmriprep_wf
with mock_config():
    wf = init_dmriprep_wf()