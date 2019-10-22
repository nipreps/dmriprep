#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""@authors: Derek Pisner, Oscar Estaban, Ariel Rokem"""
from __future__ import division, print_function
import os
import nibabel as nib
import numpy as np


def make_gradient_table(fbval, fbvec, B0_NORM_EPSILON):
    """
    Create gradient table from bval/bvec.
    Parameters
    ----------
    fbval : pathlike or str
        File path of the b-values.
    fbvec : pathlike or str
        File path of the b-vectors.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    gtab : Obj
        DiPy object storing diffusion gradient information.
    b0_ixs : 1d array
        Array containing the indices of the b0s
    """
    from pathlib import Path
    from dipy.io import read_bvals_bvecs
    from dipy.core.gradients import gradient_table

    fbval = Path(fbval)
    fbvec = Path(fbvec)

    # Read b-values and b-vectors from disk Files can be either ‘.bvals’/’.bvecs’ or ‘.txt’ or ‘.npy’ (containing
    # arrays stored with the appropriate values).
    if fbval.exists() and fbvec.exists():
        bvals, bvecs = read_bvals_bvecs(str(fbval), str(fbvec))
    else:
        raise OSError("Either bval or bvec files not found!")

    # Creating the gradient table
    gtab = gradient_table(bvals, bvecs, b0_threshold=B0_NORM_EPSILON)

    b0_ixs = np.where(gtab.b0s_mask == True)[0]

    return gtab, b0_ixs


def make_gradients_tsv(gtab, out_file):
    """
    Save gradient table as RAS-B tsv.

    Parameters
    ----------
    gtab : Obj
        DiPy object storing diffusion gradient information.
    out_file : pathlike or str
        Path to .tsv file containing RAS-B gradient table.
    """
    RASB_table = np.column_stack([gtab.bvecs, gtab.bvals])
    with open(out_file, 'wb') as f:
        f.write(b'R\tA\tS\tB\n')
        np.savetxt(out_file, RASB_table.astype('float'), fmt='%.8f', delimiter="\t")
        f.close()
    return


def save_corrected_bval_bvec(vector_dir, bvec_corrected, bval_corrected, bval_scaling):
    """
    Normalize b-vectors to be of unit length for the non-zero b-values.
    If the b-vector row reflects a B0, the vector is untouched.

    Parameters
    ----------
    vector_dir : str
        Path the output vector directory to save the corrected bval/bvec files.
    bvec_corrected : m x n 2d array
        Corrected b-vectors array.
    bval_corrected : 1d array
        Corrected b-values float array.
    bval_scaling : bool
        If True, then normalizes b-val by the square of the vector amplitude.

    Returns
    -------
    fbval_corrected : pathlike or str
        File path of the corrected b-values.
    fbvec_corrected : pathlike or str
        File path of the corrected b-vectors.
    """
    from pathlib import Path

    fbvec_corrected = str(Path(vector_dir)/'bvec_resc_corr.bvec')
    np.savetxt(fbvec_corrected, bvec_corrected.T.astype('float'), fmt='%.8f')

    if bval_scaling is True:
        fbval_corrected = str(Path(vector_dir) / 'bval_resc_corr.bval')
    else:
        fbval_corrected = str(Path(vector_dir) / 'bval_corr.bval')
    np.savetxt(fbval_corrected, bval_corrected.T.astype('int'), fmt='%d', newline=' ')
    return fbval_corrected, fbvec_corrected


def rescale_bvec(bvec, B0_NORM_EPSILON):
    """
    Normalize b-vectors to be of unit length for the non-zero b-values.
    If the b-vector row reflects a B0, the vector is untouched.

    Parameters
    ----------
    bvec : m x n 2d array
        Raw b-vectors array.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    bvec : m x n 2d array
        Unit-normed b-vectors array.
    """
    axis = int(bvec.shape[0] == 3)
    b0s = np.linalg.norm(bvec) < B0_NORM_EPSILON

    # Rescale b-vecs, skipping b0's, on the appropriate axis to unit-norm length.
    bvec[~b0s] = bvec[~b0s] / np.linalg.norm(bvec[~b0s], axis=axis)
    return bvec


def rescale_bval(bval, bvec, B0_NORM_EPSILON):
    """
    Normalize b-val by the square of the vector amplitude.
    If the b-vector row reflects a B0, the corresponding b-val entry is untouched.

    Parameters
    ----------
    bval : 1d array
        Raw b-values float array.
    bvec : m x n 2d array
        Raw b-vectors array.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    bval : 1d int array
        Vector amplitude square normed b-values array.
    """
    axis = int(bvec.shape[0] == 3)
    b0s_loc = np.where(bval < B0_NORM_EPSILON)

    # Iterate through b-vec rows to perform amplitude correction to each corresponding b-val entry.
    bval = bval.copy()
    for dvol in range(len(bvec)):
        if dvol not in b0s_loc:
            bval[dvol] = bval[dvol] * np.linalg.norm(bvec[dvol], axis=axis)**2
    return np.round(bval, 0)


def is_hemispherical(vecs):
    """
    Determine whether all points on a unit sphere lie in the same hemisphere.

    Parameters
    ----------
    vecs : numpy.ndarray
        2D numpy array with shape (N, 3) where N is the number of points.
        All points must lie on the unit sphere.

    Returns
    -------
    is_hemi : bool
        If True, one can find a hemisphere that contains all the points.
        If False, then the points do not lie in any hemisphere
    pole : numpy.ndarray
        If `is_hemi == True`, then pole is the "central" pole of the
        input vectors. Otherwise, pole is the zero vector.

    References
    ----------
    https://rstudio-pubs-static.s3.amazonaws.com/27121_a22e51b47c544980bad594d5e0bb2d04.html
    """
    import itertools
    if vecs.shape[1] != 3:
        raise ValueError("Input vectors must be 3D vectors")
    if not np.allclose(1, np.linalg.norm(vecs, axis=1)):
        raise ValueError("Input vectors must be unit vectors")

    # Generate all pairwise cross products.
    v0, v1 = zip(*[p for p in itertools.permutations(vecs, 2)])
    cross_prods = np.cross(v0, v1)

    # Normalize them.
    cross_prods /= np.linalg.norm(cross_prods, axis=1)[:, np.newaxis]

    # `cross_prods` now contains all candidate vertex points for "the polygon" in the reference. "The polygon" is a
    # subset. Find which points belong to the polygon using a dot product test with each of the original vectors.
    angles = np.arccos(np.dot(cross_prods, vecs.transpose()))

    # And test whether it is orthogonal or less.
    dot_prod_test = angles <= np.pi / 2.0

    # If there is at least one point that is orthogonal or less to each input vector, then the points lie on some
    # hemisphere.
    is_hemi = len(vecs) in np.sum(dot_prod_test.astype(int), axis=1)

    if is_hemi:
        vertices = cross_prods[np.sum(dot_prod_test.astype(int), axis=1) == len(vecs)]
        pole = np.mean(vertices, axis=0)
        pole /= np.linalg.norm(pole)
    else:
        pole = np.array([0.0, 0.0, 0.0])
    return is_hemi, pole


def set_slm(gtab, is_hemi):
    """
    Evaluate eddy compatibility and set second level model that specifies the mathematical form for how the
    diffusion gradients cause eddy currents. If the data has few directions and/or is has not been sampled on the whole
    sphere it can be advantageous to specify --slm=linear.

    Parameters
    ----------
    gtab : Obj
        DiPy object storing diffusion gradient information.
    is_hemi : bool
        If True, one can find a hemisphere that contains all the points.
        If False, then the points do not lie in any hemisphere.

    Returns
    -------
    slm : str
        Second-level model to use for eddy correction.
    """
    # Warn user if gradient table is not conducive to eddy correction.
    if ((np.sum(np.invert(gtab.b0s_mask)) < 10) and (max(gtab.bvals) < 1500)) or ((np.sum(np.invert(gtab.b0s_mask)) < 30) and (max(gtab.bvals) < 5000)):
        raise UserWarning('Too few directions in this data. Use of eddy is not recommended.')

    if is_hemi is True:
        slm = 'linear'
        print("B-vectors for this data are hemispherical. To ensure adequate eddy current correction, eddy will be run "
              "using the --slm=linear option.")
    elif np.sum(np.invert(gtab.b0s_mask)) < 30:
        slm = 'linear'
        print('Fewer than 30 diffusion-weighted directions detected. To ensure adequate eddy current correction, eddy '
              'will be run using the --slm=linear option')
    else:
        slm = 'none'
    return slm


def check_corruption(bvecs, bvals, B0_NORM_EPSILON):
    """
    Performs a variety of basic check to ensure bval/bvec files are not corrupted.

    Parameters
    ----------
    bvecs : m x n 2d array
        Raw b-vectors array.
    bvals : 1d array
        Raw b-values float array.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    bvecs : m x n 2d array
        Raw b-vectors array.
    bvals : 1d array
        Raw b-values float array.
    """
    # Correct any b0's in bvecs misstated as 10's.
    bvecs[np.where(np.any(abs(bvecs) >= 10, axis=1) == True)] = [1, 0, 0]

    # Check for bval-bvec discrepancy.
    if len(bvecs[np.where(np.logical_and(bvals > B0_NORM_EPSILON, np.where(np.all(abs(bvecs)) == 0)))]) > 0:
        raise ValueError("Corrupted bval/bvecs detected. Check to ensure volumes with a diffusion weighting are not "
                         "listed as B0s in the bvecs.")

    # Ensure that B0's in the bvecs are represented are zero floats.
    bvecs[np.where(bvals < B0_NORM_EPSILON)] = float(0)

    return bvecs, bvals


def rescale_vectors(bvals, bvecs, bval_scaling, bmag, B0_NORM_EPSILON):
    """
    Performs a variety of rescaling routines on the b vectors and values.

    Parameters
    ----------
    bvals : 1d array
        Raw b-values float array.
    bvecs : m x n 2d array
        Raw b-vectors array.
    bval_scaling : bool
        If True, then normalizes b-val by the square of the vector amplitude.
    bmag : int
        The order of magnitude to round the b-values.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    bval_mag_norm : 1d array
        Rescaled b-values float array.
    bvec_rescaled : m x n 2d array
        Rescaled b-vectors array.
    """
    from dipy.core.gradients import round_bvals
    from dmriprep.utils.vectors import rescale_bvec, rescale_bval
    # Rescale bvals by vector amplitudes.
    if bval_scaling is True:
        bvals = rescale_bval(bvals.astype('float'), bvecs.astype('float'), B0_NORM_EPSILON)

    # Round bvals by bmag.
    bval_mag_norm = round_bvals(bvals, bmag=bmag)

    # Rescale bvecs.
    bvec_rescaled = rescale_bvec(bvecs, B0_NORM_EPSILON)
    return bval_mag_norm, bvec_rescaled


def image_gradient_consistency_check(dwi_file, b0_ixs, gtab, n_bvals, bmag):
    """
    Check that b vectors/gradients and dwi image are consistent with one another.

    Parameters
    ----------
    dwi_file : str
        Optionally provide a file path to the diffusion-weighted image series to which the
        bvecs/bvals should correspond.
    b0_ixs : 1d array
        Array containing the indices of the b0s
    gtab : Obj
        DiPy object storing diffusion gradient information.
    n_bvals : int
        Number of bvals (should equate to number of total dwi directions + B0s).
    bmag : int
        The order of magnitude to round the b-values.
    """

    from dipy.reconst.dki import check_multi_b
    check_val = check_multi_b(gtab, n_bvals, non_zero=False, bmag=bmag)
    if check_val is False:
        raise ValueError('Insufficient b-values in gradient table based on the number expected')

    # Check that number of image volumes corresponds to the number of gradient encodings.
    if dwi_file:
        volume_num = nib.load(dwi_file).shape[-1]
        if not len(gtab.bvals) == volume_num:
            raise Exception("Expected %d total image samples but found %d total gradient encoding values", volume_num,
                            len(gtab.bvals))
    return


def checkvecs(fbval, fbvec, sesdir, dwi_file, B0_NORM_EPSILON=50, bval_scaling=True):
    """
    Check b-vectors and b-values alongside diffusion image volume data.

    Parameters
    ----------
    fbval : str
        File path of the b-values.
    fbvec : str
        File path of the b-vectors.
    sesdir : str
        Path the output session directory for derivative dmriprep data.
    dwi_file : str
        Optionally provide a file path to the diffusion-weighted image series to which the
        bvecs/bvals should correspond.
    B0_NORM_EPSILON : float
        Gradient threshold below which volumes and vectors are considered B0's. Default is 50.
    bval_scaling : bool
        If True, then normalizes b-val by the square of the vector amplitude. Default is True.

    Returns
    -------
    gtab : Obj
        DiPy object storing diffusion gradient information.
    is_hemi : bool
        If True, one can find a hemisphere that contains all the points.
        If False, then the points do not lie in any hemisphere.
    pole : numpy.ndarray
        If `is_hemi == True`, then pole is the "central" pole of the
        input vectors. Otherwise, pole is the zero vector.
    b0_ixs : 1d array
        Array containing the indices of the b0s
    slm : str
        Second-level model to use for eddy correction.
    """
    from pathlib import Path
    from dipy.io import read_bvals_bvecs
    from dmriprep.utils.vectors import make_gradient_table, is_hemispherical, check_corruption, save_corrected_bval_bvec, make_gradients_tsv, set_slm

    # Create vector directory if it does not already exist.
    vector_dir = str(Path(sesdir)/'vectors')
    os.makedirs(vector_dir, exist_ok=True)

    # load bvecs/bvals.
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Get b order of magnitude
    bmag = int(np.log10(np.max(bvals))) - 1

    # Perform initial corruption check, correcting for obvious anomalies.
    [bvecs, bvals] = check_corruption(bvecs, bvals, B0_NORM_EPSILON)

    # Perform b vector/value rescaling.
    [bval_mag_norm, bvec_rescaled] = rescale_vectors(bvals, bvecs, bval_scaling, bmag, B0_NORM_EPSILON)

    # Save corrected bval/bvec to file in FSL style to ensure-backwards compatibility.
    [fbval_rescaled, fbvec_rescaled] = save_corrected_bval_bvec(vector_dir, bvec_rescaled, bval_mag_norm, bval_scaling)

    # Make gradient table.
    [gtab, b0_ixs] = make_gradient_table(fbval_rescaled, fbvec_rescaled, B0_NORM_EPSILON)

    # Save gradient table to tsv.
    gtab_tsv_file = str(Path(vector_dir)/'gradients.tsv')
    make_gradients_tsv(gtab, gtab_tsv_file)

    # Check consistency of dwi image and gradient vectors.
    image_gradient_consistency_check(dwi_file, b0_ixs, gtab, len(np.unique(gtab.bvals)), bmag)

    # Check hemisphere coverage.
    [is_hemi, pole] = is_hemispherical(np.round(gtab.bvecs, 8)[~(np.round(gtab.bvecs, 8) == 0).all(1)])

    # Use sampling scheme to set second-level model for eddy correction (this step would conceivably apply to any
    # non-FSL form of eddy correction as well.
    slm = set_slm(gtab, is_hemi)

    return gtab, is_hemi, pole, b0_ixs, gtab_tsv_file, slm
