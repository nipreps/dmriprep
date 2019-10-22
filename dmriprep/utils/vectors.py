from __future__ import division, print_function
import os
import nibabel as nib
import numpy as np


def make_gtab(fbval, fbvec, vector_dir, final, b0_thr=50):
    """
    Create gradient table from bval/bvec.

    Parameters
    ----------
    fbval : str
        File path of the b-values.
    fbvec : str
        File path of the b-vectors.
    vector_dir : str
        Path to vectors directory in subject output.
    final : bool
        Indicates whether to flag the output gradient
    b0_thr : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    gtab_file : str
        File path to pickled DiPy gradient table object.
    gtab : Obj
        DiPy object storing diffusion gradient information.
    final_fbval : str
        File path of saved final b-values if `final` is True.
    final_fbvec : str
        File path of saved final b-vectors if `final` is True.
    """
    import os
    from dipy.io import save_pickle, read_bvals_bvecs
    from dipy.core.gradients import gradient_table

    # Read b-values and b-vectors from disk
    # Files can be either ‘.bvals’/’.bvecs’ or ‘.txt’ or ‘.npy’ (containing
    # arrays stored with the appropriate values).
    if fbval and fbvec:
        bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
    else:
        raise OSError("Either bvals or bvecs files not found (or rescaling failed)!")

    # Creating the gradient table
    gtab = gradient_table(bvals, bvecs, b0_threshold=b0_thr)

    # Show info
    print(gtab.info)

    # Save bval/bvec text file equivalents in the case that these are the final
    # versions of our gradient vectors
    if final is True:
        final_bval_path = "%s%s" % (vector_dir, '/final_bval.bval')
        final_bvec_path = "%s%s" % (vector_dir, '/final_bvec.bvec')
        np.savetxt(final_bval_path, bvals.astype('int'), fmt='%d', newline=' ')
        np.savetxt(final_bvec_path, bvecs.T.astype('float'), fmt='%8f')
        # Save gradient table to pickle
        gtab_file = "%s%s" % (vector_dir, "/gtab_final.pkl")
        save_pickle(gtab_file, gtab)
    else:
        def next_path(path_pattern):
            i = 1
            while os.path.exists(path_pattern % i):
                i = i * 2
            a, b = (i // 2, i)
            while a + 1 < b:
                c = (a + b) // 2 # interval midpoint
                a, b = (c, b) if os.path.exists(path_pattern % c) else (a, c)
            return path_pattern % b
        # Save gradient table to pickle
        gtab_file = next_path(vector_dir + "/gtab_%s.pkl")
        save_pickle(gtab_file, gtab)
        final_bval_path = None
        final_bvec_path = None

    return gtab_file, gtab, final_bval_path, final_bvec_path


def rescale_bvec(bvec):
    """
    Normalizes b-vectors to be of unit length for the non-zero b-values. If the
    b-vector row reflect a B0, the vector is untouched.

    Parameters
    ----------
    bvec : m x n 2d array
        Raw b-vectors array.

    Returns
    -------
    bvec_rescaled : m x n 2d array
        Unit-normed b-vectors array.
    """
    # Enforce proper dimensions
    bvec = bvec.T if bvec.shape[0] == 3 else bvec

    # Normalize values not close to norm 1
    bvec = [b / np.linalg.norm(b) if not np.isclose(np.linalg.norm(b), 0) else b for b in bvec]
    norms = np.linalg.norm(bvec, axis=-1)
    norms[np.isclose(norms, 0)] = 1
    bvec_rescaled = bvec / norms[:, None]
    return bvec_rescaled


def rescale_bval(bval, bvec):
    """
    Normalizes b-val by the square of the vector amplitude.

    Parameters
    ----------
    bval : 1d array
        Raw b-values float array.
    bvec : m x n 2d array
        Raw b-vectors array.

    Returns
    -------
    bval_rescaled : 1d int array
        Vector amplitude square normed b-values array.
    """
    # Enforce proper dimensions
    bvec = bvec.T if bvec.shape[0] == 3 else bvec

    bval_rescaled = bval.copy()
    for dvol in range(len(bvec)):
        bval_rescaled[dvol] = bval[dvol] * np.linalg.norm(bvec[dvol])**2

    return np.round(bval_rescaled, 0)


def is_hemispherical(vecs):
    """
    Test whether all points on a unit sphere lie in the same hemisphere.

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

    # Generate all pairwise cross products
    v0, v1 = zip(*[p for p in itertools.permutations(vecs, 2)])
    cross_prods = np.cross(v0, v1)

    # Normalize them
    cross_prods /= np.linalg.norm(cross_prods, axis=1)[:, np.newaxis]

    # `cross_prods` now contains all candidate vertex points for "the polygon"
    # in the reference. "The polygon" is a subset. Find which points belong to
    # the polygon using a dot product test with each of the original vectors
    angles = np.arccos(np.dot(cross_prods, vecs.transpose()))

    # And test whether it is orthogonal or less
    dot_prod_test = angles <= np.pi / 2.0

    # If there is at least one point that is orthogonal or less to each
    # input vector, then the points lie on some hemisphere
    is_hemi = len(vecs) in np.sum(dot_prod_test.astype(int), axis=1)

    if is_hemi:
        vertices = cross_prods[
            np.sum(dot_prod_test.astype(int), axis=1) == len(vecs)
        ]
        pole = np.mean(vertices, axis=0)
        pole /= np.linalg.norm(pole)
    else:
        pole = np.array([0.0, 0.0, 0.0])
    return is_hemi, pole


def checkvecs(fbval, fbvec, sesdir, dwi_file):
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
        Optionall provide a file path to the diffusion-weighted image series to which the
        bvecs/bvals should correspond.

    Returns
    -------
    gtab_file : str
        File path to pickled DiPy gradient table object.
    gtab : Obj
        DiPy object storing diffusion gradient information.
    slm : str
        Set a value for the --slm option in FSL's Eddy tool. Slm refers to
        "second level model" that specifies the mathematical form
        for how the diffusion gradients cause eddy currents. If the data has
        few directions and/or is has not been sampled on the whole sphere it
        can be advantageous to specify --slm=linear.
    """
    from dipy.io import read_bvals_bvecs
    from dipy.core.gradients import round_bvals
    from dipy.reconst.dki import check_multi_b
    from dmriprep.utils.vectors import make_gtab, rescale_bvec, rescale_bval, is_hemispherical

    # Create vector directory
    vector_dir = "%s%s" % (sesdir, '/vectors')
    os.makedirs(vector_dir, exist_ok=True)

    # load bvecs/bvals
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)

    # Check length equality
    # Correct b0's in bvecs mistated as 10's.
    bvecs[np.where(np.any(abs(bvecs) >= 10, axis=1) == True)] = [1, 0, 0]

    # Ensure that zeros are zero floats.
    bvecs[np.where(bvals == 0)] = float(0)

    # Check for bval-bvec discrepancy
    if len(bvecs[np.where(np.logical_and(bvals > 50, np.all(abs(bvecs) == np.array([0, 0, 0]), axis=1)))]) > 0:
        raise ValueError("Corrupted bval/bvecs detected. Check to ensure volumes with a diffusion weighting are not listed as B0s in the bvecs.")

    # Raise warnings if sampling scheme is not eddy-friendly
    if ((len(bvals) < 10) and (max(bvals) < 1500)) or ((len(bvals) < 30) and (max(bvals) < 5000)):
        raise UserWarning('Too few directions in this data. Use of eddy is not recommended.')

    # Save corrected
    np.savetxt(fbval, bvals.T.astype('int'), fmt='%d', newline=' ')
    np.savetxt(fbvec, bvecs.T.astype('float'), fmt='%.8f')

    # Rescale bvals
    fbval_rescaled = "%s%s" % (vector_dir, "/bval_scaled.bval")
    bval_rescaled = rescale_bval(bvals.astype('float'), bvecs.astype('float'))
    # Get b order of magnitude and round bvals by it
    bmag = int(np.log10(np.max(bval_rescaled))) - 1
    bval_rescaled_mag = round_bvals(bval_rescaled, bmag=bmag)
    np.savetxt(fbval_rescaled, bval_rescaled_mag.T.astype('int'), fmt='%d', newline=' ')

    # Rescale bvecs
    fbvec_rescaled = "%s%s" % (vector_dir, "/bvec_scaled.bvec")
    bvec_rescaled = rescale_bvec(bvecs)
    np.savetxt(fbvec_rescaled, bvec_rescaled.T.astype('float'), fmt='%.8f')

    # Make gradient table and save to pickle
    [gtab_file, gtab, _, _] = make_gtab(fbval_rescaled, fbvec_rescaled, vector_dir, final=False)

    n_bvals = len(np.unique(bval_rescaled_mag))
    check_val = check_multi_b(gtab, n_bvals, non_zero=False, bmag=bmag)
    if check_val is False:
        raise ValueError('Insufficient b-values in gradient table based on the number expected')

    # Check that number of image volumes corresponds to the number of b-vector directions
    if dwi_file:
        volume_num = nib.load(dwi_file).shape[-1]

        if not len(bvecs) == volume_num:
            raise Exception("Expected %d total image samples but found %d total vectors", volume_num, len(bvecs))

    # Check hemisphere coverage
    [is_hemi, pole] = is_hemispherical(np.round(bvec_rescaled, 8)[~(np.round(bvec_rescaled, 8) == 0).all(1)])

    # Second-level model logic
    if is_hemi is True:
        slm = 'linear'
        print("%s%s%s" % ("B-vectors for this data are hemispherical at polar vertex: ", pole,
              "To ensure adequate eddy current correction, eddy will be run using the --slm=linear option."))
    elif len(bvecs) < 30:
        slm = 'linear'
        print('Fewer than 30 diffusion-weighted directions detected. To ensure adequate eddy current correction, eddy will be run using the --slm=linear option')
    else:
        slm = 'none'

    return gtab_file, gtab, slm
