#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Image tools interfaces
~~~~~~~~~~~~~~~~~~~~~~

"""

from nipype import logging
from nipype.interfaces.base import (
    TraitedSpec, BaseInterfaceInputSpec, SimpleInterface, File
)

LOGGER = logging.getLogger('nipype.interface')


class ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='dwi file')
    in_rasb = File(exists=True, mandatory=True,
                   desc='File containing the gradient directions in RAS+ scanner coordinates')


class ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='mean b0 file')


class ExtractB0(SimpleInterface):
    input_spec = ExtractB0InputSpec
    output_spec = ExtractB0OutputSpec

    def _run_interface(self, runtime):
        self._results['out_file'] = extract_b0(
            self.inputs.in_file,
            self.inputs.in_rasb,
            newpath=runtime.cwd)
        return runtime


def extract_b0(in_file, in_rasb, b0_thres=50, newpath=None):
    """Extract the *b0* volumes from a DWI dataset."""
    import numpy as np
    import nibabel as nib
    from nipype.utils.filemanip import fname_presuffix

    out_file = fname_presuffix(
        in_file, suffix='_b0', newpath=newpath)

    img = nib.load(in_file)
    data = img.get_fdata()

    bvals = np.loadtxt(in_rasb, usecols=-1, skiprows=1)

    b0 = data[..., bvals < b0_thres]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nib.Nifti1Image(b0, img.affine, hdr).to_filename(out_file)
    return out_file
