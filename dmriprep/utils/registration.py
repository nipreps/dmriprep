"""
Linear affine registration tools for motion correction.
"""
import numpy as np
import nibabel as nb
from dipy.align.metrics import CCMetric, EMMetric, SSDMetric
from dipy.align.imaffine import (
    transform_centers_of_mass,
    AffineMap,
    MutualInformationMetric,
    AffineRegistration,
)
from dipy.align.transforms import (
    TranslationTransform3D,
    RigidTransform3D,
    AffineTransform3D,
)
from nipype.utils.filemanip import fname_presuffix

syn_metric_dict = {"CC": CCMetric, "EM": EMMetric, "SSD": SSDMetric}

__all__ = [
    "c_of_mass",
    "translation",
    "rigid",
    "affine",
    "affine_registration",
]


def apply_affine(moving, static, transform_affine, invert=False):
    """Apply an affine to transform an image from one space to another.

    Parameters
    ----------
    moving : array
       The image to be resampled

    static : array

    Returns
    -------
    warped_img : the moving array warped into the static array's space.

    """
    affine_map = AffineMap(
        transform_affine, static.shape, static.affine, moving.shape, moving.affine
    )
    if invert is True:
        warped_arr = affine_map.transform_inverse(np.asarray(moving.dataobj))
    else:
        warped_arr = affine_map.transform(np.asarray(moving.dataobj))

    return nb.Nifti1Image(warped_arr, static.affine)


def average_affines(transforms):
    affine_list = [np.load(aff) for aff in transforms]
    average_affine_file = fname_presuffix(
        transforms[0], use_ext=False, suffix="_average.npy"
    )
    np.save(average_affine_file, np.mean(affine_list, axis=0))
    return average_affine_file


# Affine registration pipeline:
affine_metric_dict = {"MI": MutualInformationMetric, "CC": CCMetric}


def c_of_mass(
    moving, static, static_affine, moving_affine, reg, starting_affine, params0=None
):
    transform = transform_centers_of_mass(static, static_affine, moving, moving_affine)
    transformed = transform.transform(moving)
    return transformed, transform.affine


def translation(
    moving, static, static_affine, moving_affine, reg, starting_affine, params0=None
):
    transform = TranslationTransform3D()
    translation = reg.optimize(
        static,
        moving,
        transform,
        params0,
        static_affine,
        moving_affine,
        starting_affine=starting_affine,
    )

    return translation.transform(moving), translation.affine


def rigid(
    moving, static, static_affine, moving_affine, reg, starting_affine, params0=None
):
    transform = RigidTransform3D()
    rigid = reg.optimize(
        static,
        moving,
        transform,
        params0,
        static_affine,
        moving_affine,
        starting_affine=starting_affine,
    )
    return rigid.transform(moving), rigid.affine


def affine(
    moving, static, static_affine, moving_affine, reg, starting_affine, params0=None
):
    transform = AffineTransform3D()
    affine = reg.optimize(
        static,
        moving,
        transform,
        params0,
        static_affine,
        moving_affine,
        starting_affine=starting_affine,
    )

    return affine.transform(moving), affine.affine


def affine_registration(
    moving,
    static,
    nbins,
    sampling_prop,
    metric,
    pipeline,
    level_iters,
    sigmas,
    factors,
    params0,
):

    """
    Find the affine transformation between two 3D images.

    Parameters
    ----------

    """
    # Define the Affine registration object we'll use with the chosen metric:
    use_metric = affine_metric_dict[metric](nbins, sampling_prop)
    affreg = AffineRegistration(
        metric=use_metric, level_iters=level_iters, sigmas=sigmas, factors=factors
    )

    if not params0:
        starting_affine = np.eye(4)
    else:
        starting_affine = params0

    # Go through the selected transformation:
    for func in pipeline:
        transformed, starting_affine = func(
            np.asarray(moving.dataobj),
            np.asarray(static.dataobj),
            static.affine,
            moving.affine,
            affreg,
            starting_affine,
            params0,
        )
    return nb.Nifti1Image(np.array(transformed), static.affine), starting_affine
