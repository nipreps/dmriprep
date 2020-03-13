from dmriprep.config.testing import mock_config
from dmriprep.workflows.base import init_single_subject_wf
with mock_config():
    wf = init_single_subject_wf('THP0005')