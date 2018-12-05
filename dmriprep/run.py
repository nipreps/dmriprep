import os.path as op
from shutil import copyfile


def run_dmriprep(dwi_file, bvec_file, bval_file,
               subjects_dir, working_dir, out_dir):

    """
    Runs dmriprep for acquisitions with just one PE direction.

    """
    import nibabel as nib
    import nipype.interfaces.freesurfer as fs
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.io as nio
    import nipype.interfaces.utility as niu
    import nipype.pipeline.engine as pe
    import numpy as np
    from nipype.algorithms.rapidart import ArtifactDetect
    from nipype.interfaces.dipy import DTI
    from nipype.interfaces.fsl.utils import AvScale
    from nipype.utils.filemanip import fname_presuffix
    from nipype.workflows.dmri.fsl.epi import create_dmri_preprocessing

    wf = create_dmri_preprocessing(name='dmriprep',
                                   use_fieldmap=False,
                                   fieldmap_registration=False)
    wf.inputs.inputnode.ref_num = 0
    wf.inputs.inputnode.in_file = dwi_file
    wf.inputs.inputnode.in_bvec = bvec_file

    dwi_fname = op.split(dwi_file)[1].split(".nii.gz")[0]
    bids_sub_name = dwi_fname.split("_")[0]
    assert bids_sub_name.startswith("sub-")

    # inputnode = wf.get_node("inputnode")
    outputspec = wf.get_node("outputnode")

    # QC: FLIRT translation and rotation parameters
    flirt = wf.get_node("motion_correct.coregistration")
    # flirt.inputs.save_mats = True

    get_tensor = pe.Node(DTI(), name="dipy_tensor")
    wf.connect(outputspec, "dmri_corrected", get_tensor, "in_file")
    # wf.connect(inputspec2,"bvals", get_tensor, "in_bval")
    get_tensor.inputs.in_bval = bval_file
    wf.connect(outputspec, "bvec_rotated", get_tensor, "in_bvec")

    scale_tensor = pe.Node(name='scale_tensor', interface=fsl.BinaryMaths())
    scale_tensor.inputs.operation = 'mul'
    scale_tensor.inputs.operand_value = 1000
    wf.connect(get_tensor, 'out_file', scale_tensor, 'in_file')

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")
    wf.connect(outputspec, "dmri_corrected", fslroi, "in_file")

    bbreg = pe.Node(fs.BBRegister(contrast_type="t2", init="fsl",
                                  out_fsl_file=True, subjects_dir=subjects_dir,
                                  epi_mask=True), name="bbreg")
    # wf.connect(inputspec2,"fsid", bbreg,"subject_id")
    bbreg.inputs.subject_id = 'freesurfer'  # bids_sub_name
    wf.connect(fslroi, "roi_file", bbreg, "source_file")

    voltransform = pe.Node(fs.ApplyVolTransform(inverse=True),
                           iterfield=['source_file', 'reg_file'],
                           name='transform')
    voltransform.inputs.subjects_dir = subjects_dir

    vt2 = voltransform.clone("transform_aparcaseg")
    vt2.inputs.interp = "nearest"

    def binarize_aparc(aparc_aseg):
        img = nib.load(aparc_aseg)
        data, aff = img.get_data(), img.affine
        outfile = fname_presuffix(
            aparc_aseg, suffix="bin.nii.gz",
            newpath=op.abspath("."), use_ext=False
        )
        nib.Nifti1Image((data > 0).astype(float), aff).to_filename(outfile)
        return outfile

    # wf.connect(inputspec2, "mask_nii", voltransform, "target_file")
    create_mask = pe.Node(niu.Function(input_names=["aparc_aseg"],
                                       output_names=["outfile"],
                                       function=binarize_aparc),
                          name="bin_aparc")

    def get_aparc_aseg(subjects_dir, sub):
        return op.join(subjects_dir, sub, "mri", "aparc+aseg.mgz")

    create_mask.inputs.aparc_aseg = get_aparc_aseg(subjects_dir, 'freesurfer')
    wf.connect(create_mask, "outfile", voltransform, "target_file")

    wf.connect(fslroi, "roi_file", voltransform, "source_file")
    wf.connect(bbreg, "out_reg_file", voltransform, "reg_file")

    vt2.inputs.target_file = get_aparc_aseg(subjects_dir, 'freesurfer')
    # wf.connect(inputspec2, "aparc_aseg", vt2, "target_file")
    wf.connect(fslroi, "roi_file", vt2, "source_file")
    wf.connect(bbreg, "out_reg_file", vt2, "reg_file")

    # AK (2017): THIS NODE MIGHT NOT BE NECESSARY
    # AK (2018) doesn't know why she said that above..
    threshold2 = pe.Node(fs.Binarize(min=0.5, out_type='nii.gz', dilate=1),
                         iterfield=['in_file'],
                         name='threshold2')
    wf.connect(voltransform, "transformed_file", threshold2, "in_file")

    # wf.connect(getmotion, "motion_params", datasink, "dti.@motparams")

    def get_flirt_motion_parameters(flirt_out_mats):
        def get_params(A):
            """This is a copy of spm's spm_imatrix where
            we already know the rotations and translations matrix,
            shears and zooms (as outputs from fsl FLIRT/avscale)
            Let A = the 4x4 rotation and translation matrix
            R = [          c5*c6,           c5*s6, s5]
                [-s4*s5*c6-c4*s6, -s4*s5*s6+c4*c6, s4*c5]
                [-c4*s5*c6+s4*s6, -c4*s5*s6-s4*c6, c4*c5]
            """
            def rang(b):
                a = min(max(b, -1), 1)
                return a
            Ry = np.arcsin(A[0, 2])
            # Rx = np.arcsin(A[1, 2] / np.cos(Ry))
            # Rz = np.arccos(A[0, 1] / np.sin(Ry))

            if (abs(Ry)-np.pi/2)**2 < 1e-9:
                Rx = 0
                Rz = np.arctan2(-rang(A[1, 0]), rang(-A[2, 0]/A[0, 2]))
            else:
                c = np.cos(Ry)
                Rx = np.arctan2(rang(A[1, 2]/c), rang(A[2, 2]/c))
                Rz = np.arctan2(rang(A[0, 1]/c), rang(A[0, 0]/c))

            rotations = [Rx, Ry, Rz]
            translations = [A[0, 3], A[1, 3], A[2, 3]]

            return rotations, translations

        motion_params = open(op.abspath('motion_parameters.par'), 'w')
        for mat in flirt_out_mats:
            res = AvScale(mat_file=mat).run()
            A = np.asarray(res.outputs.rotation_translation_matrix)
            rotations, translations = get_params(A)
            for i in rotations+translations:
                motion_params.write('%f ' % i)
            motion_params.write('\n')
        motion_params.close()
        motion_params = op.abspath('motion_parameters.par')
        return motion_params

    getmotion = pe.Node(
        niu.Function(input_names=["flirt_out_mats"],
                     output_names=["motion_params"],
                     function=get_flirt_motion_parameters),
        name="get_motion_parameters",
        iterfield="flirt_out_mats"
    )

    wf.connect(flirt, "out_matrix_file", getmotion, "flirt_out_mats")

    art = pe.Node(interface=ArtifactDetect(), name="art")
    art.inputs.use_differences = [True, True]
    art.inputs.save_plot = False
    art.inputs.use_norm = True
    art.inputs.norm_threshold = 3
    art.inputs.zintensity_threshold = 9
    art.inputs.mask_type = 'spm_global'
    art.inputs.parameter_source = 'FSL'

    wf.connect(getmotion, "motion_params", art, "realignment_parameters")
    wf.connect(outputspec, "dmri_corrected", art, "realigned_files")

    datasink = pe.Node(nio.DataSink(), name="sinker")
    datasink.inputs.base_directory = out_dir
    datasink.inputs.substitutions = [
        ("vol0000_flirt_merged.nii.gz", dwi_fname + '.nii.gz'),
        ("stats.vol0000_flirt_merged.txt", dwi_fname + ".art.json"),
        ("motion_parameters.par", dwi_fname + ".motion.txt"),
        ("_rotated.bvec", ".bvec"),
        ("aparc+aseg_warped_out", dwi_fname.replace("_dwi", "_aparc+aseg")),
        ("art.vol0000_flirt_merged_outliers.txt", dwi_fname + ".outliers.txt"),
        ("vol0000_flirt_merged", dwi_fname),
        ("_roi_bbreg_freesurfer", "_register"),
        ("aparc+asegbin_warped_thresh", dwi_fname.replace("_dwi", "_mask")),
        ("derivatives/dmriprep", "derivatives/{}/dmriprep".format(bids_sub_name))
    ]

    wf.connect(art, "statistic_files", datasink, "dmriprep.art.@artstat")
    wf.connect(art, "outlier_files", datasink, "dmriprep.art.@artoutlier")
    wf.connect(outputspec, "dmri_corrected", datasink, "dmriprep.dwi.@corrected")
    wf.connect(outputspec, "bvec_rotated", datasink, "dmriprep.dwi.@rotated")
    wf.connect(getmotion, "motion_params", datasink, "dmriprep.art.@motion")

    wf.connect(get_tensor, "out_file", datasink, "dmriprep.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "dmriprep.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "dmriprep.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "dmriprep.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "dmriprep.dti.@rd")
    wf.connect(get_tensor, "out_file", datasink, "dmriprep.dti.@scaled_tensor")

    wf.connect(bbreg, "min_cost_file", datasink, "dmriprep.reg.@mincost")
    wf.connect(bbreg, "out_fsl_file", datasink, "dmriprep.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "dmriprep.reg.@reg")
    wf.connect(threshold2, "binary_file", datasink, "dmriprep.anat.@mask")
    # wf.connect(vt2, "transformed_file", datasink, "dwi.@aparc_aseg")

    convert = pe.Node(fs.MRIConvert(out_type="niigz"), name="convert2nii")
    wf.connect(vt2, "transformed_file", convert, "in_file")
    wf.connect(convert, "out_file", datasink, "dmriprep.anat.@aparc_aseg")

    wf.base_dir = working_dir
    wf.run()

    copyfile(bval_file, op.join(
        out_dir, bids_sub_name, "dmriprep", "dwi",
        op.split(bval_file)[1]
    ))

    dmri_corrected = glob(op.join(out_dir, '*/dmriprep/dwi', '*.nii.gz'))[0]
    bvec_rotated = glob(op.join(out_dir, '*/dmriprep/dwi', '*.bvec'))[0]
    bval_file = glob(op.join(out_dir, '*/dmriprep/dwi', '*.bval'))[0]
    art_file = glob(op.join(out_dir, '*/dmriprep/art', '*.art.json'))[0]
    motion_file = glob(op.join(out_dir, '*/dmriprep/art', '*.motion.txt'))[0]
    outlier_file = glob(op.join(out_dir, '*/dmriprep/art', '*.outliers.txt'))[0]
    return dmri_corrected, bvec_rotated, art_file, motion_file, outlier_file


def run_dmriprep_pe(dwi_file, dwi_file_AP, dwi_file_PA, bvec_file, bval_file,
                    subjects_dir, working_dir, out_dir):
    """
    This assumes that there are scans with phase-encode directions AP/PA for
    topup.

    """

    import nipype.interfaces.freesurfer as fs
    import nipype.interfaces.fsl as fsl
    import nipype.interfaces.io as nio
    import nipype.interfaces.utility as niu
    import nipype.pipeline.engine as pe
    from nipype.interfaces.dipy import DTI
    from nipype.workflows.dmri.fsl.artifacts import all_fsl_pipeline

    # some bookkeeping (getting the filename, gettings the BIDS subject name)
    dwi_fname = op.split(dwi_file)[1].split(".nii.gz")[0]
    bids_sub_name = dwi_fname.split("_")[0]
    assert bids_sub_name.startswith("sub-")

    # Grab the preprocessing all_fsl_pipeline
    # AK: watch out, other datasets might be encoded LR
    epi_AP = {'echospacing': 66.5e-3, 'enc_dir': 'y-'}
    epi_PA = {'echospacing': 66.5e-3, 'enc_dir': 'y'}
    prep = all_fsl_pipeline(epi_params=epi_AP, altepi_params=epi_PA)

    # initialize an overall workflow
    wf = pe.Workflow(name="dmriprep")
    wf.base_dir = op.abspath(working_dir)

    prep.inputs.inputnode.in_file = dwi_file
    # prep.inputs.inputnode.alt_file = dwi_file_PA
    prep.inputs.inputnode.in_bvec = bvec_file
    prep.inputs.inputnode.in_bval = bval_file
    eddy = prep.get_node('fsl_eddy')
    eddy.inputs.repol = True
    eddy.inputs.niter = 1  # TODO: change back to 5 when running for real

    def drop_outliers_fn(outlier_report, threshold):
        """Get list of scans that exceed threshold for number of outliers

        Parameters
        ----------
        outlier_report: string
            Path to the fsl_eddy outlier report

        threshold: int or float
            If threshold is an int, it is treated as number of allowed outlier
            slices. If threshold is a float between 0 and 1 (exclusive), it is
            treated the fraction of allowed outlier slices before we drop the
            whole volume. Float param in not yet implemented

        Returns
        -------
        drop_scans: numpy.ndarray
            List of scan indices to drop
        """
        import numpy as np
        import os.path as op
        import parse
        with open(op.abspath(outlier_report), 'r') as fp:
            lines = fp.readlines()

        p = parse.compile(
            "Slice {slice:d} in scan {scan:d} is an outlier with "
            "mean {mean_sd:f} standard deviations off, and mean "
            "squared {mean_sq_sd:f} standard deviations off."
        )

        outliers = [p.parse(l).named for l in lines]
        scans = {d['scan'] for d in outliers}

        def num_outliers(scan, outliers):
            return len([d for d in outliers if d['scan'] == scan])

        drop_scans = np.array([
            s for s in scans
            if num_outliers(s, outliers) > threshold
        ])

        return drop_scans

    drop_outliers_node = pe.Node(niu.Function(
        input_names=["outlier_report", "threshold"],
        output_names=["drop_scans"],
        function=drop_outliers_fn),
        name="drop_outliers_node"
    )

    drop_outliers_node.inputs.threshold = 1
    wf.connect(prep, "fsl_eddy.out_outlier_report",
               drop_outliers_node, "outlier_report")

    def save_outlier_list_fn(drop_scans):
        """Save list of outlier scans to file

        Parameters
        ----------
        drop_scans: numpy.ndarray
            Path to the fsl_eddy outlier report

        Returns
        -------
        outpath: string
            Path to output file where list is saved
        """
        import numpy as np
        import os.path as op
        outpath = op.abspath("dropped_scans.txt")
        np.savetxt(outpath, drop_scans, fmt="%d")
        return outpath

    save_outlier_list_node = pe.Node(niu.Function(
        input_names=["drop_scans"],
        output_names=["outpath"],
        function=save_outlier_list_fn),
        name="save_outlier_list_node"
    )

    wf.connect(drop_outliers_node, "drop_scans",
               save_outlier_list_node, "drop_scans")

    merge = pe.Node(fsl.Merge(dimension='t'), name="mergeAPPA")
    merge.inputs.in_files = [dwi_file_AP, dwi_file_PA]
    wf.connect(merge, 'merged_file', prep, 'inputnode.alt_file')

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")
    wf.connect(prep, "outputnode.out_file", fslroi, "in_file")

    bbreg = pe.Node(fs.BBRegister(contrast_type="t2", init="coreg",
                                  out_fsl_file=True,
                                  subjects_dir=subjects_dir,
                                  epi_mask=True),
                    name="bbreg")
    bbreg.inputs.subject_id = 'freesurfer'  # bids_sub_name
    wf.connect(fslroi, "roi_file", bbreg, "source_file")

    get_tensor = pe.Node(DTI(), name="dipy_tensor")
    wf.connect(prep, "outputnode.out_file", get_tensor, "in_file")
    get_tensor.inputs.in_bval = bval_file
    wf.connect(prep, "outputnode.out_bvec", get_tensor, "in_bvec")

    scale_tensor = pe.Node(name='scale_tensor', interface=fsl.BinaryMaths())
    scale_tensor.inputs.operation = 'mul'
    scale_tensor.inputs.operand_value = 1000
    wf.connect(get_tensor, 'out_file', scale_tensor, 'in_file')

    voltransform = pe.Node(fs.ApplyVolTransform(inverse=True),
                           iterfield=['source_file', 'reg_file'],
                           name='transform')
    voltransform.inputs.subjects_dir = subjects_dir

    vt2 = voltransform.clone("transform_aparcaseg")
    vt2.inputs.interp = "nearest"

    vt3 = voltransform.clone("transform_orig")

    def binarize_aparc(aparc_aseg):
        import nibabel as nib
        from nipype.utils.filemanip import fname_presuffix
        import os.path as op
        img = nib.load(aparc_aseg)
        data, aff = img.get_data(), img.affine
        outfile = fname_presuffix(
            aparc_aseg, suffix="bin.nii.gz",
            newpath=op.abspath("."), use_ext=False
        )
        nib.Nifti1Image((data > 0).astype(float), aff).to_filename(outfile)
        return outfile

    create_mask = pe.Node(niu.Function(input_names=["aparc_aseg"],
                                       output_names=["outfile"],
                                       function=binarize_aparc),
                          name="bin_aparc")

    def get_aparc_aseg(subjects_dir, sub):
        return op.join(subjects_dir, sub, "mri", "aparc+aseg.mgz")

    def get_orig(subjects_dir, sub):
        return op.join(subjects_dir, sub, "mri", "orig.mgz")

    create_mask.inputs.aparc_aseg = get_aparc_aseg(subjects_dir, 'freesurfer')
    wf.connect(create_mask, "outfile", voltransform, "target_file")

    wf.connect(fslroi, "roi_file", voltransform, "source_file")
    wf.connect(bbreg, "out_reg_file", voltransform, "reg_file")

    vt2.inputs.target_file = get_aparc_aseg(subjects_dir, 'freesurfer')
    wf.connect(fslroi, "roi_file", vt2, "source_file")
    wf.connect(bbreg, "out_reg_file", vt2, "reg_file")

    vt3.inputs.target_file = get_orig(subjects_dir, 'freesurfer')
    wf.connect(fslroi, "roi_file", vt3, "source_file")
    wf.connect(bbreg, "out_reg_file", vt3, "reg_file")

    # AK (2017): THIS NODE MIGHT NOT BE NECESSARY
    # AK (2018) doesn't know why she said that above..
    threshold2 = pe.Node(fs.Binarize(min=0.5, out_type='nii.gz', dilate=1),
                         iterfield=['in_file'],
                         name='threshold2')
    wf.connect(voltransform, "transformed_file", threshold2, "in_file")

    datasink = pe.Node(nio.DataSink(), name="sinker")
    datasink.inputs.base_directory = out_dir
    datasink.inputs.substitutions = [
        ("vol0000_flirt_merged.nii.gz", dwi_fname + '.nii.gz'),
        ("stats.vol0000_flirt_merged.txt", dwi_fname + ".art.json"),
        ("motion_parameters.par", dwi_fname + ".motion.txt"),
        ("_rotated.bvec", ".bvec"),
        ("art.vol0000_flirt_merged_outliers.txt", dwi_fname + ".outliers.txt"),
        ("vol0000_flirt_merged", dwi_fname),
        ("_roi_bbreg_freesurfer", "_register"),
        ("dwi/eddy_corrected", "dwi/%s" % dwi_fname),
        ("dti/eddy_corrected", "dti/%s" % dwi_fname.replace("_dwi", "")),
        ("reg/eddy_corrected", "reg/%s" % dwi_fname.replace("_dwi", "")),
        ("aparc+asegbin_warped_thresh", dwi_fname.replace("_dwi", "_mask")),
        ("aparc+aseg_warped_out", dwi_fname.replace("_dwi", "_aparc+aseg")),
        ("art.eddy_corrected_outliers", dwi_fname.replace("dwi", "outliers")),
        ("color_fa", "colorfa"),
        ("orig_warped_out", dwi_fname.replace("_dwi", "_T1w")),
        # ("eddy_corrected_", dwi_fname.replace("dwi", "")),
        ("stats.eddy_corrected", dwi_fname.replace("dwi", "artStats")),
        ("eddy_corrected.eddy_parameters", dwi_fname+".eddy_parameters"),
        ("qc/eddy_corrected", "qc/"+dwi_fname),
        ("derivatives/dmriprep", "derivatives/{}/dmriprep".format(bids_sub_name))
    ]

    wf.connect(prep, "outputnode.out_file", datasink, "dmriprep.dwi.@corrected")
    wf.connect(prep, "outputnode.out_bvec", datasink, "dmriprep.dwi.@rotated")
    wf.connect(prep, "fsl_eddy.out_parameter",
               datasink, "dmriprep.qc.@eddyparams")

    wf.connect(prep, "fsl_eddy.out_movement_rms",
               datasink, "dmriprep.qc.@eddyparamsrms")
    wf.connect(prep, "fsl_eddy.out_outlier_report",
               datasink, "dmriprep.qc.@eddyparamsreport")
    wf.connect(prep, "fsl_eddy.out_restricted_movement_rms",
               datasink, "dmriprep.qc.@eddyparamsrestrictrms")
    wf.connect(prep, "fsl_eddy.out_shell_alignment_parameters",
               datasink, "dmriprep.qc.@eddyparamsshellalign")

    wf.connect(save_outlier_list_node, "outpath", datasink, "dmriprep.qc.@droppedscans")

    wf.connect(get_tensor, "out_file", datasink, "dmriprep.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "dmriprep.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "dmriprep.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "dmriprep.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "dmriprep.dti.@rd")
    wf.connect(get_tensor, "color_fa_file", datasink, "dmriprep.dti.@colorfa")
    wf.connect(get_tensor, "out_file", datasink, "dmriprep.dti.@scaled_tensor")

    wf.connect(bbreg, "min_cost_file", datasink, "dmriprep.reg.@mincost")
    wf.connect(bbreg, "out_fsl_file", datasink, "dmriprep.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "dmriprep.reg.@reg")
    wf.connect(threshold2, "binary_file", datasink, "dmriprep.anat.@mask")

    convert = pe.Node(fs.MRIConvert(out_type="niigz"), name="convert2nii")
    wf.connect(vt2, "transformed_file", convert, "in_file")
    wf.connect(convert, "out_file", datasink, "dmriprep.anat.@aparc_aseg")

    convert1 = convert.clone("convertorig2nii")
    wf.connect(vt3, "transformed_file", convert1, "in_file")
    wf.connect(convert1, "out_file", datasink, "dmriprep.anat.@anat")

    def reportNodeFunc(dwi_corrected_file, eddy_rms, eddy_report,
                       color_fa_file, anat_mask_file):
        from dmriprep.qc import create_report_json

        report = create_report_json(dwi_corrected_file, eddy_rms, eddy_report,
                                    color_fa_file, anat_mask_file)
        return report

    reportNode = pe.Node(niu.Function(
        input_names=['dwi_corrected_file', 'eddy_rms',
                     'eddy_report', 'color_fa_file',
                     'anat_mask_file'],
        output_names=['report'],
        function=reportNodeFunc
    ), name="reportJSON")

    wf.connect(prep, "outputnode.out_file", reportNode, 'dwi_corrected_file')
    wf.connect(prep, "fsl_eddy.out_movement_rms", reportNode, 'eddy_rms')
    wf.connect(prep, "fsl_eddy.out_outlier_report", reportNode, 'eddy_report')
    wf.connect(threshold2, "binary_file", reportNode, 'anat_mask_file')
    wf.connect(get_tensor, "color_fa_file", reportNode, 'color_fa_file')

    wf.connect(reportNode, 'report', datasink, 'dmriprep.report.@report')

    wf.write_graph()
    wf.run()

    copyfile(bval_file, op.join(
        out_dir, "dmriprep", "dwi", op.split(bval_file)[1]
    ))
