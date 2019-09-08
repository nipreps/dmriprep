from __future__ import division, print_function
import os
import nibabel as nib
import numpy as np


def make_gtab(fbval, fbvec, sesdir, final, b0_thr=100):
    from dipy.io import save_pickle
    from dipy.core.gradients import gradient_table
    from dipy.io import read_bvals_bvecs

    if fbval and fbvec:
        bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
    else:
        raise ValueError("Either bvals or bvecs files not found (or rescaling failed)!")

    namer_dir = sesdir + "/dmri_tmp"
    if not os.path.isdir(namer_dir):
        os.mkdir(namer_dir)

    gtab_file = "%s%s" % (namer_dir, "/gtab.pkl")

    # Creating the gradient table
    gtab = gradient_table(bvals, bvecs)

    # Correct b0 threshold
    gtab.b0_threshold = b0_thr

    # Correct b0 mask
    gtab_bvals = gtab.bvals.copy()
    b0_thr_ixs = np.where(gtab_bvals < gtab.b0_threshold)[0]
    gtab_bvals[b0_thr_ixs] = 0
    gtab.b0s_mask = gtab_bvals == 0

    # Show info
    print(gtab.info)

    # Save gradient table to pickle
    save_pickle(gtab_file, gtab)

    if final is True:
        final_bval_path = sesdir + '/final_bval.bval'
        final_bvec_path = sesdir + '/final_bvec.bvec'
        np.savetxt(final_bval_path, bvals.astype('int'), fmt='%i')
        np.savetxt(final_bvec_path, bvecs.astype('float'), fmt='%10f')
    else:
        final_bval_path = None
        final_bvec_path = None

    return gtab_file, gtab, final_bval_path, final_bvec_path


def rename_final_preprocessed_file(in_file, sesdir):
    import shutil
    out_file = sesdir + '/final_preprocessed_dwi.nii.gz'
    shutil.copy(in_file, out_file)
    return out_file


def rescale_bvec(bvec, bvec_rescaled):
    """
    Normalizes b-vectors to be of unit length for the non-zero b-values. If the
    b-value is 0, the vector is untouched.

    Parameters
    ----------
    bvec : str
        File name of the original b-vectors file.
    bvec_rescaled : str
        File name of the new (normalized) b-vectors file. Must have extension `.bvec`.

    Returns
    -------
    bvec_rescaled : str
        File name of the new (normalized) b-vectors file. Must have extension `.bvec`.
    """
    bv1 = np.array(np.loadtxt(bvec))
    # Enforce proper dimensions
    bv1 = bv1.T if bv1.shape[0] == 3 else bv1

    # Normalize values not close to norm 1
    bv2 = [
        b / np.linalg.norm(b) if not np.isclose(np.linalg.norm(b), 0) else b
        for b in bv1
    ]
    np.savetxt(bvec_rescaled, bv2)
    return bvec_rescaled


def is_hemispherical(vecs):
    """
    Test whether all points on a unit sphere lie in the same hemisphere.

    **Inputs**

    vecs : numpy.ndarray
        2D numpy array with shape (N, 3) where N is the number of points.
        All points must lie on the unit sphere.

    **Outputs**

    is_hemi : bool
        If True, one can find a hemisphere that contains all the points.
        If False, then the points do not lie in any hemisphere
    pole : numpy.ndarray
        If `is_hemi == True`, then pole is the "central" pole of the
        input vectors. Otherwise, pole is the zero vector.

    **References**

    https://rstudio-pubs-static.s3.amazonaws.com/27121_a22e51b47c544980bad594d5e0bb2d04.html  # noqa
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


def correct_vecs_and_make_b0s(fbval, fbvec, dwi_file, sesdir):
    from dipy.io import read_bvals_bvecs
    from dmriprep.utils.core import make_gtab, rescale_bvec, is_hemispherical, make_mean_b0

    namer_dir = sesdir + "/dmri_tmp"
    if not os.path.isdir(namer_dir):
        os.mkdir(namer_dir)

    bvec_rescaled = "%s%s" % (namer_dir, "/bvec_scaled.bvec")
    all_b0s_file = "%s%s" % (namer_dir, "/all_b0s.nii.gz")

    # loading bvecs/bvals
    bvals, bvecs = read_bvals_bvecs(fbval, fbvec)
    bvecs[np.where(np.any(abs(bvecs) >= 10, axis=1) == True)] = [1, 0, 0]
    bvecs[np.where(bvals == 0)] = 0
    if (
        len(
            bvecs[
                np.where(
                    np.logical_and(
                        bvals > 50, np.all(abs(bvecs) == np.array([0, 0, 0]), axis=1)
                    )
                )
            ]
        )
        > 0
    ):
        raise ValueError(
            "WARNING: Encountered potentially corrupted bval/bvecs. Check to ensure volumes with a "
            "diffusion weighting are not being treated as B0's along the bvecs"
        )

    if (len(bvals) < 10) and (max(bvals) < 1500):
        raise ValueError('Too few directions in this data. Use of eddy is not recommended.')

    if (len(bvals) < 30) and (max(bvals) < 5000):
        raise ValueError('Too few directions in this data. Use of eddy is not recommended.')

    np.savetxt(fbval, bvals.astype('int'), fmt='%i')
    np.savetxt(fbvec, bvecs.astype('float'), fmt='%10f')
    bvec_rescaled = rescale_bvec(fbvec, bvec_rescaled)
    vecs_rescaled = np.genfromtxt(bvec_rescaled)
    vecs = np.round(vecs_rescaled, 8)[~(np.round(vecs_rescaled, 8) == 0).all(1)]
    [is_hemi, pole] = is_hemispherical(vecs)
    if is_hemi is True:
        slm = 'linear'
        print("Warning: B-vectors for this data are hemispherical at polar vertex: " + str(pole) +
              " To ensure adequate eddy current correction, eddy will be run using the --slm=linear option.")
    else:
        slm = 'none'

    [gtab_file, gtab, _, _] = make_gtab(fbval, bvec_rescaled, sesdir, final=False)

    # Get b0 indices
    b0s = np.where(gtab.bvals <= gtab.b0_threshold)[0].tolist()
    print("%s%s" % ("b0's found at: ", b0s))

    # Extract and Combine all b0s collected
    print("Extracting b0's...")
    b0_vols = []
    dwi_img = nib.load(dwi_file)
    dwi_data = dwi_img.get_data()
    for b0 in b0s:
        print(b0)
        b0_vols.append(dwi_data[:, :, :, b0])

    all_b0s = np.stack(b0_vols, axis=3)
    all_b0s_aff = dwi_img.affine.copy()
    all_b0s_aff[3][3] = len(b0_vols)
    nib.save(nib.Nifti1Image(all_b0s, affine=all_b0s_aff), all_b0s_file)
    initial_mean_b0 = make_mean_b0(all_b0s_file)

    return initial_mean_b0, gtab_file, b0_vols, b0s, slm


def topup_inputs_from_dwi_files(dwi_file, sesdir, spec_acqp, b0_vols, b0s, vol_legend):
    from collections import defaultdict
    import pkg_resources
    from shutil import copyfile
    import random

    """Create a datain spec and a slspec from a list of dwi files."""
    # Write the datain.txt file
    datain_lines = []
    spec_counts = defaultdict(int)

    unique_encodings = [j for j in list(set([float(i) for i in spec_acqp.split(' ')])) if (j == 1.0) or (j == -1.0)]
    if len(unique_encodings) > 1:
        # Reverse phase encodings are present to susceptibility can be estimated via topup
        susceptibility_args = '--estimate_move_by_susceptibility'
    else:
        susceptibility_args = ''

    dwi_img = nib.load(dwi_file)
    imain_data = []
    ix = 0
    for b0_vol in b0_vols:
        num_trs = 1 if len(b0_vol.shape) < 4 else b0_vol.shape[3]
        if vol_legend:
            vol_legend_consec = [sum(vol_legend[:i+1]) for i in range(len(vol_legend))]
            b0_level = next(x[0] for x in enumerate(vol_legend_consec) if x[1] > b0s[ix])
            datain_lines.extend([spec_acqp[b0_level]] * num_trs)
            spec_counts[spec_acqp[b0_level]] += num_trs
        else:
            datain_lines.extend([spec_acqp] * num_trs)
            spec_counts[spec_acqp] += num_trs
        imain_data.append(b0_vol)
        ix = ix + 1

    # Make a 4d series
    imain_output = sesdir + "/topup_imain.nii.gz"
    imain_data_4d = [imain_vol[..., np.newaxis] for imain_vol in imain_data]
    imain_img = nib.Nifti1Image(
        np.concatenate(imain_data_4d, 3), dwi_img.affine, dwi_img.header
    )
    assert imain_img.shape[3] == len(datain_lines)
    imain_img.to_filename(imain_output)

    # Write the datain text file
    datain_file = sesdir + "/acqparams.txt"
    with open(datain_file, "w") as f:
        f.write("\n".join(datain_lines))

    example_b0 = b0_vols[0]
    topup_config = pkg_resources.resource_filename('dmriprep.config', "b02b0.cnf")
    topup_config_odd = pkg_resources.resource_filename('dmriprep.config', "b02b0_1.cnf")

    if 1 in (example_b0.shape[0] % 2, example_b0.shape[1] % 2, example_b0.shape[2] % 2):
        print("Using slower b02b0_1.cnf because an axis has an odd number of slices")
        topup_config_odd_tmp = sesdir + '/b02b0_1_' + str(random.randint(1, 1000)) + '.cnf'
        copyfile(topup_config_odd, topup_config_odd_tmp)
        topup_config = topup_config_odd_tmp
    else:
        topup_config_tmp = sesdir + '/b02b0_' + str(random.randint(1, 1000)) + '.cnf'
        copyfile(topup_config, topup_config_tmp)
        topup_config = topup_config_tmp

    return datain_file, imain_output, example_b0, datain_lines, topup_config, susceptibility_args


def eddy_inputs_from_dwi_files(sesdir, gtab_file):
    from dipy.io import load_pickle

    b0s_mask_all = []
    gtab = load_pickle(gtab_file)
    b0s_mask = gtab.b0s_mask
    b0s_mask_all.append(b0s_mask)

    # Create the index file
    index_file = sesdir + "/index.txt"
    ix_vec = []
    i = 1
    pastfirst0s = False
    for val in gtab.bvals:
        if val > gtab.b0_threshold:
            pastfirst0s = True
        elif val <= gtab.b0_threshold and pastfirst0s is True:
            i = i + 1
        ix_vec.append(i)
    with open(index_file, "w") as f:
        f.write(" ".join(map(str, ix_vec)))

    return index_file


def id_outliers_fn(outlier_report, threshold, dwi_file):
    """Get list of scans that exceed threshold for number of outliers
    Parameters
    ----------
    outlier_report: string
        Path to the fsl_eddy outlier report
    threshold: int or float
        If threshold is an int, it is treated as number of allowed outlier
        slices. If threshold is a float between 0 and 1 (exclusive), it is
        treated the fraction of allowed outlier slices before we drop the
        whole volume.
    dwi_file: string
        Path to nii dwi file to determine total number of slices
    Returns
    -------
    drop_scans: numpy.ndarray
        List of scan indices to drop
    """
    import nibabel as nib
    import numpy as np
    import os.path as op
    import parse

    with open(op.abspath(outlier_report), "r") as fp:
        lines = fp.readlines()

    p = parse.compile(
        "Slice {slice:d} in scan {scan:d} is an outlier with "
        "mean {mean_sd:f} standard deviations off, and mean "
        "squared {mean_sq_sd:f} standard deviations off."
    )

    outliers = [p.parse(l).named for l in lines]
    scans = {d["scan"] for d in outliers}

    def num_outliers(scan, outliers):
        return len([d for d in outliers if d["scan"] == scan])

    if 0 < threshold < 1:
        img = nib.load(dwi_file)
        try:
            threshold *= img.header.get_n_slices()
        except nib.spatialimages.HeaderDataError:
            print(
                "WARNING. We are not sure which dimension has the "
                "slices in this image. So we are using the 3rd dim.",
                img.shape,
            )
            threshold *= img.shape[2]

    drop_scans = np.array([s for s in scans if num_outliers(s, outliers) > threshold])

    outpath = op.abspath("dropped_scans.txt")
    np.savetxt(outpath, drop_scans, fmt="%d")

    return drop_scans, outpath


def drop_outliers_fn(in_file, in_bval, in_bvec, drop_scans, in_sigma=None, perc_missing=0.15):
    """Drop outlier volumes from dwi file
    Parameters
    ----------
    in_file: string
        Path to nii dwi file to drop outlier volumes from
    in_bval: string
        Path to bval file to drop outlier volumes from
    in_bvec: string
        Path to bvec file to drop outlier volumes from
    drop_scans: numpy.ndarray or str
        List of scan indices to drop. If str, then assume path to text file
        listing outlier volumes.

    Returns
    -------
    out_file: string
        Path to "thinned" output dwi file
    out_bval: string
        Path to "thinned" output bval file
    out_bvec: string
        Path to "thinned" output bvec file
    """
    import nibabel as nib
    import numpy as np
    import os.path as op
    from nipype.utils.filemanip import fname_presuffix

    if isinstance(drop_scans, str):
        try:
            drop_scans = np.genfromtxt(drop_scans).tolist()
            if not isinstance(drop_scans, list):
                drop_scans = [drop_scans]

        except TypeError:
            print(
                "Unrecognized file format. Unable to load vector from drop_scans file."
            )

    print("%s%s" % ('Dropping outlier volumes:\n', drop_scans))

    img = nib.load(op.abspath(in_file))
    drop_perc = (len(drop_scans))/float(img.shape[-1])
    if drop_perc > perc_missing:
        raise ValueError('Missing > ' + str(np.round(100*drop_perc, 2)) + '% of volumes after outlier removal. '
                                                                          'This dataset is unuseable based on the '
                                                                          'given rejection threshold.')
    # drop 4d outliers from dwi
    img_data = img.get_data()
    img_data_thinned = np.delete(img_data, drop_scans, axis=3)
    if isinstance(img, nib.nifti1.Nifti1Image):
        img_thinned = nib.Nifti1Image(
            img_data_thinned.astype(np.float64), img.affine, header=img.header
        )
    elif isinstance(img, nib.nifti2.Nifti2Image):
        img_thinned = nib.Nifti2Image(
            img_data_thinned.astype(np.float64), img.affine, header=img.header
        )
    else:
        raise TypeError("in_file does not contain Nifti image datatype.")

    out_file = fname_presuffix(in_file, suffix="_thinned", newpath=op.abspath("."))
    nib.save(img_thinned, op.abspath(out_file))

    # drop outliers from sigma (if 4d)
    if in_sigma is not None:
        sigma = np.load(op.abspath(in_sigma))
        if len(sigma.shape) == 4:
            sigma_thinned = np.delete(sigma, drop_scans, axis=3)
            out_sigma = fname_presuffix(in_sigma, suffix="_thinned", newpath=op.abspath("."))
            np.save(sigma_thinned, op.abspath(out_sigma))
        else:
            out_sigma = in_sigma
    else:
        out_sigma = None

    bval = np.loadtxt(in_bval)
    bval_thinned = np.delete(bval, drop_scans, axis=0)
    out_bval = fname_presuffix(in_bval, suffix="_thinned", newpath=op.abspath("."))
    np.savetxt(out_bval, bval_thinned.astype('int'), fmt='%i')

    bvec = np.loadtxt(in_bvec)
    if bvec.shape[0] == 3:
        bvec_thinned = np.delete(bvec, drop_scans, axis=1)
    else:
        bvec_thinned = np.delete(bvec, drop_scans, axis=0)
    out_bvec = fname_presuffix(in_bvec, suffix="_thinned", newpath=op.abspath("."))
    np.savetxt(out_bvec, bvec_thinned.astype('float'), fmt='%10f')

    return out_file, out_bval, out_bvec, out_sigma


def get_params(A):
    """This is a copy of spm's spm_imatrix where
    we already know the rotations and translations matrix,
    shears and zooms (as outputs from fsl FLIRT/avscale)
    Let A = the 4x4 rotation and translation matrix
    R = [          c5*c6,           c5*s6, s5]
        [-s4*s5*c6-c4*s6, -s4*s5*s6+c4*c6, s4*c5]
        [-c4*s5*c6+s4*s6, -c4*s5*s6-s4*c6, c4*c5]
    """

    def rang(b):
        a = min(max(b, -1), 1)
        return a

    Ry = np.arcsin(A[0, 2])
    # Rx = np.arcsin(A[1, 2] / np.cos(Ry))
    # Rz = np.arccos(A[0, 1] / np.sin(Ry))

    if (abs(Ry) - np.pi / 2) ** 2 < 1e-9:
        Rx = 0
        Rz = np.arctan2(-rang(A[1, 0]), rang(-A[2, 0] / A[0, 2]))
    else:
        c = np.cos(Ry)
        Rx = np.arctan2(rang(A[1, 2] / c), rang(A[2, 2] / c))
        Rz = np.arctan2(rang(A[0, 1] / c), rang(A[0, 0] / c))

    rotations = [Rx, Ry, Rz]
    translations = [A[0, 3], A[1, 3], A[2, 3]]

    return rotations, translations


def get_flirt_motion_parameters(flirt_mats):
    import os.path as op
    from nipype.interfaces.fsl.utils import AvScale
    from dmriprep.utils.core import get_params

    motion_params = open(op.abspath("motion_parameters.par"), "w")
    for mat in flirt_mats:
        res = AvScale(mat_file=mat).run()
        A = np.asarray(res.outputs.rotation_translation_matrix)
        rotations, translations = get_params(A)
        for i in rotations + translations:
            motion_params.write("%f " % i)
        motion_params.write("\n")
    motion_params.close()
    motion_params = op.abspath("motion_parameters.par")
    return motion_params


def read_nifti_sidecar(json_file):
    import json

    with open(json_file, "r") as f:
        metadata = json.load(f)

    if 'vol_legend' not in metadata:
        pe_dir = metadata["PhaseEncodingDirection"]
        trt = metadata.get("TotalReadoutTime")
        if trt is None:
            pass

        return {
            "PhaseEncodingDirection": pe_dir,
            "TotalReadoutTime": trt,
        }
    else:
        idxs = list(map(lambda x: x + 1, list(range(len(metadata['vol_legend'])))))
        pe_dirs = []
        trts = []
        for idx in idxs:
            pe_dirs.append(metadata["PhaseEncodingDirection_" + str(idx)])
            trts.append(metadata.get("TotalReadoutTime_" + str(idx)))
            if len(list(set(trts))) == 1 and list(set(trts))[0] is None:
                pass
        vol_legend = metadata['vol_legend']

        return {
            "PhaseEncodingDirection": pe_dirs,
            "TotalReadoutTime": trts,
            "vol_legend": vol_legend,
        }


def extract_metadata(metadata):
    from dmriprep.utils.core import read_nifti_sidecar, compute_readout

    acqp_lines = {
        "i": "1 0 0 %.6f",
        "j": "0 1 0 %.6f",
        "k": "0 0 1 %.6f",
        "i-": "-1 0 0 %.6f",
        "j-": "0 -1 0 %.6f",
        "k-": "0 0 -1 %.6f",
    }
    spec = read_nifti_sidecar(metadata)

    try:
        total_rdout = spec["TotalReadoutTime"]
    except:
        try:
            total_rdout = compute_readout(spec)
        except KeyError as e:
            print('Readout time not found in .json metadata and could not be computed using %s. '
                  'Cannot proceed with TOPUP/Eddy' % str(e))

    if isinstance(list(spec.values())[0], list):
        total_readout = list(set(total_rdout))
        if len(total_readout) != 1:
            raise ValueError('Multiple readout times detected!')
        spec_lines = []
        spec_acqps = []
        for line in spec["PhaseEncodingDirection"]:
            spec_line = acqp_lines[line]
            spec_lines.append(acqp_lines[line])
            spec_acqps.append(spec_line % total_readout[0])
        vol_legend = spec['vol_legend']
    else:
        spec_line = acqp_lines[spec["PhaseEncodingDirection"]]
        spec_acqps = spec_line % total_rdout
        vol_legend = None
    return spec_acqps, vol_legend


def check_shelled(gtab_file):
    from dipy.io import load_pickle

    # Check whether data is shelled
    gtab = load_pickle(gtab_file)
    if len(np.unique(gtab.bvals)) > 2:
        is_shelled = True
    else:
        is_shelled = False
    return is_shelled


def make_mean_b0(in_file):
    import time

    b0_img = nib.load(in_file)
    b0_img_data = b0_img.get_data()
    mean_b0 = np.mean(b0_img_data, axis=3, dtype=b0_img_data.dtype)
    mean_file_out = in_file.split(".nii.gz")[0] + "_mean_b0.nii.gz"
    nib.save(
        nib.Nifti1Image(mean_b0, affine=b0_img.affine, header=b0_img.header),
        mean_file_out,
    )
    while os.path.isfile(mean_file_out) is False:
        time.sleep(1)
    return mean_file_out


def suppress_gibbs(in_file, sesdir):
    from time import time
    from dipy.denoise.gibbs import gibbs_removal

    t = time()
    img = nib.load(in_file)
    img_data = img.get_data()
    gibbs_corr_data = gibbs_removal(img_data)
    print("Time taken for gibbs suppression: ", -t + time())
    gibbs_free_file = sesdir + "/gibbs_free_data.nii.gz"
    nib.save(
        nib.Nifti1Image(gibbs_corr_data.astype(np.float32), img.affine, img.header),
        gibbs_free_file,
    )
    return gibbs_free_file


def estimate_sigma(in_file, gtab_file, mask, denoise_strategy, N=1, smooth_factor=3):
    import os
    from dipy.io import load_pickle
    from dipy.denoise.noise_estimate import estimate_sigma
    from dipy.denoise.pca_noise_estimate import pca_noise_estimate

    gtab = load_pickle(gtab_file)
    sigma_path = os.path.dirname(gtab_file) + '/sigma.npy'
    img = nib.load(in_file)
    img_data = np.asarray(img.get_data(caching='unchanged'), dtype=np.float32)
    mask_data = np.asarray(nib.load(mask).get_data(caching='unchanged'), dtype=np.bool)

    if denoise_strategy == "mppca" or denoise_strategy == "localpca":
        sigma = pca_noise_estimate(img_data, gtab, correct_bias=True, smooth=smooth_factor)
    elif denoise_strategy == "nlmeans":
        sigma = estimate_sigma(img_data, N=N)
    elif denoise_strategy == 'nlsam':
        try:
            import nlsam
        except:
            ImportError('NLSAM not installed. See https://github.com/samuelstjean/nlsam.git')
        from nlsam.smoothing import local_standard_deviation
        from nlsam.bias_correction import root_finder_sigma

        # Fix the implausible signals
        img_data[..., gtab.b0s_mask] = np.max(img_data, axis=-1, keepdims=True)

        # Noise estimation part
        sigma = root_finder_sigma(img_data, local_standard_deviation(img_data), N, mask=mask_data)
    else:
        sigma = None
        sigma_path = None
        raise ValueError("Denoising strategy not recognized.")

    np.save(sigma_path, sigma)
    return sigma_path


def denoise(
    in_file,
    sesdir,
    gtab_file,
    mask,
    denoise_strategy,
    sigma_path,
    omp_nthreads,
    N=1,
    patch_radius=2,
    tau_factor=2.3,
    block_radius=1,
    n_iter=10,
    sh_order=8
):
    from time import time
    from dipy.denoise.localpca import genpca
    from dipy.denoise.nlmeans import nlmeans
    from dipy.io import load_pickle

    gtab = load_pickle(gtab_file)
    t = time()
    img = nib.load(in_file)
    img_data = np.asarray(img.get_data(caching='unchanged'), dtype=np.float32)
    mask_data = np.asarray(nib.load(mask).get_data(caching='unchanged'), dtype=np.bool)

    if sigma_path:
        sigma = np.load(sigma_path)
        if denoise_strategy == "mppca":
            print('Running Marchenko-Pastur(MP) PCA denoising...')
            img_data_den = genpca(img_data, sigma=sigma, mask=mask_data,
                                  patch_radius=patch_radius,
                                  pca_method='eig', tau_factor=None,
                                  return_sigma=False, out_dtype=None)
        elif denoise_strategy == "localpca":
            print('Running Local PCA denoising...')
            img_data_den = genpca(img_data, sigma=sigma, mask=mask_data,
                                  patch_radius=patch_radius,
                                  pca_method='eig', tau_factor=tau_factor,
                                  return_sigma=False, out_dtype=None)
        elif denoise_strategy == "nlmeans":
            print('Running Non-Local Means denoising...')
            img_data_den = nlmeans(
                img_data,
                sigma=sigma,
                mask=mask_data,
                patch_radius=patch_radius,
                block_radius=block_radius,
                rician=True,
            )
        elif denoise_strategy == 'nlsam':
            print('Running Non Local Spatial and Angular Matching denoising...')
            try:
                import nlsam
            except:
                ImportError('NLSAM not installed. See https://github.com/samuelstjean/nlsam.git')
            from nlsam.denoiser import nlsam_denoise
            from nlsam.smoothing import sh_smooth
            from nlsam.bias_correction import stabilization

            # Fix the implausible signals
            img_data[..., gtab.b0s_mask] = np.max(img_data, axis=-1, keepdims=True)

            # Stabilizer part
            data_stabilized = stabilization(img_data, sh_smooth(img_data, gtab.bvals, gtab.bvecs.T, sh_order=sh_order),
                                            mask=mask_data, sigma=sigma, N=N)

            # Denoising
            sigma_3d = np.median(sigma, axis=-1)
            block_size = np.array([3, 3, 3, 5])
            img_data_den = nlsam_denoise(data_stabilized, sigma_3d, gtab.bvals, gtab.bvecs, block_size,
                                         mask=mask_data, is_symmetric=False, subsample=True,
                                         n_iter=n_iter, b0_threshold=gtab.b0_threshold, split_b0s=True,
                                         verbose=True, use_threading=True, mp_method=None, n_cores=int(omp_nthreads))

        else:
            raise ValueError("Denoising strategy not recognized.")
        print("Time taken for denoising: ", -t + time())
        denoised_file = sesdir + "/preprocessed_data_denoised_" + denoise_strategy + ".nii.gz"
        nib.save(
            nib.Nifti1Image(img_data_den.astype(np.float32), img.affine, img.header),
            denoised_file,
        )
    else:
        raise ValueError('Cannot run denoising without sigma estimate!')

    return denoised_file


def compute_readout(params):
    """
    Computes readout time from epi params (see `eddy documentation
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/EDDY/Faq#How_do_I_know_what_to_put_into_my_--acqp_file.3F>`_).

    .. warning:: ``params['echospacing']`` should be in *sec* units.


    """
    epi_factor = 1.0
    acc_factor = 1.0
    try:
        if params['epi_factor'] > 1:
            epi_factor = float(params['epi_factor'] - 1)
    except:
        pass
    try:
        if params['acc_factor'] > 1:
            acc_factor = 1.0 / params['acc_factor']
    except:
        pass
    return acc_factor * epi_factor * params['echospacing']


def make_basename(out_corrected):
    base_name = out_corrected.split('.nii.gz')[0]
    return base_name


def bytesto(bytes, to, bsize=1024):
    """convert bytes to megabytes, etc.
       sample code:
           print('mb= ' + str(bytesto(314575262000000, 'm')))
       sample output:
           mb= 300002347.946
    """

    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(bytes)
    for i in range(a[to]):
        r = r / bsize

    return(r)