.. include:: links.rst

--------------------
Development road map
--------------------
This road-map serves as a guide for developers as well as a way for us to
communicate to users and other stake-holders aboout the expectations they should
have about the current functionality of the software and future developments.

Version 0.3 (Targetted for March 1st, 2020)
-------------------------------------------
This version should be considered an early alpha of the software, but will
contain a full pipeline of processing from a raw BIDS dataset to analyzable data.

At this point, the processing pipeline will include the following major steps:

#. Susceptibility distortion correction.
    Using `SDCFlows <https://github.com/poldracklab/sdcflows>`__

#. Signal drift estimation
    Leveraging the :math:`b=0` extraction, rescaling and averaging that was merged in `#50 <https://github.com/nipreps/dmriprep/pull/50>`__

Version 0.4 (April 1st, 2020)
-----------------------------
#. Head motion correction.

    A SHOREline-based approach, ported from QSIPREP. In cases where the data are
    "shelled", 3dSHORE will be used as the diffusion model. If the data are
    single-shell, we will use SFM as the diffusion model.

#. Eddy current correction.

    We will explore the possible adaptations of the HMC based on SHOREline above.
    In cases where the data are "shelled", 3dSHORE will be
    used as the diffusion model. If the data are single-shell, we will use SFM
    as the diffusion model.

#. Framewise-displacement calculation

    We will identify volumes that are outliers in terms of head motion, or other
    severe artifacts that make them likely candidates for exclusion from further
    analysis.

Version 0.5 (May 1st, 2020)
----------------------------

#. Registration between dMRI and T1w image.

#. Identification of outlier measurements (+ imputation?)

If we get around to doing thesee steps earlier, they can also be included in
earlier releases.


Version 1.0 (Targetted for September 2020)
------------------------------------------

After integrating the above steps, we will spend the time leading to a 1.0
testing the software on various datasets, evaluating and validating the
resulting derivatives.


Long-term plans
---------------

In the long run we would like to explore the following processing steps:

- Gibbs ringing (using DIPY's image-based implementation).
- Denoising (e.g., MP-PCA)
- Rician bias correction
- Gradient non-linearity correction
- Bias field correction
- Signal drift correction
