.. include:: links.rst

Development road-map
====================
This road-map serves as a guide for developers as well as a way for us to
communicate to users and other stake-holders about the expectations they should
have for the current functionality of the software and future developments.

If you would like to be part of the team developing this road-map, please be sure to
read our `Contributors Guidelines <https://www.nipreps.org/community/CONTRIBUTING>`__.
Then, you can contact the developers through the `Mattermost channel <https://mattermost.brainhack.org/brainhack/channels/dmriprep>`__ to be invited to our bi-weekly meetings.

This road-map proposes a :abbr:`RERO (release early, release often)` philosophy, scheduling
a monthly release until the first stable 1.0 release is reached.

.. important::

    Updated: Dec 18, 2020
    Latest release: `0.3.0 (October 13, 2020) <changes.html#october-13-2020>`__.

Version 0.4 (Before end of 2020)
--------------------------------
Version 0.4 will condense all the outcomes of our sprint towards ISMRM's 2021 abstracts deadline.
This mostly includes house-keeping work, and most prominently, the integration of the *SDCFlows* 2.0
alpha releases, which makes *dMRIPrep* go ahead of *fMRIPrep* in addressing distortions caused by
:math:`B_0` inhomogeneity.

This release will also include Salim's efforts in `#144 <https://github.com/nipreps/dmriprep/pull/144>`__
to provide a temporary implementation of head-motion and eddy-currents correction using
FSL's ``eddy``.
This temporary solution will be replaced by our 3dSHORE-based algorithm ported from QSIPREP,
and left in place for researchers who prefer this option.

Version 0.5 (January, 2021)
---------------------------
#. Continue with the *SDCFlows 2.0* integration:

    - Cover more complex fieldmap specifications
    - Automatically set up "*fieldmap-less*" estimations

#. First draft of ISBI 2021 tutorial:

    - Accept the design for our ISBI 2021 tutorial and document it on the notebooks repo.
    - First draft
    - Start development
    - Plan for supporting Derek and Ariel in taking the head-motion correction to the finish line.

# Finalize the development of ISBI 2021 tutorial (April 2021)

Version 0.6 (December, 2021)
----------------------------
#. Head motion correction.

    A SHOREline-based approach, ported from QSIPREP. In cases where the data are
    "shelled", 3dSHORE will be used as the diffusion model. If the data are
    single-shell, we will use SFM as the diffusion model.
    Development is undergoing at the `eddymotion project
    <https://github.com/nipreps/eddymotion>__`.
    
      - Integrate B\ :sub:`0` field maps `#42 <https://github.com/nipreps/eddymotion/issues/42>`__.
      - Add base integration and unit tests `#40 <https://github.com/nipreps/eddymotion/issues/40>`__.
      - Implementation of a Gaussian Process `#53 <https://github.com/nipreps/eddymotion/issues/53>`__.
      - FiberFox tests (head-motion) `#46 <https://github.com/nipreps/eddymotion/issues/46>`__.
      - FiberFox tests (eddy) `#47 <https://github.com/nipreps/eddymotion/issues/47>`__.
      - FiberFox tests (both) `#48 <https://github.com/nipreps/eddymotion/issues/48>`__.
      - ISMRM'22 abstract (10 November 2021 at 03:59 UTC)
    
#. Framewise-displacement (or equivalent) calculation

    We will identify volumes that are outliers in terms of head-motion, or other
    severe artifacts that make them likely candidates for exclusion from further
    analysis.
    Regarding the *or equivalent* note above: following with `this conversation
    <https://neurostars.org/t/head-motion-parameters-different-when-using-fmriprep-and-spm/17386/4>`__,
    it could be interesting to calculate some sort of average displacement of voxels
    within the white-matter mask instead.

#. Finalize ongoing PRs about reporting number of shells

    - `#73 <https://github.com/nipreps/dmriprep/pull/73>`__
    - `#129 <https://github.com/nipreps/dmriprep/pull/129>`__

#. :math:`B_1` inhomogeneity correction

    - Decide whether it can be brought around from estimation on T1w images
    - Decide whether it should be a default-off option that can be enabled with
      a flag, or else, generate both conversions always.

#. Initiate Phase I of testing

    - Compose our test-bed dataset
    - Document Phase I testing and reporting protocols
    - Start execution

Version 0.7 (January, 2022)
-------------------------
The *noisy month*. This is not a musical event, but a development cycle where we will
focus on the implementation of steps addressing noise in DWI:

#. Identification of outlier measurements (+ imputation?)

#. Implementation of component-based noise identification techniques

    - Comparison of multiple approaches including MP-PCA, NLMeans, and Patch2Self (`#132 <https://github.com/nipreps/dmriprep/issues/132>`__)

#. Gibbs-ringing: investigate whether it should be estimated if other techniques
   are in place (i.e., component-based above), and ordering of steps.

#. Rician bias modeling.

#. DWI carpet-plot and confounds collation.

#. Testing Phase I execution

Version 0.8 (April, 2022)
-------------------------
This release will only address bugfixes conducive to finishing evaluation Phase I,
which should conform a pretty solid ensemble ready for premiere in ISMRM 2021.

Version 0.9 (May, 2022)
-----------------------
#. First official presentation at ISMRM 2021 (should the abstract be accepted)
#. Evaluation Phase II starts.

  - Determine an appropriate dataset
  - Plan for benchmarking experiments (`#121 <https://github.com/nipreps/dmriprep/issues/121>`__)
  - Start with addressing issues as they are reported

Version 1.0 (Targetted for September 2022)
------------------------------------------
Wrap-up evaluation Phase II with the first stable release of *dMRIPrep*.

Long-term plans
---------------
In the long run we would like to explore the following processing steps:

- Gradient non-linearity correction
