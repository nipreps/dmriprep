import os.path as op
from shutil import copyfile


def run_preAFQ(dwi_file, dwi_file_AP, dwi_file_PA, bvec_file, bval_file,
               subjects_dir, working_dir, out_dir):
    """This is for HBN diffusion data

    Assuming phase-encode direction is AP/PA for topup
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
    wf = pe.Workflow(name="preAFQ")
    wf.base_dir = op.abspath(working_dir)

    prep.inputs.inputnode.in_file = dwi_file
    # prep.inputs.inputnode.alt_file = dwi_file_PA
    prep.inputs.inputnode.in_bvec = bvec_file
    prep.inputs.inputnode.in_bval = bval_file
    eddy = prep.get_node('fsl_eddy')
    eddy.inputs.repol = True
    eddy.inputs.niter = 1  # TODO: change back to 5 when running for real

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
        ("derivatives/preafq", "derivatives/{}/preafq".format(bids_sub_name))
    ]

    wf.connect(prep, "outputnode.out_file", datasink, "preafq.dwi.@corrected")
    wf.connect(prep, "outputnode.out_bvec", datasink, "preafq.dwi.@rotated")
    wf.connect(prep, "fsl_eddy.out_parameter",
               datasink, "preafq.qc.@eddyparams")

    wf.connect(prep, "fsl_eddy.out_movement_rms",
               datasink, "preafq.qc.@eddyparamsrms")
    wf.connect(prep, "fsl_eddy.out_outlier_report",
               datasink, "preafq.qc.@eddyparamsreport")
    wf.connect(prep, "fsl_eddy.out_restricted_movement_rms",
               datasink, "preafq.qc.@eddyparamsrestrictrms")
    wf.connect(prep, "fsl_eddy.out_shell_alignment_parameters",
               datasink, "preafq.qc.@eddyparamsshellalign")

    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "preafq.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "preafq.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "preafq.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "preafq.dti.@rd")
    wf.connect(get_tensor, "color_fa_file", datasink, "preafq.dti.@colorfa")
    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@scaled_tensor")

    wf.connect(bbreg, "min_cost_file", datasink, "preafq.reg.@mincost")
    wf.connect(bbreg, "out_fsl_file", datasink, "preafq.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "preafq.reg.@reg")
    wf.connect(threshold2, "binary_file", datasink, "preafq.anat.@mask")

    convert = pe.Node(fs.MRIConvert(out_type="niigz"), name="convert2nii")
    wf.connect(vt2, "transformed_file", convert, "in_file")
    wf.connect(convert, "out_file", datasink, "preafq.anat.@aparc_aseg")

    convert1 = convert.clone("convertorig2nii")
    wf.connect(vt3, "transformed_file", convert1, "in_file")
    wf.connect(convert1, "out_file", datasink, "preafq.anat.@anat")

    def reportNodeFunc(dwi_corrected_file, eddy_rms, eddy_report,
                       color_fa_file, anat_mask_file):
        from preafq.qc import create_report_json

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

    wf.connect(reportNode, 'report', datasink, 'preafq.report.@report')

    wf.run()

    copyfile(bval_file, op.join(
        out_dir, bids_sub_name, "preafq", "dwi", op.split(bval_file)[1]
    ))
