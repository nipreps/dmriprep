========
dmriprep
========


.. image:: https://img.shields.io/pypi/v/dmriprep.svg
        :target: https://pypi.python.org/pypi/dmriprep

.. image:: https://img.shields.io/travis/akeshavan/dmriprep.svg
        :target: https://travis-ci.org/akeshavan/dmriprep

.. image:: https://readthedocs.org/projects/dmriprep/badge/?version=latest
        :target: https://dmriprep.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Preprocessing of neuroimaging data in preparation for AFQ analysis
------------------------------------------------------------------

* Free software: BSD license
* Documentation: https://dmriprep.readthedocs.io.

Preparing your data
-------------------

You should have raw data organized in the BIDS format. Also, you should have run Freesurfer and the results should be in a derivatives/ folder:

.. code-block:: console

    bids
    ├── derivatives
    │   └── sub-01
    │       └── freesurfer
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
