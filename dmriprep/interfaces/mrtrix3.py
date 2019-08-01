#!/usr/bin/env python

from __future__ import (
    print_function,
    division,
    unicode_literals,
    absolute_import,
)

from nipype.interfaces.base import traits, TraitedSpec, File
from nipype.interfaces.mrtrix3.base import MRTrix3BaseInputSpec, MRTrix3Base


class MRResizeInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    size = traits.List(
        traits.Int(),
        argstr="-size %s",
        desc="define the new image size for the output image. This should be "
        "specified as a comma-separated list.",
    )
    voxel_size = traits.List(
        traits.Float(),
        argstr="-voxel %s",
        desc="define the new voxel size for the output image. This can be "
        "specified either as a single value to be used for all "
        "dimensions, or as a comma-separated list of the size for each "
        "voxel dimension.",
    )
    scale = traits.Float(
        argstr="-scale %s",
        desc="scale the image resolution by the supplied factor. This can be "
        "specified either as a single value to be used for all "
        "dimensions, or as a comma-separated list of scale factors for "
        "each dimension.",
    )
    interp = traits.Enum(
        "nearest",
        "linear",
        "cubic",
        "sinc",
        default="cubic",
        argstr="-interp %s",
        desc="set the interpolation method to use when resizing (choices: "
        "nearest, linear, cubic, sinc. Default: cubic).",
    )

    out_file = File(
        argstr="%s",
        name_template="%s_resized",
        name_source=["in_file"],
        keep_extension=True,
        position=-1,
        desc="the output resized DWI image",
    )


class MRResizeOutputSpec(TraitedSpec):
    out_file = File(desc="the output resized DWI image", exists=True)


class MRResize(MRTrix3Base):
    """
    Resize an image by defining the new image resolution, voxel size or a scale factor
    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/mrresize.html>
    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> resize = mrt.MRResize()
    >>> resize.inputs.in_file = 'dwi.mif'
    >>> denoise.inputs.mask = 'mask.mif'
    >>> denoise.cmdline                               # doctest: +ELLIPSIS
    'dwidenoise -mask mask.mif dwi.mif dwi_denoised.mif'
    >>> denoise.run()                                 # doctest: +SKIP
    """

    _cmd = "mrresize"
    input_spec = MRResizeInputSpec
    output_spec = MRResizeOutputSpec
