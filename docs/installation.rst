.. highlight:: shell

============
Installation
============

Docker Container
================

.. code-block:: console

    $ git clone https://github.com/nipy/dmriprep
    $ cd dmriprep
    $ make docker

If you don't want to log into the docker image:

.. code-block:: console

    $ docker run -ti -v $BIDS_INPUT_DIR:/inputs -v $OUTPUT_DIR:/outputs dmriprep:prod dmriprep /inputs /outputs

If you want to log into the image:

.. code-block:: console

    $ docker run -ti -v $BIDS_INPUT_DIR:/inputs -v $OUTPUT_DIR:/outputs dmriprep:prod

Run this inside the docker image:

.. code-block:: console

    $ dmriprep /inputs /output --participant-label 01

Singularity Container
=====================

Preparing a Singularity image (Singularity version < 2.5)
---------------------------------------------------------

Running a Singularity Image
---------------------------

Manually Prepared Environment (Python 3.5+)
===========================================

To install dmriprep, run this command in your terminal:

.. code-block:: console

    $ pip install dmriprep

This is the preferred method to install dmriprep, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for dmriprep can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/nipy/dmriprep

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/nipy/dmriprep/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/nipy/dmriprep
.. _tarball: https://github.com/nipy/dmriprep/tarball/master

External Dependencies
---------------------
