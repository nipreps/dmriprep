import itertools
import logging

import numpy as np


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
