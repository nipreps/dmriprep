"""Handling the gradient table."""
from pathlib import Path
import numpy as np
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (
    SimpleInterface, BaseInterfaceInputSpec, TraitedSpec,
    File, traits, isdefined
)
from ..utils.vectors import DiffusionGradientTable, reorient_vecs_from_ras_b, \
    B0_THRESHOLD, BVEC_NORM_EPSILON


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


def _undefined(objekt, name, default=None):
    value = getattr(objekt, name)
    if not isdefined(value):
        return default
    return value


class _ReorientVectorsInputSpec(BaseInterfaceInputSpec):
    in_rasb = File(exists=True)
    affines = traits.Array()
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
        rasb_file = _undefined(self.inputs, 'in_rasb')

        reor_table = reorient_vecs_from_ras_b(
            rasb_file=rasb_file,
            affines=self.inputs.affines,
            b0_threshold=self.inputs.b0_threshold,
        )

        cwd = Path(runtime.cwd).absolute()
        reor_rasb_file = fname_presuffix(
            self.inputs.in_rasb, use_ext=False, suffix='_reoriented.tsv',
            newpath=str(cwd))
        np.savetxt(str(reor_rasb_file), reor_table,
                   delimiter='\t', header='\t'.join('RASB'),
                   fmt=['%.8f'] * 3 + ['%g'])

        self._results['out_rasb'] = reor_rasb_file
        return runtime
