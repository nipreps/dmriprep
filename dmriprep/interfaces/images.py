"""Image tools interfaces."""

from nipype import logging
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec, SimpleInterface, File
)

LOGGER = logging.getLogger('nipype.interface')


class ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='dwi file')
    b0_ixs = traits.List(traits.Int, mandatory=True,
                         desc='Index of b0s')


class ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='b0 file')


class ExtractB0(SimpleInterface):
    """

    Example
    -------

    >>> os.chdir(tmpdir)
    >>> check = ExtractB0(
    ...    in_file=str(data_dir / 'dwi.nii.gz'),
    ...    b0_ixs=[0, 9, 18, 27, 36, 45, 54, 63, 72, 81, 90, 100]).run()

    """
    input_spec = ExtractB0InputSpec
    output_spec = ExtractB0OutputSpec

    def _run_interface(self, runtime):
        self._results['out_file'] = extract_b0(
            self.inputs.in_file,
            self.inputs.b0_ixs,
            newpath=runtime.cwd)
        return runtime


def extract_b0(in_file, b0_ixs, newpath=None):
    """Extract the *b0* volumes from a DWI dataset."""
    import numpy as np
    import nibabel as nib
    from nipype.utils.filemanip import fname_presuffix

    out_file = fname_presuffix(
        in_file, suffix='_b0', newpath=newpath)

    img = nib.load(in_file)
    data = img.get_fdata()

    b0 = data[..., b0_ixs]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nib.Nifti1Image(b0, img.affine, hdr).to_filename(out_file)
    return out_file
