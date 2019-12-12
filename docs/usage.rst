.. include:: links.rst

.. _Usage :

-----
Usage
-----

Execution and the BIDS format
-----------------------------
The *dMRIPrep* workflow takes as principal input the path of the dataset
that is to be processed.
The input dataset is required to be in valid :abbr:`BIDS (Brain Imaging Data
Structure)` format, and it must include at least one T1w structural image and
(unless disabled with a flag) a BOLD series.
We highly recommend that you validate your dataset with the free, online
`BIDS Validator <http://bids-standard.github.io/bids-validator/>`_.

The exact command to run *dMRIPrep* depends on the Installation_ method.
The common parts of the command follow the `BIDS-Apps
<https://github.com/BIDS-Apps>`_ definition.
Example: ::

    dmriprep data/bids_root/ out/ participant -w work/


Command-Line Arguments
----------------------
.. argparse::
   :ref: dmriprep.cli.run.get_parser
   :prog: dmriprep
   :nodefault:
   :nodefaultconst:

.. _fs_license:

The FreeSurfer license
----------------------
*dMRIPrep* uses FreeSurfer tools, which require a license to run.

To obtain a FreeSurfer license, simply register for free at
https://surfer.nmr.mgh.harvard.edu/registration.html.

When using manually-prepared environments or singularity, FreeSurfer will search 
for a license key file first using the ``$FS_LICENSE`` environment variable and then 
in the default path to the license key file (``$FREESURFER_HOME/license.txt``). 
If using the ``--cleanenv`` flag and ``$FS_LICENSE`` is set, use ``--fs-license-file $FS_LICENSE`` 
to pass the license file location to *dMRIPrep*.

It is possible to run the docker container pointing the image to a local path
where a valid license file is stored.
For example, if the license is stored in the ``$HOME/.licenses/freesurfer/license.txt``
file on the host system: ::

    $ docker run -ti --rm \
        -v $HOME/fullds005:/data:ro \
        -v $HOME/dockerout:/out \
        -v $HOME/.licenses/freesurfer/license.txt:/opt/freesurfer/license.txt \
        nipreps/dmriprep:latest \
        /data /out/out \
        participant \
        --ignore fieldmaps
