"""
Linear affine registration tools for motion correction.
"""
import attr

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
    return transform


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

    return translation


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
    return rigid


def affine(moving, static, static_affine, moving_affine, reg, starting_affine,
           params0=None):
    """
    """
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

    return affine


@attr.s(slots=True, frozen=True)
class AffineRegistration():
    def __init__(self):
        nbins = attr.ib(default=32)
        sampling_prop = attr.ib(default=1.0)
        metric = attr.ib(default="MI")
        level_iters = attr.ib(default=[10000, 1000, 100])
        sigmas = attr.ib(defaults=[3, 1, 0.0])
        factors = attr.ib(defaults=[4, 2, 1])
        pipeline = attr.ib(defaults=[c_of_mass, translation, rigid, affine])

    def fit(self, static, moving, params0=None):
        """
        static, moving : nib.Nifti1Image class images
        """
        if params0 is None:
            starting_affine = np.eye(4)
        else:
            starting_affine = params0

        use_metric = affine_metric_dict[self.metric](self.nbins,
                                                     self.sampling_prop)
        affreg = AffineRegistration(
            metric=use_metric,
            level_iters=self.level_iters,
            sigmas=self.sigmas,
            factors=self.factors)

        # Go through the selected transformation:
        for func in self.pipeline:
            transform = func(
                np.asarray(moving.dataobj),
                np.asarray(static.dataobj),
                static.affine,
                moving.affine,
                affreg,
                starting_affine,
                params0,
            )
            starting_affine = transform.affine

        self.static_affine_ = static.affine
        self.moving_affine_ = moving.affine
        self.affine_ = starting_affine
        self.reg_ = AffineMap(starting_affine,
                              static.shape, static.affine,
                              moving.shape, moving.affine)

    def apply(self, moving):
        """

        """
        data = moving.get_fdata()
        assert np.all(moving.affine, self.moving_affine_)
        return nb.Nifti1Image(np.array(self.reg_.transform(data)),
                              self.static_affine_)
