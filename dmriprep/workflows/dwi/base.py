#!/usr/bin/env python
from ..fieldmap import init_fmap_wf


def init_dwi_preproc_wf(subject_id, dwi_file, layout):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import (
        freesurfer as fs,
        fsl,
        mrtrix3,
        ants,
        io as nio,
        utility as niu,
    )
    from nipype import logging

    fmaps = []
    fmaps = layout.get_fieldmap(dwi_file, return_list=True)

    for fmap in fmaps:
        if fmap["suffix"] == "phase":
            fmap_key = "phase1"
        else:
            fmap_key = fmap["suffix"]
        fmap["metadata"] = layout.get_metadata(fmap[fmap_key])

    if not fmaps:
        raise Exception(
            "No fieldmap images found for participant {}. "
            "All workflows require fieldmap images".format(subject_id)
        )

    if fmaps[0]["suffix"] == "fieldmap":
        fmap_wf = init_fmap_wf()

    dwi_wf = pe.Workflow(name="dwi_preproc_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "subject_id",
                "dwi_file",
                "metadata",
                "bvec_file",
                "bval_file",
                "out_dir",
                "eddy_niter",
                "slice_outlier_threshold",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_file", "out_mask", "out_bvec"]),
        name="outputnode",
    )

    # name noise and out_file using fname_presuffix
    denoise = pe.Node(
        mrtrix3.DWIDenoise(noise="noise.nii.gz", out_file="denoised.nii.gz"),
        name="denoise",
    )

    # name unring using fname_presuffix
    unring = pe.Node(mrtrix3.MRDeGibbs(out_file="unringed.nii.gz"), name="unring")

    def gen_index(in_file):
        import os.path as op
        import numpy as np
        import nibabel as nb
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file, suffix="_index.txt", newpath=op.abspath("."), use_ext=False
        )
        vols = nb.load(in_file, mmap=NUMPY_MMAP).get_data().shape[-1]
        index_lines = np.ones((vols,))
        index_lines_reshape = index_lines.reshape(1, index_lines.shape[0])
        np.savetxt(out_file, index_lines_reshape, fmt="%i")
        return out_file

    gen_idx = pe.Node(
        niu.Function(
            input_names=["in_file"], output_names=["out_file"], function=gen_index
        ),
        name="gen_index",
    )

    def gen_acqparams(in_file, metadata):
        import os.path as op
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file, suffix="_acqparams.txt", newpath=op.abspath("."), use_ext=False
        )

        acq_param_dict = {
            "j": "0 1 0 %.7f",
            "j-": "0 -1 0 %.7f",
            "i": "1 0 0 %.7f",
            "i-": "-1 0 0 %.7f",
            "k": "0 0 1 %.7f",
            "k-": "0 0 -1 %.7f",
        }

        pe_dir = metadata.get("PhaseEncodingDirection")
        total_readout = metadata.get("TotalReadoutTime")

        acq_param_lines = acq_param_dict[pe_dir] % total_readout

        with open(out_file, "w") as f:
            f.write(acq_param_lines)

        return out_file

    acqp = pe.Node(
        niu.Function(
            input_names=["in_file", "metadata"],
            output_names=["out_file"],
            function=gen_acqparams,
        ),
        name="acqp",
    )

    def b0_average(in_dwi, in_bval, b0_thresh=10.0, out_file=None):
        """
        A function that averages the *b0* volumes from a DWI dataset.
        As current dMRI data are being acquired with all b-values > 0.0,
        the *lowb* volumes are selected by specifying the parameter b0_thresh.
        .. warning:: *b0* should be already registered (head motion artifact
        should be corrected).
        """
        import numpy as np
        import nibabel as nb
        import os.path as op
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        if out_file is None:
            out_file = fname_presuffix(
                in_dwi, suffix="_avg_b0", newpath=op.abspath(".")
            )

        imgs = np.array(nb.four_to_three(nb.load(in_dwi, mmap=NUMPY_MMAP)))
        bval = np.loadtxt(in_bval)
        index = np.argwhere(bval <= b0_thresh).flatten().tolist()

        b0s = [im.get_data().astype(np.float32) for im in imgs[index]]
        b0 = np.average(np.array(b0s), axis=0)

        hdr = imgs[0].header.copy()
        hdr.set_data_shape(b0.shape)
        hdr.set_xyzt_units("mm")
        hdr.set_data_dtype(np.float32)
        nb.Nifti1Image(b0, imgs[0].affine, hdr).to_filename(out_file)
        return out_file

    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=["in_dwi", "in_bval"],
            output_names=["out_file"],
            function=b0_average,
        ),
        name="b0_avg_pre",
    )

    # dilate mask
    bet_dwi0 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True), name="bet_dwi_pre")

    # mrtrix3.MaskFilter

    ecc = pe.Node(
        fsl.Eddy(repol=True, cnr_maps=True, residuals=True, method="jac"),
        name="fsl_eddy",
    )

    import multiprocessing

    ecc.inputs.num_threads = multiprocessing.cpu_count()

    from numba import cuda

    try:
        if cuda.gpus:
            ecc.inputs.use_cuda = True
    except:
        ecc.inputs.use_cuda = False

    eddy_quad = pe.Node(fsl.EddyQuad(verbose=True), name="eddy_quad")

    get_path = lambda x: x.split(".nii.gz")[0].split("_fix")[0]
    get_qc_path = lambda x: x.split(".nii.gz")[0] + ".qc"

    dwi_bias_corr = pe.Node(ants.N4BiasFieldCorrection(), name="dwi_bias_corr")

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")

    def get_b0_mask_fn(b0_file):
        import nibabel as nib
        from nipype.utils.filemanip import fname_presuffix
        from dipy.segment.mask import median_otsu
        import os

        mask_file = fname_presuffix(
            b0_file, suffix="_mask", newpath=os.path.abspath(".")
        )
        img = nib.load(b0_file)
        data, aff = img.get_data(), img.affine
        _, mask = median_otsu(data, 2, 1)
        nib.Nifti1Image(mask.astype(float), aff).to_filename(mask_file)
        return mask_file

    b0mask_node = pe.Node(
        niu.Function(
            input_names=["b0_file"], output_names=["mask_file"], function=get_b0_mask_fn
        ),
        name="getB0Mask",
    )

    dwi_wf.connect(
        [
            (inputnode, denoise, [("dwi_file", "in_file")]),
            (denoise, unring, [("out_file", "in_file")]),
            (inputnode, avg_b0_0, [("bval_file", "in_bval")]),
            (unring, avg_b0_0, [("out_file", "in_dwi")]),
            (avg_b0_0, bet_dwi0, [("out_file", "in_file")]),
            (inputnode, gen_idx, [("dwi_file", "in_file")]),
            (inputnode, acqp, [("dwi_file", "in_file"), ("metadata", "metadata")]),
            (unring, ecc, [("out_file", "in_file")]),
            (inputnode, ecc, [("bval_file", "in_bval"), ("bvec_file", "in_bvec")]),
            (bet_dwi0, ecc, [("mask_file", "in_mask")]),
            (gen_idx, ecc, [("out_file", "in_index")]),
            (acqp, ecc, [("out_file", "in_acqp")]),
            (ecc, fslroi, [("out_corrected", "in_file")]),
            (fslroi, b0mask_node, [("roi_file", "b0_file")]),
            (
                ecc,
                eddy_quad,
                [
                    (("out_corrected", get_path), "base_name"),
                    (("out_corrected", get_qc_path), "output_dir"),
                ],
            ),
            (inputnode, eddy_quad, [("bval_file", "bval_file")]),
            (ecc, eddy_quad, [("out_rotated_bvecs", "bvec_file")]),
            (b0mask_node, eddy_quad, [("mask_file", "mask_file")]),
            (gen_idx, eddy_quad, [("out_file", "idx_file")]),
            (acqp, eddy_quad, [("out_file", "param_file")]),
            (ecc, outputnode, [("out_corrected", "out_file")]),
            (b0mask_node, outputnode, [("mask_file", "out_mask")]),
            (ecc, outputnode, [("out_rotated_bvecs", "out_bvec")]),
            (
                inputnode,
                fmap_wf,
                [
                    ("fieldmap", "inputnode.fieldmap"),
                    ("magnitude", "inputnode.magnitude"),
                ],
            ),
            (bet_dwi0, fmap_wf, [("out_file", "inputnode.b0_stripped")]),
            (fmap_wf, ecc, [(("outputnode.out_fmap", get_path), "field")]),
            (fmap_wf, eddy_quad, [(("outputnode.out_fmap", get_path), "field")]),
        ]
    )

    return dwi_wf
