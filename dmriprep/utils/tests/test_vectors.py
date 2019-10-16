#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@authors: Derek Pisner
"""
import os
import numpy as np
from pathlib import Path
from dmriprep.utils import vectors


def test_make_gtab():
    """
    Test for gradient table generation from bval/bvec
    """
    from dipy.core.gradients import GradientTable
    vector_dir = str(Path(__file__).parent/"data")
    fbval = vector_dir + '/bval'
    fbvec = vector_dir + '/bvec'
    final = False
    b0_thr = 50
    [gtab_file, gtab, final_bval_path, final_bvec_path] = vectors.make_gtab(fbval, fbvec, vector_dir, final, b0_thr)
    assert gtab_file is not None and os.path.isfile(gtab_file)
    assert gtab is not None and gtab.__class__ == GradientTable
    assert gtab.b0_threshold == 50
    assert np.sum(gtab.b0s_mask) == 2
    assert final_bval_path is None and final_bvec_path is None
    os.remove(gtab_file)
    final = True
    [gtab_file, gtab, final_bval_path, final_bvec_path] = vectors.make_gtab(fbval, fbvec, vector_dir, final, b0_thr)
    assert gtab_file is not None and 'final' in gtab_file and os.path.isfile(gtab_file)
    assert gtab is not None and gtab.__class__ == GradientTable
    assert gtab.b0_threshold == 50
    assert np.sum(gtab.b0s_mask) == 2
    assert final_bval_path is not None and final_bvec_path is not None
    os.remove(gtab_file)
    os.remove(final_bval_path)
    os.remove(final_bvec_path)


def test_rescale_bvec():
    """
    Test b-vector rescaling
    """
    vector_dir = str(Path(__file__).parent/"data")
    fbvec = vector_dir + '/bvec'
    bvec = np.genfromtxt(fbvec)
    bvec_rescaled = vectors.rescale_bvec(bvec)
    assert np.max(bvec_rescaled) < 1.0 and np.min(bvec_rescaled) > -1.0
    assert np.sum(np.count_nonzero(bvec.T, axis=1).astype('bool')) == np.sum(np.count_nonzero(bvec_rescaled, axis=1).astype('bool'))


def test_rescale_bval():
    """
    Test b-value rescaling
    """
    vector_dir = str(Path(__file__).parent/"data")
    fbvec = vector_dir + '/bvec'
    bvec = np.genfromtxt(fbvec)
    fbval = vector_dir + '/bval'
    bval = np.genfromtxt(fbval)

    bval_rescaled = vectors.rescale_bval(bval, bvec)

    assert len(bval_rescaled) == len(bval)
    assert np.sum(np.count_nonzero(bval, axis=0).astype('bool')) == np.sum(np.count_nonzero(bval_rescaled, axis=0).astype('bool'))


def test_check_vecs():
    """
    Test routines for vector integrity checking and correction
    """
    from dipy.core.gradients import GradientTable
    sesdir = str(Path(__file__).parent/"data")
    fbval = sesdir + '/bval'
    fbvec = sesdir + '/bvec'
    dwi_file = None

    [gtab_file, gtab, slm] = vectors.checkvecs(fbval, fbvec, sesdir, dwi_file)
    assert gtab_file is not None and os.path.isfile(gtab_file)
    assert gtab is not None and gtab.__class__ == GradientTable
    assert np.sum(gtab.b0s_mask) == 2
    assert slm == 'none'
    os.remove(gtab_file)
