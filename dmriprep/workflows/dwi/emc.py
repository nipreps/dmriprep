import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu, afni, ants
from dmriprep.workflows.dwi.base import _list_squeeze
from dmriprep.interfaces.images import (
    SignalPrediction,
    CalculateCNR,
    ReorderOutputs,
    ExtractB0,
    MatchTransforms,
    RescaleB0,
    CombineMotions,
    ImageMath,
)
from dmriprep.interfaces.reports import IterationSummary, EMCReport
from dmriprep.interfaces.vectors import ReorientVectors, CheckGradientTable
from dmriprep.interfaces.register import Register, ApplyAffine
from dmriprep.utils.images import (
    save_4d_to_3d,
    save_3d_to_4d,
    prune_b0s_from_dwis,
    average_images,
)
from dmriprep.utils.vectors import _rasb_to_bvec_list, _rasb_to_bval_floats
from dmriprep.utils.register import average_affines
from pkg_resources import resource_filename as pkgrf


def linear_alignment_workflow(transform, precision, iternum=0):
    import_list = [
        "import warnings",
        'warnings.filterwarnings("ignore")',
        "import sys",
        "import os",
        "import numpy as np",
        "import networkx as nx",
        "import nibabel as nb",
        "from nipype.utils.filemanip import fname_presuffix",
    ]

    iteration_wf = pe.Workflow(name="iterative_alignment_%03d" % iternum)
    input_node_fields = ["image_paths", "template_image", "iteration_num"]
    linear_alignment_inputnode = pe.Node(
        niu.IdentityInterface(fields=input_node_fields),
        name="linear_alignment_inputnode",
    )
    linear_alignment_inputnode.inputs.iteration_num = iternum
    linear_alignment_outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["registered_image_paths", "affine_transforms", "updated_template"]
        ),
        name="linear_alignment_outputnode",
    )

    settings = pkgrf(
        "dmriprep",
        "config/emc_{precision}_{transform}.json".format(
            precision=precision, transform=transform
        ),
    )

    iter_reg = pe.MapNode(
        Register(settings, pipeline=[transform]),
        name="reg_%03d" % iternum,
        iterfield=["moving_image"],
    )

    # Run the images through affine registration
    iteration_wf.connect(
        linear_alignment_inputnode, "image_paths", iter_reg, "moving_image"
    )
    iteration_wf.connect(
        linear_alignment_inputnode, "template_image", iter_reg, "fixed_image"
    )

    # Average the images
    averaged_images = pe.Node(
        niu.Function(
            input_names=["images"],
            output_names=["output_average_image"],
            function=average_images,
            imports=import_list,
        ),
        name="averaged_images",
    )
    iteration_wf.connect(iter_reg, "warped_image", averaged_images, "images")

    # Apply the inverse to the average image
    transforms_to_list = pe.Node(niu.Merge(1), name="transforms_to_list")
    transforms_to_list.inputs.ravel_inputs = True
    iteration_wf.connect(iter_reg, "forward_transforms", transforms_to_list, "in1")
    avg_affines = pe.Node(
        niu.Function(
            input_names=["transforms"],
            output_names=["average_affine_file"],
            function=average_affines,
            imports=import_list,
        ),
        name="avg_affine",
    )
    iteration_wf.connect(transforms_to_list, "out", avg_affines, "transforms")

    invert_average = pe.Node(ApplyAffine(), name="invert_average")
    invert_average.inputs.invert_transform = True

    avg_to_list = pe.Node(niu.Merge(1), name="to_list")
    iteration_wf.connect(avg_affines, "average_affine_file", avg_to_list, "in1")
    iteration_wf.connect(avg_to_list, "out", invert_average, "transform_affine")
    iteration_wf.connect(
        averaged_images, "output_average_image", invert_average, "moving_image"
    )
    iteration_wf.connect(
        averaged_images, "output_average_image", invert_average, "fixed_image"
    )
    iteration_wf.connect(
        invert_average, "warped_image", linear_alignment_outputnode, "updated_template"
    )
    iteration_wf.connect(
        iter_reg, "forward_transforms", linear_alignment_outputnode, "affine_transforms"
    )
    iteration_wf.connect(
        iter_reg, "warped_image", linear_alignment_outputnode, "registered_image_paths"
    )

    return iteration_wf


def init_b0_emc_wf(num_iters=3, transform="rigid", name="b0_emc_wf"):
    b0_emc_wf = pe.Workflow(name=name)

    b0_emc_inputnode = pe.Node(
        niu.IdentityInterface(fields=["b0_images", "initial_template"]),
        name="b0_emc_inputnode",
    )

    b0_emc_outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "final_template",
                "forward_transforms",
                "iteration_templates",
                "motion_params",
                "aligned_images",
            ]
        ),
        name="b0_emc_outputnode",
    )

    # Iteratively create a template
    # Store the registration targets
    iter_templates = pe.Node(niu.Merge(num_iters), name="iteration_templates")
    b0_emc_wf.connect(b0_emc_inputnode, "initial_template", iter_templates, "in1")

    # Perform an initial coarse, rigid alignment to the b0 template
    initial_reg = linear_alignment_workflow(
        transform=transform, precision="coarse", iternum=0
    )
    b0_emc_wf.connect(
        b0_emc_inputnode,
        "initial_template",
        initial_reg,
        "linear_alignment_inputnode.template_image",
    )
    b0_emc_wf.connect(
        b0_emc_inputnode,
        "b0_images",
        initial_reg,
        "linear_alignment_inputnode.image_paths",
    )
    reg_iters = [initial_reg]

    # Perform subsequent rigid alignment iterations
    for iternum in range(1, num_iters):
        reg_iters.append(
            linear_alignment_workflow(
                transform=transform, precision="precise", iternum=iternum
            )
        )
        b0_emc_wf.connect(
            reg_iters[-2],
            "linear_alignment_outputnode.updated_template",
            reg_iters[-1],
            "linear_alignment_inputnode.template_image",
        )
        b0_emc_wf.connect(
            b0_emc_inputnode,
            "b0_images",
            reg_iters[-1],
            "linear_alignment_inputnode.image_paths",
        )
        b0_emc_wf.connect(
            reg_iters[-1],
            "linear_alignment_outputnode.updated_template",
            iter_templates,
            "in%d" % (iternum + 1),
        )

    # Attach to outputs
    # The last iteration aligned to the output from the second-to-last
    b0_emc_wf.connect(
        reg_iters[-2],
        "linear_alignment_outputnode.updated_template",
        b0_emc_outputnode,
        "final_template",
    )
    b0_emc_wf.connect(
        reg_iters[-1],
        "linear_alignment_outputnode.affine_transforms",
        b0_emc_outputnode,
        "forward_transforms",
    )
    b0_emc_wf.connect(
        reg_iters[-1],
        "linear_alignment_outputnode.registered_image_paths",
        b0_emc_outputnode,
        "aligned_images",
    )
    b0_emc_wf.connect(iter_templates, "out", b0_emc_outputnode, "iteration_templates")

    return b0_emc_wf


def init_enhance_and_skullstrip_template_mask_wf(name):
    eastm_workflow = pe.Workflow(name=name)
    eastm_inputnode = pe.Node(
        niu.IdentityInterface(fields=["in_file"]), name="eastm_inputnode"
    )
    eastm_outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["mask_file", "skull_stripped_file", "bias_corrected_file"]
        ),
        name="eastm_outputnode",
    )

    # Truncate intensity values so they're OK for N4
    truncate_values = pe.Node(
        ImageMath(
            dimension=3,
            operation="TruncateImageIntensity",
            secondary_arg="0.0 0.98 512",
        ),
        name="truncate_values",
    )

    # Truncate intensity values for creating a mask
    # (there are many high outliers in b=0 images)
    truncate_values_for_masking = pe.Node(
        ImageMath(
            dimension=3, operation="TruncateImageIntensity", secondary_arg="0.0 0.9 512"
        ),
        name="truncate_values_for_masking",
    )

    # N4 will break if any negative values are present.
    rescale_image = pe.Node(
        ImageMath(dimension=3, operation="RescaleImage", secondary_arg="0 1000"),
        name="rescale_image",
    )

    # Run N4 normally, force num_threads=1 for stability (images are small, no need for >1)
    n4_correct = pe.Node(
        ants.N4BiasFieldCorrection(
            dimension=3,
            n_iterations=[200, 200],
            convergence_threshold=1e-6,
            bspline_order=3,
            bspline_fitting_distance=150,
            copy_header=True,
        ),
        name="n4_correct",
        n_procs=1,
    )

    # Sharpen the b0 ref
    sharpen_image = pe.Node(
        ImageMath(dimension=3, operation="Sharpen"), name="sharpen_image"
    )

    # Basic mask
    initial_mask = pe.Node(afni.Automask(outputtype="NIFTI_GZ"), name="initial_mask")

    # Fill holes left by Automask
    fill_holes = pe.Node(
        ImageMath(dimension=3, operation="FillHoles", secondary_arg="2"),
        name="fill_holes",
    )

    # Dilate before smoothing
    dilate_mask = pe.Node(
        ImageMath(dimension=3, operation="MD", secondary_arg="1"), name="dilate_mask"
    )

    # Smooth the mask and use it as a weight for N4
    smooth_mask = pe.Node(
        ImageMath(dimension=3, operation="G", secondary_arg="4"), name="smooth_mask"
    )

    # Make a "soft" skull-stripped image
    apply_mask = pe.Node(
        ants.MultiplyImages(
            dimension=3, output_product_image="SkullStrippedRef.nii.gz"
        ),
        name="apply_mask",
    )

    eastm_workflow.connect(
        [
            (eastm_inputnode, truncate_values, [("in_file", "in_file")]),
            (truncate_values, rescale_image, [("out_file", "in_file")]),
            (eastm_inputnode, truncate_values_for_masking, [("in_file", "in_file")]),
            (truncate_values_for_masking, initial_mask, [("out_file", "in_file")]),
            (initial_mask, fill_holes, [("out_file", "in_file")]),
            (fill_holes, dilate_mask, [("out_file", "in_file")]),
            (dilate_mask, smooth_mask, [("out_file", "in_file")]),
            (rescale_image, n4_correct, [("out_file", "input_image")]),
            (smooth_mask, n4_correct, [("out_file", "weight_image")]),
            (n4_correct, sharpen_image, [("output_image", "in_file")]),
            (sharpen_image, eastm_outputnode, [("out_file", "bias_corrected_file")]),
            (sharpen_image, apply_mask, [("out_file", "first_input")]),
            (smooth_mask, apply_mask, [("out_file", "second_input")]),
            (
                apply_mask,
                eastm_outputnode,
                [("output_product_image", "skull_stripped_file")],
            ),
            (fill_holes, eastm_outputnode, [("out_file", "mask_file")]),
        ]
    )

    return eastm_workflow


def init_emc_model_iteration_wf(
    precision, transform, prune_b0s, model_name, name="emc_model_iter0"
):
    emc_model_iter_workflow = pe.Workflow(name=name)
    emc_model_iteration_inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "original_dwi_files",
                "original_rasb_file",
                "aligned_dwi_files",
                "aligned_vectors",
                "b0_median",
                "b0_mask",
                "b0_indices",
            ]
        ),
        name="emc_model_iteration_inputnode",
    )

    emc_model_iteration_outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "emc_transforms",
                "aligned_dwis",
                "aligned_vectors",
                "predicted_dwis",
                "motion_params",
            ]
        ),
        name="emc_model_iteration_outputnode",
    )

    # Predict signal from a given coordinate on the sphere
    predict_dwis = pe.MapNode(
        SignalPrediction(prune_b0s=prune_b0s, model_name=model_name),
        iterfield=["bval_to_predict", "bvec_to_predict"],
        name="predict_dwis",
    )
    predict_dwis.synchronize = True

    # Register original images to the predicted images
    settings = pkgrf(
        "dmriprep",
        "config/emc_{precision}_{transform}.json".format(
            precision=precision, transform="affine"
        ),
    )
    register_to_predicted = pe.MapNode(
        Register(settings, pipeline=transform),
        iterfield=["moving_image", "fixed_image"],
        name="register_to_predicted",
    )
    register_to_predicted.synchronize = True

    # Apply new transforms to vectors
    post_vector_transforms = pe.Node(ReorientVectors(), name="post_vector_transforms")

    # Summarize the motion
    calculate_motion = pe.Node(CombineMotions(), name="calculate_motion")

    emc_model_iter_workflow.connect(
        [
            # Send inputs to DWI prediction
            (
                emc_model_iteration_inputnode,
                predict_dwis,
                [
                    ("aligned_dwi_files", "aligned_dwi_files"),
                    ("aligned_vectors", "aligned_vectors"),
                    ("b0_indices", "b0_indices"),
                    ("b0_median", "b0_median"),
                    ("b0_mask", "b0_mask"),
                    (("aligned_vectors", _rasb_to_bvec_list), "bvec_to_predict"),
                    (("aligned_vectors", _rasb_to_bval_floats), "bval_to_predict"),
                ],
            ),
            (predict_dwis, register_to_predicted, [("predicted_image", "fixed_image")]),
            (
                emc_model_iteration_inputnode,
                register_to_predicted,
                [("original_dwi_files", "moving_image")],
            ),
            (
                register_to_predicted,
                calculate_motion,
                [(("forward_transforms", _list_squeeze), "transform_files")],
            ),
            (
                emc_model_iteration_inputnode,
                calculate_motion,
                [("original_dwi_files", "source_files"), ("b0_median", "ref_file")],
            ),
            (
                calculate_motion,
                emc_model_iteration_outputnode,
                [("motion_file", "motion_params")],
            ),
            (
                register_to_predicted,
                post_vector_transforms,
                [(("forward_transforms", _list_squeeze), "affines")],
            ),
            (
                emc_model_iteration_inputnode,
                post_vector_transforms,
                [("aligned_vectors", "rasb_file"), ("b0_median", "dwi_file")],
            ),
            (
                predict_dwis,
                emc_model_iteration_outputnode,
                [("predicted_image", "predicted_dwis")],
            ),
            (
                post_vector_transforms,
                emc_model_iteration_outputnode,
                [("out_rasb", "aligned_vectors")],
            ),
            (
                register_to_predicted,
                emc_model_iteration_outputnode,
                [
                    ("warped_image", "aligned_dwis"),
                    ("forward_transforms", "emc_transforms"),
                ],
            ),
        ]
    )

    return emc_model_iter_workflow


def init_dwi_model_emc_wf(num_iters=2, name="dwi_model_emc_wf"):
    dwi_model_emc_wf_workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "original_dwi_files",
                "original_rasb_file",
                "aligned_dwi_files",
                "b0_indices",
                "initial_transforms",
                "aligned_vectors",
                "b0_median",
                "b0_mask",
                "warped_b0_images",
            ]
        ),
        name="dwi_model_emc_inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "emc_transforms",
                "model_predicted_images",
                "cnr_image",
                "optimization_data",
            ]
        ),
        name="dwi_model_emc_outputnode",
    )

    # Instantiate an initial LOO prediction workflow
    initial_model_iteration = init_emc_model_iteration_wf(
        precision="coarse",
        transform=["rigid", "affine"],
        prune_b0s=True,
        model_name="tensor",
        name="initial_model_iteration",
    )

    # Collect motion estimates across iterations
    collect_motion_params = pe.Node(niu.Merge(num_iters), name="collect_motion_params")

    dwi_model_emc_wf_workflow.connect(
        [
            # Connect the first iteration
            (
                inputnode,
                initial_model_iteration,
                [
                    (
                        "original_dwi_files",
                        "emc_model_iteration_inputnode.original_dwi_files",
                    ),
                    (
                        "original_rasb_file",
                        "emc_model_iteration_inputnode.original_rasb_file",
                    ),
                    ("b0_median", "emc_model_iteration_inputnode.b0_median"),
                    ("b0_mask", "emc_model_iteration_inputnode.b0_mask"),
                    ("b0_indices", "emc_model_iteration_inputnode.b0_indices"),
                    (
                        "aligned_vectors",
                        "emc_model_iteration_inputnode.aligned_vectors",
                    ),
                    (
                        "aligned_dwi_files",
                        "emc_model_iteration_inputnode.aligned_dwi_files",
                    ),
                ],
            ),
            (
                initial_model_iteration,
                collect_motion_params,
                [("emc_model_iteration_outputnode.motion_params", "in1")],
            ),
        ]
    )

    model_iterations = [initial_model_iteration]
    # Perform additional iterations of LOO prediction
    for iteration_num in range(num_iters - 1):
        iteration_name = "EMC_iteration%03d" % (iteration_num + 1)
        motion_key = "in%d" % (iteration_num + 2)
        model_iterations.append(
            init_emc_model_iteration_wf(
                precision="precise",
                transform=["rigid", "affine"],
                prune_b0s=False,
                model_name="sfm",
                name=iteration_name,
            )
        )
        dwi_model_emc_wf_workflow.connect(
            [
                (
                    model_iterations[-2],
                    model_iterations[-1],
                    [
                        (
                            "emc_model_iteration_outputnode.aligned_dwis",
                            "emc_model_iteration_inputnode.aligned_dwi_files",
                        ),
                        (
                            "emc_model_iteration_outputnode.aligned_vectors",
                            "emc_model_iteration_inputnode.aligned_vectors",
                        ),
                    ],
                ),
                (
                    inputnode,
                    model_iterations[-1],
                    [
                        ("b0_mask", "emc_model_iteration_inputnode.b0_mask"),
                        ("b0_indices", "emc_model_iteration_inputnode.b0_indices"),
                        (
                            "original_dwi_files",
                            "emc_model_iteration_inputnode.original_dwi_files",
                        ),
                        (
                            "original_rasb_file",
                            "emc_model_iteration_inputnode.original_rasb_file",
                        ),
                        ("b0_median", "emc_model_iteration_inputnode.b0_median"),
                    ],
                ),
                (
                    model_iterations[-1],
                    collect_motion_params,
                    [("emc_model_iteration_outputnode.motion_params", motion_key)],
                ),
            ]
        )

    # Return to the original, b0-interspersed ordering
    reorder_dwi_xforms = pe.Node(ReorderOutputs(), name="reorder_dwi_xforms")

    # Create a report:
    emc_report = pe.Node(EMCReport(), name="emc_report")

    calculate_cnr = pe.Node(CalculateCNR(), name="calculate_cnr")

    if num_iters > 1:
        summarize_iterations = pe.Node(IterationSummary(), name="summarize_iterations")
        dwi_model_emc_wf_workflow.connect(
            [
                (
                    collect_motion_params,
                    summarize_iterations,
                    [("out", "collected_motion_files")],
                ),
                (
                    summarize_iterations,
                    outputnode,
                    [("iteration_summary_file", "optimization_data")],
                ),
                (
                    summarize_iterations,
                    emc_report,
                    [("iteration_summary_file", "iteration_summary")],
                ),
            ]
        )

    dwi_model_emc_wf_workflow.connect(
        [
            (
                model_iterations[-1],
                reorder_dwi_xforms,
                [
                    (
                        "emc_model_iteration_outputnode.emc_transforms",
                        "model_based_transforms",
                    ),
                    (
                        "emc_model_iteration_outputnode.predicted_dwis",
                        "model_predicted_images",
                    ),
                    (
                        "emc_model_iteration_outputnode.aligned_dwis",
                        "warped_dwi_images",
                    ),
                ],
            ),
            (
                inputnode,
                reorder_dwi_xforms,
                [
                    ("b0_median", "b0_median"),
                    ("warped_b0_images", "warped_b0_images"),
                    ("b0_indices", "b0_indices"),
                    ("initial_transforms", "initial_transforms"),
                ],
            ),
            (
                reorder_dwi_xforms,
                outputnode,
                [
                    ("emc_warped_images", "aligned_dwis"),
                    ("full_transforms", "emc_transforms"),
                    ("full_predicted_dwi_series", "model_predicted_images"),
                ],
            ),
            (inputnode, emc_report, [("original_dwi_files", "original_images")]),
            (
                reorder_dwi_xforms,
                calculate_cnr,
                [
                    ("emc_warped_images", "emc_warped_images"),
                    ("full_predicted_dwi_series", "predicted_images"),
                ],
            ),
            (inputnode, calculate_cnr, [("b0_mask", "mask_image")]),
            (calculate_cnr, outputnode, [("cnr_image", "cnr_image")]),
            (
                reorder_dwi_xforms,
                emc_report,
                [
                    ("full_predicted_dwi_series", "model_predicted_images"),
                    ("emc_warped_images", "registered_images"),
                ],
            )
        ]
    )

    return dwi_model_emc_wf_workflow


def init_emc_wf(name, mem_gb=3, omp_nthreads=8):
    import_list = [
        "import warnings",
        'warnings.filterwarnings("ignore")',
        "import sys",
        "import os",
        "import numpy as np",
        "import networkx as nx",
        "import nibabel as nb",
        "from nipype.utils.filemanip import fname_presuffix",
    ]

    emc_wf = pe.Workflow(name=name)

    meta_inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file", "in_bval", "in_bvec", "b0_template"]),
        name="meta_inputnode",
    )

    # Instantiate vectors object
    vectors_node = pe.Node(CheckGradientTable(), name="emc_vectors_node")

    # Extract B0s
    extract_b0s_node = pe.Node(ExtractB0(), name="extract_b0_node")

    # Split B0s into separate images
    split_b0s_node = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["out_files"],
            function=save_4d_to_3d,
            imports=import_list,
        ),
        name="split_b0s_node",
    )

    # Remove b0s from dwi series
    prune_b0s_from_dwis_node = pe.Node(
        niu.Function(
            input_names=["in_files", "b0_ixs"],
            output_names=["out_files"],
            function=prune_b0s_from_dwis,
            imports=import_list,
        ),
        name="prune_b0s_from_dwis_node",
    )

    # Split dwi series into 3d images
    split_dwis_node = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["out_files"],
            function=save_4d_to_3d,
            imports=import_list,
        ),
        name="split_dwis_node",
    )

    # Merge B0s into a single 4d image
    merge_b0s_node = pe.Node(
        niu.Function(
            input_names=["in_files"],
            output_names=["out_file"],
            function=save_3d_to_4d,
            imports=import_list,
        ),
        name="merge_b0s_node",
    )

    # Order affine transforms to correspond with split dwi files
    match_transforms_node = pe.Node(MatchTransforms(), name="match_transforms_node")

    # Create a skull-stripped and enhanced b0
    eastm_wf = init_enhance_and_skullstrip_template_mask_wf(
        name="enhance_and_skullstrip_template_mask_wf"
    )

    # Instantiate b0 eddy correction
    b0_emc_wf = init_b0_emc_wf()

    # Initialize with the transforms provided
    b0_based_image_transforms = pe.MapNode(
        ApplyAffine(),
        iterfield=["moving_image", "transform_affine"],
        name="b0_based_image_transforms",
    )

    # Rotate vectors
    b0_based_vector_transforms = pe.Node(
        ReorientVectors(), name="b0_based_vector_transforms"
    )

    # Grab the median of the aligned B0 images
    b0_median = pe.Node(RescaleB0(), name="b0_median")

    # Do model-based motion correction
    dwi_model_emc_wf = init_dwi_model_emc_wf(num_iters=2)

    # Warp the modeled images into non-motion-corrected space
    uncorrect_model_images = pe.MapNode(
        ApplyAffine(),
        iterfield=["moving_image", "transform_affine"],
        name="uncorrect_model_images",
    )
    uncorrect_model_images.inputs.invert_transform = True

    # Save to 4d image
    merge_EMC_corrected_dwis_node = pe.Node(
        niu.Function(
            input_names=["in_files"],
            output_names=["out_file"],
            function=save_3d_to_4d,
            imports=import_list,
        ),
        name="merge_EMC_corrected_dwis_node",
    )

    meta_outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "final_emc_4d_series"
                "final_template",
                "forward_transforms",
                "noise_free_dwis",
                "cnr_image",
                "optimization_data",
            ]
        ),
        name="meta_outputnode",
    )

    emc_wf.connect(
        [
            # Create initial transforms to apply to bias-reduced B0 template
            (
                meta_inputnode,
                vectors_node,
                [
                    ("dwi_file", "dwi_file"),
                    ("in_bval", "in_bval"),
                    ("in_bvec", "in_bvec"),
                ],
            ),
            (meta_inputnode, extract_b0s_node, [("dwi_file", "in_file")]),
            (vectors_node, extract_b0s_node, [("b0_ixs", "b0_ixs")]),
            (extract_b0s_node, split_b0s_node, [("out_file", "in_file")]),
            (meta_inputnode, split_dwis_node, [("dwi_file", "in_file")]),
            (split_b0s_node, b0_emc_wf, [("out_files", "b0_emc_inputnode.b0_images")]),
            (
                meta_inputnode,
                b0_emc_wf,
                [("b0_template", "b0_emc_inputnode.initial_template")],
            ),
            (
                b0_emc_wf,
                match_transforms_node,
                [
                    (
                        ("b0_emc_outputnode.forward_transforms", _list_squeeze),
                        "transforms",
                    )
                ],
            ),
            (vectors_node, match_transforms_node, [("b0_ixs", "b0_indices")]),
            (split_dwis_node, match_transforms_node, [("out_files", "dwi_files")]),
            (
                b0_emc_wf,
                eastm_wf,
                [("b0_emc_outputnode.final_template", "eastm_inputnode.in_file")],
            ),
            (meta_inputnode, b0_based_vector_transforms, [("dwi_file", "dwi_file")]),
            (
                match_transforms_node,
                b0_based_vector_transforms,
                [("transforms", "affines")],
            ),
            (vectors_node, b0_based_vector_transforms, [("out_rasb", "rasb_file")]),
            (
                split_dwis_node,
                b0_based_image_transforms,
                [("out_files", "moving_image")],
            ),
            (
                match_transforms_node,
                b0_based_image_transforms,
                [("transforms", "transform_affine")],
            ),
            (
                b0_emc_wf,
                merge_b0s_node,
                [("b0_emc_outputnode.aligned_images", "in_files")],
            ),
            (merge_b0s_node, b0_median, [("out_file", "in_file")]),
            (eastm_wf, b0_median, [("eastm_outputnode.mask_file", "mask_file")]),
            (b0_median, b0_based_image_transforms, [("out_ref", "fixed_image")]),

            # Perform signal prediction from vectors
            (vectors_node, prune_b0s_from_dwis_node, [("b0_ixs", "b0_ixs")]),
            (split_dwis_node, prune_b0s_from_dwis_node, [("out_files", "in_files")]),
            (
                prune_b0s_from_dwis_node,
                dwi_model_emc_wf,
                [("out_files", "dwi_model_emc_inputnode.original_dwi_files")],
            ),
            (
                vectors_node,
                dwi_model_emc_wf,
                [("out_rasb", "dwi_model_emc_inputnode.original_rasb_file")],
            ),
            (
                b0_based_image_transforms,
                dwi_model_emc_wf,
                [("warped_image", "dwi_model_emc_inputnode.aligned_dwi_files")],
            ),
            (
                b0_based_vector_transforms,
                dwi_model_emc_wf,
                [("out_rasb", "dwi_model_emc_inputnode.aligned_vectors")],
            ),
            (
                b0_median,
                dwi_model_emc_wf,
                [("out_ref", "dwi_model_emc_inputnode.b0_median")],
            ),
            (
                eastm_wf,
                dwi_model_emc_wf,
                [("eastm_outputnode.mask_file", "dwi_model_emc_inputnode.b0_mask")],
            ),
            (
                vectors_node,
                dwi_model_emc_wf,
                [("b0_ixs", "dwi_model_emc_inputnode.b0_indices")],
            ),
            (
                match_transforms_node,
                dwi_model_emc_wf,
                [("transforms", "dwi_model_emc_inputnode.initial_transforms")],
            ),
            (
                b0_emc_wf,
                dwi_model_emc_wf,
                [
                    (
                        "b0_emc_outputnode.aligned_images",
                        "dwi_model_emc_inputnode.warped_b0_images",
                    )
                ],
            ),
            (
                b0_emc_wf,
                meta_outputnode,
                [("b0_emc_outputnode.final_template", "final_template")],
            ),
            (
                dwi_model_emc_wf,
                meta_outputnode,
                [
                    ("dwi_model_emc_outputnode.emc_transforms", "forward_transforms"),
                    ("dwi_model_emc_outputnode.optimization_data", "optimization_data"),
                    ("dwi_model_emc_outputnode.cnr_image", "cnr_image"),
                ],
            ),
            (
                b0_emc_wf,
                uncorrect_model_images,
                [("b0_emc_outputnode.final_template", "fixed_image")],
            ),
            (
                dwi_model_emc_wf,
                uncorrect_model_images,
                [("dwi_model_emc_outputnode.emc_transforms", "transform_affine")],
            ),
            (split_dwis_node, uncorrect_model_images, [("out_files", "moving_image")]),
            (
                uncorrect_model_images,
                meta_outputnode,
                [("warped_image", "noise_free_dwis")],
            ),
            (
                uncorrect_model_images,
                merge_EMC_corrected_dwis_node,
                [("warped_image", "in_files")],
            ),
            (
                merge_EMC_corrected_dwis_node,
                meta_outputnode,
                [("out_file", "final_emc_4d_series")],
            ),
        ]
    )
    return emc_wf
