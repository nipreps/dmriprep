#!/usr/bin/env python

"""

Pre-processing dMRI workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: dmriprep.workflows.dwi.base
.. automodule:: dmriprep.workflows.dwi.prep_dwi
.. automodule:: dmriprep.workflows.dwi.tensor
.. automodule:: dmriprep.workflows.dwi.outputs

"""

from .base import init_dwi_preproc_wf
from .prep_dwi import init_prep_dwi_wf
from .tensor import init_tensor_wf
from .outputs import init_output_wf

__all__ = [
    "init_dwi_preproc_wf",
    "init_prep_dwi_wf",
    "init_tensor_wf",
    "init_output_wf"
]
