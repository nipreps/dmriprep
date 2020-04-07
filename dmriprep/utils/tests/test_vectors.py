"""Test vector utilities."""
import pytest
import numpy as np
from dmriprep.utils import vectors as v
from collections import namedtuple


def test_corruption(tmpdir, dipy_test_data, monkeypatch):
    """Check whether b-value rescaling is operational."""
    tmpdir.chdir()

    bvals = dipy_test_data['bvals']
    bvecs = dipy_test_data['bvecs']

    dgt = v.DiffusionGradientTable(**dipy_test_data)
    affine = dgt.affine.copy()

    # Test vector hemisphere coverage
    assert np.all(dgt.pole == [0., 0., 0.])

    dgt.to_filename('dwi.tsv')
    dgt = v.DiffusionGradientTable(rasb_file='dwi.tsv')
    assert dgt.normalized is False
    with pytest.raises(TypeError):
        dgt.to_filename('dwi', filetype='fsl')   # You can do this iff the affine is set.

    # check accessing obj.affine
    dgt = v.DiffusionGradientTable(dwi_file=namedtuple('Affine', ['affine'])(affine))
    assert np.all(dgt.affine == affine)
    dgt = v.DiffusionGradientTable(dwi_file=affine)
    assert np.all(dgt.affine == affine)

    # Perform various corruption checks using synthetic corrupted bval-bvec.
    dgt = v.DiffusionGradientTable()
    dgt.bvecs = bvecs
    with pytest.raises(ValueError):
        dgt.bvals = bvals[:-1]

    dgt = v.DiffusionGradientTable()
    dgt.bvals = bvals
    with pytest.raises(ValueError):
        dgt.bvecs = bvecs[:-1]

    # Missing b0
#     bval_no_b0 = bvals.copy()
#     bval_no_b0[0] = 51
#     with pytest.raises(ValueError):
#         dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
#                                        bvals=bval_no_b0, bvecs=bvecs)
#     bvec_no_b0 = bvecs.copy()
#     bvec_no_b0[0] = np.array([1.0, 0.0, 0.0])
#     with pytest.raises(ValueError):
#         dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
#                                        bvals=bvals, bvecs=bvec_no_b0)

    # Corrupt b0 b-val
    bval_odd_b0 = bvals.copy()
    bval_odd_b0[bval_odd_b0 == 0] = 1e-8
    dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
                                   bvals=bval_odd_b0, bvecs=bvecs)
    assert dgt.bvals[0] == 0

    # Corrupt b0 b-vec
    bvec_odd_b0 = bvecs.copy()
    b0mask = np.all(bvec_odd_b0 == 0, axis=1)
    bvec_odd_b0[b0mask] = [10, 10, 10]
    dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
                                   bvals=bvals, bvecs=bvec_odd_b0)
    assert np.all(dgt.bvecs[b0mask] == [0., 0., 0.])

    # Test normalization
    bvecs_factor = 2.0 * bvecs
    dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
                                   bvals=bvals, bvecs=bvecs_factor)
    assert -1.0 <= np.max(np.abs(dgt.gradients[..., :-1])) <= 1.0
    assert dgt.normalized is True

    def mock_func(*args, **kwargs):
        return 'called!'

    with monkeypatch.context() as m:
        m.setattr(v, 'normalize_gradients', mock_func)
        assert dgt.normalize() is None  # Test nothing is executed.

    with monkeypatch.context() as m:
        m.setattr(v, 'bvecs2ras', mock_func)
        assert dgt.generate_vecval() is None  # Test nothing is executed.

    # Miscellaneous tests
    with pytest.raises(ValueError):
        dgt.to_filename('path', filetype='mrtrix')


def test_bval_scheme(dipy_test_data):
    '''basic smoke test'''
    dgt = v.DiffusionGradientTable(**dipy_test_data)

    bval_scheme = v.bval_centers(dgt)

    print(bval_scheme)
    assert len(np.unique(bval_scheme)) == 4
    np.testing.assert_array_equal(bval_scheme.astype(int), dgt.bvals)


class FakeDiffTable():
    ''' just takes the bval input to diff table - for testing more options'''
    def __init__(self, bvals):
        self.bvals = bvals


def test_bval_when_only_b0_present():
    ''' all the weird schemes '''
    all_zeros = np.array([0, 0])
    res_a = v.bval_centers(FakeDiffTable(bvals=all_zeros))
    np.testing.assert_array_equal(res_a, all_zeros)


def test_more_complez_bval():
    bvals_b = [5, 300, 300, 300, 300, 300, 305, 1005, 995, 1000, 1000, 1005, 1000,
               1000, 1005, 995, 1000, 1005, 5, 995, 1000, 1000, 995, 1005, 995, 1000,
               995, 995, 2005, 2000, 2005, 2005, 1995, 2000, 2005, 2000, 1995, 2005, 5,
               1995, 2005, 1995, 1995, 2005, 2005, 1995, 2000, 2000, 2000, 1995, 2000, 2000,
               2005, 2005, 1995, 2005, 2005, 1990, 1995, 1995, 1995, 2005, 2000, 1990, 2010, 5]
    res_b = v.bval_centers(FakeDiffTable(bvals=np.array(bvals_b)))
    assert len(np.unique(res_b)) == 4
    np.testing.assert_allclose(np.unique(res_b), np.array([5., 300.83333333, 999.5, 2000.]))
