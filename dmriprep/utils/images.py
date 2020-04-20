"""Utilities to handle images."""
import numpy as np
import nibabel as nb
from nipype.utils.filemanip import fname_presuffix


def extract_b0(in_file, b0_ixs, out_path=None):
    """Extract the *b0* volumes from a DWI dataset."""
    if out_path is None:
        out_path = fname_presuffix(in_file, suffix="_b0")

    img = nb.load(in_file)
    bzeros = np.squeeze(np.asanyarray(img.dataobj)[..., b0_ixs])

    hdr = img.header.copy()
    hdr.set_data_shape(bzeros.shape)
    hdr.set_xyzt_units("mm")
    nb.Nifti1Image(bzeros, img.affine, hdr).to_filename(out_path)
    return out_path


def rescale_b0(in_file, mask_file, out_path=None):
    """Rescale the input volumes using the median signal intensity."""
    if out_path is None:
        out_path = fname_presuffix(in_file, suffix="_rescaled", use_ext=True)

    img = nb.squeeze_image(nb.load(in_file))
    if img.dataobj.ndim == 3:
        return in_file, [1.0]

    mask_data = nb.load(mask_file).get_fdata() > 0

    dtype = img.get_data_dtype()
    data = img.get_fdata()

    median_signal = np.median(data[mask_data, ...], axis=0)
    # Normalize to the first volume
    signal_drift = median_signal[0] / median_signal
    data /= signal_drift

    nb.Nifti1Image(data.astype(dtype), img.affine, img.header).to_filename(out_path)
    return out_path, signal_drift.tolist()


def median(in_file, out_path=None):
    """Average a 4D dataset across the last dimension using median."""
    if out_path is None:
        out_path = fname_presuffix(in_file, suffix="_b0ref", use_ext=True)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file
    if img.shape[-1] == 1:
        nb.squeeze_image(img).to_filename(out_path)
        return out_path

    dtype = img.get_data_dtype()
    median_data = np.median(img.get_fdata(), axis=-1)

    nb.Nifti1Image(median_data.astype(dtype), img.affine, img.header).to_filename(
        out_path
    )
    return out_path
