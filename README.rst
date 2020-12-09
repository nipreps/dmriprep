========
dMRIPrep
========

.. image:: https://img.shields.io/badge/chat-mattermost-blue
    :target: https://mattermost.brainhack.org/brainhack/channels/dmriprep

.. image:: https://img.shields.io/badge/docker-nipreps/dmriprep-brightgreen.svg?logo=docker&style=flat
  :target: https://hub.docker.com/r/nipreps/dmriprep/tags/

.. image:: https://img.shields.io/pypi/v/dmriprep.svg
    :target: https://pypi.python.org/pypi/dmriprep

.. image:: https://circleci.com/gh/nipreps/dmriprep.svg?style=svg
    :target: https://circleci.com/gh/nipreps/dmriprep

.. image:: https://github.com/nipreps/dmriprep/workflows/Python%20package/badge.svg
    :target: https://github.com/nipreps/dmriprep/actions

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3392201.svg
    :target: https://doi.org/10.5281/zenodo.3392201

[`Documentation <https://www.nipreps.org/dmriprep/>`__]
[`Support at neurostars.org <https://neurostars.org/tags/dmriprep>`__]

About
-----
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

The workflow is based on `Nipype <https://nipype.readthedocs.io>`__ and
encompasses a large set of tools from other neuroimaging packages.
This pipeline was designed to provide the best software implementation for each state of
preprocessing, and will be updated as newer and better neuroimaging software
becomes available.

dMRIPrep performs basic preprocessing steps such as head-motion correction,
susceptibility-derived distortion correction, eddy current correction, etc.
providing outputs that can be easily submitted to a variety of diffusion models.

Getting involved
----------------
We welcome all contributions!
We'd like to ask you to familiarize yourself with our `contributing guidelines <https:/www.nipreps.org/community/CONTRIBUTING>`__.
For ideas for contributing to *dMRIPrep*, please see the current list of `issues <https://github.com/nipreps/dmriprep/issues>`__.
For making your contribution, we use the GitHub flow, which is
nicely explained in the chapter `Contributing to a Project <http://git-scm.com/book/en/v2/GitHub-Contributing-to-a-Project>`__ in Pro Git
by Scott Chacon and also in the `Making a change section <https://www.nipreps.org/community/CONTRIBUTING/#making-a-change>`__ of our guidelines.
If you're still not sure where to begin, feel free to pop into `Mattermost <https://mattermost.brainhack.org/brainhack/channels/dmriprep>`__ and introduce yourself!
Our project maintainers will do their best to answer any question or concerns and will be happy to help you find somewhere to get started.

Want to learn more about our future plans for developing `dMRIPrep`?
Please take a look at our `milestones board <https://github.com/nipreps/dmriprep/milestones>`__ and `project roadmap <https://www.nipreps.org/dmriprep/roadmap.html>`__.

We ask that all contributors to `dMRIPrep` across all project-related spaces (including but not limited to: GitHub, Mattermost, and project emails), adhere to our `code of conduct <https://www.nipreps.org/community/CODE_OF_CONDUCT>`__.
