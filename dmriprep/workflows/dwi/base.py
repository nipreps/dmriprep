# -*- coding: utf-8 -*-

"""
Orchestrating the dwi preprocessing workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""

from bids import BIDSLayout
from nipype.pipeline import engine as pe
from nipype.interfaces import ants, fsl, mrtrix3, utility as niu
from numba import cuda

from .prep_dwi import init_prep_dwi_wf
from .tensor import init_tensor_wf

# from ..fieldmap.base import init_sdc_prep_wf

FMAP_PRIORITY = {"epi": 0, "fieldmap": 1, "phasediff": 2, "phase": 3, "syn": 4}


def init_dwi_preproc_wf(subject_id, dwi_file, metadata, parameters):

    # fmaps = []
    # synb0 = ""
    #
    # # If use_synb0 set, get synb0 from files
    # if parameters.synb0_dir:
    #     synb0_layout = BIDSLayout(
    #         parameters.synb0_dir, validate=False, derivatives=True
    #     )
    #     synb0 = synb0_layout.get(subject=subject_id, return_type="file")[0]
    # else:
    #     fmaps = parameters.layout.get_fieldmap(dwi_file, return_list=True)
    #     if not fmaps:
    #         raise Exception(
    #             "No fieldmaps found for participant {}. "
    #             "All workflows require fieldmaps".format(subject_id)
    #         )
    #
    #     for fmap in fmaps:
    #         fmap["metadata"] = parameters.layout.get_metadata(
    #             fmap[fmap["suffix"]]
    #         )
    #
    # sdc_wf = init_sdc_prep_wf(
    #     subject_id,
    #     fmaps,
    #     metadata,
    #     parameters.layout,
    #     parameters.bet_mag,
    #     synb0,
    # )

    dwi_wf = pe.Workflow(name="dwi_preproc_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "subject_id",
                "dwi_file",
                "dwi_meta",
                "bvec_file",
                "bval_file",
                "out_dir",
                "eddy_niter",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "out_dwi",
                "out_bval",
                "out_bvec",
                "index",
                "acq_params",
                "out_mask",
                "out_b0_pre",
                "out_b0_mask_pre",
                "out_eddy_quad_json",
                "out_eddy_quad_pdf",
                "out_dtifit_FA",
                "out_dtifit_V1",
                "out_dtifit_sse",
                "out_noise",
            ]
        ),
        name="outputnode",
    )

    dwi_prep_wf = init_prep_dwi_wf(parameters.ignore, parameters.output_resolution)

    def gen_index(in_file):
        import os
        import numpy as np
        import nibabel as nib
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file, suffix="_index.txt", newpath=os.path.abspath("."), use_ext=False
        )
        vols = nib.load(in_file, mmap=NUMPY_MMAP).get_data().shape[-1]
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
        import os
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file,
            suffix="_acqparams.txt",
            newpath=os.path.abspath("."),
            use_ext=False,
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

    dwi_wf.connect(
        [
            (inputnode, gen_idx, [("dwi_file", "in_file")]),
            (inputnode, acqp, [("dwi_file", "in_file"), ("dwi_meta", "metadata")]),
        ]
    )

    def b0_average(in_dwi, in_bval, b0_thresh, out_file=None):
        """
        A function that averages the *b0* volumes from a DWI dataset.
        As current dMRI data are being acquired with all b-values > 0.0,
        the *lowb* volumes are selected by specifying the parameter b0_thresh.
        .. warning:: *b0* should be already registered (head motion artifact
        should be corrected).
        """
        import os
        import numpy as np
        import nibabel as nib
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        if out_file is None:
            out_file = fname_presuffix(
                in_dwi, suffix="_avg_b0", newpath=os.path.abspath(".")
            )

        imgs = np.array(nib.four_to_three(nib.load(in_dwi, mmap=NUMPY_MMAP)))
        bval = np.loadtxt(in_bval)
        index = np.argwhere(bval <= b0_thresh).flatten().tolist()

        b0s = [im.get_data().astype(np.float32) for im in imgs[index]]
        b0 = np.average(np.array(b0s), axis=0)

        hdr = imgs[0].header.copy()
        hdr.set_data_shape(b0.shape)
        hdr.set_xyzt_units("mm")
        hdr.set_data_dtype(np.float32)
        nib.Nifti1Image(b0, imgs[0].affine, hdr).to_filename(out_file)
        return out_file

    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=["in_dwi", "in_bval", "b0_thresh"],
            output_names=["out_file"],
            function=b0_average,
        ),
        name="b0_avg_pre",
    )

    avg_b0_0.inputs.b0_thresh = parameters.b0_thresh

    bet_dwi0 = pe.Node(
        fsl.BET(frac=parameters.bet_dwi, mask=True, robust=True), name="bet_dwi_pre"
    )

    ecc = pe.Node(fsl.Eddy(repol=True, cnr_maps=True, residuals=True), name="fsl_eddy")

    if parameters.omp_nthreads:
        ecc.inputs.num_threads = parameters.omp_nthreads

    try:
        if cuda.gpus:
            ecc.inputs.use_cuda = True
    except:
        ecc.inputs.use_cuda = False

    denoise_eddy = pe.Node(mrtrix3.DWIDenoise(), name="denoise_eddy")

    eddy_quad = pe.Node(fsl.EddyQuad(verbose=True), name="eddy_quad")

    get_path = lambda x: x.split(".nii.gz")[0].split("_fix")[0]
    get_qc_path = lambda x: x.split(".nii.gz")[0] + ".qc"

    if set(parameters.ignore) == set(["denoise", "unring"]):
        wf.connect(
            [
                (inputnode, avg_b0_0, [("dwi_file", "in_file")])(
                    inputnode, ecc, [("dwi_file", "in_file")]
                )
            ]
        )

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")

    bias_correct = pe.Node(mrtrix3.DWIBiasCorrect(use_ants=True), name="bias_correct")

    def get_b0_mask_fn(b0_file):
        import os
        import nibabel as nib
        from nipype.utils.filemanip import fname_presuffix
        from dipy.segment.mask import median_otsu

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
            (inputnode, dwi_prep_wf, [("dwi_file", "inputnode.dwi_file")]),
            (dwi_prep_wf, avg_b0_0, [("outputnode.out_file", "in_dwi")]),
            (inputnode, avg_b0_0, [("bval_file", "in_bval")]),
            (avg_b0_0, bet_dwi0, [("out_file", "in_file")]),
            (dwi_prep_wf, ecc, [("outputnode.out_file", "in_file")]),
            (inputnode, ecc, [("bval_file", "in_bval"), ("bvec_file", "in_bvec")]),
            (bet_dwi0, ecc, [("mask_file", "in_mask")]),
            (gen_idx, ecc, [("out_file", "in_index")]),
            (acqp, ecc, [("out_file", "in_acqp")]),
            (ecc, denoise_eddy, [("out_corrected", "in_file")]),
            (
                ecc,
                bias_correct,
                [("out_corrected", "in_file"), ("out_rotated_bvecs", "in_bvec")],
            ),
            (inputnode, bias_correct, [("bval_file", "in_bval")]),
            (bias_correct, fslroi, [("out_file", "in_file")]),
            (fslroi, b0mask_node, [("roi_file", "b0_file")]),
            (
                ecc,
                eddy_quad,
                [
                    (("out_corrected", get_path), "base_name"),
                    (("out_corrected", get_qc_path), "output_dir"),
                    ("out_rotated_bvecs", "bvec_file"),
                ],
            ),
            (inputnode, eddy_quad, [("bval_file", "bval_file")]),
            (b0mask_node, eddy_quad, [("mask_file", "mask_file")]),
            (gen_idx, eddy_quad, [("out_file", "idx_file")]),
            (acqp, eddy_quad, [("out_file", "param_file")]),
        ]
    )

    tensor_wf = init_tensor_wf()

    dwi_wf.connect(
        [
            (inputnode, tensor_wf, [("bval_file", "inputnode.bval_file")]),
            (b0mask_node, tensor_wf, [("mask_file", "inputnode.mask_file")]),
            (
                ecc,
                tensor_wf,
                [
                    ("out_corrected", "inputnode.dwi_file"),
                    ("out_rotated_bvecs", "inputnode.bvec_file"),
                ],
            ),
        ]
    )

    # # If synb0 is meant to be used
    # if parameters.synb0_dir:
    #     dwi_wf.connect(
    #         [
    #             (
    #                 sdc_wf,
    #                 ecc,
    #                 [
    #                     ("outputnode.out_topup", "in_topup_fieldcoef"),
    #                     ("outputnode.out_movpar", "in_topup_movpar"),
    #                 ],
    #             ),
    #             (
    #                 sdc_wf,
    #                 eddy_quad,
    #                 [("outputnode.out_enc_file", "param_file")],
    #             ),
    #         ]
    #     )
    #     ecc.inputs.in_acqp = parameters.acqp_file
    # else:
    #     # Decide what ecc will take: topup or fmap
    #     fmaps.sort(key=lambda fmap: FMAP_PRIORITY[fmap["suffix"]])
    #     fmap = fmaps[0]
    #     # Else If epi files detected
    #     if fmap["suffix"] == "epi":
    #         dwi_wf.connect(
    #             [
    #                 (
    #                     sdc_wf,
    #                     ecc,
    #                     [
    #                         ("outputnode.out_topup", "in_topup_fieldcoef"),
    #                         ("outputnode.out_enc_file", "in_acqp"),
    #                         ("outputnode.out_movpar", "in_topup_movpar"),
    #                     ],
    #                 ),
    #                 (
    #                     sdc_wf,
    #                     eddy_quad,
    #                     [("outputnode.out_enc_file", "param_file")],
    #                 ),
    #             ]
    #         )
    #     # Otherwise (fieldmaps)
    #     else:
    #         dwi_wf.connect(
    #             [
    #                 (
    #                     sdc_wf,
    #                     ecc,
    #                     [(("outputnode.out_fmap", get_path), "field")],
    #                 ),
    #                 (acqp, ecc, [("out_file", "in_acqp")]),
    #                 (acqp, eddy_quad, [("out_file", "param_file")]),
    #             ]
    #         )

    dwi_wf.connect(
        [
            (ecc, outputnode, [("out_corrected", "out_dwi")]),
            (inputnode, outputnode, [("bval_file", "out_bval")]),
            (ecc, outputnode, [("out_rotated_bvecs", "out_bvec")]),
            (gen_idx, outputnode, [("out_file", "index")]),
            (acqp, outputnode, [("out_file", "acq_params")]),
            (b0mask_node, outputnode, [("mask_file", "out_mask")]),
            (avg_b0_0, outputnode, [("out_file", "out_b0_pre")]),
            (bet_dwi0, outputnode, [("mask_file", "out_b0_mask_pre")]),
            (
                eddy_quad,
                outputnode,
                [("qc_json", "out_eddy_quad_json"), ("qc_pdf", "out_eddy_quad_pdf")],
            ),
            (
                tensor_wf,
                outputnode,
                [
                    ("outputnode.FA_file", "out_dtifit_FA"),
                    ("outputnode.V1_file", "out_dtifit_V1"),
                    ("outputnode.sse_file", "out_dtifit_sse"),
                ],
            ),
        ]
    )

    return dwi_wf
