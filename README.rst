========
dmriprep
========


.. image:: https://img.shields.io/pypi/v/dmriprep.svg
        :target: https://pypi.python.org/pypi/dmriprep

.. image:: https://img.shields.io/travis/akeshavan/dmriprep.svg
        :target: https://travis-ci.org/akeshavan/dmriprep

.. image:: https://api.codacy.com/project/badge/Grade/01a2d18ee62846e3817c6dccd7f8f5f1
    :target: https://www.codacy.com/app/nipy/dmriprep?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=nipy/dmriprep&amp;utm_campaign=Badge_Grade
    :alt: Codacy Badge

.. image:: https://readthedocs.org/projects/dmriprep/badge/?version=latest
        :target: https://dmriprep-personal.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Preprocessing of neuroimaging dwi data
--------------------------------------

* Free software: BSD license
* Documentation: https://dmriprep-personal.readthedocs.io.

Preparing your data
-------------------

You should have raw data organized in the BIDS format. Also, you should have run Freesurfer and the results should be in a derivatives/ folder:

.. code-block:: console

    bids
    ├── derivatives
    │   └── freesurfer
    │       └── sub-01
    └── sub-01
      ├── dwi
      │   ├── sub-01_ses-01_dwi.bval
      │   ├── sub-01_ses-01_dwi.bvec
      │   ├── sub-01_ses-01_dwi.json
      │   └── sub-01_ses-01_dwi.nii.gz
      └── fmap
          ├── sub-01_ses-01_acq-dwi_dir-AP_epi.json
          ├── sub-01_ses-01_acq-dwi_dir-AP_epi.nii.gz
          ├── sub-01_ses-01_acq-dwi_dir-PA_epi.json
          └── sub-01_ses-01_acq-dwi_dir-PA_epi.nii.gz

Features
--------

* TODO

Credits
-------

This package was created with `Cookiecutter <https://github.com/audreyr/cookiecutter>`_ and the `audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`_ project template.
Several pieces of code have been taken from `fmriprep <https://github.com/poldracklab/fmriprep>`_, `niworkflows <https://github.com/poldracklab/niworkflows>`_ and `sdcflows <https://github.com/poldracklab/sdcflows>`_.
