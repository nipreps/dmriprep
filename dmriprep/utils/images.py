import numpy as np
import nibabel as nb
from nipype.utils.filemanip import fname_presuffix


def extract_b0(in_file, b0_ixs, out_path=None):
    """Extract the *b0* volumes from a DWI dataset."""
    if out_path is None:
        out_path = fname_presuffix(
            in_file, suffix='_b0', use_ext=True)

    img = nb.load(in_file)
    data = img.get_fdata(dtype='float32')

    b0 = data[..., b0_ixs]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(b0, img.affine, hdr).to_filename(out_path)
    return out_path


def rescale_b0(in_file, mask_file, out_path=None):
    """Rescale the input volumes using the median signal intensity."""
    if out_path is None:
        out_path = fname_presuffix(
            in_file, suffix='_rescaled_b0', use_ext=True)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file

    data = img.get_fdata(dtype='float32')
    mask_img = nb.load(mask_file)
    mask_data = mask_img.get_fdata(dtype='float32')

    median_signal = np.median(data[mask_data > 0, ...], axis=0)
    rescaled_data = 1000 * data / median_signal
    hdr = img.header.copy()
    nb.Nifti1Image(rescaled_data, img.affine, hdr).to_filename(out_path)
    return out_path


def median(in_file, dtype=None, out_path=None):
    """Average a 4D dataset across the last dimension using median."""
    if out_path is None:
        out_path = fname_presuffix(
            in_file, suffix='_b0ref', use_ext=True)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file
    if img.shape[-1] == 1:
        nb.squeeze_image(img).to_filename(out_path)
        return out_path

    median_data = np.median(img.get_fdata(dtype=dtype),
                            axis=-1)

    hdr = img.header.copy()
    hdr.set_xyzt_units('mm')
    if dtype is not None:
        hdr.set_data_dtype(dtype)
    nb.Nifti1Image(median_data, img.affine, hdr).to_filename(out_path)
    return out_path
