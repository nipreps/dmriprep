#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""@authors: Derek Pisner, Oscar Estaban, Ariel Rokem"""
import os
import numpy as np
from pathlib import Path
from dmriprep.utils import vectors


def test_check_vecs():
    """Test CheckVecs interface functionality."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.core.gradients import GradientTable
    from dmriprep.interfaces.vectors import CheckVecs

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    sesdir = join(home, '.dipy', 'sherbrooke_3shell')
    fdwi = join(sesdir, 'HARDI193.nii.gz')
    fbval = join(sesdir, 'HARDI193.bval')
    fbvec = join(sesdir, 'HARDI193.bvec')

    cv = CheckVecs()
    cv.inputs.B0_NORM_EPSILON = 50
    cv.inputs.bval_scaling = True
    cv.inputs.dwi_file = fdwi
    cv.inputs.fbval = fbval
    cv.inputs.fbvec = fbvec
    cv.inputs.sesdir = sesdir

    res = cv.run()

    assert res.outputs.gtab is not None and res.outputs.gtab.__class__ == GradientTable
    assert res.outputs.is_hemi is False
    assert isinstance(res.outputs.pole, (np.ndarray, np.generic)) is True
    assert np.sum(res.outputs.gtab.b0s_mask) == len(res.outputs.b0_ixs)
    assert os.path.isfile(res.outputs.gtab_tsv_file) is True
    assert res.outputs.slm == 'none'


def test_make_and_save_gradient_table():
    """Test for gradient table generation and saving from bval/bvec."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.core.gradients import GradientTable

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    sesdir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(sesdir, 'HARDI193.bval')
    fbvec = join(sesdir, 'HARDI193.bvec')

    b0_thr = 50
    # Create vector directory if it does not already exist.
    vector_dir = str(Path(sesdir)/'vectors')
    os.makedirs(vector_dir, exist_ok=True)
    gtab_tsv_file = str(Path(vector_dir) / 'gradients.tsv')

    [gtab, b0_ixs] = vectors.make_gradient_table(fbval, fbvec, b0_thr)
    vectors.make_gradients_tsv(gtab, gtab_tsv_file)

    assert gtab is not None and gtab.__class__ == GradientTable
    assert gtab.b0_threshold == 50
    assert np.sum(gtab.b0s_mask) == len(b0_ixs)
    assert os.path.isfile(gtab_tsv_file) is True
    os.remove(gtab_tsv_file)


def test_rescale_vectors():
    """Test vector rescaling."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join
    from dipy.io import read_bvals_bvecs

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    sesdir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(sesdir, 'HARDI193.bval')
    fbvec = join(sesdir, 'HARDI193.bvec')

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

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    sesdir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(sesdir, 'HARDI193.bval')
    fbvec = join(sesdir, 'HARDI193.bvec')

    b0_thr = 50

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Perform initial corruption check, correcting for obvious anomalies.
    [bvecs_checked, bvals_checked] = vectors.check_corruption(bvecs, bvals, b0_thr)
    assert bvecs_checked is not None
    assert bvals_checked is not None


def test_hemisphericity():
    """Test vector hemisphere coverage and second-level model setting based on that coverage."""
    from dipy.data import fetch_sherbrooke_3shell
    from os.path import expanduser, join

    fetch_sherbrooke_3shell()
    home = expanduser('~')
    sesdir = join(home, '.dipy', 'sherbrooke_3shell')
    fbval = join(sesdir, 'HARDI193.bval')
    fbvec = join(sesdir, 'HARDI193.bvec')

    b0_thr = 50

    [gtab, _] = vectors.make_gradient_table(fbval, fbvec, b0_thr)

    # Check hemisphere coverage.
    [is_hemi, pole] = vectors.is_hemispherical(np.round(gtab.bvecs, 8)[~(np.round(gtab.bvecs, 8) == 0).all(1)])

    # Use sampling scheme to set second-level model for eddy correction (this step would conceivably apply to any
    # non-FSL form of eddy correction as well.
    slm = vectors.set_slm(gtab, is_hemi)
    assert is_hemi is False
    assert isinstance(pole, (np.ndarray, np.generic)) is True
    assert slm == 'none'