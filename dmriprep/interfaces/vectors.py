#!/usr/bin/env python
# -*- coding: utf-8 -*-
from nipype.interfaces.base import SimpleInterface, BaseInterfaceInputSpec, TraitedSpec, File, traits, Directory, isdefined


class CleanVecsInputSpec(BaseInterfaceInputSpec):
    """Input interface wrapper for CleanVecs"""
    basedir = Directory(exists=True, mandatory=False)
    dwi_file = File(exists=True, mandatory=True)
    fbval = File(exists=False, mandatory=False)
    fbvec = File(exists=False, mandatory=False)
    rasb_tsv_file = File(exists=False, mandatory=False)
    rescale = traits.Bool(True, usedefault=True)
    save_fsl_style = traits.Bool(True, usedefault=True)
    B0_NORM_EPSILON = traits.Float(50)
    bval_scaling = traits.Bool(True, usedefault=True)


class CleanVecsOutputSpec(TraitedSpec):
    """Output interface wrapper for CleanVecs"""
    from dipy.core.gradients import GradientTable
    gtab = traits.Instance(GradientTable)
    is_hemi = traits.Bool()
    pole = traits.Array()
    b0_ixs = traits.Array()
    slm = traits.Str()
    fbval_out_file = traits.Any()
    fbvec_out_file = traits.Any()
    rasb_tsv_out_file = File(exists=True, mandatory=True)


class CleanVecs(SimpleInterface):
    """Interface wrapper for CleanVecs"""
    input_spec = CleanVecsInputSpec
    output_spec = CleanVecsOutputSpec

    def _run_interface(self, runtime):
        from dmriprep.utils.vectors import VectorTools
        if isdefined(self.inputs.fbval) and isdefined(self.inputs.fbvec):
            fbval = self.inputs.fbval
            fbvec = self.inputs.fbvec
        else:
            fbval = None
            fbvec = None

        if isdefined(self.inputs.rasb_tsv_file):
            rasb_tsv_file = self.inputs.rasb_tsv_file
        else:
            rasb_tsv_file = None

        if isdefined(self.inputs.basedir):
            basedir = self.inputs.basedir
        else:
            basedir = runtime.cwd

        vt = VectorTools(basedir, self.inputs.dwi_file, fbval, fbvec, rasb_tsv_file, self.inputs.B0_NORM_EPSILON,
                         self.inputs.bval_scaling)

        # Read in vectors
        if rasb_tsv_file is not None:
            vt.read_rasb_tsv()
        elif fbval is not None and fbvec is not None:
            vt.read_bvals_bvecs()
        else:
            raise OSError('VectorTools methods require either fbval/fbvec input files or an input rasb .tsv file.')

        # Rescale vectors
        if self.inputs.rescale is True:
            vt.rescale_vecs()

        # Build gradient table
        gtab, b0_ixs = vt.build_gradient_table()

        # Check vector integrity
        is_hemi, pole, slm = vt.checkvecs()

        if self.inputs.save_fsl_style is True:
            fbval_out_file, fbvec_out_file = vt.save_vecs_fsl()
        else:
            fbval_out_file = None
            fbvec_out_file = None

        self._results['gtab'] = gtab
        self._results['is_hemi'] = is_hemi
        self._results['pole'] = pole
        self._results['slm'] = slm
        self._results['b0_ixs'] = b0_ixs
        self._results['fbval_out_file'] = fbval_out_file
        self._results['fbvec_out_file'] = fbvec_out_file
        self._results['rasb_tsv_out_file'] = vt.write_rasb_tsv()
        return runtime
