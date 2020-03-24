from pathlib import Path
import numpy as np
import nibabel as nb
from nipype.utils.filemanip import fname_presuffix


def extract_b0(in_file, b0_ixs, out_path=None):
    """
    Extract the *b0* volumes from a DWI dataset.

    Parameters
    ----------
    in_file : str
        DWI NIfTI file.
    b0_ixs : list
        List of B0 indices in `in_file`.
    out_path : str
        Optionally specify an output path.

    Returns
    -------
    out_path : str
       4D NIfTI file consisting of B0's.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> b0_ixs = np.where(np.loadtxt(str(data_dir / 'bval')) <= 50)[0].tolist()[:2]
    >>> in_file = str(data_dir / 'dwi.nii.gz')
    >>> out_path = extract_b0(in_file, b0_ixs)
    >>> assert os.path.isfile(out_path)
    """
    if out_path is None:
        out_path = fname_presuffix(
            in_file, suffix='_b0', use_ext=True)

    img = nb.load(in_file)
    data = img.get_fdata()

    b0 = data[..., b0_ixs]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    nb.Nifti1Image(b0.astype(hdr.get_data_dtype()), img.affine, hdr).to_filename(out_path)
    return out_path


def rescale_b0(in_file, mask_file, out_path=None):
    """
    Rescale the input volumes using the median signal intensity.

    Parameters
    ----------
    in_file : str
        A NIfTI file consisting of one or more B0's.
    mask_file : str
        A B0 mask NIFTI file.
    out_path : str
        Optionally specify an output path.

    Returns
    -------
    out_path : str
       A rescaled B0 NIFTI file.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> mask_file = str(data_dir / 'dwi_mask.nii.gz')
    >>> in_file = str(data_dir / 'dwi_b0.nii.gz')
    >>> out_path = rescale_b0(in_file, mask_file)
    >>> assert os.path.isfile(out_path)
    """
    if out_path is None:
        out_path = fname_presuffix(
            in_file, suffix='_rescaled', use_ext=True)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file

    data = img.get_fdata()
    mask_img = nb.load(mask_file)
    mask_data = mask_img.get_fdata()

    median_signal = np.median(data[mask_data > 0, ...], axis=0)
    rescaled_data = 1000 * data / median_signal
    hdr = img.header.copy()
    nb.Nifti1Image(rescaled_data, img.affine, hdr).to_filename(out_path)
    return out_path


def median(in_file, dtype=None, out_path=None):
    """
    Summarize a 4D dataset across the last dimension using median.

    Parameters
    ----------
    in_file : str
        A NIfTI file consisting of one or more B0's.
    out_path : str
        Optionally specify an output path for `out_path`.

    Returns
    -------
    out_path : str
       A 3D B0 NIFTI file.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> in_file = str(data_dir / 'dwi_b0.nii.gz')
    >>> out_path = median(in_file)
    >>> assert os.path.isfile(out_path)
    """
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
    else:
        dtype = hdr.get_data_dtype()
    nb.Nifti1Image(median_data.astype(dtype), img.affine, hdr).to_filename(out_path)
    return out_path


def average_images(images, out_path=None):
    """
    Average a 4D dataset across the last dimension using mean.

    Parameters
    ----------
    images : str
        A list of NIFTI file paths.
    out_path : str
        Optionally specify an output path for `out_path`.

    Returns
    -------
    out_path : str
       A 3D NIFTI file averaged along the 4th dimension.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> in_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> out_files = save_4d_to_3d(in_file)
    >>> out_path = average_images(out_files)
    >>> assert os.path.isfile(out_path)
    """
    from nilearn.image import mean_img

    average_img = mean_img([nb.load(img) for img in images])
    if out_path is None:
        out_path = fname_presuffix(
            images[0], use_ext=False, suffix="_mean.nii.gz"
        )
    average_img.to_filename(out_path)
    return out_path


def get_list_data(file_list, dtype=np.float32):
    """
    Load 3D volumes from a list of file paths into a 4D array.

    Parameters
    ----------
    file_list : str
        A list of file paths to 3D NIFTI images.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> in_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> out_files = save_4d_to_3d(in_file)
    >>> assert len(out_files) == get_list_data(out_files).shape[-1]
    """
    return nb.concat_images([nb.load(fname) for fname in file_list]).get_fdata(dtype=dtype)


def match_transforms(dwi_files, transforms, b0_ixs):
    """
    Arrange the order of a list of transforms.

    This is a helper function for :abbr:`EMC (Eddy-currents and Motion Correction)`.
    Sorts the input list of affine transforms  to correspond with that of
    each individual dwi volume file, accounting for the indices of :math:`b = 0` volumes.

    Parameters
    ----------
    dwi_files : list
        A list of file paths to 3D diffusion-weighted NIFTI volumes.
    transforms : list
        A list of ndarrays.
    b0_ixs : list
        List of B0 indices.

    Returns
    -------
    nearest_affines : list
       A list of affine file paths that correspond to each of the split
       dwi volumes.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> from dmriprep.utils.vectors import DiffusionGradientTable
    >>> dwi_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> check = DiffusionGradientTable(
    ...     dwi_file=dwi_file,
    ...     bvecs=str(dipy_datadir / "HARDI193.bvec"),
    ...     bvals=str(dipy_datadir / "HARDI193.bval"))
    >>> check.generate_rasb()
    >>> # Conform to the orientation of the image:
    >>> affines = np.zeros((check.gradients.shape[0], 4, 4))
    >>> transforms = []
    >>> for ii, aff in enumerate(affines):
    ...     aff_file = f'aff_{ii}.npy'
    ...     np.save(aff_file, aff)
    ...     transforms.append(aff_file)
    >>> dwi_files = save_4d_to_3d(dwi_file)
    >>> b0_ixs = np.where((check.bvals) <= 50)[0].tolist()[:2]
    >>> nearest_affines = match_transforms(dwi_files, transforms, b0_ixs)
    >>> assert sum([os.path.isfile(i) for i in nearest_affines]) == len(nearest_affines)
    >>> assert len(nearest_affines) == len(dwi_files)
    """
    num_dwis = len(dwi_files)
    num_transforms = len(transforms)

    if num_dwis == num_transforms:
        return transforms

    # Do sanity checks
    if not len(transforms) == len(b0_ixs):
        raise Exception("number of transforms does not match number of b0 images")

    # Create a list of which emc affines go with each of the split images
    nearest_affines = []
    for index in range(num_dwis):
        nearest_b0_num = np.argmin(np.abs(index - np.array(b0_ixs)))
        this_transform = transforms[nearest_b0_num]
        nearest_affines.append(this_transform)

    return nearest_affines


def save_4d_to_3d(in_file):
    """
    Split a 4D dataset along the last dimension into multiple 3D volumes.

    Parameters
    ----------
    in_file : str
        DWI NIfTI file.

    Returns
    -------
    out_files : list
       A list of file paths to 3d NIFTI images.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> in_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> out_files = save_4d_to_3d(in_file)
    >>> assert len(out_files) == nb.load(in_file).shape[-1]
    """
    files_3d = nb.four_to_three(nb.load(in_file))
    out_files = []
    for i, file_3d in enumerate(files_3d):
        out_file = fname_presuffix(in_file, suffix="_tmp_{}".format(i))
        file_3d.to_filename(out_file)
        out_files.append(out_file)
    del files_3d
    return out_files


def prune_b0s_from_dwis(in_files, b0_ixs):
    """
    Remove *b0* volume files from a complete list of DWI volume files.

    Parameters
    ----------
    in_files : list
        A list of NIfTI file paths corresponding to each 3D volume of a
        DWI image (i.e. including B0's).
    b0_ixs : list
        List of B0 indices.

    Returns
    -------
    out_files : list
       A list of file paths to 3d NIFTI images.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> b0_ixs = np.where(np.loadtxt(str(dipy_datadir / "HARDI193.bval")) <= 50)[0].tolist()[:2]
    >>> in_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> threeD_files = save_4d_to_3d(in_file)
    >>> out_files = prune_b0s_from_dwis(threeD_files, b0_ixs)
    >>> assert sum([os.path.isfile(i) for i in out_files]) == len(out_files)
    >>> assert len(out_files) == len(threeD_files) - len(b0_ixs)
    """
    if in_files[0].endswith("_warped.nii.gz"):
        out_files = [
            i
            for j, i in enumerate(
                sorted(
                    in_files, key=lambda x: int(x.split("_")[-2].split(".nii.gz")[0])
                )
            )
            if j not in b0_ixs
        ]
    else:
        out_files = [
            i
            for j, i in enumerate(
                sorted(
                    in_files, key=lambda x: int(x.split("_")[-1].split(".nii.gz")[0])
                )
            )
            if j not in b0_ixs
        ]
    return out_files


def save_3d_to_4d(in_files):
    """
    Concatenate a list of 3D volumes into a 4D output.

    Parameters
    ----------
    in_files : list
        A list of file paths to 3D NIFTI images.

    Returns
    -------
    out_file : str
       A file path to a 4d NIFTI image of concatenated 3D volumes.

    Examples
    --------
    >>> os.chdir(tmpdir)
    >>> in_file = str(dipy_datadir / "HARDI193.nii.gz")
    >>> threeD_files = save_4d_to_3d(in_file)
    >>> out_file = save_3d_to_4d(threeD_files)
    >>> assert len(threeD_files) == nb.load(out_file).shape[-1]
    """
    img_4d = nb.funcs.concat_images([nb.load(img_3d) for img_3d in in_files])
    out_file = fname_presuffix(in_files[0], suffix="_merged")
    img_4d.to_filename(out_file)
    return out_file
