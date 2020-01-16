import numpy as np
import nibabel as nb
from nipype.utils.filemanip import fname_presuffix


def extract_b0(in_file, b0_ixs, newpath=None):
    """Extract the *b0* volumes from a DWI dataset."""
    out_file = fname_presuffix(
        in_file, suffix='_b0', newpath=newpath)

    img = nb.load(in_file)
    data = img.get_fdata(dtype='float32')

    b0 = data[..., b0_ixs]

    hdr = img.header.copy()
    hdr.set_data_shape(b0.shape)
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(b0, img.affine, hdr).to_filename(out_file)
    return out_file


def rescale_b0(in_file, mask_file, newpath=None):
    """Rescale the input volumes using the median signal intensity."""
    out_file = fname_presuffix(
        in_file, suffix='_rescaled_b0', newpath=newpath)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file

    data = img.get_fdata(dtype='float32')
    mask_img = nb.load(mask_file)
    mask_data = mask_img.get_fdata(dtype='float32')

    median_signal = np.median(data[mask_data > 0, ...], axis=0)
    rescaled_data = 1000 * data / median_signal
    hdr = img.header.copy()
    nb.Nifti1Image(rescaled_data, img.affine, hdr).to_filename(out_file)
    return out_file


def median(in_file, newpath=None):
    """Average a 4D dataset across the last dimension using median."""
    out_file = fname_presuffix(
        in_file, suffix='_b0ref', newpath=newpath)

    img = nb.load(in_file)
    if img.dataobj.ndim == 3:
        return in_file
    if img.shape[-1] == 1:
        nb.squeeze_image(img).to_filename(out_file)
        return out_file

    median_data = np.median(img.get_fdata(dtype='float32'),
                            axis=-1)

    hdr = img.header.copy()
    hdr.set_xyzt_units('mm')
    hdr.set_data_dtype(np.float32)
    nb.Nifti1Image(median_data, img.affine, hdr).to_filename(out_file)
    return out_file


def quick_load_images(image_list, dtype=np.float32):
    example_img = nb.load(image_list[0])
    num_images = len(image_list)
    output_matrix = np.zeros(tuple(example_img.shape) + (num_images,), dtype=dtype)
    for image_num, image_path in enumerate(image_list):
        output_matrix[..., image_num] = nb.load(image_path).get_fdata(dtype=dtype)
    return output_matrix


def match_transforms(dwi_files, transforms, b0_indices):
    original_b0_indices = np.array(b0_indices)
    num_dwis = len(dwi_files)
    num_transforms = len(transforms)

    if num_dwis == num_transforms:
        return transforms

    # Do sanity checks
    if not len(transforms) == len(b0_indices):
        raise Exception('number of transforms does not match number of b0 images')

    # Create a list of which emc affines go with each of the split images
    nearest_affines = []
    for index in range(num_dwis):
        nearest_b0_num = np.argmin(np.abs(index - original_b0_indices))
        this_transform = transforms[nearest_b0_num]
        nearest_affines.append(this_transform)

    return nearest_affines


def save_4d_to_3d(in_file):
    files_3d = nb.four_to_three(nb.load(in_file))
    out_files = []
    for i, file_3d in enumerate(files_3d):
        out_file = fname_presuffix(in_file, suffix='_tmp_{}'.format(i))
        file_3d.to_filename(out_file)
        out_files.append(out_file)
    del files_3d
    return out_files


def prune_b0s_from_dwis(in_files, b0_ixs):
    if in_files[0].endswith('_trans.nii.gz'):
        out_files = [i for j, i in enumerate(sorted(in_files,
                                                    key=lambda x: int(x.split("_")[-2].split('.nii.gz')[0]))) if j
                     not in b0_ixs]
    else:
        out_files = [i for j, i in enumerate(sorted(in_files,
                                                    key=lambda x: int(x.split("_")[-1].split('.nii.gz')[0]))) if j
                     not in b0_ixs]
    return out_files


def save_3d_to_4d(in_files):
    img_4d = nb.funcs.concat_images([nb.load(img_3d) for img_3d in in_files])
    out_file = fname_presuffix(in_files[0], suffix='_merged')
    img_4d.to_filename(out_file)
    del img_4d
    return out_file
