#!/usr/bin/env python

"""

Pre-processing dMRI workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: dmriprep.workflows.dwi.base
.. automodule:: dmriprep.workflows.dwi.artifacts
.. automodule:: dmriprep.workflows.dwi.util
.. automodule:: dmriprep.workflows.dwi.eddy
.. automodule:: dmriprep.workflows.dwi.tensor
.. automodule:: dmriprep.workflows.dwi.outputs

"""

from .base import init_dwi_preproc_wf
from .artifacts import init_dwi_artifacts_wf
from .util import init_dwi_resize_wf
from .eddy import init_dwi_eddy_wf
from .tensor import init_dwi_tensor_wf
from .outputs import init_dwi_derivatives_wf

__all__ = [
    'init_dwi_preproc_wf',
    'init_dwi_artifacts_wf',
    'init_dwi_resize_wf',
    'init_dwi_eddy_wf',
    'init_dwi_tensor_wf',
    'init_dwi_derivatives_wf'
]
