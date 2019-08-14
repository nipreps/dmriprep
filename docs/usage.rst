.. include:: links.rst

Usage
-----

Execution and the BIDS format
=============================

The ``dmriprep`` workflow takes as principal input the path of the dataset
that is to be processed.
The input dataset is required to be in valid :abbr:`BIDS (Brain Imaging Data
Structure)` format, and it must include at least one T1w structural image and
a dwi series.

.. code-block:: console

    bids
    └── sub-01
      ├── anat
      │   └── sub-01_T1w.nii.gz
      ├── dwi
      │   ├── sub-01_dwi.bval
      │   ├── sub-01_dwi.bvec
      │   ├── sub-01_dwi.json
      │   └── sub-01_dwi.nii.gz
      └── fmap
          ├── sub-01_acq-dwi_dir-AP_epi.json
          ├── sub-01_acq-dwi_dir-AP_epi.nii.gz
          ├── sub-01_acq-dwi_dir-PA_epi.json
          └── sub-01_acq-dwi_dir-PA_epi.nii.gz

We highly recommend that you validate your dataset with the free, online
`BIDS Validator <http://bids-standard.github.io/bids-validator/>`_.

The exact command to run ``dmriprep`` depends on the Installation_ method.
The common parts of the command follow the `BIDS-Apps
<https://github.com/BIDS-Apps>`_ definition.

Example: ::

    dmriprep data/bids_root/ out/ participant -w work/


Command-Line Arguments
======================

.. click:: dmriprep.cli:main
    :prog: dmriprep
    :show-nested:

Debugging
=========

Logs and crash files are output into the
``<output dir>/dmriprep/sub-<participant_label>/log`` directory.
Information on how to customize and understand these files can be found on the
`nipype debugging <http://nipype.readthedocs.io/en/latest/users/debug.html>`_
page.
