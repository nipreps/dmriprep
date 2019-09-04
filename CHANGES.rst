Upcoming release (TBD)
======================

0.2.0 (September 6, 2019)
=======================

  * ENH: Add workflows for ANTs and BrainSuite nonlinear registration-based distortion correction
  * ENH: Add workflow for concatenating dwi scans based on ``--concat_dwis`` list
  * ENH: Enable parallel processing of nodes
  * ENH: Run ``bids-validator`` before pipeline start
  * ENH: Switch crash logs from pickled objects to text files for easier reading by the user
  * MAINT: Migrate to a setup.cfg style of installation
  * ENH: If b0s in the same phase encoding direction don't exist, allow topup to use them from the dwi image
  * ENH: Switch post-eddy mask creation node to use ``dwi2mask`` instead of ``median_otsu``
  * ENH: Take in a pre-specified acquisition parameters file for eddy instead of creating anew using ``--acqp_file``
  * ENH: Update command line interface with stricter validation of input arguments and options
  * ENH: Add workflow for using a synthetic b0 as a reverse PE image for topup (must be pre-generated)
  * ENH: Add workflows for susceptibility distortion correction using fieldmap, phasediff and phase1/phase2 scans
  * ENH: Add command line options for ignoring denoising and unringing and setting desired output resolution
  * ENH: Add ``dwidenoise``, ``mrdegibbs``, ``mrresize``, and ``dwibiascorrect`` from Mrtrix3 as preprocessing steps for the dwi images
  * ENH: Refactor ``run_dmriprep_pe`` workflow into a single subject workflow with separate sub-workflows for dwi pre-processing and topup

0.1.0 (September 6, 2018)
=========================

  * First release on GitHub.
