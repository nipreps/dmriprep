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
(unless disabled with a flag) one :abbr:`DWI (diffusion weighted imaging)` series.
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

When using manually-prepared environments or Singularity, FreeSurfer will search
for a license key file first using the ``$FS_LICENSE`` environment variable and then
in the default path to the license key file (``$FREESURFER_HOME/license.txt``).
If using the ``--cleanenv`` flag and ``$FS_LICENSE`` is set, use ``--fs-license-file $FS_LICENSE``
to pass the license file location to *dMRIPrep*.

It is possible to run the Docker container pointing the image to a local path
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


Usage tracking with Google Analytics
------------------------------------
To be able to assess usage of the software, we are recording each use of the
:abbr:`CLI (command-line interface)` as an event in Google Analytics,
using `popylar <https://popylar.github.io>`__.
``

For now, the only information that we are recording is the fact that the CLI was
called and whether the call completed successfully. In addition, through Google
Analytics, we will have access to very general information, such as the country
and city in which the computer using the CLI was located and the time that it
was used. At this time, we do not record any additional information, although in
the future we may want to record statistics on the computational environment in
which the CLI was called, such as the operating system.

Opting out of this usage tracking can be done by calling the CLI with the
``--notrack`` flag::

    dmriprep data/bids_root/ out/ participant -w work/ --notrack
