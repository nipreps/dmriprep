#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
from pathlib import Path
from dmriprep.utils import vectors


def test_make_and_save_gradient_table():
    """Test for gradient table generation and saving from bval/bvec."""
    from dipy.data import fetch_sherbrooke_3shell
    from dipy.io import read_bvals_bvecs
    from os.path import expanduser, join
    from dipy.core.gradients import GradientTable

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    basedir = join(home, '.dipy', 'sherbrooke_3shell')
    fdwi = join(basedir, 'HARDI193.nii.gz')
    fbval = join(basedir, 'HARDI193.bval')
    fbvec = join(basedir, 'HARDI193.bvec')

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    b0_thr = 50
    # Create vector directory if it does not already exist.
    vector_dir = str(Path(basedir)/'vectors')
    os.makedirs(vector_dir, exist_ok=True)
    gtab_tsv_file = str(Path(vector_dir) / 'gradients.tsv')

    [gtab, b0_ixs] = vectors.make_gradient_table(bvals, bvecs, b0_thr)
    vectors.write_gradients_tsv(bvecs, bvals, gtab_tsv_file)

    [bvals_read, bvecs_read] = vectors.read_gradients_tsv(gtab_tsv_file)

    assert gtab is not None and gtab.__class__ == GradientTable
    assert gtab.b0_threshold == 50
    assert np.sum(gtab.b0s_mask) == len(b0_ixs)
    assert os.path.isfile(gtab_tsv_file) is True
    assert np.isclose(bvecs_read.all(), bvecs.all())
    assert np.isclose(bvals_read.all(), bvals.all())
    os.remove(gtab_tsv_file)


def test_rescale_vectors():
    """Test vector rescaling."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.io import read_bvals_bvecs

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    basedir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(basedir, 'HARDI193.bval')
    fbvec = join(basedir, 'HARDI193.bvec')

    bval_scaling = True
    b0_thr = 50

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Get b order of magnitude
    bmag = int(np.log10(np.max(bvals))) - 1

    [bval_normed, bvec_normed] = vectors.rescale_vectors(bvals, bvecs, bval_scaling, bmag, b0_thr)
    assert np.max(bvec_normed) < 1.0 and np.min(bvec_normed) > -1.0
    assert len(bvecs) == len(bvec_normed)
    assert np.sum(np.count_nonzero(bvecs, axis=1).astype('bool')) == np.sum(np.count_nonzero(bvec_normed,
                                                                                               axis=1).astype('bool'))
    assert len(bvals) == len(bval_normed)
    assert np.sum(np.count_nonzero(bvals, axis=0).astype('bool')) == np.sum(np.count_nonzero(bval_normed,
                                                                                             axis=0).astype('bool'))


def test_vector_checkers():
    """Test for vector corruption."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.io import read_bvals_bvecs
    import itertools

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    basedir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(basedir, 'HARDI193.bval')
    fbvec = join(basedir, 'HARDI193.bvec')

    b0_thr = 50

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Perform various corruption checks using synthetic corrupted bval-bvec.
    bval_short = bvals[:-1]
    bval_long = np.hstack([bvals, bvals[-1]])
    bval_no_b0 = bvals.copy()
    bval_no_b0[0] = 51
    bval_odd_b0 = bvals.copy()
    bval_odd_b0[np.where(abs(bval_odd_b0) == 0)] = 0.00000001
    bvec_short = bvecs[:-1]
    bvec_long = np.vstack([bvecs, 0.5*bvecs[-1]])
    bvec_no_b0 = bvecs.copy()
    bvec_no_b0[np.where(np.all(abs(bvec_no_b0) == 0, axis=1) == True)] = [1, 1, 1]
    bvec_odd_b0 = bvecs.copy()
    bvec_odd_b0[np.where(np.all(abs(bvec_odd_b0) == 0, axis=1) == True)] = [10, 10, 10]

    bval_lists = [bvals, bval_short, bval_long, bval_no_b0, bval_odd_b0]
    bvec_lists = [bvecs, bvec_short, bvec_long, bvec_no_b0, bvec_odd_b0]
    for bval, bvec in list(itertools.product(bval_lists, bvec_lists)):
        [bvecs_checked, bvals_checked] = vectors.check_corruption(bvec, bval, b0_thr)
        if (bval is bvals) and (bvec is bvecs):
            assert bvecs_checked is not None
            assert bvals_checked is not None
        else:
            with pytest.raises(Exception) as e_info:
                assert bvecs_checked is None
                assert bvals_checked is None


def test_hemisphericity():
    """Test vector hemisphere coverage and second-level model setting based on that coverage."""
    from dipy.data import fetch_sherbrooke_3shell
    from dipy.io import read_bvals_bvecs
    from os.path import expanduser, join

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    basedir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(basedir, 'HARDI193.bval')
    fbvec = join(basedir, 'HARDI193.bvec')

    b0_thr = 50

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
    [gtab, _] = vectors.make_gradient_table(bvals, bvecs, b0_thr)

    # Check hemisphere coverage.
    [is_hemi, pole] = vectors.is_hemispherical(np.round(gtab.bvecs, 8)[~(np.round(gtab.bvecs, 8) == 0).all(1)])

    # Use sampling scheme to set second-level model for eddy correction (this step would conceivably apply to any
    # non-FSL form of eddy correction as well.
    slm = vectors.set_slm(gtab, is_hemi)
    assert is_hemi is False
    assert isinstance(pole, (np.ndarray, np.generic)) is True
    assert slm == 'none'


def test_clean_vecs():
    """Test CleanVecs interface functionality."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.core.gradients import GradientTable
    from dmriprep.interfaces.vectors import CleanVecs
    import itertools

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    basedir = join(home, '.dipy', 'sherbrooke_3shell')
    fdwi = join(basedir, 'HARDI193.nii.gz')
    fbval = join(basedir, 'HARDI193.bval')
    fbvec = join(basedir, 'HARDI193.bvec')

    # Smoke test parameter combos
    for bool_list in list(itertools.product([True, False], repeat=3)):
        cv = CleanVecs()
        cv.inputs.B0_NORM_EPSILON = 50
        cv.inputs.bval_scaling = bool_list[0]
        cv.inputs.rescale = bool_list[1]
        cv.inputs.save_fsl_style = bool_list[2]
        cv.inputs.dwi_file = fdwi
        cv.inputs.fbval = fbval
        cv.inputs.fbvec = fbvec
        cv.inputs.basedir = basedir

        res = cv.run()

        assert res.outputs.gtab is not None and res.outputs.gtab.__class__ == GradientTable
        assert res.outputs.is_hemi is False
        assert isinstance(res.outputs.pole, (np.ndarray, np.generic)) is True
        assert np.sum(res.outputs.gtab.b0s_mask) == len(res.outputs.b0_ixs)
        assert os.path.isfile(res.outputs.rasb_tsv_out_file) is True
        if cv.inputs.save_fsl_style is True:
            assert os.path.isfile(res.outputs.fbval_out_file) is True
            assert os.path.isfile(res.outputs.fbvec_out_file) is True
            os.remove(res.outputs.fbval_out_file)
            os.remove(res.outputs.fbvec_out_file)
        assert res.outputs.slm == 'none'
        os.remove(res.outputs.rasb_tsv_out_file)
