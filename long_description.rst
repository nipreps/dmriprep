Preprocessing of diffusion MRI (dMRI) involves numerous steps to clean and standardize
the data before fitting a particular model.
Generally, researchers create ad hoc preprocessing workflows for each dataset,
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

The workflow is based on `Nipype <https://nipype.readthedocs.io>`_ and encompases a large
set of tools from well-known neuroimaging packages, including
`FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_,
`ANTs <https://stnava.github.io/ANTs/>`_,
`FreeSurfer <https://surfer.nmr.mgh.harvard.edu/>`_,
`AFNI <https://afni.nimh.nih.gov/>`_,
and `Nilearn <https://nilearn.github.io/>`_.
This pipeline was designed to provide the best software implementation for each state of
preprocessing, and will be updated as newer and better neuroimaging software becomes
available.

dMRIPrep performs basic preprocessing steps (coregistration, normalization, unwarping,
segmentation, skullstripping etc.) providing outputs that can be
easily submitted to a variety of tractography algorithms.

[Documentation `dmriprep.org <https://dmriprep.readthedocs.io>`_]
[Support `neurostars.org <https://neurostars.org/tags/fmriprep>`_]
