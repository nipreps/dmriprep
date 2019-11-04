"""Test vector utilities."""
import pytest
import numpy as np
from dmriprep.utils import vectors as v


def test_corruption(dipy_test_data):
    """Check whether b-value rescaling is operational."""

    bvecs = np.loadtxt(dipy_test_data['bvecs']).T
    bvals = np.loadtxt(dipy_test_data['bvals'])

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
    bval_no_b0 = bvals.copy()
    bval_no_b0[0] = 51
    with pytest.raises(ValueError):
        dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
                                       bvals=bval_no_b0, bvecs=bvecs)
    bvec_no_b0 = bvecs.copy()
    bvec_no_b0[0] = np.array([1.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        dgt = v.DiffusionGradientTable(dwi_file=dipy_test_data['dwi_file'],
                                       bvals=bvals, bvecs=bvec_no_b0)

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


def test_hemisphericity(dipy_test_data):
    """Test vector hemisphere coverage."""

    dgt = v.DiffusionGradientTable(**dipy_test_data)
    assert np.all(dgt.pole == [0., 0., 0.])
