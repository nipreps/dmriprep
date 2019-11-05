"""Registration tools interfaces."""

import os
import nibabel as nb
import numpy as np
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec, File, SimpleInterface)
from nipype.interfaces import fsl, afni


class EstimateReferenceImageInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="b0 file")
    pre_mask = File(exists=True, mandatory=True, desc="rough mask of skull-stripped b0")
    mc_method = traits.Enum(
        "AFNI", "FSL", usedefault=True,
        desc="Which software to use to perform motion correction")


class EstimateReferenceImageOutputSpec(TraitedSpec):
    ref_image = File(exists=True, desc="3D reference image")


class EstimateReferenceImage(SimpleInterface):
    """
    Given an 4D EPI file estimate an optimal reference image that could be later
    used for motion estimation and coregistration purposes. If detected uses
    T1 saturated volumes (non-steady state) otherwise a median of
    of a subset of motion corrected volumes is used.
    """
    input_spec = EstimateReferenceImageInputSpec
    output_spec = EstimateReferenceImageOutputSpec

    def _run_interface(self, runtime):
        ref_name = self.inputs.in_file
        pre_mask_name = self.inputs.pre_mask

        ref_nii = nb.load(ref_name)
        pre_mask_nii = nb.load(pre_mask_name)

        out_ref_fname = os.path.join(runtime.cwd, "ref_dwi.nii.gz")

        # If reference is only 1 volume, return it directly
        if len(ref_nii.shape) == 3:
            ref_nii.header.extensions.clear()
            ref_nii.to_filename(out_ref_fname)
            self._results['ref_image'] = out_ref_fname
            return runtime
        else:
            ref_nii.header.extensions.clear()

            if self.inputs.mc_method == "AFNI":
                res = afni.Volreg(in_file=ref_name, args='-Fourier -twopass',
                                  zpad=4, outputtype='NIFTI_GZ').run()
            elif self.inputs.mc_method == "FSL":
                res = fsl.MCFLIRT(in_file=ref_name,
                                  ref_vol=0, interpolation='sinc').run()
            mc_ref_nii = nb.load(res.outputs.out_file)

            pre_mask_data = pre_mask_nii.get_fdata()

            image_data = mc_ref_nii.get_fdata()

            normalized_image_data = 1000 * image_data / image_data[pre_mask_data, ...].mean(axis=-1)

            median_image_data = np.median(normalized_image_data, axis=-1)

            nb.Nifti1Image(median_image_data, ref_nii.affine,
                           ref_nii.header).to_filename(out_ref_fname)

            self._results["ref_image"] = out_ref_fname

            return runtime
