"""Image tools interfaces."""

from nipype import logging
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec, SimpleInterface, File
)

LOGGER = logging.getLogger('nipype.interface')


class _ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='dwi file')
    b0_ixs = traits.List(traits.Int, mandatory=True,
                         desc='Index of b0s')


class _ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='b0 file')


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
        self._results['out_file'] = extract_b0(
            self.inputs.in_file,
            self.inputs.b0_ixs,
            newpath=runtime.cwd)
        return runtime


def extract_b0(in_file, b0_ixs, newpath=None):
    """Extract the *b0* volumes from a DWI dataset."""
    import numpy as np
    import nibabel as nb
    from nipype.utils.filemanip import fname_presuffix

    out_file = fname_presuffix(
        in_file, suffix='_b0', newpath=newpath)

    img = nb.load(in_file)
    data = img.get_fdata(dtype='float32')

    b0 = data[..., b0_ixs]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(b0, img.affine, hdr).to_filename(out_file)
    return out_file


class _RescaleB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='b0s file')
    mask_file = File(exists=True, mandatory=True, desc='mask file')


class _RescaleB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='b0 file')


class RescaleB0(SimpleInterface):
    """
    Rescale the b0 volumes to deal with average signal decay over time
    and output the median image.

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
        self._results['out_file'] = rescale_b0(
            self.inputs.in_file,
            self.inputs.mask_file,
            newpath=runtime.cwd)
        return runtime


def rescale_b0(in_file, mask_file, newpath=None):
    """
    Rescale the input volumes using the median signal intensity
    and output a median image.
    """
    import numpy as np
    import nibabel as nb
    from nipype.utils.filemanip import fname_presuffix

    out_file = fname_presuffix(
        in_file, suffix='_median_b0', newpath=newpath)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file
    if img.shape[-1] == 1:
        nb.squeeze_image(img).to_filename(out_file)
        return out_file

    data = img.get_fdata(dtype='float32')
    mask_img = nb.load(mask_file)
    mask_data = mask_img.get_fdata(dtype='float32')

    median_signal = data[mask_data > 0, ...].median(axis=0)

    rescaled_data = 1000 * data / median_signal

    median_data = np.median(rescaled_data, axis=-1)

    hdr = img.header.copy()
    hdr.set_data_shape(median_data.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(median_data, img.affine, hdr).to_filename(out_file)
    return out_file
