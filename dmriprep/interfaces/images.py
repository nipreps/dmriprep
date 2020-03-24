"""Image tools interfaces."""
from pathlib import Path
from nipype import logging
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec, SimpleInterface, File,
    InputMultiObject, OutputMultiObject
)
from dmriprep.utils.images import extract_b0, summarize_images, rescale_b0, match_transforms

LOGGER = logging.getLogger('nipype.interface')


class _ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='dwi file')
    b0_ixs = traits.List(traits.Int, mandatory=True, desc='Index of b0s')


class _ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output b0 file')


class ExtractB0(SimpleInterface):
    """
    Extract all b=0 volumes from a dwi series.

    Example
    -------
    >>> os.chdir(tmpdir)
    >>> extract_b0 = ExtractB0()
    >>> extract_b0.inputs.in_file = str(data_dir / 'dwi.nii.gz')
    >>> extract_b0.inputs.b0_ixs = [0, 1, 2]
    >>> res = extract_b0.run()  # doctest: +SKIP

    """

    input_spec = _ExtractB0InputSpec
    output_spec = _ExtractB0OutputSpec

    def _run_interface(self, runtime):
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            self.inputs.in_file,
            suffix='_b0',
            use_ext=True,
            newpath=str(Path(runtime.cwd).absolute()),
        )

        self._results['out_file'] = extract_b0(
            self.inputs.in_file, self.inputs.b0_ixs, out_file
        )
        return runtime


class _RescaleB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='b0s file')
    mask_file = File(exists=True, mandatory=True, desc='mask file')


class _RescaleB0OutputSpec(TraitedSpec):
    out_ref = File(exists=True, desc='One average b0 file')
    out_b0s = File(exists=True, desc='series of rescaled b0 volumes')


class RescaleB0(SimpleInterface):
    """
    Rescale the b0 volumes to deal with average signal decay over time.

    Example
    -------
    >>> os.chdir(tmpdir)
    >>> rescale_b0 = RescaleB0()
    >>> rescale_b0.inputs.in_file = str(data_dir / 'dwi.nii.gz')
    >>> rescale_b0.inputs.mask_file = str(data_dir / 'dwi_mask.nii.gz')
    >>> res = rescale_b0.run()  # doctest: +SKIP

    """

    input_spec = _RescaleB0InputSpec
    output_spec = _RescaleB0OutputSpec

    def _run_interface(self, runtime):
        import numpy as np
        from nipype.utils.filemanip import fname_presuffix

        out_b0s = fname_presuffix(
            self.inputs.in_file,
            suffix='_rescaled',
            use_ext=True,
            newpath=str(Path(runtime.cwd).absolute())
        )
        out_ref = fname_presuffix(
            self.inputs.in_file,
            suffix='_ref',
            use_ext=True,
            newpath=str(Path(runtime.cwd).absolute())
        )

        self._results['out_b0s'] = rescale_b0(
            self.inputs.in_file,
            self.inputs.mask_file, out_b0s
        )
        self._results['out_ref'] = summarize_images(
            self._results['out_b0s'], method=np.median,
            out_path=out_ref
        )
        return runtime


class _MatchTransformsInputSpec(BaseInterfaceInputSpec):
    b0_indices = traits.List(mandatory=True)
    dwi_files = InputMultiObject(File(exists=True), mandatory=True)
    transforms = InputMultiObject(File(exists=True), mandatory=True)


class _MatchTransformsOutputSpec(TraitedSpec):
    transforms = OutputMultiObject(File(exists=True), mandatory=True)


class MatchTransforms(SimpleInterface):
    """
    Interface for mapping the `match_transforms` function across lists of inputs.
    """
    input_spec = _MatchTransformsInputSpec
    output_spec = _MatchTransformsOutputSpec

    def _run_interface(self, runtime):
        self._results["transforms"] = match_transforms(
            self.inputs.dwi_files, self.inputs.transforms, self.inputs.b0_indices
        )
        return runtime
