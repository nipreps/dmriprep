#!/usr/bin/env python

from __future__ import (
    print_function,
    division,
    unicode_literals,
    absolute_import,
)

from nipype.interfaces.base import traits, TraitedSpec, File
from nipype.interfaces.mrtrix3.base import MRTrix3BaseInputSpec, MRTrix3Base


class DWIDenoiseInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    mask = File(exists=True, argstr="-mask %s", position=1, desc="mask image")
    extent = traits.Tuple(
        (traits.Int, traits.Int, traits.Int),
        argstr="-extent %d,%d,%d",
        desc="set the window size of the denoising filter. (default = 5,5,5)",
    )
    noise = File(
        argstr="-noise %s",
        name_template="%s_noise",
        name_source=["in_file"],
        keep_extension=True,
        desc="the output noise map",
    )
    out_file = File(
        argstr="%s",
        name_template="%s_denoised",
        name_source=["in_file"],
        keep_extension=True,
        position=-1,
        desc="the output denoised DWI image",
    )


class DWIDenoiseOutputSpec(TraitedSpec):
    out_file = File(desc="the output denoised DWI image", exists=True)
    noise = File(desc="the output noise map (if generated)", exists=True)


class DWIDenoise(MRTrix3Base):
    """
    Denoise DWI data and estimate the noise level based on the optimal
    threshold for PCA.
    DWI data denoising and noise map estimation by exploiting data redundancy
    in the PCA domain using the prior knowledge that the eigenspectrum of
    random covariance matrices is described by the universal Marchenko Pastur
    distribution.
    Important note: image denoising must be performed as the first step of the
    image processing pipeline. The routine will fail if interpolation or
    smoothing has been applied to the data prior to denoising.
    Note that this function does not correct for non-Gaussian noise biases.
    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/dwidenoise.html>
    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> denoise = mrt.DWIDenoise()
    >>> denoise.inputs.in_file = 'dwi.mif'
    >>> denoise.inputs.mask = 'mask.mif'
    >>> denoise.cmdline                               # doctest: +ELLIPSIS
    'dwidenoise -mask mask.mif dwi.mif dwi_denoised.mif'
    >>> denoise.run()                                 # doctest: +SKIP
    """

    _cmd = "dwidenoise"
    input_spec = DWIDenoiseInputSpec
    output_spec = DWIDenoiseOutputSpec


class MRDeGibbsInputSpec(MRTrix3BaseInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        position=-2,
        mandatory=True,
        desc="input DWI image",
    )
    axes = traits.ListInt(
        default_value=[0, 1],
        usedefault=True,
        sep=",",
        minlen=2,
        maxlen=2,
        argstr="-axes %s",
        desc="indicate the plane in which the data was acquired (axial = 0,1; "
        "coronal = 0,2; sagittal = 1,2",
    )
    nshifts = traits.Int(
        default_value=20,
        usedefault=True,
        argstr="-nshifts %d",
        desc="discretization of subpixel spacing (default = 20)",
    )
    minW = traits.Int(
        default_value=1,
        usedefault=True,
        argstr="-minW %d",
        desc="left border of window used for total variation (TV) computation "
        "(default = 1)",
    )
    maxW = traits.Int(
        default_value=3,
        usedefault=True,
        argstr="-maxW %d",
        desc="right border of window used for total variation (TV) computation "
        "(default = 3)",
    )
    out_file = File(
        name_template="%s_unr",
        name_source="in_file",
        keep_extension=True,
        argstr="%s",
        position=-1,
        desc="the output unringed DWI image",
        genfile=True,
    )


class MRDeGibbsOutputSpec(TraitedSpec):
    out_file = File(desc="the output unringed DWI image", exists=True)


class MRDeGibbs(MRTrix3Base):
    """
    Remove Gibbs ringing artifacts.
    This application attempts to remove Gibbs ringing artefacts from MRI images
    using the method of local subvoxel-shifts proposed by Kellner et al.
    This command is designed to run on data directly after it has been
    reconstructed by the scanner, before any interpolation of any kind has
    taken place. You should not run this command after any form of motion
    correction (e.g. not after dwipreproc). Similarly, if you intend running
    dwidenoise, you should run this command afterwards, since it has the
    potential to alter the noise structure, which would impact on dwidenoise's
    performance.
    Note that this method is designed to work on images acquired with full
    k-space coverage. Running this method on partial Fourier ('half-scan') data
    may lead to suboptimal and/or biased results, as noted in the original
    reference below. There is currently no means of dealing with this; users
    should exercise caution when using this method on partial Fourier data, and
    inspect its output for any obvious artefacts.
    For more information, see
    <https://mrtrix.readthedocs.io/en/latest/reference/commands/mrdegibbs.html>
    Example
    -------
    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> unring = mrt.MRDeGibbs()
    >>> unring.inputs.in_file = 'dwi.mif'
    >>> unring.cmdline
    'mrdegibbs -axes 0,1 -maxW 3 -minW 1 -nshifts 20 dwi.mif dwi_unr.mif'
    >>> unring.run()                                 # doctest: +SKIP
    """

    _cmd = "mrdegibbs"
    input_spec = MRDeGibbsInputSpec
    output_spec = MRDeGibbsOutputSpec


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
