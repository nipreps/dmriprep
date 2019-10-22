#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""@authors: Derek Pisner, Oscar Estaban, Ariel Rokem"""
from __future__ import division, print_function
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, TraitedSpec, File, traits, Directory


class CheckVecsInputSpec(BaseInterfaceInputSpec):
    """Input interface wrapper for CheckVecs"""
    fbval = File(exists=True, mandatory=True)
    fbvec = File(exists=True, mandatory=True)
    sesdir = Directory(exists=True, mandatory=True)
    dwi_file = File(exists=True, mandatory=True)
    B0_NORM_EPSILON = traits.Float(50)
    bval_scaling = traits.Bool(True)


class CheckVecsOutputSpec(TraitedSpec):
    """Output interface wrapper for CheckVecs"""
    from dipy.core.gradients import GradientTable
    gtab = traits.Instance(GradientTable)
    is_hemi = traits.Bool()
    pole = traits.Array()
    b0_ixs = traits.Array()
    gtab_tsv_file = File(exists=True, mandatory=True)
    slm = traits.Str()


class CheckVecs(BaseInterface):
    """Interface wrapper for CheckVecs"""
    input_spec = CheckVecsInputSpec
    output_spec = CheckVecsOutputSpec

    def _run_interface(self, runtime):
        from dmriprep.utils.vectors import checkvecs
        [gtab, is_hemi, pole, b0_ixs, gtab_tsv_file, slm] = checkvecs(
            self.inputs.fbval,
            self.inputs.fbvec,
            self.inputs.sesdir,
            self.inputs.dwi_file,
            self.inputs.B0_NORM_EPSILON,
            self.inputs.bval_scaling)
        setattr(self, '_gtab', gtab)
        setattr(self, '_is_hemi', is_hemi)
        setattr(self, '_pole', pole)
        setattr(self, '_b0_ixs', b0_ixs)
        setattr(self, '_gtab_tsv_file', gtab_tsv_file)
        setattr(self, '_slm', slm)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['gtab'] = getattr(self, '_gtab')
        outputs['is_hemi'] = getattr(self, '_is_hemi')
        outputs['pole'] = getattr(self, '_pole')
        outputs['b0_ixs'] = getattr(self, '_b0_ixs')
        outputs['gtab_tsv_file'] = getattr(self, '_gtab_tsv_file')
        outputs['slm'] = getattr(self, '_slm')
        return outputs

