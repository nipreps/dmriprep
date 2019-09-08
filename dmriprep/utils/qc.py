import base64
import os.path as op
from io import BytesIO
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from dipy.segment.mask import median_otsu
from nipype.utils.filemanip import save_json, load_json


def normalize_xform(img):
    """ Set identical, valid qform and sform matrices in an image
    Selects the best available affine (sform > qform > shape-based), and
    coerces it to be qform-compatible (no shears).
    The resulting image represents this same affine as both qform and sform,
    and is marked as NIFTI_XFORM_ALIGNED_ANAT, indicating that it is valid,
    not aligned to template, and not necessarily preserving the original
    coordinates.
    If header would be unchanged, returns input image.
    """
    # Let nibabel convert from affine to quaternions, and recover xform
    tmp_header = img.header.copy()
    tmp_header.set_qform(img.affine)
    xform = tmp_header.get_qform()
    xform_code = 2

    # Check desired codes
    qform, qform_code = img.get_qform(coded=True)
    sform, sform_code = img.get_sform(coded=True)
    if all(
        (
            qform is not None and np.allclose(qform, xform),
            sform is not None and np.allclose(sform, xform),
            int(qform_code) == xform_code,
            int(sform_code) == xform_code,
        )
    ):
        return img

    new_img = img.__class__(img.get_data(), xform, img.header)
    # Unconditionally set sform/qform
    new_img.set_sform(xform, xform_code)
    new_img.set_qform(xform, xform_code)

    return new_img


def reorient_dwi(dwi_prep, bvecs, out_dir):
    """
    A function to reorient any dwi image and associated bvecs to RAS+.

    Parameters
    ----------
    dwi_prep : str
        File path to a dwi Nifti1Image.
    bvecs : str
        File path to corresponding bvecs file.
    out_dir : str
        Path to output directory.

    Returns
    -------
    out_fname : str
        File path to the reoriented dwi Nifti1Image.
    out_bvec_fname : str
        File path to corresponding reoriented bvecs file.
    """
    from dmriprep.utils.qc import normalize_xform

    fname = dwi_prep
    bvec_fname = bvecs
    out_bvec_fname = "%s%s" % (out_dir, "/bvecs_reor.bvec")

    input_img = nib.load(fname)
    input_axcodes = nib.aff2axcodes(input_img.affine)
    reoriented = nib.as_closest_canonical(input_img)
    normalized = normalize_xform(reoriented)
    # Is the input image oriented how we want?
    new_axcodes = ("R", "A", "S")
    if normalized is not input_img:
        out_fname = "%s%s%s%s" % (
            out_dir,
            "/",
            dwi_prep.split("/")[-1].split(".nii.gz")[0],
            "_reor_RAS.nii.gz",
        )
        print("%s%s%s" % ("Reorienting ", dwi_prep, " to RAS+..."))

        # Flip the bvecs
        input_orientation = nib.orientations.axcodes2ornt(input_axcodes)
        desired_orientation = nib.orientations.axcodes2ornt(new_axcodes)
        transform_orientation = nib.orientations.ornt_transform(
            input_orientation, desired_orientation
        )
        bvec_array = np.loadtxt(bvec_fname)
        if bvec_array.shape[0] != 3:
            bvec_array = bvec_array.T
        if not bvec_array.shape[0] == transform_orientation.shape[0]:
            raise ValueError("Unrecognized bvec format")
        output_array = np.zeros_like(bvec_array)
        for this_axnum, (axnum, flip) in enumerate(transform_orientation):
            output_array[this_axnum] = bvec_array[int(axnum)] * float(flip)
        np.savetxt(out_bvec_fname, output_array, fmt="%.8f ")
    else:
        out_fname = "%s%s%s%s" % (
            out_dir,
            "/",
            dwi_prep.split("/")[-1].split(".nii.gz")[0],
            "_noreor_RAS.nii.gz",
        )
        out_bvec_fname = bvec_fname

    normalized.to_filename(out_fname)

    return out_fname, out_bvec_fname


def reorient_img(img, out_dir):
    """
    A function to reorient any non-dwi image to RAS+.

    Parameters
    ----------
    img : str
        File path to a Nifti1Image.
    out_dir : str
        Path to output directory.

    Returns
    -------
    out_name : str
        File path to reoriented Nifti1Image.
    """
    from dmriprep.utils.qc import normalize_xform

    # Load image, orient as RAS
    orig_img = nib.load(img)
    reoriented = nib.as_closest_canonical(orig_img)
    normalized = normalize_xform(reoriented)

    # Image may be reoriented
    if normalized is not orig_img:
        print("%s%s%s" % ("Reorienting ", img, " to RAS+..."))
        out_name = "%s%s%s%s" % (
            out_dir,
            "/",
            img.split("/")[-1].split(".nii.gz")[0],
            "_reor_RAS.nii.gz",
        )
    else:
        out_name = "%s%s%s%s" % (
            out_dir,
            "/",
            img.split("/")[-1].split(".nii.gz")[0],
            "_noreor_RAS.nii.gz",
        )

    normalized.to_filename(out_name)

    return out_name


def match_target_vox_res(img_file, vox_size, out_dir):
    """
    A function to resample an image to a given isotropic voxel resolution.

    Parameters
    ----------
    img_file : str
        File path to a Nifti1Image.
    vox_size : str
        Voxel size in mm. (e.g. 2mm).
    out_dir : str
        Path to output directory.

    Returns
    -------
    img_file : str
        File path to resampled Nifti1Image.
    """
    import os
    from dipy.align.reslice import reslice

    # Check dimensions
    img = nib.load(img_file)
    data = img.get_fdata()
    affine = img.affine
    hdr = img.header
    zooms = hdr.get_zooms()[:3]
    if vox_size == "1mm":
        new_zooms = (1.0, 1.0, 1.0)
    elif vox_size == "2mm":
        new_zooms = (2.0, 2.0, 2.0)

    if (abs(zooms[0]), abs(zooms[1]), abs(zooms[2])) != new_zooms:
        print("Reslicing image " + img_file + " to " + vox_size + "...")
        img_file_res = "%s%s%s%s%s%s" % (
            out_dir,
            "/",
            os.path.basename(img_file).split(".nii.gz")[0],
            "_res",
            vox_size,
            ".nii.gz",
        )
        data2, affine2 = reslice(data, affine, zooms, new_zooms)
        img2 = nib.Nifti1Image(data2, affine=affine2)
        nib.save(img2, img_file_res)
        img_file = img_file_res
    else:
        img_file_nores = "%s%s%s%s%s%s" % (
            out_dir,
            "/",
            os.path.basename(img_file).split(".nii.gz")[0],
            "_nores",
            vox_size,
            ".nii.gz",
        )
        nib.save(img, img_file_nores)
        img_file = img_file_nores

    return img_file


def check_orient_and_dims(infile, vox_size, bvecs, outdir, overwrite=True):
    """
    An API to reorient any image to RAS+ and resample any image to a given voxel resolution.

    Parameters
    ----------
    infile : str
        File path to a dwi Nifti1Image.
    vox_size : str
        Voxel size in mm. (e.g. 2mm).
    bvecs : str
        File path to corresponding bvecs file if infile is a dwi.
    outdir : str
        Path to output directory.
    overwrite : bool
        Boolean indicating whether to overwrite existing outputs. Default is True.

    Returns
    -------
    outfile : str
        File path to the reoriented and/or resample Nifti1Image.
    bvecs : str
        File path to corresponding reoriented bvecs file if outfile is a dwi.
    """
    import warnings

    warnings.filterwarnings("ignore")
    from dmriprep.utils.qc import reorient_dwi, match_target_vox_res

    # Check orientation
    # dwi case
    # Check orientation
    if ("RAS" not in infile) or (overwrite is True):
        [infile, bvecs] = reorient_dwi(infile, bvecs, outdir)
    # Check dimensions
    if ("reor" not in infile) or (overwrite is True):
        outfile = match_target_vox_res(infile, vox_size, outdir)
        print(outfile)

    return outfile, bvecs


def mplfig(data, outfile=None, as_bytes=False):
    fig = plt.figure(frameon=False, dpi=data.shape[0])
    fig.set_size_inches(float(data.shape[1])/data.shape[0], 1)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(data, aspect=1, cmap=plt.cm.Greys_r)  # previous aspect="normal"
    if outfile:
        fig.savefig(outfile, dpi=data.shape[0], transparent=True)
        plt.close()
        return outfile
    if as_bytes:
        IObytes = BytesIO()
        plt.savefig(IObytes, format='png', dpi=data.shape[0], transparent=True)
        IObytes.seek(0)
        base64_jpgData = base64.b64encode(IObytes.read())
        return base64_jpgData.decode("ascii")


def mplfigcontour(data, outfile=None, as_bytes=False):
    fig = plt.figure(frameon=False)
    fig.set_size_inches(float(data.shape[1])/data.shape[0], 1)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    bg = np.zeros(data.shape)
    bg[:] = np.nan
    ax.imshow(bg, aspect=1, cmap=plt.cm.Greys_r)  # used to be aspect="normal"
    ax.contour(data, colors="red", linewidths=0.1)
    if outfile:
        fig.savefig(outfile, dpi=data.shape[0], transparent=True)
        plt.close()
        return outfile
    if as_bytes:
        IObytes = BytesIO()
        plt.savefig(IObytes, format='png', dpi=data.shape[0], transparent=True)
        IObytes.seek(0)
        base64_jpgData = base64.b64encode(IObytes.read())
        return base64_jpgData.decode("ascii")


def load_and_reorient(filename):
    img = nib.load(filename)
    data, aff = img.get_data(), img.affine
    data = reorient_array(data, aff)
    return data


def reshape3D(data, n=256):
    return np.pad(data, (
        (
            (n-data.shape[0]) // 2,
            ((n-data.shape[0]) + (data.shape[0] % 2 > 0)) // 2
        ),
        (
            (n-data.shape[1]) // 2,
            ((n-data.shape[1]) + (data.shape[1] % 2 > 0)) // 2
        ),
        (0, 0)
    ), "constant", constant_values=(0, 0))


def reshape4D(data, n=256):
    return np.pad(data, (
        (
            (n-data.shape[0]) // 2,
            ((n-data.shape[0]) + (data.shape[0] % 2 > 0)) // 2
        ),
        (
            (n-data.shape[1]) // 2,
            ((n-data.shape[1]) + (data.shape[1] % 2 > 0)) // 2
        ),
        (0, 0), (0, 0)
    ), "constant", constant_values=(0, 0))


def get_middle_slices(data, slice_direction):
    slicer = {"ax": 0, "cor": 1, "sag": 2}
    all_data_slicer = [slice(None), slice(None), slice(None)]
    num_slices = data.shape[slicer[slice_direction]]
    slice_num = int(num_slices / 2)
    all_data_slicer[slicer[slice_direction]] = slice_num
    tile = data[tuple(all_data_slicer)]

    # make it a square
    N = max(tile.shape[:2])
    tile = reshape3D(tile, N)

    return tile


def nearest_square(limit):
    answer = 0
    while (answer+1)**2 < limit:
        answer += 1
    if (answer ** 2) == limit:
        return answer
    else:
        return answer + 1


def create_sprite_from_tiles(tile, out_file=None, as_bytes=False):
    num_slices = tile.shape[-1]
    N = nearest_square(num_slices)
    M = int(np.ceil(num_slices/N))
    # tile is square, so just make a big arr
    pix = tile.shape[0]

    if len(tile.shape) == 3:
        mosaic = np.zeros((N*tile.shape[0], M*tile.shape[0]))
    else:
        mosaic = np.zeros((N*tile.shape[0], M*tile.shape[0], tile.shape[-2]))

    mosaic[:] = np.nan
    helper = np.arange(N*M).reshape((N, M))

    for t in range(num_slices):
        x, y = np.nonzero(helper == t)
        xmin = x[0] * pix
        xmax = (x[0] + 1) * pix
        ymin = y[0] * pix
        ymax = (y[0] + 1) * pix

        if len(tile.shape) == 3:
            mosaic[xmin:xmax, ymin:ymax] = tile[:, :, t]
        else:
            mosaic[xmin:xmax, ymin:ymax, :] = tile[:, :, :, t]

    if as_bytes:
        img = mplfig(mosaic, out_file, as_bytes=as_bytes)
        return dict(img=img, N=N, M=M, pix=pix, num_slices=num_slices)

    if out_file:
        img = mplfig(mosaic, out_file), N, M, pix, num_slices

    return dict(mosaic=mosaic, N=N, M=M, pix=pix, num_slices=num_slices)


def createSprite4D(dwi_file):

    # initialize output dict
    output = []

    # load the file
    dwi = load_and_reorient(dwi_file)[:, :, :, 1:]

    # create tiles from center slice on each orientation
    for orient in ['sag', 'ax', 'cor']:
        tile = get_middle_slices(dwi, orient)

        # create sprite images for each
        results = create_sprite_from_tiles(tile, as_bytes=True)
        results['img_type'] = '4dsprite'
        results['orientation'] = orient
        output.append(results)

    return output


def createB0_ColorFA_Mask_Sprites(b0_file, colorFA_file, mask_file):
    colorfa = load_and_reorient(colorFA_file)
    b0 = load_and_reorient(b0_file)[:, :, :, 0]
    anat_mask = load_and_reorient(mask_file)

    N = max(*b0.shape[:2])

    # make a b0 sprite
    b0 = reshape3D(b0, N)
    _, mask = median_otsu(b0)
    outb0 = create_sprite_from_tiles(b0, as_bytes=True)
    outb0['img_type'] = 'brainsprite'

    # make a colorFA sprite, masked by b0
    Q = reshape4D(colorfa, N)
    Q[np.logical_not(mask)] = np.nan
    Q = np.moveaxis(Q,  -2, -1)
    outcolorFA = create_sprite_from_tiles(Q, as_bytes=True)
    outcolorFA['img_type'] = 'brainsprite'

    # make an anat mask contour sprite
    outmask = create_sprite_from_tiles(reshape3D(anat_mask, N))
    img = mplfigcontour(outmask.pop("mosaic"), as_bytes=True)
    outmask['img'] = img

    return outb0, outcolorFA, outmask


def create_report_json(dwi_corrected_file, eddy_rms, eddy_report,
                       color_fa_file, anat_mask_file,
                       outlier_indices,
                       eddy_qc_file,
                       outpath=op.abspath('./report.json')):

    report = {}
    report['dwi_corrected'] = createSprite4D(dwi_corrected_file)

    b0, colorFA, mask = createB0_ColorFA_Mask_Sprites(dwi_corrected_file,
                                                      color_fa_file,
                                                      anat_mask_file)
    report['b0'] = b0
    report['colorFA'] = colorFA
    report['anat_mask'] = mask
    report['outlier_volumes'] = outlier_indices.tolist()

    with open(eddy_report, 'r') as f:
        report['eddy_report'] = f.readlines()

    report['eddy_params'] = np.genfromtxt(eddy_rms).tolist()
    eddy_qc = load_json(eddy_qc_file)
    report['eddy_quad'] = eddy_qc
    save_json(outpath, report)
    return outpath
