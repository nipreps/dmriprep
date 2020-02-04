"""Register tools interfaces."""
import numpy as np
import nibabel as nb
import dmriprep
from nipype import logging
from pathlib import Path
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (
    traits,
    TraitedSpec,
    BaseInterfaceInputSpec,
    InputMultiObject,
    SimpleInterface,
    File,
)


LOGGER = logging.getLogger("nipype.interface")


class _ApplyAffineInputSpec(BaseInterfaceInputSpec):
    moving_image = File(
        exists=True, mandatory=True, desc="image to apply transformation from"
    )
    fixed_image = File(
        exists=True, mandatory=True, desc="image to apply transformation to"
    )
    transform_affine = InputMultiObject(
        File(exists=True), mandatory=True, desc="transformation affine"
    )
    invert_transform = traits.Bool(False, usedefault=True)


class _ApplyAffineOutputSpec(TraitedSpec):
    warped_image = File(exists=True, desc="Outputs warped image")


class ApplyAffine(SimpleInterface):
    """
    Interface to apply an affine transformation to an image.
    """

    input_spec = _ApplyAffineInputSpec
    output_spec = _ApplyAffineOutputSpec

    def _run_interface(self, runtime):
        from dmriprep.utils.register import apply_affine

        warped_image_nifti = apply_affine(
            nb.load(self.inputs.moving_image),
            nb.load(self.inputs.fixed_image),
            np.load(self.inputs.transform_affine[0]),
            self.inputs.invert_transform,
        )
        cwd = Path(runtime.cwd).absolute()
        warped_file = fname_presuffix(
            self.inputs.moving_image,
            use_ext=False,
            suffix="_warped.nii.gz",
            newpath=str(cwd),
        )

        warped_image_nifti.to_filename(warped_file)

        self._results["warped_image"] = warped_file
        return runtime


class _RegisterInputSpec(BaseInterfaceInputSpec):
    moving_image = File(
        exists=True, mandatory=True, desc="image to apply transformation from"
    )
    fixed_image = File(
        exists=True, mandatory=True, desc="image to apply transformation to"
    )
    nbins = traits.Int(default_value=32, usedefault=True)
    sampling_prop = traits.Float(defualt_value=1, usedefault=True)
    metric = traits.Str(default_value="MI", usedefault=True)
    level_iters = traits.List(
        trait=traits.Any(), value=[10000, 1000, 100], usedefault=True
    )
    sigmas = traits.List(trait=traits.Any(), value=[5.0, 2.5, 0.0], usedefault=True)
    factors = traits.List(trait=traits.Any(), value=[4, 2, 1], usedefault=True)
    params0 = traits.ArrayOrNone(value=None, usedefault=True)
    pipeline = traits.List(
        trait=traits.Any(),
        value=["c_of_mass", "translation", "rigid", "affine"],
        usedefault=True,
    )


class _RegisterOutputSpec(TraitedSpec):
    forward_transforms = traits.List(
        File(exists=True), desc="List of output transforms for forward registration"
    )
    warped_image = File(exists=True, desc="Outputs warped image")


class Register(SimpleInterface):
    """
    Interface to perform affine registration.
    """

    input_spec = _RegisterInputSpec
    output_spec = _RegisterOutputSpec

    def _run_interface(self, runtime):
        from dmriprep.utils.register import affine_registration

        reg_types = ["c_of_mass", "translation", "rigid", "affine"]
        pipeline = [
            getattr(dmriprep.utils.register, i)
            for i in self.inputs.pipeline
            if i in reg_types
        ]

        warped_image_nifti, forward_transform_mat = affine_registration(
            nb.load(self.inputs.moving_image),
            nb.load(self.inputs.fixed_image),
            self.inputs.nbins,
            self.inputs.sampling_prop,
            self.inputs.metric,
            pipeline,
            self.inputs.level_iters,
            self.inputs.sigmas,
            self.inputs.factors,
            self.inputs.params0,
        )
        cwd = Path(runtime.cwd).absolute()
        warped_file = fname_presuffix(
            self.inputs.moving_image,
            use_ext=False,
            suffix="_warped.nii.gz",
            newpath=str(cwd),
        )
        forward_transform_file = fname_presuffix(
            self.inputs.moving_image,
            use_ext=False,
            suffix="_forward_transform.npy",
            newpath=str(cwd),
        )
        warped_image_nifti.to_filename(warped_file)

        np.save(forward_transform_file, forward_transform_mat)
        self._results["warped_image"] = warped_file
        self._results["forward_transforms"] = [forward_transform_file]
        return runtime
