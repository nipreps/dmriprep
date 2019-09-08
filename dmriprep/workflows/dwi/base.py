# -*- coding: utf-8 -*-
import os


def init_dwi_preproc_wf(
    sub,
    ses,
    dwi_file,
    fbval,
    fbvec,
    metadata,
    out_dir,
    sdc_method,
    denoise_strategy,
    vox_size,
    outlier_thresh,
    omp_nthreads,
    eddy_mem_gb
):
    import json
    import shutil
    from numba import cuda
    import pkg_resources
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu
    from nipype.interfaces import fsl
    from nipype.algorithms.rapidart import ArtifactDetect
    from dmriprep.interfaces import fsl_extensions
    from dmriprep.utils import core, qc
    from shutil import which

    import_list = [
        "import sys",
        "import os",
        "import numpy as np",
        "import nibabel as nib",
        "import warnings",
        'warnings.filterwarnings("ignore")',
    ]

    subdir = "%s%s%s" % (out_dir, "/", sub)
    if not os.path.isdir(subdir):
        os.mkdir(subdir)
    sesdir = "%s%s%s%s%s" % (out_dir, "/", sub, "/ses-", ses)
    if not os.path.isdir(sesdir):
        os.mkdir(sesdir)

    eddy_cfg_file = pkg_resources.resource_filename('dmriprep.config', "eddy_params.json")

    # Create dictionary of eddy args
    with open(eddy_cfg_file, "r") as f:
        eddy_args = json.load(f)

    wf = pe.Workflow(name="single_subject_dmri_" + str(ses))
    wf.base_dir = sesdir
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_file",
                "fbvec",
                "fbval",
                "metadata",
                "sub",
                "ses",
                "sesdir",
                "denoise_strategy",
                "vox_size",
                "outlier_thresh",
                "eddy_cfg_file",
                "omp_nthreads"
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.dwi_file = dwi_file
    inputnode.inputs.fbvec = fbvec
    inputnode.inputs.fbval = fbval
    inputnode.inputs.metadata = metadata
    inputnode.inputs.sub = sub
    inputnode.inputs.ses = ses
    inputnode.inputs.sesdir = sesdir
    inputnode.inputs.denoise_strategy = denoise_strategy
    inputnode.inputs.vox_size = vox_size
    inputnode.inputs.outlier_thresh = outlier_thresh
    inputnode.inputs.eddy_cfg_file = eddy_cfg_file
    inputnode.inputs.omp_nthreads = omp_nthreads

    check_orient_and_dims_dwi_node = pe.Node(
        niu.Function(
            input_names=["infile", "vox_size", "bvecs", "outdir"],
            output_names=["outfile", "bvecs"],
            function=qc.check_orient_and_dims,
            imports=import_list,
        ),
        name="check_orient_and_dims_dwi_node",
    )
    check_orient_and_dims_dwi_node._mem_gb = 1

    # Make gtab and get b0 indices
    correct_vecs_and_make_b0s_node = pe.Node(
        niu.Function(
            input_names=["fbval", "fbvec", "dwi_file", "sesdir"],
            output_names=["initial_mean_b0", "gtab_file", "b0_vols", "b0s", "slm"],
            function=core.correct_vecs_and_make_b0s,
            imports=import_list,
        ),
        name="correct_vecs_and_make_b0s",
    )
    correct_vecs_and_make_b0s_node._mem_gb = 1

    btr_node_premoco = pe.Node(fsl.BET(), name="bet_pre_moco")
    btr_node_premoco.inputs.mask = True
    btr_node_premoco.inputs.frac = 0.2
    btr_node_premoco._mem_gb = 1

    apply_mask_premoco_node = pe.Node(fsl.ApplyMask(), name="apply_mask_pre_moco")
    apply_mask_premoco_node._mem_gb = 1

    # Detect and remove motion outliers
    fsl_split_node = pe.Node(fsl.Split(dimension="t"), name="fsl_split")
    fsl_split_node._mem_gb = 1

    coreg = pe.MapNode(
        fsl.FLIRT(no_search=True, interp="spline", padding_size=1, dof=6),
        name="coregistration",
        iterfield=["in_file"],
    )
    coreg._mem_gb = 1

    get_motion_params_node = pe.Node(
        niu.Function(
            input_names=["flirt_mats"],
            output_names=["motion_params"],
            function=core.get_flirt_motion_parameters,
            imports=import_list,
        ),
        name="get_motion_params",
    )
    get_motion_params_node._mem_gb = 0.5

    fsl_merge_node = pe.Node(fsl.Merge(dimension="t"), name="fsl_merge")
    fsl_merge_node._mem_gb = 2

    art_node = pe.Node(interface=ArtifactDetect(), name="art")
    art_node.inputs.use_differences = [True, True]
    art_node.inputs.save_plot = False
    art_node.inputs.use_norm = True
    # scan-to-scan head-motion composite changes
    art_node.inputs.norm_threshold = 3
    # z-score scan-to-scan global signal changes
    art_node.inputs.zintensity_threshold = 9
    art_node.inputs.mask_type = "spm_global"
    art_node.inputs.parameter_source = "FSL"
    art_node._mem_gb = 1

    drop_outliers_fn_node = pe.Node(
        niu.Function(
            input_names=["in_file", "in_bval", "in_bvec", "drop_scans", "in_sigma"],
            output_names=["out_file", "out_bval", "out_bvec", "out_sigma"],
            function=core.drop_outliers_fn,
            imports=import_list,
        ),
        name="drop_outliers_fn",
    )
    drop_outliers_fn_node._mem_gb = 1

    make_gtab_node = pe.Node(
        niu.Function(
            input_names=["fbval", "fbvec", "sesdir", "final"],
            output_names=["gtab_file", "gtab", "final_bval_path", "final_bvec_path"],
            function=core.make_gtab,
            imports=import_list,
        ),
        name="make_gtab",
    )
    make_gtab_node.inputs.final = False
    make_gtab_node._mem_gb = 1

    estimate_noise_node = pe.Node(
        niu.Function(
            input_names=["in_file", "gtab_file", "mask", "denoise_strategy"],
            output_names=["sigma_path"],
            function=core.estimate_sigma,
            imports=import_list,
        ),
        name="estimate_noise",
    )
    estimate_noise_node._mem_gb = omp_nthreads*2
    estimate_noise_node.n_procs = omp_nthreads

    # Suppress gibbs ringing
    suppress_gibbs_node = pe.Node(
        niu.Function(
            input_names=["in_file", "sesdir"],
            output_names=["gibbs_free_file"],
            function=core.suppress_gibbs,
            imports=import_list,
        ),
        name="suppress_gibbs",
    )
    suppress_gibbs_node._mem_gb = 12
    suppress_gibbs_node.n_procs = 6

    extract_metadata_node = pe.Node(
        niu.Function(
            input_names=["metadata"],
            output_names=["spec_acqps", "vol_legend"],
            function=core.extract_metadata,
            imports=import_list,
        ),
        name="extract_metadata",
    )
    extract_metadata_node._mem_gb = 0.5

    # Gather TOPUP/EDDY inputs
    check_shelled_node = pe.Node(
        niu.Function(
            input_names=["gtab_file"],
            output_names=["check_shelled"],
            function=core.check_shelled,
            imports=import_list,
        ),
        name="check_shelled",
    )
    check_shelled_node._mem_gb = 0.5

    get_topup_inputs_node = pe.Node(
        niu.Function(
            input_names=["dwi_file", "sesdir", "spec_acqp", "b0_vols", "b0s", "vol_legend"],
            output_names=[
                "datain_file",
                "imain_output",
                "example_b0",
                "datain_lines",
                "topup_config",
                "susceptibility_args"
            ],
            function=core.topup_inputs_from_dwi_files,
            imports=import_list,
        ),
        name="get_topup_inputs",
    )
    get_topup_inputs_node._mem_gb = 0.5

    get_eddy_inputs_node = pe.Node(
        niu.Function(
            input_names=["sesdir", "gtab_file"],
            output_names=["index_file"],
            function=core.eddy_inputs_from_dwi_files,
            imports=import_list,
        ),
        name="get_eddy_inputs",
    )
    get_eddy_inputs_node._mem_gb = 0.5

    # Run TOPUP
    topup_node = pe.Node(fsl.TOPUP(), name="topup")
    topup_node._mem_gb = 14
    topup_node.n_procs = 8
    topup_node.interface.mem_gb = 14
    topup_node.interface.n_procs = 8

    # Run BET on mean b0 of TOPUP-corrected output
    make_mean_b0_node = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["mean_file_out"],
            function=core.make_mean_b0,
            imports=import_list,
        ),
        name="make_mean_b0",
    )
    btr_node = pe.Node(fsl.BET(), name="bet")
    btr_node.inputs.mask = True
    btr_node.inputs.frac = 0.2
    btr_node._mem_gb = 1

    # Run EDDY
    eddy_node = pe.Node(fsl_extensions.ExtendedEddy(**eddy_args), name="eddy")
    eddy_node.inputs.num_threads = omp_nthreads
    eddy_node._mem_gb = eddy_mem_gb
    eddy_node.n_procs = omp_nthreads
    eddy_node.interface.mem_gb = eddy_mem_gb
    eddy_node.interface.n_procs = omp_nthreads

    make_basename_node = pe.Node(
        niu.Function(
            input_names=["out_corrected"],
            output_names=["base_name"],
            function=core.make_basename,
            imports=import_list,
        ),
        name="make_basename",
    )
    btr_node._mem_gb = 0.5

    # Handle gpu case
    try:
        if cuda.gpus:
            eddy_node.inputs.use_cuda = True
    except:
        eddy_node.inputs.use_cuda = False

    eddy_quad = pe.Node(fsl.EddyQuad(verbose=True), name='eddy_quad')
    eddy_quad.inputs.verbose = True
    eddy_qc_outdir = sesdir + '/eddy_quad'
    if os.path.isdir(eddy_qc_outdir):
        shutil.rmtree(eddy_qc_outdir)
    eddy_quad.inputs.output_dir = eddy_qc_outdir
    eddy_quad._mem_gb = 1

    make_gtab_node_final = pe.Node(
        niu.Function(
            input_names=["fbval", "fbvec", "sesdir", "final"],
            output_names=["gtab_file", "gtab", "final_bval_path", "final_bvec_path"],
            function=core.make_gtab,
            imports=import_list,
        ),
        name="make_gtab_final",
    )
    make_gtab_node_final.inputs.final = True
    make_gtab_node_final._mem_gb = 1

    apply_mask_node = pe.Node(fsl.ApplyMask(), name="apply_mask")
    apply_mask_node._mem_gb = 1

    id_outliers_from_eddy_report_node = pe.Node(
        niu.Function(
            input_names=["outlier_report", "threshold", "dwi_file"],
            output_names=["drop_scans", "outpath"],
            function=core.id_outliers_fn,
            imports=import_list,
        ),
        name="id_outliers_from_eddy_report",
    )
    id_outliers_from_eddy_report_node._mem_gb = 1

    drop_outliers_from_eddy_report_node = pe.Node(
        niu.Function(
            input_names=["in_file", "in_bval", "in_bvec", "drop_scans", "in_sigma"],
            output_names=["out_file", "out_bval", "out_bvec", "out_sigma"],
            function=core.drop_outliers_fn,
            imports=import_list,
        ),
        name="drop_outliers_from_eddy_report",
    )
    drop_outliers_from_eddy_report_node._mem_gb = 1

    denoise_node = pe.Node(
        niu.Function(
            input_names=["in_file", "sesdir", "gtab_file", "mask", "denoise_strategy", "sigma_path", "omp_nthreads"],
            output_names=["denoised_file"],
            function=core.denoise,
            imports=import_list,
        ),
        name="denoise",
    )
    if denoise_strategy == 'nlsam':
        denoise_node._mem_gb = omp_nthreads*6
    else:
        denoise_node._mem_gb = omp_nthreads*4
    denoise_node.n_procs = omp_nthreads

    which('N4BiasFieldCorrection')
    if which('N4BiasFieldCorrection') is not None:
        no_ants = False
    else:
        print('Warning: could not import ANTS so N4BiasFieldCorrection cannot be performed.')
        no_ants = True

    rename_final_preprocessed_file_node = pe.Node(
        niu.Function(
            input_names=["in_file", "sesdir"],
            output_names=["out_file"],
            function=core.rename_final_preprocessed_file,
            imports=import_list,
        ),
        name="rename_final_preprocessed_file",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["preprocessed_data", "final_bvec", "final_bval",
                                      "out_eddy_quad_pdf", "out_eddy_quad_json"]),
        name="outputnode",
    )

    wf.connect([(inputnode, check_orient_and_dims_dwi_node, [("fbvec", "bvecs"),
                                                             ("dwi_file", "infile"),
                                                             ("vox_size", "vox_size"),
                                                             ("sesdir", "outdir")]),
                (inputnode, correct_vecs_and_make_b0s_node, [("fbval", "fbval"),
                                                             ("sesdir", "sesdir")]),
                (check_orient_and_dims_dwi_node, correct_vecs_and_make_b0s_node, [("bvecs", "fbvec"),
                                                                                  ("outfile", "dwi_file")]),
                (correct_vecs_and_make_b0s_node, btr_node_premoco, [("initial_mean_b0", "in_file")]),
                (btr_node_premoco, apply_mask_premoco_node, [("mask_file", "mask_file")]),
                (check_orient_and_dims_dwi_node, apply_mask_premoco_node, [("outfile", "in_file")]),
                (apply_mask_premoco_node, fsl_split_node, [("out_file", "in_file")]),
                (correct_vecs_and_make_b0s_node, coreg, [("initial_mean_b0", "reference")]),
                (fsl_split_node, coreg, [("out_files", "in_file")]),
                (coreg, get_motion_params_node, [("out_matrix_file", "flirt_mats")]),
                (coreg, fsl_merge_node, [("out_file", "in_files")]),
                (get_motion_params_node, art_node, [("motion_params", "realignment_parameters")]),
                (fsl_merge_node, art_node, [("merged_file", "realigned_files")]),
                (check_orient_and_dims_dwi_node, drop_outliers_fn_node, [("bvecs", "in_bvec"),
                                                                         ("outfile", "in_file")]),
                (inputnode, drop_outliers_fn_node, [("fbval", "in_bval")]),
                (art_node, drop_outliers_fn_node, [("outlier_files", "drop_scans")]),
                (inputnode, estimate_noise_node, [("denoise_strategy", "denoise_strategy")]),
                (drop_outliers_fn_node, make_gtab_node, [("out_bvec", "fbvec"),
                                                         ("out_bval", "fbval")]),
                (inputnode, make_gtab_node, [("sesdir", "sesdir")]),
                (drop_outliers_fn_node, estimate_noise_node, [("out_file", "in_file")]),
                (btr_node_premoco, estimate_noise_node, [("mask_file", "mask")]),
                (make_gtab_node, estimate_noise_node, [("gtab_file", "gtab_file")]),
                (inputnode, suppress_gibbs_node, [("sesdir", "sesdir")]),
                (drop_outliers_fn_node, suppress_gibbs_node, [("out_file", "in_file")]),
                (suppress_gibbs_node, eddy_node, [("gibbs_free_file", "in_file")]),
                (inputnode, extract_metadata_node, [("metadata", "metadata")]),
                (make_gtab_node, check_shelled_node, [("gtab_file", "gtab_file")]),
                (inputnode, get_eddy_inputs_node, [("sesdir", "sesdir")]),
                (make_gtab_node, get_eddy_inputs_node, [("gtab_file", "gtab_file")]),
                (extract_metadata_node, get_eddy_inputs_node, [("spec_acqps", "spec_acqp")]),
                (make_mean_b0_node, btr_node, [("mean_file_out", "in_file")]),
                (check_shelled_node, eddy_node, [("check_shelled", "is_shelled")]),
                (correct_vecs_and_make_b0s_node, eddy_node, [("slm", "slm")]),
                (btr_node, eddy_node, [("mask_file", "in_mask")]),
                (get_eddy_inputs_node, eddy_node, [("index_file", "in_index")]),
                (drop_outliers_fn_node, eddy_node, [("out_bval", "in_bval"),
                                                    ("out_bvec", "in_bvec")]),
                (eddy_node, id_outliers_from_eddy_report_node, [("out_corrected", "dwi_file"),
                                                                ("out_outlier_report", "outlier_report")]),
                (inputnode, id_outliers_from_eddy_report_node, [("outlier_thresh", "threshold")]),
                (id_outliers_from_eddy_report_node, drop_outliers_from_eddy_report_node, [("drop_scans", "drop_scans")]),
                (eddy_node, drop_outliers_from_eddy_report_node, [("out_corrected", "in_file"),
                                                                  ("out_rotated_bvecs", "in_bvec")]),
                (estimate_noise_node, drop_outliers_from_eddy_report_node, [("sigma_path", "in_sigma")]),
                (drop_outliers_fn_node, drop_outliers_from_eddy_report_node, [("out_bval", "in_bval")]),
                (drop_outliers_from_eddy_report_node, apply_mask_node, [("out_file", "in_file")]),
                (btr_node, apply_mask_node, [("mask_file", "mask_file")]),
                (inputnode, denoise_node, [("sesdir", "sesdir"),
                                           ('omp_nthreads', 'omp_nthreads'),
                                           ("denoise_strategy", "denoise_strategy")]),
                (drop_outliers_from_eddy_report_node, denoise_node, [("out_sigma", "sigma_path")]),
                (btr_node, denoise_node, [("mask_file", "mask")]),
                (make_gtab_node_final, denoise_node, [("gtab_file", "gtab_file")]),
                (apply_mask_node, denoise_node, [("out_file", "in_file")]),
                (drop_outliers_from_eddy_report_node, make_gtab_node_final, [("out_bvec", "fbvec")]),
                (drop_outliers_from_eddy_report_node, make_gtab_node_final, [("out_bval", "fbval")]),
                (inputnode, make_gtab_node_final, [("sesdir", "sesdir")]),
                (make_gtab_node_final, outputnode, [("final_bvec_path", "final_bvec")]),
                (inputnode, rename_final_preprocessed_file_node, [("sesdir", "sesdir")]),
                (eddy_node, eddy_quad, [("out_rotated_bvecs", "bvec_file")]),
                (eddy_node, make_basename_node, [("out_corrected", "out_corrected")]),
                (make_basename_node, eddy_quad, [("base_name", "base_name")]),
                (drop_outliers_fn_node, eddy_quad, [("out_bval", "bval_file")]),
                (make_gtab_node_final, outputnode, [("final_bval_path", "final_bval")]),
                (btr_node, eddy_quad, [("mask_file", "mask_file")]),
                (get_eddy_inputs_node, eddy_quad, [("index_file", "idx_file")]),
                (eddy_quad, outputnode, [('qc_json', 'out_eddy_quad_json'),
                                         ('qc_pdf', 'out_eddy_quad_pdf')])
                ])

    if no_ants is True:
        wf.connect([
            (denoise_node, rename_final_preprocessed_file_node, [("denoised_file", "in_file")]),
            (rename_final_preprocessed_file_node, outputnode, [("out_file", "preprocessed_data")])
        ])
    else:
        from nipype.interfaces import ants
        n4 = pe.Node(ants.N4BiasFieldCorrection(dimension=3, save_bias=True,
                                                bspline_fitting_distance=600, bspline_order=4,
                                                n_iterations=[50, 50, 40, 30], shrink_factor=2,
                                                convergence_threshold=1e-6),
                     name='Bias_b0')
        n4.inputs.num_threads = omp_nthreads
        n4.n_procs = omp_nthreads
        n4._mem_gb = omp_nthreads*4
        n4.interface.n_procs = omp_nthreads
        n4.interface.mem_gb = omp_nthreads*4

        split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
        split._mem_gb = 1
        mult = pe.MapNode(fsl.MultiImageMaths(op_string='-div %s'), iterfield=['in_file'],
                          name='RemoveBiasOfDWIs')
        mult._mem_gb = 1
        thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'], name='RemoveNegative')
        thres._mem_gb = 1
        merge = pe.Node(fsl.utils.Merge(dimension='t'), name='MergeDWIs')
        merge._mem_gb = 1

        wf.connect([
            (denoise_node, split, [("denoised_file", "in_file")]),
            (make_mean_b0_node, n4, [("mean_file_out", 'input_image')]),
            (btr_node, n4, [("mask_file", 'mask_image')]),
            (n4, mult, [('bias_image', 'operand_files')]),
            (split, mult, [('out_files', 'in_file')]),
            (mult, thres, [('out_file', 'in_file')]),
            (thres, merge, [('out_file', 'in_files')]),
            (merge, rename_final_preprocessed_file_node, [('merged_file', "in_file")]),
            (rename_final_preprocessed_file_node, outputnode, [("out_file", "preprocessed_data")])
        ])

    # TODO: Flesh out the sdc-fieldmap option
    # if sdc_method == 'fieldmap':
    #     wf.connect([
    #         (inputnode, eddy_node, [('fieldmap_file', 'field')])
    #     ])

    if sdc_method == 'topup':
        wf.connect([
            (drop_outliers_fn_node, get_topup_inputs_node, [("out_file", "dwi_file")]),
            (inputnode, get_topup_inputs_node, [("sesdir", "sesdir")]),
            (correct_vecs_and_make_b0s_node, get_topup_inputs_node, [("b0_vols", "b0_vols"),
                                                                     ("b0s", "b0s")]),
            (extract_metadata_node, get_topup_inputs_node, [("spec_acqps", "spec_acqp"),
                                                            ("vol_legend", "vol_legend")]),
            (get_topup_inputs_node, topup_node, [("datain_file", "encoding_file"),
                                                 ("imain_output", "in_file"),
                                                 ("topup_config", "config")]),
            (topup_node, make_mean_b0_node, [("out_corrected", "in_file")]),
            (topup_node, eddy_node, [("out_movpar", "in_topup_movpar"),
                                     ("out_fieldcoef", "in_topup_fieldcoef")]),
            (get_topup_inputs_node, eddy_node, [("datain_file", "in_acqp"), ("susceptibility_args", "args")]),
            (topup_node, eddy_quad, [("out_field", "field")]),
            (get_topup_inputs_node, eddy_quad, [("datain_file", "param_file")]),
        ])

    return wf


def init_base_wf(
    bids_dict,
    output_dir,
    sdc_method,
    denoise_strategy,
    vox_size,
    outlier_thresh,
    omp_nthreads,
    work_dir
):
    import os
    import nibabel as nib
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu
    from dmriprep.workflows.dwi.base import init_dwi_preproc_wf, wf_multi_session
    from dmriprep.workflows.dwi.util import init_dwi_concat_wf
    from dmriprep.utils import core

    participant = list(bids_dict.keys())[0]
    sessions = list(bids_dict[participant].keys())

    # Multiple sessions case
    if len(sessions) > 1:
        wf = wf_multi_session(bids_dict,
                              participant,
                              sessions,
                              output_dir,
                              sdc_method,
                              denoise_strategy,
                              vox_size,
                              outlier_thresh,
                              omp_nthreads,
                              work_dir)
    else:
        # Single session case
        session = sessions[0]
        if len(bids_dict[participant][session].keys()) == 1:
            dwi_file = bids_dict[participant][session][1]['dwi_file']
            fbvec = bids_dict[participant][session][1]['fbvec']
            fbval = bids_dict[participant][session][1]['fbval']
            metadata = bids_dict[participant][session][1]['metadata']

            dwi_img = nib.load(dwi_file)
            if vox_size == '2mm':
                res_factor = dwi_img.header.get_zooms()[1]/2
            elif vox_size == '1mm':
                res_factor = dwi_img.header.get_zooms()[1]/1
            else:
                res_factor = 1
            exp_bytes = res_factor * 24 * dwi_img.shape[0] * dwi_img.shape[1] * dwi_img.shape[2] * dwi_img.shape[3]
            eddy_mem_gb = core.bytesto(exp_bytes, to='g', bsize=1024)

            wf = init_dwi_preproc_wf(participant,
                                     session,
                                     dwi_file,
                                     fbval,
                                     fbvec,
                                     metadata,
                                     output_dir,
                                     sdc_method,
                                     denoise_strategy,
                                     vox_size,
                                     outlier_thresh,
                                     omp_nthreads,
                                     eddy_mem_gb)
        else:
            # Multiple runs case
            dwi_files = []
            fbvecs = []
            fbvals = []
            metadata_files = []
            for acq in bids_dict[participant][session].keys():
                dwi_files.append(bids_dict[participant][session][acq]['dwi_file'])
                fbvecs.append(bids_dict[participant][session][acq]['fbvec'])
                fbvals.append(bids_dict[participant][session][acq]['fbval'])
                metadata_files.append(bids_dict[participant][session][acq]['metadata'])

            wf_multi_run_name = "%s%s%s%s" % ('wf_multi_run_', participant, '_', session)
            wf = pe.Workflow(name=wf_multi_run_name)
            wf.base_dir = work_dir + '/' + wf_multi_run_name
            if not os.path.isdir(wf.base_dir):
                os.mkdir(wf.base_dir)

            dwi_img = nib.load(dwi_files[0])
            if vox_size == '2mm':
                res_factor = dwi_img.header.get_zooms()[1]/2
            elif vox_size == '1mm':
                res_factor = dwi_img.header.get_zooms()[1]/1
            else:
                res_factor = 1
            exp_bytes = res_factor * 24 * dwi_img.shape[0] * dwi_img.shape[1] * dwi_img.shape[2] * dwi_img.shape[3]
            eddy_mem_gb = core.bytesto(exp_bytes, to='g', bsize=1024)

            meta_inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_files",
                                                                   "fbvecs",
                                                                   "fbvals",
                                                                   "metadata_files",
                                                                   "sub",
                                                                   "ses",
                                                                   "output_dir",
                                                                   "sdc_method",
                                                                   "denoise_strategy",
                                                                   "vox_size",
                                                                   "outlier_thresh",
                                                                   "omp_nthreads",
                                                                   "eddy_mem_gb"]),
                                     name='meta_inputnode')

            meta_inputnode.inputs.dwi_files = dwi_files
            meta_inputnode.inputs.fbvecs = fbvecs
            meta_inputnode.inputs.fbvals = fbvals
            meta_inputnode.inputs.metadata_files = metadata_files
            meta_inputnode.inputs.sub = participant
            meta_inputnode.inputs.ses = session
            meta_inputnode.inputs.output_dir = output_dir
            meta_inputnode.inputs.sdc_method = sdc_method
            meta_inputnode.inputs.denoise_strategy = denoise_strategy
            meta_inputnode.inputs.vox_size = vox_size
            meta_inputnode.inputs.outlier_thresh = outlier_thresh
            meta_inputnode.inputs.omp_nthreads = omp_nthreads
            meta_inputnode.inputs.eddy_mem_gb = eddy_mem_gb

            wf_concat = init_dwi_concat_wf(dwi_files, fbvals, fbvecs, metadata_files, participant, session, output_dir)

            wf_dwi_preproc = init_dwi_preproc_wf(participant,
                                                 session,
                                                 dwi_files[0],
                                                 fbvals[0],
                                                 fbvecs[0],
                                                 metadata_files[0],
                                                 output_dir,
                                                 sdc_method,
                                                 denoise_strategy,
                                                 vox_size,
                                                 outlier_thresh,
                                                 omp_nthreads,
                                                 eddy_mem_gb)

            meta_outputnode = pe.Node(
                niu.IdentityInterface(fields=["preprocessed_data", "final_bvec", "final_bval",
                                              "out_eddy_quad_json", "out_eddy_quad_pdf"]),
                name="meta_outputnode",
            )
            wf.add_nodes([meta_inputnode])
            wf.add_nodes([wf_concat])
            wf.add_nodes([wf_dwi_preproc])
            wf.add_nodes([meta_outputnode])

            wf.connect([(meta_inputnode, wf.get_node('dwi_concat_wf').get_node('inputnode'),
                         [('dwi_files', 'dwi_files'),
                          ('fbvecs', 'fbvecs'),
                          ('fbvals', 'fbvals'),
                          ('metadata_files', 'metadata_files'),
                          ('sub', 'participant'),
                          ('ses', 'session'),
                          ('output_dir', 'output_dir')]),
                        (wf.get_node('dwi_concat_wf').get_node('outputnode'), wf_dwi_preproc.get_node('inputnode'),
                         [('dwi_file', 'dwi_file'),
                          ('bvec_file', 'fbvec'),
                          ('bval_file', 'fbval'),
                          ('metadata_file', 'metadata')]),
                        (meta_inputnode, wf_dwi_preproc.get_node('inputnode'),
                         [('sub', 'participant'),
                          ('ses', 'session'),
                          ('output_dir', 'output_dir'),
                          ('sdc_method', 'sdc_method'),
                          ('denoise_strategy', 'denoise_strategy'),
                          ('vox_size', 'vox_size'),
                          ('outlier_thresh', 'outlier_thresh'),
                          ('omp_nthreads', 'omp_nthreads'),
                          ('eddy_mem_gb', 'eddy_mem_gb')]),
                        (wf_dwi_preproc.get_node('outputnode'), meta_outputnode,
                         [("final_bval", "final_bval"),
                          ("preprocessed_data", "preprocessed_data"),
                          ("final_bvec", "final_bvec"),
                          ("out_eddy_quad_json", "out_eddy_quad_json"),
                          ("out_eddy_quad_pdf", "out_eddy_quad_pdf")])
                    ])

            wf.get_node(wf_dwi_preproc.name).get_node('check_orient_and_dims_dwi_node')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('correct_vecs_and_make_b0s')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('bet_pre_moco')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('bet_pre_moco').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('apply_mask_pre_moco')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('apply_mask_pre_moco').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('fsl_split')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('fsl_split').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('coregistration')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('coregistration').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('get_motion_params')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('fsl_merge')._mem_gb = 2
            wf.get_node(wf_dwi_preproc.name).get_node('fsl_merge').interface._mem_gb = 2
            wf.get_node(wf_dwi_preproc.name).get_node('art')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('art').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('drop_outliers_fn')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('make_gtab')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('extract_metadata')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('check_shelled')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('get_topup_inputs')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('get_eddy_inputs')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('make_mean_b0')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('make_basename')._mem_gb = 0.5
            wf.get_node(wf_dwi_preproc.name).get_node('eddy_quad')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('eddy_quad').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('make_gtab_final')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('apply_mask')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('apply_mask').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('id_outliers_from_eddy_report')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('drop_outliers_from_eddy_report')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('SplitDWIs')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('SplitDWIs').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('RemoveBiasOfDWIs')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('RemoveBiasOfDWIs').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('RemoveNegative')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('RemoveNegative').interface._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('MergeDWIs')._mem_gb = 1
            wf.get_node(wf_dwi_preproc.name).get_node('MergeDWIs').interface._mem_gb = 1

            wf.get_node(wf_dwi_preproc.name).get_node('topup')._n_procs = 8
            wf.get_node(wf_dwi_preproc.name).get_node('topup')._mem_gb = 14
            wf.get_node(wf_dwi_preproc.name).get_node('topup').interface.n_procs = 8
            wf.get_node(wf_dwi_preproc.name).get_node('topup').interface.mem_gb = 14
            wf.get_node(wf_dwi_preproc.name).get_node('Bias_b0')._n_procs = omp_nthreads
            wf.get_node(wf_dwi_preproc.name).get_node('Bias_b0')._mem_gb = omp_nthreads*4
            wf.get_node(wf_dwi_preproc.name).get_node('Bias_b0').interface.n_procs = omp_nthreads
            wf.get_node(wf_dwi_preproc.name).get_node('Bias_b0').interface.mem_gb = omp_nthreads*4
            wf.get_node(wf_dwi_preproc.name).get_node('eddy')._n_procs = omp_nthreads
            wf.get_node(wf_dwi_preproc.name).get_node('eddy')._mem_gb = eddy_mem_gb
            wf.get_node(wf_dwi_preproc.name).get_node('eddy').interface.n_procs = omp_nthreads
            wf.get_node(wf_dwi_preproc.name).get_node('eddy').interface.mem_gb = eddy_mem_gb
            wf.get_node(wf_dwi_preproc.name).get_node('suppress_gibbs')._n_procs = 6
            wf.get_node(wf_dwi_preproc.name).get_node('suppress_gibbs')._mem_gb = 12
            wf.get_node(wf_dwi_preproc.name).get_node('estimate_noise')._n_procs = omp_nthreads
            wf.get_node(wf_dwi_preproc.name).get_node('estimate_noise')._mem_gb = omp_nthreads*2
            wf.get_node(wf_dwi_preproc.name).get_node('denoise')._n_procs = omp_nthreads
            if denoise_strategy == 'nlsam':
                wf.get_node(wf_dwi_preproc.name).get_node('denoise')._mem_gb = omp_nthreads*6
            else:
                wf.get_node(wf_dwi_preproc.name).get_node('denoise')._mem_gb = omp_nthreads*4


        cfg = dict(execution={'stop_on_first_crash': False, 'crashfile_format': 'txt', 'parameterize_dirs': True,
                              'display_variable': ':0', 'job_finished_timeout': 120, 'matplotlib_backend': 'Agg',
                              'plugin': 'MultiProc', 'use_relative_paths': True, 'remove_unnecessary_outputs': False,
                              'remove_node_directories': False})
        for key in cfg.keys():
            for setting, value in cfg[key].items():
                wf.config[key][setting] = value

    return wf


# Multi-session pipeline
def wf_multi_session(bids_dict,
                     participant,
                     sessions,
                     output_dir,
                     sdc_method,
                     denoise_strategy,
                     vox_size,
                     outlier_thresh,
                     omp_nthreads,
                     work_dir):
    """A function interface for generating multiple single-session workflows -- i.e. a 'multi-session' workflow"""
    import os
    import nibabel as nib
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu
    from dmriprep.workflows.dwi.base import init_dwi_preproc_wf
    from dmriprep.workflows.dwi.util import init_dwi_concat_wf
    from dmriprep.utils import core

    wf_multi_session_name = "%s%s%s" % ('wf_multi_session_', participant, '_multi_session')
    wf_multi = pe.Workflow(name=wf_multi_session_name)
    wf_multi.base_dir = work_dir + '/' + wf_multi_session_name
    if not os.path.isdir(wf_multi.base_dir):
        os.mkdir(wf_multi.base_dir)

    i = 0
    if len(bids_dict[participant][sessions[0]].keys()) == 1:
        for session in sessions:
            dwi_file = bids_dict[participant][session][1]['dwi_file']
            dwi_img = nib.load(dwi_file)
            if vox_size == '2mm':
                res_factor=dwi_img.header.get_zooms()[1]/2
            elif vox_size == '1mm':
                res_factor = dwi_img.header.get_zooms()[1]/1
            else:
                res_factor = 1
            exp_bytes = res_factor * 24 * dwi_img.shape[0] * dwi_img.shape[1] * dwi_img.shape[2] * dwi_img.shape[3]
            eddy_mem_gb = core.bytesto(exp_bytes, to='g', bsize=1024)
            fbvec = bids_dict[participant][session][1]['fbvec']
            fbval = bids_dict[participant][session][1]['fbval']
            metadata = bids_dict[participant][session][1]['metadata']
            wf = init_dwi_preproc_wf(participant,
                                     session,
                                     dwi_file,
                                     fbval,
                                     fbvec,
                                     metadata,
                                     output_dir,
                                     sdc_method,
                                     denoise_strategy,
                                     vox_size,
                                     outlier_thresh,
                                     omp_nthreads,
                                     eddy_mem_gb)
            wf_multi.add_nodes([wf])
            i = i + 1

        wf_multi.get_node(wf.name).get_node('check_orient_and_dims_dwi_node')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('correct_vecs_and_make_b0s')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('bet_pre_moco')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('bet_pre_moco').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('apply_mask_pre_moco')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('apply_mask_pre_moco').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('fsl_split')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('fsl_split').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('coregistration')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('coregistration').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('get_motion_params')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('fsl_merge')._mem_gb = 2
        wf_multi.get_node(wf.name).get_node('fsl_merge').interface._mem_gb = 2
        wf_multi.get_node(wf.name).get_node('art')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('art').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('drop_outliers_fn')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('make_gtab')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('extract_metadata')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('check_shelled')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('get_topup_inputs')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('get_eddy_inputs')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('make_mean_b0')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('make_basename')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node('eddy_quad')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('eddy_quad').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('make_gtab_final')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('apply_mask')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('apply_mask').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('id_outliers_from_eddy_report')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('drop_outliers_from_eddy_report')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('SplitDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('SplitDWIs').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('RemoveBiasOfDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('RemoveBiasOfDWIs').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('RemoveNegative')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('RemoveNegative').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('MergeDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node('MergeDWIs').interface._mem_gb = 1

        wf_multi.get_node(wf.name).get_node('topup')._n_procs = 8
        wf_multi.get_node(wf.name).get_node('topup')._mem_gb = 14
        wf_multi.get_node(wf.name).get_node('topup').interface.n_procs = 8
        wf_multi.get_node(wf.name).get_node('topup').interface.mem_gb = 14
        wf_multi.get_node(wf.name).get_node('Bias_b0')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node('Bias_b0')._mem_gb = omp_nthreads*4
        wf_multi.get_node(wf.name).get_node('Bias_b0').interface.n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node('Bias_b0').interface.mem_gb = omp_nthreads*4
        wf_multi.get_node(wf.name).get_node('eddy')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node('eddy')._mem_gb = eddy_mem_gb
        wf_multi.get_node(wf.name).get_node('eddy').interface.n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node('eddy').interface.mem_gb = eddy_mem_gb
        wf_multi.get_node(wf.name).get_node('suppress_gibbs')._n_procs = 6
        wf_multi.get_node(wf.name).get_node('suppress_gibbs')._mem_gb = 12
        wf_multi.get_node(wf.name).get_node('estimate_noise')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node('estimate_noise')._mem_gb = omp_nthreads*2
        wf_multi.get_node(wf.name).get_node('denoise')._n_procs = omp_nthreads
        if denoise_strategy == 'nlsam':
            wf_multi.get_node(wf.name).get_node('denoise')._mem_gb = omp_nthreads*6
        else:
            wf_multi.get_node(wf.name).get_node('denoise')._mem_gb = omp_nthreads*4

    else:
        for session in sessions:
            dwi_files = []
            fbvecs = []
            fbvals = []
            metadata_files = []
            for acq in bids_dict[participant][session].keys():
                dwi_files.append(bids_dict[participant][session][acq]['dwi_file'])
                fbvecs.append(bids_dict[participant][session][acq]['fbvec'])
                fbvals.append(bids_dict[participant][session][acq]['fbval'])
                metadata_files.append(bids_dict[participant][session][acq]['metadata'])

            wf_multi_run_name = "%s%s%s%s%s%s" % ('wf_multi_run_', participant, '_', session, '_', acq)
            wf = pe.Workflow(name=wf_multi_run_name)
            wf.base_dir = work_dir + '/' + wf_multi_run_name
            if not os.path.isdir(wf.base_dir):
                os.mkdir(wf.base_dir)

            dwi_img = nib.load(dwi_files[0])
            if vox_size == '2mm':
                res_factor=dwi_img.header.get_zooms()[1]/2
            elif vox_size == '1mm':
                res_factor = dwi_img.header.get_zooms()[1]/1
            else:
                res_factor = 1
            exp_bytes = res_factor * 24 * dwi_img.shape[0] * dwi_img.shape[1] * dwi_img.shape[2] * dwi_img.shape[3]
            eddy_mem_gb = core.bytesto(exp_bytes, to='g', bsize=1024)

            meta_inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_files",
                                                                   "fbvecs",
                                                                   "fbvals",
                                                                   "metadata_files",
                                                                   "sub",
                                                                   "ses",
                                                                   "output_dir",
                                                                   "sdc_method",
                                                                   "denoise_strategy",
                                                                   "vox_size",
                                                                   "outlier_thresh",
                                                                   "omp_nthreads",
                                                                   "eddy_mem_gb"]),
                                     name='meta_inputnode')

            meta_inputnode.inputs.dwi_files = dwi_files
            meta_inputnode.inputs.fbvecs = fbvecs
            meta_inputnode.inputs.fbvals = fbvals
            meta_inputnode.inputs.metadata_files = metadata_files
            meta_inputnode.inputs.sub = participant
            meta_inputnode.inputs.ses = session
            meta_inputnode.inputs.output_dir = output_dir
            meta_inputnode.inputs.sdc_method = sdc_method
            meta_inputnode.inputs.denoise_strategy = denoise_strategy
            meta_inputnode.inputs.vox_size = vox_size
            meta_inputnode.inputs.outlier_thresh = outlier_thresh
            meta_inputnode.inputs.omp_nthreads = omp_nthreads
            meta_inputnode.inputs.eddy_mem_gb = eddy_mem_gb

            wf_concat = init_dwi_concat_wf(dwi_files, fbvals, fbvecs, metadata_files, participant, session, output_dir)

            wf_dwi_preproc = init_dwi_preproc_wf(participant,
                                                 session,
                                                 dwi_files[0],
                                                 fbvals[0],
                                                 fbvecs[0],
                                                 metadata_files[0],
                                                 output_dir,
                                                 sdc_method,
                                                 denoise_strategy,
                                                 vox_size,
                                                 outlier_thresh,
                                                 omp_nthreads,
                                                 eddy_mem_gb)

            meta_outputnode = pe.Node(
                niu.IdentityInterface(fields=["preprocessed_data", "final_bvec", "final_bval",
                                              "out_eddy_quad_json", "out_eddy_quad_pdf"]),
                name="meta_outputnode",
            )
            wf.add_nodes([meta_inputnode])
            wf.add_nodes([wf_concat])
            wf.add_nodes([wf_dwi_preproc])
            wf.add_nodes([meta_outputnode])

            wf.connect([(meta_inputnode, wf.get_node('dwi_concat_wf').get_node('inputnode'),
                         [('dwi_files', 'dwi_files'),
                          ('fbvecs', 'fbvecs'),
                          ('fbvals', 'fbvals'),
                          ('metadata_files', 'metadata_files'),
                          ('sub', 'participant'),
                          ('ses', 'session'),
                          ('output_dir', 'output_dir')]),
                        (wf.get_node('dwi_concat_wf').get_node('outputnode'), wf_dwi_preproc.get_node('inputnode'),
                         [('dwi_file', 'dwi_file'),
                          ('bvec_file', 'fbvec'),
                          ('bval_file', 'fbval'),
                          ('metadata_file', 'metadata')]),
                        (meta_inputnode, wf_dwi_preproc.get_node('inputnode'),
                         [('sub', 'participant'),
                          ('ses', 'session'),
                          ('output_dir', 'output_dir'),
                          ('sdc_method', 'sdc_method'),
                          ('denoise_strategy', 'denoise_strategy'),
                          ('vox_size', 'vox_size'),
                          ('outlier_thresh', 'outlier_thresh'),
                          ('omp_nthreads', 'omp_nthreads'),
                          ('eddy_mem_gb', 'eddy_mem_gb')]),
                        (wf_dwi_preproc.get_node('outputnode'), meta_outputnode,
                         [("final_bval", "final_bval"),
                          ("preprocessed_data", "preprocessed_data"),
                          ("final_bvec", "final_bvec"),
                          ("out_eddy_quad_json", "out_eddy_quad_json"),
                          ("out_eddy_quad_pdf", "out_eddy_quad_pdf")])
                    ])

            wf_multi.add_nodes([wf])
            i = i + 1

        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('check_orient_and_dims_dwi_node')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('correct_vecs_and_make_b0s')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('bet_pre_moco')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('bet_pre_moco').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('apply_mask_pre_moco')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('apply_mask_pre_moco').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('fsl_split')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('fsl_split').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('coregistration')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('coregistration').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('get_motion_params')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('fsl_merge')._mem_gb = 2
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('fsl_merge').interface._mem_gb = 2
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('art')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('art').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('drop_outliers_fn')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('make_gtab')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('extract_metadata')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('check_shelled')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('get_topup_inputs')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('get_eddy_inputs')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('make_mean_b0')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('make_basename')._mem_gb = 0.5
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy_quad')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy_quad').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('make_gtab_final')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('apply_mask')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('apply_mask').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('id_outliers_from_eddy_report')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('drop_outliers_from_eddy_report')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('SplitDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('SplitDWIs').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('RemoveBiasOfDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('RemoveBiasOfDWIs').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('RemoveNegative')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('RemoveNegative').interface._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('MergeDWIs')._mem_gb = 1
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('MergeDWIs').interface._mem_gb = 1

        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('topup')._n_procs = 8
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('topup')._mem_gb = 14
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('topup').interface.n_procs = 8
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('topup').interface.mem_gb = 14
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('Bias_b0')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('Bias_b0')._mem_gb = omp_nthreads*4
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('Bias_b0').interface.n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('Bias_b0').interface.mem_gb = omp_nthreads*4
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy')._mem_gb = eddy_mem_gb
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy').interface.n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('eddy').interface.mem_gb = eddy_mem_gb
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('suppress_gibbs')._n_procs = 6
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('suppress_gibbs')._mem_gb = 12
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('estimate_noise')._n_procs = omp_nthreads
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('estimate_noise')._mem_gb = omp_nthreads*2
        wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('denoise')._n_procs = omp_nthreads
        if denoise_strategy == 'nlsam':
            wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('denoise')._mem_gb = omp_nthreads*6
        else:
            wf_multi.get_node(wf.name).get_node(wf_dwi_preproc.name).get_node('denoise')._mem_gb = omp_nthreads*4

        cfg = dict(execution={'stop_on_first_crash': False, 'crashfile_format': 'txt', 'parameterize_dirs': True,
                              'display_variable': ':0', 'job_finished_timeout': 120, 'matplotlib_backend': 'Agg',
                              'plugin': 'MultiProc', 'use_relative_paths': True, 'remove_unnecessary_outputs': False,
                              'remove_node_directories': False})
        for key in cfg.keys():
            for setting, value in cfg[key].items():
                wf_multi.config[key][setting] = value

    return wf_multi
