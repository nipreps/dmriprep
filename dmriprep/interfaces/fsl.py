#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Interface for FSL Eddy (temporary until updated Eddy spec is merged)
"""
from __future__ import print_function, division, unicode_literals, \
    absolute_import
from builtins import str

import os

from nipype.utils.filemanip import fname_presuffix

from nipype.interfaces.base import (traits, TraitedSpec, File, isdefined)
from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec


class EddyInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='--imain=%s',
        desc='File containing all the images to estimate distortions for')
    in_mask = File(
        exists=True,
        mandatory=True,
        argstr='--mask=%s',
        desc='Mask to indicate brain')
    in_index = File(
        exists=True,
        mandatory=True,
        argstr='--index=%s',
        desc=('File containing indices for all volumes in --imain '
              'into --acqp and --topup'))
    in_acqp = File(
        exists=True,
        mandatory=True,
        argstr='--acqp=%s',
        desc='File containing acquisition parameters')
    in_bvec = File(
        exists=True,
        mandatory=True,
        argstr='--bvecs=%s',
        desc='File containing the b-vectors for all volumes in --imain')
    in_bval = File(
        exists=True,
        mandatory=True,
        argstr='--bvals=%s',
        desc='File containing the b-values for all volumes in --imain')
    out_base = traits.Str(
        default_value='eddy_corrected',
        usedefault=True,
        argstr='--out=%s',
        desc='basename for output (warped) image')
    session = File(
        exists=True,
        argstr='--session=%s',
        desc='File containing session indices for all volumes in --imain')
    in_topup_fieldcoef = File(
        exists=True,
        argstr='--topup=%s',
        requires=['in_topup_movpar'],
        desc='topup file containing the field coefficients')
    in_topup_movpar = File(
        exists=True,
        requires=['in_topup_fieldcoef'],
        desc='topup movpar.txt file')
    field = File(
        exists=True,
        argstr='--field=%s',
        desc=('NonTOPUP fieldmap scaled in Hz - filename has to be provided '
              'without an extension. TOPUP is strongly recommended'))
    field_mat = File(
        exists=True,
        argstr='--field_mat=%s',
        requires=['field'],
        desc=('Matrix that specifies the relative locations of the field '
              'specified by --field and first volume in file --imain'))
    flm = traits.Enum(
        'linear',
        'quadratic',
        'cubic',
        argstr='--flm=%s',
        desc='First level EC model')
    slm = traits.Enum(
        'none',
        'linear',
        'quadratic',
        argstr='--slm=%s',
        desc='Second level EC model')
    fwhm = traits.Float(
        default_value=0,
        usedefault=True,
        argstr='--fwhm=%s',
        desc='FWHM for conditioning filter when estimating the parameters')
    niter = traits.Int(
        default_value=5,
        usedefault=True,
        argstr='--niter=%s',
        desc='Number of iterations')
    fep = traits.Bool(
        False, argstr='--fep', desc='Fill empty planes in x- or y-directions')
    initrand = traits.Bool(
        False,
        argstr='--initrand',
        desc='Resets rand for when selecting voxels',
        min_ver='5.0.10')
    interp = traits.Enum(
        'spline',
        'trilinear',
        argstr='--interp=%s',
        desc='Interpolation model for estimation step')
    method = traits.Enum(
        'jac',
        'lsr',
        argstr='--resamp=%s',
        desc='Final resampling method (jacobian/least squares)')
    nvoxhp = traits.Int(
        default_value=1000,
        usedefault=True,
        argstr='--nvoxhp=%s',
        desc='# of voxels used to estimate the hyperparameters')
    fudge_factor = traits.Float(
        default_value=10.0,
        usedefault=True,
        argstr='--ff=%s',
        desc='Fudge factor for hyperparameter error variance')
    dont_sep_offs_move = traits.Bool(
        False,
        argstr='--dont_sep_offs_move',
        desc='Do NOT attempt to separate field offset from subject movement')
    dont_peas = traits.Bool(
        False,
        argstr='--dont_peas',
        desc='Do NOT perform a post-eddy alignment of shells')
    repol = traits.Bool(
        default_value=False,
        argstr='--repol',
        desc='Detect and replace outlier slices')
    outlier_nstd = traits.Int(
        argstr='--ol_nstd',
        desc='Number of std off to qualify as outlier',
        requires=['repol'],
        min_ver='5.0.10')
    outlier_nvox = traits.Int(
        argstr='--ol_nvox',
        desc='Min # of voxels in a slice for inclusion in outlier detection',
        requires=['repol'],
        min_ver='5.0.10')
    outlier_type = traits.Enum(
        'sw',
        'gw',
        'both',
        argstr='--ol_type',
        desc='Type of outliers, slicewise (sw), groupwise (gw) or both (both)',
        requires=['repol'],
        min_ver='5.0.10')
    outlier_pos = traits.Bool(
        False,
        argstr='--ol_pos',
        desc='Consider both positive and negative outliers if set',
        requires=['repol'],
        min_ver='5.0.10')
    outlier_sqr = traits.Bool(
        False,
        argstr='--ol_sqr',
        desc='Consider outliers among sums-of-squared differences if set',
        requires=['repol'],
        min_ver='5.0.10')
    mb = traits.Int(
        argstr='--mb=%s',
        desc='Multi-band factor',
        min_ver='5.0.10')
    mb_offs = traits.Enum(
        0,
        1,
        -1,
        argstr='--mb_offs=%s',
        desc=('Multi-band offset (-1 if bottom slice removed, 1 if '
              'top slice removed'),
        requires=['mb'],
        min_ver='5.0.10')
    mporder = traits.Int(
        argstr='--mporder=%s',
        desc='Order of slice-to-vol movement model',
        requires=['slspec'],
        min_ver='5.0.11')
    s2v_niter = traits.Int(
        argstr='--s2v_niter=%s',
        desc='Number of iterations for slice-to-vol',
        requires=['slspec'],
        min_ver='5.0.11')
    s2v_lambda = traits.Int(
        agstr='--s2v_lambda',
        desc='Regularisation weight for slice-to-vol movement (reasonable range 1-10)',
        requires=['slspec'],
        min_ver='5.0.11')
    s2v_interp = traits.Enum(
        'trilinear',
        'spline',
        argstr='--s2v_interp=%s',
        desc='Slice-to-vol interpolation model for estimation step',
        requires=['slspec'],
        min_ver='5.0.11')
    slspec = traits.File(
        exists=True,
        argstr='--slspec=%s',
        desc='Name of text file completely specifying slice/group acquisition',
        xor=['json'],
        min_ver='5.0.11')
    json = traits.File(
        exists=True,
        argstr='--json=%s',
        desc='Name of .json text file with information about slice timing',
        xor=['slspec'],
        min_ver='6.0.1')
    estimate_move_by_susceptibility = traits.Bool(
        False,
        argstr='--estimate_move_by_susceptibility',
        desc='Estimate how susceptibility field changes with subject movement',
        min_ver='6.0.1')
    mbs_niter = traits.Int(
        argstr='--mbs_niter=%s',
        desc='Number of iterations for MBS estimation',
        requires=['estimate_move_by_susceptibility'],
        min_ver='6.0.1')
    mbs_lambda = traits.Int(
        argstr='--mbs_lambda=%s',
        desc='Weighting of regularisation for MBS estimation',
        requires=['estimate_move_by_susceptibility'],
        min_ver='6.0.1')
    mbs_ksp = traits.Int(
        argstr='--mbs_ksp=%smm',
        desc='Knot-spacing for MBS field estimation',
        requires=['estimate_move_by_susceptibility'],
        min_ver='6.0.1')
    is_shelled = traits.Bool(
        False,
        argstr='--data_is_shelled',
        desc=('Override internal check to ensure that data are acquired '
              'on a set of b-value shells'))
    num_threads = traits.Int(
        default_value=1,
        usedefault=True,
        nohash=True,
        desc="Number of openmp threads to use")
    use_cuda = traits.Bool(False, desc="Run eddy using cuda gpu")
    cnr_maps = traits.Bool(
        False, desc='Output CNR-Maps', argstr='--cnr_maps', min_ver='5.0.10')
    residuals = traits.Bool(
        False, desc='Output Residuals', argstr='--residuals', min_ver='5.0.10')


class EddyOutputSpec(TraitedSpec):
    out_corrected = File(
        exists=True, desc='4D image file containing all the corrected volumes')
    out_parameter = File(
        exists=True,
        desc=('Text file with parameters defining the field and'
              'movement for each scan'))
    out_rotated_bvecs = File(
        exists=True, desc='File containing rotated b-values for all volumes')
    out_movement_rms = File(
        exists=True, desc='Summary of the "total movement" in each volume')
    out_restricted_movement_rms = File(
        exists=True,
        desc=('Summary of the "total movement" in each volume '
              'disregarding translation in the PE direction'))
    out_shell_alignment_parameters = File(
        exists=True,
        desc=('Text file containing rigid body movement parameters '
              'between the different shells as estimated by a '
              'post-hoc mutual information based registration'))
    out_shell_pe_translation_parameters = File(
        exists=True,
        desc=('Text file containing translation along the PE-direction '
              'between the different shells as estimated by a '
              'post-hoc mutual information based registration'))
    out_outlier_map = File(
        exists=True,
        desc=('Matrix where rows represent volumes and columns represent '
              'slices. "0" indicates that scan-slice is not an outlier '
              'and "1" indicates that it is'))
    out_outlier_n_stdev_map = File(
        exists=True,
        desc=('Matrix where rows represent volumes and columns represent '
              'slices. Values indicate number of standard deviations off the '
              'mean difference between observation and prediction is'))
    out_outlier_n_sqr_stdev_map = File(
        exists=True,
        desc=('Matrix where rows represent volumes and columns represent '
              'slices. Values indicate number of standard deivations off the '
              'square root of the mean squared difference between observation '
              'and prediction is'))
    out_outlier_report = File(
        exists=True,
        desc=('Text file with a plain language report on what '
              'outlier slices eddy has found'))
    out_outlier_free = File(
        exists=True,
        desc=('4D image file not corrected for susceptibility or eddy-'
              'current distortions or subject movement but with outlier '
              'slices replaced'))
    out_movement_over_time = File(
        exists=True,
        desc=('Text file containing translations (mm) and rotations '
              '(radians) for each excitation'))
    out_cnr_maps = File(
        exists=True, desc='path/name of file with the cnr_maps')
    out_residuals = File(
        exists=True, desc='path/name of file with the residuals')


class Eddy(FSLCommand):
    """
    Interface for FSL eddy, a tool for estimating and correcting eddy
    currents induced distortions. `User guide
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide>`_ and
    `more info regarding acqp file
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/Faq#How_do_I_know_what_to_put_into_my_--acqp_file.3F>`_.
    Examples
    --------
    >>> from nipype.interfaces.fsl import Eddy
    >>> eddy = Eddy()
    >>> eddy.inputs.in_file = 'epi.nii'
    >>> eddy.inputs.in_mask  = 'epi_mask.nii'
    >>> eddy.inputs.in_index = 'epi_index.txt'
    >>> eddy.inputs.in_acqp  = 'epi_acqp.txt'
    >>> eddy.inputs.in_bvec  = 'bvecs.scheme'
    >>> eddy.inputs.in_bval  = 'bvals.scheme'
    >>> eddy.inputs.use_cuda = True
    >>> eddy.cmdline # doctest: +ELLIPSIS
    'eddy_cuda --ff=10.0 --fwhm=0 --acqp=epi_acqp.txt --bvals=bvals.scheme \
--bvecs=bvecs.scheme --imain=epi.nii --index=epi_index.txt \
--mask=epi_mask.nii --niter=5 --nvoxhp=1000 --out=.../eddy_corrected'
    >>> eddy.inputs.use_cuda = False
    >>> eddy.cmdline # doctest: +ELLIPSIS
    'eddy_openmp --ff=10.0 --fwhm=0 --acqp=epi_acqp.txt --bvals=bvals.scheme \
--bvecs=bvecs.scheme --imain=epi.nii --index=epi_index.txt \
--mask=epi_mask.nii --niter=5 --nvoxhp=1000 --out=.../eddy_corrected'
    >>> res = eddy.run() # doctest: +SKIP
    """
    _cmd = 'eddy_openmp'
    input_spec = EddyInputSpec
    output_spec = EddyOutputSpec

    _num_threads = 1

    def __init__(self, **inputs):
        super(Eddy, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, 'num_threads')
        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()
        self.inputs.on_trait_change(self._use_cuda, 'use_cuda')
        if isdefined(self.inputs.use_cuda):
            self._use_cuda()

    def _num_threads_update(self):
        self._num_threads = self.inputs.num_threads
        if not isdefined(self.inputs.num_threads):
            if 'OMP_NUM_THREADS' in self.inputs.environ:
                del self.inputs.environ['OMP_NUM_THREADS']
        else:
            self.inputs.environ['OMP_NUM_THREADS'] = str(
                self.inputs.num_threads)

    def _use_cuda(self):
        self._cmd = 'eddy_cuda' if self.inputs.use_cuda else 'eddy_openmp'

    def _run_interface(self, runtime):
        # If 'eddy_openmp' is missing, use 'eddy'
        FSLDIR = os.getenv('FSLDIR', '')
        cmd = self._cmd
        if all((FSLDIR != '', cmd == 'eddy_openmp',
                not os.path.exists(os.path.join(FSLDIR, 'bin', cmd)))):
            self._cmd = 'eddy'
        runtime = super(Eddy, self)._run_interface(runtime)

        # Restore command to avoid side-effects
        self._cmd = cmd
        return runtime

    def _format_arg(self, name, spec, value):
        if name == 'in_topup_fieldcoef':
            return spec.argstr % value.split('_fieldcoef')[0]
        if name == 'field':
            return spec.argstr % fname_presuffix(value, use_ext=False)
        if name == 'out_base':
            return spec.argstr % os.path.abspath(value)
        return super(Eddy, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_corrected'] = os.path.abspath(
            '%s.nii.gz' % self.inputs.out_base)
        outputs['out_parameter'] = os.path.abspath(
            '%s.eddy_parameters' % self.inputs.out_base)

        # File generation might depend on the version of EDDY
        out_rotated_bvecs = os.path.abspath(
            '%s.eddy_rotated_bvecs' % self.inputs.out_base)
        out_movement_rms = os.path.abspath(
            '%s.eddy_movement_rms' % self.inputs.out_base)
        out_restricted_movement_rms = os.path.abspath(
            '%s.eddy_restricted_movement_rms' % self.inputs.out_base)
        out_shell_alignment_parameters = os.path.abspath(
            '%s.eddy_post_eddy_shell_alignment_parameters' %
            self.inputs.out_base)
        out_shell_pe_translation_parameters = os.path.abspath(
            '%s.eddy_post_eddy_shell_PE_translation_parameters' %
            self.inputs.out_base)
        out_outlier_map = os.path.abspath(
            '%s.eddy_outlier_map' % self.inputs.out_base)
        out_outlier_n_stdev_map = os.path.abspath(
            '%s.eddy_outlier_n_stdev_map' % self.inputs.out_base)
        out_outlier_n_sqr_stdev_map = os.path.abspath(
            '%s.eddy_outlier_n_sqr_stdev_map' % self.inputs.out_base)
        out_outlier_report = os.path.abspath(
            '%s.eddy_outlier_report' % self.inputs.out_base)
        if isdefined(self.inputs.repol) and self.inputs.repol:
            out_outlier_free = os.path.abspath(
                '%s.eddy_outlier_free_data' % self.inputs.out_base)
            if os.path.exists(out_outlier_free):
                outputs['out_outlier_free'] = out_outlier_free
        if isdefined(self.inputs.mporder) and self.inputs.mporder > 0:
            out_movement_over_time = os.path.abspath(
                '%s.eddy_movement_over_time' % self.inputs.out_base)
            if os.path.exists(out_movement_over_time):
                outputs['out_movement_over_time'] = out_movement_over_time
        if isdefined(self.inputs.cnr_maps) and self.inputs.cnr_maps:
            out_cnr_maps = os.path.abspath(
                '%s.eddy_cnr_maps.nii.gz' % self.inputs.out_base)
            if os.path.exists(out_cnr_maps):
                outputs['out_cnr_maps'] = out_cnr_maps
        if isdefined(self.inputs.residuals) and self.inputs.residuals:
            out_residuals = os.path.abspath(
                '%s.eddy_residuals.nii.gz' % self.inputs.out_base)
            if os.path.exists(out_residuals):
                outputs['out_residuals'] = out_residuals

        if os.path.exists(out_rotated_bvecs):
            outputs['out_rotated_bvecs'] = out_rotated_bvecs
        if os.path.exists(out_movement_rms):
            outputs['out_movement_rms'] = out_movement_rms
        if os.path.exists(out_restricted_movement_rms):
            outputs['out_restricted_movement_rms'] = \
                out_restricted_movement_rms
        if os.path.exists(out_shell_alignment_parameters):
            outputs['out_shell_alignment_parameters'] = \
                out_shell_alignment_parameters
        if os.path.exists(out_shell_pe_translation_parameters):
            outputs['out_shell_pe_translation_parameters'] = \
                out_shell_pe_translation_parameters
        if os.path.exists(out_outlier_map):
            outputs['out_outlier_map'] = out_outlier_map
        if os.path.exists(out_outlier_n_stdev_map):
            outputs['out_outlier_n_stdev_map'] = out_outlier_n_stdev_map
        if os.path.exists(out_outlier_n_sqr_stdev_map):
            outputs['out_outlier_n_sqr_stdev_map'] = out_outlier_n_sqr_stdev_map
        if os.path.exists(out_outlier_report):
            outputs['out_outlier_report'] = out_outlier_report

        return outputs
