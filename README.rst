========
dMRIPrep
========

.. image:: https://badgen.net/badge/chat/on%20mattermost/blue
    :target: https://mattermost.brainhack.org/brainhack/channels/dmriprep

.. image:: https://img.shields.io/pypi/v/dmriprep.svg
    :target: https://pypi.python.org/pypi/dmriprep

.. image:: https://circleci.com/gh/nipreps/dmriprep.svg?style=svg
    :target: https://circleci.com/gh/nipreps/dmriprep

.. image:: https://travis-ci.org/nipreps/dmriprep.svg?branch=master
    :target: https://travis-ci.org/nipreps/dmriprep

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3392201.svg
    :target: https://doi.org/10.5281/zenodo.3392201

[`Documentation <https://nipreps.github.io/dmriprep/>`__]
[`Support at neurostars.org <https://neurostars.org/tags/dmriprep>`__]

The preprocessing of diffusion MRI (dMRI) involves numerous steps to clean and standardize
the data before fitting a particular model.
Generally, researchers create ad-hoc preprocessing workflows for each dataset,
building upon a large inventory of available tools.
The complexity of these workflows has snowballed with rapid advances in
acquisition and processing.
dMRIPrep is an analysis-agnostic tool that addresses the challenge of robust and
reproducible preprocessing for whole-brain dMRI data.
dMRIPrep automatically adapts a best-in-breed workflow to the idiosyncrasies of
virtually any dataset, ensuring high-quality preprocessing without manual intervention.
dMRIPrep equips neuroscientists with an easy-to-use and transparent preprocessing
workflow, which can help ensure the validity of inference and the interpretability
of results.

The workflow is based on `Nipype <https://nipype.readthedocs.io>`__ and encompases a large
set of tools from well-known neuroimaging packages, including
`FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`__,
`ANTs <https://stnava.github.io/ANTs/>`__,
`FreeSurfer <https://surfer.nmr.mgh.harvard.edu/>`__,
`AFNI <https://afni.nimh.nih.gov/>`__,
and `Nilearn <https://nilearn.github.io/>`__.
This pipeline was designed to provide the best software implementation for each state of
preprocessing, and will be updated as newer and better neuroimaging software becomes
available.

dMRIPrep performs basic preprocessing steps (coregistration, normalization, unwarping,
segmentation, skullstripping etc.) providing outputs that can be
easily submitted to a variety of tractography algorithms.
