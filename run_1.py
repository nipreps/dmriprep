def get_flirt_motion_parameters(eddy_params):
        import nipype.interfaces.fsl.utils as fsl
        import os
        import numpy as np

        data = np.genfromtxt(eddy_params)
        translations = data[:,:3]
        rotations = data[:,3:6]
        rigid = np.hstack((rotations, translations))
        
        motion_params = os.path.abspath('motion_parameters.par')
        np.savetxt(motion_params, rigid)

        return motion_params


def run_preAFQ(dwi_file, dwi_file_AP, dwi_file_PA, bvec_file, bval_file, subjects_dir, working_dir, sink_dir):
    """
        This is for HBN diffusion data
        Assuming phase-encode direction is AP/PA for topup
    """
    import nipype.interfaces.freesurfer as fs
    import nipype.interfaces.fsl as fsl
    from nipype.interfaces.fsl.utils import AvScale
    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as niu
    import nipype.interfaces.io as nio
    from nipype.workflows.dmri.fsl.epi import create_dmri_preprocessing
    from nipype.interfaces.dipy import DTI
    from nipype.utils.filemanip import fname_presuffix
    import os
    from nipype.interfaces.dipy import DTI
    from nipype.interfaces.c3 import C3dAffineTool
    from nipype.workflows.dmri.fsl.artifacts import all_fsl_pipeline, remove_bias

    # some bookkeeping (getting the filename, gettings the BIDS subject name)
    dwi_filename = os.path.split(dwi_file)[1].split(".nii.gz")[0]
    bids_subject_name = dwi_filename.split("_")[0]
    assert bids_subject_name.startswith("sub-")

    # Grab the preprocessing all_fsl_pipeline
    # AK: watch out, other datasets might be encoded LR
    epi_AP = {'echospacing': 66.5e-3, 'enc_dir': 'y-'}
    epi_PA = {'echospacing': 66.5e-3, 'enc_dir': 'y'}
    prep = all_fsl_pipeline(epi_params=epi_AP, altepi_params=epi_PA)
    prep_inputspec = prep.get_node('inputnode')
    prep_outputspec = prep.get_node('outputnode')
    #print(prep_inputspec, prep_outputspec)

    # initialize an overall workflow
    wf = pe.Workflow(name="preAFQ")
    wf.base_dir = os.path.abspath(working_dir)
    # wf.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
    #             (datasource, prep,
    #             [('dwi', 'inputnode.in_file'), ('dwi_rev', 'inputnode.alt_file'),
    #             ('bvals', 'inputnode.in_bval'), ('bvecs', 'inputnode.in_bvec')]),
    #             (prep, bias, [('outputnode.out_file', 'inputnode.in_file'),
    #                         ('outputnode.out_mask', 'inputnode.in_mask')]),
    #             (datasource, bias, [('bvals', 'inputnode.in_bval')])])

    # wf = create_dmri_preprocessing(name='preAFQ', 
    #                             use_fieldmap=False,
    #                             fieldmap_registration=False)

    prep.inputs.inputnode.in_file = dwi_file
    #prep.inputs.inputnode.alt_file = dwi_file_PA
    prep.inputs.inputnode.in_bvec = bvec_file
    prep.inputs.inputnode.in_bval = bval_file
    #print(prep.inputs)

    merge = pe.Node(fsl.Merge(dimension='t'), name="mergeAPPA")
    merge.inputs.in_files = [dwi_file_AP, dwi_file_PA]
    wf.connect(merge, 'merged_file', prep, 'inputnode.alt_file')


    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")
    wf.connect(prep, "outputnode.out_file", fslroi, "in_file")

    bbreg = pe.Node(fs.BBRegister(contrast_type="t2", init="fsl", out_fsl_file=True,
                                  subjects_dir=subjects_dir,
                                  epi_mask=True),
                    name="bbreg")
    bbreg.inputs.subject_id = 'freesurfer' #bids_subject_name
    wf.connect(fslroi,"roi_file", bbreg, "source_file")

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
        import os
        img = nib.load(aparc_aseg)
        data, aff = img.get_data(), img.affine
        outfile = fname_presuffix(aparc_aseg, suffix="bin.nii.gz", newpath=os.path.abspath("."), use_ext=False)
        nib.Nifti1Image((data > 0).astype(float), aff).to_filename(outfile)
        return outfile

    create_mask = pe.Node(niu.Function(input_names=["aparc_aseg"], 
                                       output_names=["outfile"], 
                                       function=binarize_aparc),
                  name="bin_aparc")

    def get_aparc_aseg(subjects_dir, sub):
        return os.path.join(subjects_dir, sub, "mri", "aparc+aseg.mgz")
    
    def get_orig(subjects_dir, sub):
        return os.path.join(subjects_dir, sub, "mri", "orig.mgz")

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

    # art detect stuff

    motion = pe.Node(niu.Function(input_names=['eddy_params'], 
                                  output_names=['motion_file'],
                                  function=get_flirt_motion_parameters), 
                     name="reformat_motion")
    
    wf.connect(prep, "fsl_eddy.out_parameter", motion, "eddy_params")

    from nipype.algorithms.rapidart import ArtifactDetect

    art = pe.Node(interface=ArtifactDetect(), name="art")
    art.inputs.use_differences = [True, True]
    art.inputs.save_plot=False
    art.inputs.use_norm = True
    art.inputs.norm_threshold = 3
    art.inputs.zintensity_threshold = 9
    art.inputs.mask_type = 'spm_global'
    art.inputs.parameter_source = 'FSL'

    wf.connect(motion, "motion_file", art, "realignment_parameters")
    wf.connect(prep, "outputnode.out_file", art, "realigned_files")

    datasink = pe.Node(nio.DataSink(),name="sinker")
    datasink.inputs.base_directory = sink_dir
    datasink.inputs.substitutions = [("vol0000_flirt_merged.nii.gz", dwi_filename+'.nii.gz'),
                                     ("stats.vol0000_flirt_merged.txt", dwi_filename+".art.json"),
                                     ("motion_parameters.par", dwi_filename+".motion.txt"),
                                     ("_rotated.bvec", ".bvec"),
                                     ("art.vol0000_flirt_merged_outliers.txt", dwi_filename+ ".outliers.txt"),
                                     ("vol0000_flirt_merged", dwi_filename),
                                     ("_roi_bbreg_freesurfer", "_register"),
                                     ("dwi/eddy_corrected", "dwi/%s" % dwi_filename),
                                     ("dti/eddy_corrected", "dti/%s" % dwi_filename.replace("_dwi", "")),
                                     ("reg/eddy_corrected", "reg/%s" % dwi_filename.replace("_dwi", "")),
                                     ("aparc+asegbin_warped_thresh", dwi_filename.replace("_dwi", "_mask")),
                                     ("aparc+aseg_warped_out", dwi_filename.replace("_dwi", "_aparc+aseg")),
                                     ("art.eddy_corrected_outliers", dwi_filename.replace("dwi", "outliers")),
                                     ("color_fa", "colorfa"),
                                     ("orig_warped_out", dwi_filename.replace("_dwi", "_T1w")),
                                     #("eddy_corrected_", dwi_filename.replace("dwi", "")),
                                     ("stats.eddy_corrected", dwi_filename.replace("dwi", "artStats")),
                                     ("eddy_corrected.eddy_parameters", dwi_filename+".eddy_parameters"),
                                     ("derivatives/preafq", "derivatives/{}/preafq".format(bids_subject_name))]

    
    wf.connect(art, "statistic_files", datasink, "preafq.qc.@artstat")
    wf.connect(art, "outlier_files", datasink, "preafq.qc.@artoutlier")

    wf.connect(prep, "outputnode.out_file", datasink, "preafq.dwi.@corrected")
    wf.connect(prep, "outputnode.out_bvec", datasink, "preafq.dwi.@rotated")
    wf.connect(prep, "fsl_eddy.out_parameter", datasink, "preafq.qc.@eddyparams")
    
    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "preafq.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "preafq.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "preafq.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "preafq.dti.@rd")
    wf.connect(get_tensor, "color_fa_file", datasink, "preafq.dti.@colorfa")
    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@scaled_tensor")

    wf.connect(bbreg, "min_cost_file", datasink, "preafq.reg.@mincost")
    wf.connect(bbreg,"out_fsl_file", datasink, "preafq.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "preafq.reg.@reg")
    wf.connect(threshold2, "binary_file", datasink, "preafq.anat.@mask")

    convert = pe.Node(fs.MRIConvert(out_type="niigz"), name="convert2nii")
    wf.connect(vt2, "transformed_file", convert, "in_file")
    wf.connect(convert, "out_file", datasink, "preafq.anat.@aparc_aseg")

    convert1 = convert.clone("convertorig2nii")
    wf.connect(vt3, "transformed_file", convert1, "in_file")
    wf.connect(convert1, "out_file", datasink, "preafq.anat.@anat")

    #wf.base_dir = working_dir
    #wf.write_graph()
    wf.run()

    from glob import glob 
    import os
    from shutil import copyfile

    copyfile(bval_file, os.path.join(sink_dir, bids_subject_name, "preafq", "dwi", os.path.split(bval_file)[1]))
    
    # dmri_corrected = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.nii.gz'))[0]
    # bvec_rotated = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.bvec'))[0]
    # bval_file = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.bval'))[0]
    # # art_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.art.json'))[0]
    # # motion_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.motion.txt'))[0]
    # # outlier_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.outliers.txt'))[0]
    # return dmri_corrected, bvec_rotated, #art_file, motion_file, outlier_file