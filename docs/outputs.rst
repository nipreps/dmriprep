Outputs of dMRIPrep
===================

dMRIPrep generates:

  1. **Visual QA (quality assurance) reports**

  2. **Pre-processed imaging data**

Visual Reports
--------------

Preprocessed data (dMRIPrep *derivatives*)
------------------------------------------

Anatomical derivatives are placed in each subject's ``anat`` subfolder:

Diffusion derivatives are stored in the ``dwi`` subfolder.

.. code-block:: console

    dmriprep/
      sub-001/
        ses-01/
          dwi/
            # preprocessed diffusion weighted images
            sub-001_ses-01_desc-preproc.dwi.nii.gz
            sub-001_ses-01_desc-preproc.dwi.bval
            sub-001_ses-01_desc-preproc.dwi.bvec
            sub-001_ses-01_desc-preproc.dwi.json
            # mask
            sub-001_ses-01_desc-brain_mask.nii.gz
            # model-derived maps
            sub-001_ses-01_model-DTI_desc-preproc_FA.nii.gz
            sub-001_ses-01_model-DTI_desc-preproc_MD.nii.gz
            sub-001_ses-01_model-DTI_desc-preproc_AD.nii.gz
            sub-001_ses-01_model-DTI_desc-preproc_RD.nii.gz
            # directionally-encoded colour (DEC) maps
            sub-001_ses-01_model-DTI_desc-DEC_FA.nii.gz
            # grey/white matter masks
            sub-001_ses-01_desc-aparcaseg_dseg.nii.gz
            sub-001_ses-01_desc-aseg_dseg.nii.gz
          anat/
      dataset_description.json
      sub-001.html
      index.html
