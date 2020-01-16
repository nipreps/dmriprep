"""Handling the gradient table."""
import os
from pathlib import Path
import numpy as np
import pandas as pd
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (
    SimpleInterface, BaseInterfaceInputSpec, TraitedSpec,
    File, traits, isdefined, InputMultiObject
)
from ..utils.vectors import DiffusionGradientTable, reorient_vecs_from_ras_b, B0_THRESHOLD, BVEC_NORM_EPSILON
from subprocess import Popen, PIPE

def _undefined(objekt, name, default=None):
    value = getattr(objekt, name)
    if not isdefined(value):
        return default
    return value


class _CheckGradientTableInputSpec(BaseInterfaceInputSpec):
    dwi_file = File(exists=True, mandatory=True)
    in_bvec = File(exists=True, xor=['in_rasb'])
    in_bval = File(exists=True, xor=['in_rasb'])
    in_rasb = File(exists=True, xor=['in_bval', 'in_bvec'])
    b0_threshold = traits.Float(B0_THRESHOLD, usedefault=True)
    bvec_norm_epsilon = traits.Float(BVEC_NORM_EPSILON, usedefault=True)
    b_scale = traits.Bool(True, usedefault=True)


class _CheckGradientTableOutputSpec(TraitedSpec):
    out_rasb = File(exists=True)
    out_bval = File(exists=True)
    out_bvec = File(exists=True)
    full_sphere = traits.Bool()
    pole = traits.Tuple(traits.Float, traits.Float, traits.Float)
    b0_ixs = traits.List(traits.Int)


class CheckGradientTable(SimpleInterface):
    """
    Ensure the correctness of the gradient table.

    Example
    -------

    >>> os.chdir(tmpdir)
    >>> check = CheckGradientTable(
    ...     dwi_file=str(data_dir / 'dwi.nii.gz'),
    ...     in_rasb=str(data_dir / 'dwi.tsv')).run()
    >>> check.outputs.pole
    (0.0, 0.0, 0.0)
    >>> check.outputs.full_sphere
    True

    >>> check = CheckGradientTable(
    ...     dwi_file=str(data_dir / 'dwi.nii.gz'),
    ...     in_bvec=str(data_dir / 'bvec'),
    ...     in_bval=str(data_dir / 'bval')).run()
    >>> check.outputs.pole
    (0.0, 0.0, 0.0)
    >>> check.outputs.full_sphere
    True
    >>> newrasb = np.loadtxt(check.outputs.out_rasb, skiprows=1)
    >>> oldrasb = np.loadtxt(str(data_dir / 'dwi.tsv'), skiprows=1)
    >>> np.allclose(newrasb, oldrasb, rtol=1.e-3)
    True

    """

    input_spec = _CheckGradientTableInputSpec
    output_spec = _CheckGradientTableOutputSpec

    def _run_interface(self, runtime):
        rasb_file = _undefined(self.inputs, 'in_rasb')

        table = DiffusionGradientTable(
            self.inputs.dwi_file,
            bvecs=_undefined(self.inputs, 'in_bvec'),
            bvals=_undefined(self.inputs, 'in_bval'),
            rasb_file=rasb_file,
            b_scale=self.inputs.b_scale,
            bvec_norm_epsilon=self.inputs.bvec_norm_epsilon,
            b0_threshold=self.inputs.b0_threshold,
        )
        pole = table.pole
        self._results['pole'] = tuple(pole)
        self._results['full_sphere'] = np.all(pole == 0.0)
        self._results['b0_ixs'] = np.where(table.b0mask)[0].tolist()

        cwd = Path(runtime.cwd).absolute()
        if rasb_file is None:
            rasb_file = fname_presuffix(
                self.inputs.dwi_file, use_ext=False, suffix='.tsv',
                newpath=str(cwd))
            table.to_filename(rasb_file)
        self._results['out_rasb'] = rasb_file
        table.to_filename('%s/dwi' % cwd, filetype='fsl')
        self._results['out_bval'] = str(cwd / 'dwi.bval')
        self._results['out_bvec'] = str(cwd / 'dwi.bvec')
        return runtime


class _ReorientVectorsInputSpec(BaseInterfaceInputSpec):
    rasb_file = File(exists=True)
    affines = traits.List()
    b0_threshold = traits.Float(B0_THRESHOLD, usedefault=True)


class _ReorientVectorsOutputSpec(TraitedSpec):
    out_rasb = File(exists=True)


class ReorientVectors(SimpleInterface):
    """
    Reorient Vectors
    Example
    -------
    >>> os.chdir(tmpdir)
    >>> oldrasb = str(data_dir / 'dwi.tsv')
    >>> oldrasb_mat = np.loadtxt(str(data_dir / 'dwi.tsv'), skiprows=1)
    >>> # The simple case: all affines are identity
    >>> affine_list = np.zeros((len(oldrasb_mat[:, 3][oldrasb_mat[:, 3] != 0]), 4, 4))
    >>> for i in range(4):
    >>>     affine_list[:, i, i] = 1
    >>>     reor_vecs = ReorientVectors()
    >>> reor_vecs = ReorientVectors()
    >>> reor_vecs.inputs.affines = affine_list
    >>> reor_vecs.inputs.in_rasb = oldrasb
    >>> res = reor_vecs.run()
    >>> out_rasb = res.outputs.out_rasb
    >>> out_rasb_mat = np.loadtxt(out_rasb, skiprows=1)
    >>> npt.assert_equal(oldrasb_mat, out_rasb_mat)
    True
    """

    input_spec = _ReorientVectorsInputSpec
    output_spec = _ReorientVectorsOutputSpec

    def _run_interface(self, runtime):
        from nipype.utils.filemanip import fname_presuffix
        reor_table = reorient_vecs_from_ras_b(
            rasb_file=self.inputs.rasb_file,
            affines=self.inputs.affines,
            b0_threshold=self.inputs.b0_threshold,
        )

        cwd = Path(runtime.cwd).absolute()
        reor_rasb_file = fname_presuffix(
            self.inputs.rasb_file, use_ext=False, suffix='_reoriented.tsv',
            newpath=str(cwd))
        np.savetxt(str(reor_rasb_file), reor_table,
                   delimiter='\t', header='\t'.join('RASB'),
                   fmt=['%.8f'] * 3 + ['%g'])

        self._results['out_rasb'] = reor_rasb_file
        return runtime


def get_fsl_motion_params(itk_file, src_file, ref_file, working_dir):
    tmp_fsl_file = fname_presuffix(itk_file, newpath=working_dir,
                                   suffix='_FSL.xfm', use_ext=False)
    fsl_convert_cmd = "c3d_affine_tool " \
        "-ref {ref_file} " \
        "-src {src_file} " \
        "-itk {itk_file} " \
        "-ras2fsl -o {fsl_file}".format(
            src_file=src_file, ref_file=ref_file, itk_file=itk_file,
            fsl_file=tmp_fsl_file)
    os.system(fsl_convert_cmd)
    proc = Popen(['avscale', '--allparams', tmp_fsl_file, src_file], stdout=PIPE,
                 stderr=PIPE)
    stdout, _ = proc.communicate()

    def get_measures(line):
        line = line.strip().split()
        return np.array([float(num) for num in line[-3:]])

    lines = stdout.decode("utf-8").split("\n")
    flip = np.array([1, -1, -1])
    rotation = get_measures(lines[6]) * flip
    translation = get_measures(lines[8]) * flip
    scale = get_measures(lines[10])
    shear = get_measures(lines[12])

    return np.concatenate([scale, shear, rotation, translation])


class CombineMotionsInputSpec(BaseInterfaceInputSpec):
    transform_files = InputMultiObject(File(exists=True), mandatory=True,
                                       desc='transform files from hmc')
    source_files = InputMultiObject(File(exists=True), mandatory=True,
                                    desc='Moving images')
    ref_file = File(exists=True, mandatory=True, desc='Fixed Image')


class CombineMotionsOututSpec(TraitedSpec):
    motion_file = File(exists=True)
    spm_motion_file = File(exists=True)


class CombineMotions(SimpleInterface):
    input_spec = CombineMotionsInputSpec
    output_spec = CombineMotionsOututSpec

    def _run_interface(self, runtime):
        collected_motion = []
        output_fname = os.path.join(runtime.cwd, "motion_params.csv")
        output_spm_fname = os.path.join(runtime.cwd, "spm_movpar.txt")
        ref_file = self.inputs.ref_file
        for motion_file, src_file in zip(self.inputs.transform_files,
                                         self.inputs.source_files):
            collected_motion.append(
                get_fsl_motion_params(motion_file, src_file, ref_file, runtime.cwd))

        final_motion = np.row_stack(collected_motion)
        cols = ["scaleX", "scaleY", "scaleZ", "shearXY", "shearXZ",
                "shearYZ", "rotateX", "rotateY", "rotateZ", "shiftX", "shiftY",
                "shiftZ"]
        motion_df = pd.DataFrame(data=final_motion, columns=cols)
        motion_df.to_csv(output_fname, index=False)
        self._results['motion_file'] = output_fname

        spmcols = motion_df[['shiftX', 'shiftY', 'shiftZ', 'rotateX', 'rotateY', 'rotateZ']]
        self._results['spm_motion_file'] = output_spm_fname
        np.savetxt(output_spm_fname, spmcols.values)

        return runtime
