#!/usr/bin/env python

from __future__ import (
    print_function,
    division,
    unicode_literals,
    absolute_import,
)

from builtins import str

import os
import numpy as np
import nibabel as nb
import warnings

from nipype.interfaces.base import traits, TraitedSpec, InputMultiPath, File, isdefined
from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec, Info

class EddyInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='--imain=%s',
        desc=('File containing all the images to estimate '
              'distortions for'))
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
        desc=('File containing the b-vectors for all volumes in '
              '--imain'))
    in_bval = File(
        exists=True,
        mandatory=True,
        argstr='--bvals=%s',
        desc=('File containing the b-values for all volumes in '
              '--imain'))
    out_base = traits.Str(
        'eddy_corrected',
        argstr='--out=%s',
        usedefault=True,
        desc=('basename for output (warped) image'))
    session = File(
        exists=True,
        argstr='--session=%s',
        desc=('File containing session indices for all volumes in '
              '--imain'))
    in_topup_fieldcoef = File(
        #exists=True,
        argstr="--topup=%s",
        requires=['in_topup_movpar'],
        desc=('topup file containing the field '
              'coefficients'))
    in_topup_movpar = File(
        exists=True,
        requires=['in_topup_fieldcoef'],
        desc='topup movpar.txt file')

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

    fep = traits.Bool(
        False, argstr='--fep', desc='Fill empty planes in x- or y-directions')

    interp = traits.Enum(
        'spline',
        'trilinear',
        argstr='--interp=%s',
        desc='Interpolation model for estimation step')

    nvoxhp = traits.Int(
        1000, usedefault=True,
        argstr='--nvoxhp=%s',
        desc=('# of voxels used to estimate the '
              'hyperparameters'))

    fudge_factor = traits.Float(
        10.0, usedefault=True,
        argstr='--ff=%s',
        desc=('Fudge factor for hyperparameter '
              'error variance'))

    dont_sep_offs_move = traits.Bool(
        False,
        argstr='--dont_sep_offs_move',
        desc=('Do NOT attempt to separate '
              'field offset from subject '
              'movement'))

    dont_peas = traits.Bool(
        False,
        argstr='--dont_peas',
        desc="Do NOT perform a post-eddy alignment of "
        "shells")

    fwhm = traits.Float(
        desc=('FWHM for conditioning filter when estimating '
              'the parameters'),
        argstr='--fwhm=%s')

    niter = traits.Int(5, usedefault=True,
                       argstr='--niter=%s', desc='Number of iterations')

    method = traits.Enum(
        'jac',
        'lsr',
        argstr='--resamp=%s',
        desc=('Final resampling method (jacobian/least '
              'squares)'))
    repol = traits.Bool(
        False, argstr='--repol', desc='Detect and replace outlier slices')
    num_threads = traits.Int(
        1,
        usedefault=True,
        nohash=True,
        desc="Number of openmp threads to use")
    is_shelled = traits.Bool(
        False,
        argstr='--data_is_shelled',
        desc="Override internal check to ensure that "
        "date are acquired on a set of b-value "
        "shells")
    field = traits.Str(
        argstr='--field=%s',
        desc="NonTOPUP fieldmap scaled in Hz - filename has "
        "to be provided without an extension. TOPUP is "
        "strongly recommended")
    field_mat = File(
        exists=True,
        argstr='--field_mat=%s',
        desc="Matrix that specifies the relative locations of "
        "the field specified by --field and first volume "
        "in file --imain")
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
        desc=('text file with parameters definining the field and'
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
        desc=('File containing rigid body movement parameters '
              'between the different shells as estimated by a '
              'post-hoc mutual information based registration'))
    out_outlier_report = File(
        exists=True,
        desc=('Text-file with a plain language report on what '
              'outlier slices eddy has found'))
    out_cnr_maps = File(
        exists=True, desc='path/name of file with the cnr_maps')
    out_residuals = File(
        exists=True, desc='path/name of file with the residuals')


class Eddy(FSLCommand):
    """
    Interface for FSL eddy, a tool for estimating and correcting eddy
    currents induced distortions. `User guide
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Eddy/UsersGuide>`_ and
    `more info regarding acqp file
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/Faq#How_do_I_know_what_to_put_into_my_--acqp_file>`_.
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
    'eddy_cuda --ff=10.0 --acqp=epi_acqp.txt --bvals=bvals.scheme \
--bvecs=bvecs.scheme --imain=epi.nii --index=epi_index.txt \
--mask=epi_mask.nii --niter=5 --nvoxhp=1000 --out=.../eddy_corrected'
    >>> eddy.inputs.use_cuda = False
    >>> eddy.cmdline # doctest: +ELLIPSIS
    'eddy_openmp --ff=10.0 --acqp=epi_acqp.txt --bvals=bvals.scheme \
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
        out_outlier_report = os.path.abspath(
            '%s.eddy_outlier_report' % self.inputs.out_base)
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
        if os.path.exists(out_outlier_report):
            outputs['out_outlier_report'] = out_outlier_report

        return outputs

class EddyQuadInputSpec(FSLCommandInputSpec):
    base_name = traits.Str(
        'eddy_corrected',
        usedefault=True,
        argstr='%s',
        desc=("Basename (including path) for EDDY output files, i.e., "
              "corrected images and QC files"),
        position=0,
    )
    idx_file = File(
        exists=True,
        mandatory=True,
        argstr="--eddyIdx %s",
        desc=("File containing indices for all volumes into acquisition "
              "parameters")
    )
    param_file = File(
        exists=True,
        mandatory=True,
        argstr="--eddyParams %s",
        desc="File containing acquisition parameters"
    )
    mask_file = File(
        exists=True,
        mandatory=True,
        argstr="--mask %s",
        desc="Binary mask file"
    )
    bval_file = File(
        exists=True,
        mandatory=True,
        argstr="--bvals %s",
        desc="b-values file"
    )
    bvec_file = File(
        exists=True,
        argstr="--bvecs %s",
        desc=("b-vectors file - only used when <base_name>.eddy_residuals "
              "file is present")
    )
    output_dir = traits.Str(
        name_template='%s.qc',
        name_source=['base_name'],
        argstr='--output-dir %s',
        desc="Output directory - default = '<base_name>.qc'",
    )
    field = File(
        exists=True,
        argstr='--field %s',
        desc="TOPUP estimated field (in Hz)",
    )
    slice_spec = File(
        exists=True,
        argstr='--slspec %s',
        desc="Text file specifying slice/group acquisition",
    )
    verbose = traits.Bool(
        argstr='--verbose',
        desc="Display debug messages",
    )


class EddyQuadOutputSpec(TraitedSpec):
    qc_json = File(
        exists=True,
        desc=("Single subject database containing quality metrics and data "
              "info.")
    )
    qc_pdf = File(
        exists=True,
        desc="Single subject QC report."
    )
    avg_b_png = traits.List(
        File(exists=True),
        desc=("Image showing mid-sagittal, -coronal and -axial slices of "
              "each averaged b-shell volume.")
    )
    avg_b0_pe_png = traits.List(
        File(exists=True),
        desc=("Image showing mid-sagittal, -coronal and -axial slices of "
              "each averaged pe-direction b0 volume. Generated when using "
              "the -f option.")
    )
    cnr_png = traits.List(
        File(exists=True),
        desc=("Image showing mid-sagittal, -coronal and -axial slices of "
              "each b-shell CNR volume. Generated when CNR maps are "
              "available.")
    )
    vdm_png = File(
        exists=True,
        desc=("Image showing mid-sagittal, -coronal and -axial slices of "
              "the voxel displacement map. Generated when using the -f "
              "option.")
    )
    residuals = File(
        exists=True,
        desc=("Text file containing the volume-wise mask-averaged squared "
              "residuals. Generated when residual maps are available.")
    )
    clean_volumes = File(
        exists=True,
        desc=("Text file containing a list of clean volumes, based on "
              "the eddy squared residuals. To generate a version of the "
              "pre-processed dataset without outlier volumes, use: "
              "`fslselectvols -i <eddy_corrected_data> -o "
              "eddy_corrected_data_clean --vols=vols_no_outliers.txt`")
    )


class EddyQuad(FSLCommand):
    """
    Interface for FSL eddy_quad, a tool for generating single subject reports
    and storing the quality assessment indices for each subject.
    `User guide <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddyqc/UsersGuide>`_
    Examples
    --------
    >>> from nipype.interfaces.fsl import EddyQuad
    >>> quad = EddyQuad()
    >>> quad.inputs.base_name  = 'eddy_corrected'
    >>> quad.inputs.idx_file   = 'epi_index.txt'
    >>> quad.inputs.param_file = 'epi_acqp.txt'
    >>> quad.inputs.mask_file  = 'epi_mask.nii'
    >>> quad.inputs.bval_file  = 'bvals.scheme'
    >>> quad.inputs.bvec_file  = 'bvecs.scheme'
    >>> quad.inputs.output_dir = 'eddy_corrected.qc'
    >>> quad.inputs.field      = 'fieldmap_phase_fslprepared.nii'
    >>> quad.inputs.verbose    = True
    >>> quad.cmdline
    'eddy_quad eddy_corrected --bvals bvals.scheme --bvecs bvecs.scheme \
--field fieldmap_phase_fslprepared.nii --eddyIdx epi_index.txt \
--mask epi_mask.nii --output-dir eddy_corrected.qc --eddyParams epi_acqp.txt \
--verbose'
    >>> res = quad.run() # doctest: +SKIP
    """
    _cmd = 'eddy_quad'
    input_spec = EddyQuadInputSpec
    output_spec = EddyQuadOutputSpec

    def _list_outputs(self):
        from glob import glob
        outputs = self.output_spec().get()

        # If the output directory isn't defined, the interface seems to use
        # the default but not set its value in `self.inputs.output_dir`
        if not isdefined(self.inputs.output_dir):
            out_dir = os.path.abspath(os.path.basename(self.inputs.base_name) + '.qc')
        else:
            out_dir = os.path.abspath(self.inputs.output_dir)

        outputs['qc_json'] = os.path.join(out_dir, 'qc.json')
        outputs['qc_pdf'] = os.path.join(out_dir, 'qc.pdf')

        # Grab all b* files here. This will also grab the b0_pe* files
        # as well, but only if the field input was provided. So we'll remove
        # them later in the next conditional.
        outputs['avg_b_png'] = sorted(glob(
            os.path.join(out_dir, 'avg_b*.png')
        ))

        if isdefined(self.inputs.field):
            outputs['avg_b0_pe_png'] = sorted(glob(
                os.path.join(out_dir, 'avg_b0_pe*.png')
            ))

            # The previous glob for `avg_b_png` also grabbed the
            # `avg_b0_pe_png` files so we have to remove them
            # from `avg_b_png`.
            for fname in outputs['avg_b0_pe_png']:
                outputs['avg_b_png'].remove(fname)

            outputs['vdm_png'] = os.path.join(out_dir, 'vdm.png')

        outputs['cnr_png'] = sorted(glob(os.path.join(out_dir, 'cnr*.png')))

        residuals = os.path.join(out_dir, 'eddy_msr.txt')
        if os.path.isfile(residuals):
            outputs['residuals'] = residuals

        clean_volumes = os.path.join(out_dir, 'vols_no_outliers.txt')
        if os.path.isfile(clean_volumes):
            outputs['clean_volumes'] = clean_volumes

        return outputs
