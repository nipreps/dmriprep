"""Utilities to operate on diffusion gradients."""
from .. import config
from pathlib import Path
from itertools import permutations
import nibabel as nb
import numpy as np
from dipy.core.gradients import round_bvals

B0_THRESHOLD = 50
BVEC_NORM_EPSILON = 0.1


class DiffusionGradientTable:
    """Data structure for DWI gradients."""

    __slots__ = [
        "_affine",
        "_b0_thres",
        "_b_scale",
        "_bvals",
        "_bvec_norm_epsilon",
        "_bvecs",
        "_gradients",
        "_normalized",
        "_raise_inconsistent",
        "_transforms",
    ]

    def __init__(
        self,
        b0_threshold=B0_THRESHOLD,
        b_scale=True,
        bvals=None,
        bvec_norm_epsilon=BVEC_NORM_EPSILON,
        bvecs=None,
        dwi_file=None,
        raise_inconsistent=False,
        rasb_file=None,
        transforms=None,
    ):
        """
        Create a new table of diffusion gradients.

        Parameters
        ----------
        b0_threshold : :obj:`float`
            The upper threshold to consider a low-b shell as :math:`b=0`.
        b_scale : :obj:`bool`
            Automatically scale the *b*-values with the norm of the corresponding
            *b*-vectors before the latter are normalized.
        bvals : str or os.pathlike or numpy.ndarray
            File path of the b-values.
        b_vec_norm_epsilon : :obj:`float`
            The minimum difference in the norm of two *b*-vectors to consider them different.
        bvecs : str or os.pathlike or numpy.ndarray
            File path of the b-vectors.
        dwi_file : str or os.pathlike or nibabel.spatialimage
            File path to the diffusion-weighted image series to which the
            bvecs/bvals correspond.
        raise_inconsistent : :obj:`bool`
            If ``True``, a :obj:`ValueError` is raised when discrepancies are found between the
            :math:`b=0` lists calculated from the *b*-vectors and *b*-values, respectively.
            If ``False``, inconsistencies will be mended (if possible).
        rasb_file : str or os.pathlike
            File path to a RAS-B gradient table. If rasb_file is provided,
            then bvecs and bvals will be dismissed.
        transforms : :obj:`list` of :obj:`numpy.ndarray`
            A list of affine transforms to rotate the list of vectors.

        Example
        -------
        >>> os.chdir(tmpdir)
        >>> old_rasb = str(data_dir / 'dwi.tsv')
        >>> old_rasb_mat = np.loadtxt(str(data_dir / 'dwi.tsv'), skiprows=1)
        >>> from dmriprep.utils.vectors import bvecs2ras
        >>> check = DiffusionGradientTable(
        ...     dwi_file=str(data_dir / 'dwi.nii.gz'),
        ...     rasb_file=str(data_dir / 'dwi.tsv'))
        >>> # Conform to the orientation of the image:
        >>> old_rasb_mat[:, :3] = bvecs2ras(check.affine, old_rasb_mat[:, :3])
        >>> affines = np.zeros((old_rasb_mat.shape[0], 4, 4))
        >>> aff_file_list = []
        >>> for ii, aff in enumerate(affines):
        ...     aff_file = f'aff_{ii}.npy'
        ...     np.save(aff_file, aff)
        ...     aff_file_list.append(aff_file)
        >>> check._transforms = aff_file_list
        >>> out_rasb_mat = check.reorient_rasb()
        >>> np.allclose(old_rasb_mat, out_rasb_mat)
        True

        """
        self._affine = None
        self._b0_thres = b0_threshold
        self._b_scale = b_scale
        self._bvals = None
        self._bvec_norm_epsilon = bvec_norm_epsilon
        self._bvecs = None
        self._gradients = None
        self._normalized = False
        self._raise_inconsistent = raise_inconsistent
        self._transforms = transforms

        if dwi_file is not None:
            self.affine = dwi_file
        if rasb_file is not None:
            self.gradients = rasb_file
            if self.affine is not None:
                self.generate_vecval()
        elif dwi_file is not None and bvecs is not None and bvals is not None:
            self.bvecs = bvecs
            self.bvals = bvals
            self.generate_rasb()

    @property
    def affine(self):
        """Get the affine for RAS+/image-coordinates conversions."""
        return self._affine

    @property
    def gradients(self):
        """Get gradient table (rasb)."""
        return self._gradients

    @property
    def bvecs(self):
        """Get the N x 3 list of bvecs."""
        return self._bvecs

    @property
    def bvals(self):
        """Get the N b-values."""
        return self._bvals

    @property
    def normalized(self):
        """Return whether b-vecs have been normalized."""
        return self._normalized

    @affine.setter
    def affine(self, value):
        if isinstance(value, (str, Path)):
            dwi_file = nb.load(str(value))
            self._affine = dwi_file.affine.copy()
            return
        if hasattr(value, "affine"):
            self._affine = value.affine
        self._affine = np.array(value)

    @gradients.setter
    def gradients(self, value):
        if isinstance(value, (str, Path)):
            value = np.loadtxt(value, skiprows=1)
        self._gradients = value

    @bvecs.setter
    def bvecs(self, value):
        if isinstance(value, (str, Path)):
            value = np.loadtxt(str(value)).T
        else:
            value = np.array(value, dtype="float32")

        # Correct any b0's in bvecs misstated as 10's.
        value[np.any(abs(value) >= 10, axis=1)] = np.zeros(3)
        if self.bvals is not None and value.shape[0] != self.bvals.shape[0]:
            raise ValueError("The number of b-vectors and b-values do not match")
        self._bvecs = value

    @bvals.setter
    def bvals(self, value):
        if isinstance(value, (str, Path)):
            value = np.loadtxt(str(value)).flatten()
        if self.bvecs is not None and value.shape[0] != self.bvecs.shape[0]:
            raise ValueError("The number of b-vectors and b-values do not match")
        self._bvals = np.array(value)

    @property
    def b0mask(self):
        """Get a mask of low-b frames."""
        return np.squeeze(self.gradients[..., -1] < self._b0_thres)

    def normalize(self):
        """Normalize (l2-norm) b-vectors."""
        if self._normalized:
            return

        self._bvecs, self._bvals = normalize_gradients(
            self.bvecs,
            self.bvals,
            b0_threshold=self._b0_thres,
            bvec_norm_epsilon=self._bvec_norm_epsilon,
            b_scale=self._b_scale,
            raise_error=self._raise_inconsistent,
        )
        self._normalized = True

    def generate_rasb(self):
        """Compose RAS+B gradient table."""
        if self.gradients is None:
            self.normalize()
            _ras = bvecs2ras(self.affine, self.bvecs)
            self.gradients = np.hstack((_ras, self.bvals[..., np.newaxis]))

    def reorient_rasb(self):
        """Reorient the vectors based o a list of affine transforms."""
        from dipy.core.gradients import gradient_table_from_bvals_bvecs, reorient_bvecs

        affines = self._transforms.copy()
        bvals = self._bvals
        bvecs = self._bvecs

        # Verify that number of non-B0 volumes corresponds to the number of
        # affines. If not, try to fix it, or raise an error:
        if len(self._bvals[self._bvals >= self._b0_thres]) != len(affines):
            b0_indices = np.where(self._bvals <= self._b0_thres)[0].tolist()
            if len(self._bvals[self._bvals >= self._b0_thres]) < len(affines):
                for i in sorted(b0_indices, reverse=True):
                    del affines[i]
            if len(self._bvals[self._bvals >= self._b0_thres]) > len(affines):
                ras_b_mat = self._gradients.copy()
                ras_b_mat = np.delete(ras_b_mat, tuple(b0_indices), axis=0)
                bvals = ras_b_mat[:, 3]
                bvecs = ras_b_mat[:, 0:3]
            if len(self._bvals[self._bvals > self._b0_thres]) != len(affines):
                raise ValueError(
                    "Affine transformations do not correspond to gradients"
                )

        # Build gradient table object
        gt = gradient_table_from_bvals_bvecs(bvals, bvecs, b0_threshold=self._b0_thres)

        # Reorient table
        new_gt = reorient_bvecs(gt, [np.load(aff) for aff in affines])

        return np.hstack((new_gt.bvecs, new_gt.bvals[..., np.newaxis]))

    def generate_vecval(self):
        """Compose a bvec/bval pair in image coordinates."""
        if self.bvecs is None or self.bvals is None:
            if self.affine is None:
                raise TypeError(
                    "Cannot generate b-vectors & b-values in image coordinates. "
                    "Please set the corresponding DWI image's affine matrix."
                )
            self._bvecs = bvecs2ras(
                np.linalg.inv(self.affine), self.gradients[..., :-1]
            )
            self._bvals = self.gradients[..., -1].flatten()

    @property
    def pole(self):
        """
        Check whether the b-vectors cover a full or just half a shell.

        If pole is all-zeros then the b-vectors cover a full sphere.

        """
        self.generate_rasb()
        return calculate_pole(
            self.gradients[..., :-1], bvec_norm_epsilon=self._bvec_norm_epsilon
        )

    def to_filename(self, filename, filetype="rasb"):
        """Write files (RASB, bvecs/bvals) to a given path."""
        if filetype.lower() == "rasb":
            self.generate_rasb()
            np.savetxt(
                str(filename),
                self.gradients,
                delimiter="\t",
                header="\t".join("RASB"),
                fmt=["%.8f"] * 3 + ["%g"],
            )
        elif filetype.lower() == "fsl":
            self.generate_vecval()
            np.savetxt("%s.bvec" % filename, self.bvecs.T, fmt="%.6f")
            np.savetxt("%s.bval" % filename, self.bvals, fmt="%.6f")
        else:
            raise ValueError('Unknown filetype "%s"' % filetype)


def normalize_gradients(
    bvecs,
    bvals,
    b0_threshold=B0_THRESHOLD,
    bvec_norm_epsilon=BVEC_NORM_EPSILON,
    b_scale=True,
    raise_error=False,
):
    """
    Normalize b-vectors and b-values.

    The resulting b-vectors will be of unit length for the non-zero b-values.
    The resultinb b-values will be normalized by the square of the
    corresponding vector amplitude.

    Parameters
    ----------
    bvecs : m x n 2d array
        Raw b-vectors array.
    bvals : 1d array
        Raw b-values float array.
    b0_threshold : float
        Gradient threshold below which volumes and vectors are considered B0's.

    Returns
    -------
    bvecs : m x n 2d array
        Unit-normed b-vectors array.
    bvals : 1d int array
        Vector amplitude square normed b-values array.

    Examples
    --------
    >>> bvecs = np.vstack((np.zeros(3), 2.0 * np.eye(3), -0.8 * np.eye(3), np.ones(3)))
    >>> bvals = np.array([1000] * bvecs.shape[0])
    >>> normalize_gradients(bvecs, bvals, 50, raise_error=True)
    Traceback (most recent call last):
    ValueError:

    >>> bvals[0] = 0.0
    >>> norm_vecs, norm_vals = normalize_gradients(bvecs, bvals)
    >>> np.all(norm_vecs[0] == 0)
    True

    >>> norm_vecs[1, ...].tolist()
    [1.0, 0.0, 0.0]

    >>> norm_vals[0]
    0
    >>> norm_vals[1]
    4000
    >>> norm_vals[-2]
    600
    >>> norm_vals[-1]
    3000

    >>> norm_vecs, norm_vals = normalize_gradients(bvecs, bvals, b_scale=False)
    >>> norm_vals[0]
    0
    >>> np.all(norm_vals[1:] == 1000)
    True

    """
    bvals = np.array(bvals, dtype="float32")
    bvecs = np.array(bvecs, dtype="float32")

    b0s = bvals < b0_threshold
    b0_vecs = np.linalg.norm(bvecs, axis=1) < bvec_norm_epsilon

    # Check for bval-bvec discrepancy.
    if not np.all(b0s == b0_vecs):
        msg = f"Inconsistent bvals and bvecs ({b0s.sum()}, {b0_vecs.sum()} low-b, respectively)."
        if raise_error:
            raise ValueError(msg)
        config.loggers.cli.warning(msg)

    # Rescale b-vals if requested
    if b_scale:
        bvals[~b0s] *= np.linalg.norm(bvecs[~b0s], axis=1) ** 2

    # Ensure b0s have (0, 0, 0) vectors
    bvecs[b0s, :3] = np.zeros(3)

    # Round bvals
    bvals = round_bvals(bvals)

    # Rescale b-vecs, skipping b0's, on the appropriate axis to unit-norm length.
    bvecs[~b0s] /= np.linalg.norm(bvecs[~b0s], axis=1)[..., np.newaxis]
    return bvecs, bvals.astype("uint16")


def calculate_pole(bvecs, bvec_norm_epsilon=BVEC_NORM_EPSILON):
    """
    Check whether the b-vecs cover a hemisphere, and if so, calculate the pole.

    Parameters
    ----------
    bvecs : numpy.ndarray
        2D numpy array with shape (N, 3) where N is the number of points.
        All points must lie on the unit sphere.

    Returns
    -------
    pole : numpy.ndarray
        A zero-vector if ``bvecs`` covers the full sphere, and the unit vector
        locating the hemisphere pole othewise.

    Examples
    --------
    >>> bvecs = [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0),
    ...          (0.0, 1.0, 0.0), (0.0, -1.0, 0.0),
    ...          (0.0, 0.0, 1.0)]  # Just half a sphere
    >>> calculate_pole(bvecs).tolist()
    [0.0, 0.0, 1.0]

    >>> bvecs += [(0.0, 0.0, -1.0)]  # Make it a full-sphere
    >>> calculate_pole(bvecs).tolist()
    [0.0, 0.0, 0.0]

    References
    ----------
    https://rstudio-pubs-static.s3.amazonaws.com/27121_a22e51b47c544980bad594d5e0bb2d04.html

    """
    bvecs = np.array(bvecs, dtype="float32")  # Normalize inputs
    b0s = np.linalg.norm(bvecs, axis=1) < bvec_norm_epsilon

    bvecs = bvecs[~b0s]
    # Generate all pairwise cross products.
    pairs = np.array(list(permutations(bvecs, 2)))
    pairs = np.swapaxes(pairs, 0, 1)
    cross_prods = np.cross(pairs[0, ...], pairs[1, ...])

    # Normalize them.
    cross_norms = np.linalg.norm(cross_prods, axis=1)
    cross_zeros = cross_norms < 1.0e-4
    cross_prods = cross_prods[~cross_zeros]
    cross_prods /= cross_norms[~cross_zeros, np.newaxis]

    # `cross_prods` now contains all candidate vertex points for "the polygon"
    # in the reference.
    # "The polygon" is a subset.
    # Find which points belong to the polygon using a dot product test
    # with each of the original vectors.
    angles = np.arccos(cross_prods.dot(bvecs.T))

    # And test whether it is orthogonal or less.
    dot_prod_test = angles <= np.pi / 2.0
    ntests = dot_prod_test.sum(axis=1) == len(bvecs)

    # If there is at least one point that is orthogonal or less to each
    # input vector, then the points lie on some hemisphere.
    is_hemi = np.any(ntests)

    pole = np.zeros(3)
    if is_hemi:
        vertices = cross_prods[ntests]
        pole = np.mean(vertices, axis=0)
        pole /= np.linalg.norm(pole)
    return pole


def bvecs2ras(affine, bvecs, norm=True, bvec_norm_epsilon=0.2):
    """
    Convert b-vectors given in image coordinates to RAS+.

    Examples
    --------
    >>> bvecs2ras(2.0 * np.eye(3), [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)]).tolist()
    [[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]]

    >>> affine = np.eye(4)
    >>> affine[0, 0] *= -1.0  # Make it LAS
    >>> bvecs2ras(affine, [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)]).tolist()
    [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]

    >>> affine = np.eye(3)
    >>> affine[:2, :2] *= -1.0  # Make it LPS
    >>> bvecs2ras(affine, [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)]).tolist()
    [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]

    >>> affine[:2, :2] = [[0.0, 1.0], [1.0, 0.0]]  # Make it ARS
    >>> bvecs2ras(affine, [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)]).tolist()
    [[0.0, 1.0, 0.0], [0.0, -1.0, 0.0]]

    >>> bvecs2ras(affine, [(0.0, 0.0, 0.0)]).tolist()
    [[0.0, 0.0, 0.0]]

    >>> bvecs2ras(2.0 * np.eye(3), [(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)],
    ...           norm=False).tolist()
    [[2.0, 0.0, 0.0], [-2.0, 0.0, 0.0]]

    """
    if affine.shape == (4, 4):
        affine = affine[:3, :3]

    bvecs = np.array(bvecs, dtype="float32")  # Normalize inputs
    rotated_bvecs = affine[np.newaxis, ...].dot(bvecs.T)[0].T
    if norm is True:
        norms_bvecs = np.linalg.norm(rotated_bvecs, axis=1)
        b0s = norms_bvecs < bvec_norm_epsilon
        rotated_bvecs[~b0s] /= norms_bvecs[~b0s, np.newaxis]
        rotated_bvecs[b0s] = np.zeros(3)
    return rotated_bvecs


def rasb_dwi_length_check(dwi_file, rasb_file):
    """Check the number of encoding vectors and number of orientations in the DWI file."""
    return nb.load(dwi_file).shape[-1] == len(np.loadtxt(rasb_file, skiprows=1))


def b0mask_from_data(dwi_file, mask_file, z_thres=3.0):
    """
    Evaluate B0 locations relative to mean signal variation.

    Standardizes (z-score) the average DWI signal within mask and threshold.
    This is a data-driven way of estimating which volumes in the DWI dataset are
    really encoding *low-b* acquisitions.

    Parameters
    ----------
    dwi_file : :obj:`str`
        File path to the diffusion-weighted image series.
    mask_file : :obj:`str`
        File path to a mask corresponding to the DWI file.
    z_thres : :obj:`float`
        The z-value to consider a volume as a *low-b* orientation.

    """
    data = np.asanyarray(nb.load(dwi_file).dataobj)
    mask = np.asanyarray(nb.load(mask_file).dataobj) > 0.5
    signal_means = np.median(data[mask, np.newaxis], axis=0)
    zscored_means = signal_means - np.median(signal_means)
    zscored_means /= zscored_means.std()
    return zscored_means > z_thres
