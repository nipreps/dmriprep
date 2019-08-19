Upcoming release (TBD)
======================

0.2.0 (August 20, 2019)
=======================

  * ENH: Add ``collect_participants`` and ``validate_input_dir`` functions (taken from niworkflows)
  * ENH: Add ``dwidenoise``, ``mrdegibbs``, ``mrresize``, and ``dwibiascorrect`` from Mrtrix3 as preprocessing steps for the dwi images
  * ENH: Add workflow for using a synthetic b0 as a reverse PE image for topup
  * ENH: Add workflows for dealing with fieldmap, phasediff and phase1/phase2 scans (taken from sdcflows)
  * ENH: Switch crash logs from pickle to text files for easier reading by the user
  * MAINT: Migrate to a setup.cfg style of installation
  * ENH: Refactor ``run_dmriprep_pe`` workflow into a single subject workflow with separate sub-workflows for dwi and fieldmap pre-processing

0.1.0 (September 6, 2018)
=========================

  * First release on GitHub.
