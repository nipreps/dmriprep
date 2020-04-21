"""Image tools interfaces."""
from pathlib import Path

from nipype import logging
from nipype.interfaces.base import (
    BaseInterfaceInputSpec,
    File,
    SimpleInterface,
    TraitedSpec,
    traits,
)

from dmriprep.utils.images import extract_b0, median, rescale_b0

LOGGER = logging.getLogger("nipype.interface")


class _ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="dwi file")
    b0_ixs = traits.List(traits.Int, mandatory=True, desc="Index of b0s")


class _ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="output b0 file")


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
            suffix="_b0",
            newpath=str(Path(runtime.cwd).absolute()),
        )

        self._results["out_file"] = extract_b0(
            self.inputs.in_file, self.inputs.b0_ixs, out_path=out_file
        )
        return runtime


class _RescaleB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="b0s file")
    mask_file = File(exists=True, mandatory=True, desc="mask file")


class _RescaleB0OutputSpec(TraitedSpec):
    out_ref = File(exists=True, desc="One average b0 file")
    out_b0s = File(exists=True, desc="series of rescaled b0 volumes")
    signal_drift = traits.List(traits.Float, desc="estimated signal drift factors")


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
        from nipype.utils.filemanip import fname_presuffix

        out_b0s = fname_presuffix(
            self.inputs.in_file,
            suffix="_rescaled",
            newpath=str(Path(runtime.cwd).absolute()),
        )
        out_ref = fname_presuffix(
            self.inputs.in_file,
            suffix="_ref",
            newpath=str(Path(runtime.cwd).absolute()),
        )

        self._results["out_b0s"], self._results["signal_drift"] = rescale_b0(
            self.inputs.in_file, self.inputs.mask_file, out_b0s
        )
        self._results["out_ref"] = median(self._results["out_b0s"], out_path=out_ref)
        return runtime
