def run_preAFQ(dwi_file, bvec_file, bval_file, subjects_dir, working_dir, sink_dir):
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

    wf = create_dmri_preprocessing(name='preAFQ', 
                                use_fieldmap=False,
                                fieldmap_registration=False)
    wf.inputs.inputnode.ref_num = 0
    wf.inputs.inputnode.in_file = dwi_file
    wf.inputs.inputnode.in_bvec = bvec_file

    dwi_filename = os.path.split(dwi_file)[1].split(".nii.gz")[0]
    bids_subject_name = dwi_filename.split("_")[0]
    assert bids_subject_name.startswith("sub-")

    inputnode = wf.get_node("inputnode")
    outputspec = wf.get_node("outputnode")

    #QC: FLIRT translation and rotation parameters
    flirt = wf.get_node("motion_correct.coregistration")
    #flirt.inputs.save_mats = True

    get_tensor = pe.Node(DTI(), name="dipy_tensor")
    wf.connect(outputspec, "dmri_corrected",get_tensor,"in_file")
    #wf.connect(inputspec2,"bvals", get_tensor, "in_bval")
    get_tensor.inputs.in_bval = bval_file
    wf.connect(outputspec, "bvec_rotated", get_tensor, "in_bvec")

    scale_tensor = pe.Node(name='scale_tensor', interface=fsl.BinaryMaths())
    scale_tensor.inputs.operation = 'mul'
    scale_tensor.inputs.operand_value = 1000
    wf.connect(get_tensor, 'out_file', scale_tensor, 'in_file')

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")
    wf.connect(outputspec, "dmri_corrected", fslroi, "in_file")

    bbreg = pe.Node(fs.BBRegister(contrast_type="t2", init="fsl", out_fsl_file=True,
                                  subjects_dir=subjects_dir,
                                  epi_mask=True),
                    name="bbreg")
    #wf.connect(inputspec2,"fsid", bbreg,"subject_id")
    bbreg.inputs.subject_id = 'freesurfer' #bids_subject_name
    wf.connect(fslroi,"roi_file", bbreg, "source_file")

    voltransform = pe.Node(fs.ApplyVolTransform(inverse=True),
                              iterfield=['source_file', 'reg_file'],
                              name='transform')
    voltransform.inputs.subjects_dir = subjects_dir

    vt2 = voltransform.clone("transform_aparcaseg")
    vt2.inputs.interp = "nearest"

    def binarize_aparc(aparc_aseg):
        import nibabel as nib
        from nipype.utils.filemanip import fname_presuffix
        import os
        img = nib.load(aparc_aseg)
        data, aff = img.get_data(), img.affine
        outfile = fname_presuffix(aparc_aseg, suffix="bin.nii.gz", newpath=os.path.abspath("."), use_ext=False)
        nib.Nifti1Image((data > 0).astype(float), aff).to_filename(outfile)
        return outfile

    #wf.connect(inputspec2, "mask_nii", voltransform, "target_file")
    create_mask = pe.Node(niu.Function(input_names=["aparc_aseg"], 
                                       output_names=["outfile"], 
                                       function=binarize_aparc),
                  name="bin_aparc")

    def get_aparc_aseg(subjects_dir, sub):
        return os.path.join(subjects_dir, sub, "mri", "aparc+aseg.mgz")

    create_mask.inputs.aparc_aseg = get_aparc_aseg(subjects_dir, 'freesurfer')
    wf.connect(create_mask, "outfile", voltransform, "target_file")

    wf.connect(fslroi, "roi_file", voltransform, "source_file")
    wf.connect(bbreg, "out_reg_file", voltransform, "reg_file")

    vt2.inputs.target_file = get_aparc_aseg(subjects_dir, 'freesurfer')
    #wf.connect(inputspec2, "aparc_aseg", vt2, "target_file")
    wf.connect(fslroi, "roi_file", vt2, "source_file")
    wf.connect(bbreg, "out_reg_file", vt2, "reg_file")

    # AK (2017): THIS NODE MIGHT NOT BE NECESSARY 
    # AK (2018) doesn't know why she said that above..
    threshold2 = pe.Node(fs.Binarize(min=0.5, out_type='nii.gz', dilate=1),
                            iterfield=['in_file'],
                            name='threshold2')
    wf.connect(voltransform, "transformed_file", threshold2, "in_file")


    #wf.connect(getmotion, "motion_params", datasink, "dti.@motparams")

    def get_flirt_motion_parameters(flirt_out_mats):
        import nipype.interfaces.fsl.utils as fsl
        import os
        import numpy as np
        
        def get_params(A):
            """This is a copy of spm's spm_imatrix where
            we already know the rotations and translations matrix,
            shears and zooms (as outputs from fsl FLIRT/avscale)
            Let A = the 4x4 rotation and translation matrix
            R = [          c5*c6,           c5*s6, s5]
                [-s4*s5*c6-c4*s6, -s4*s5*s6+c4*c6, s4*c5]
                [-c4*s5*c6+s4*s6, -c4*s5*s6-s4*c6, c4*c5]
            """
            import numpy as np

            def rang(b):
                a = min(max(b, -1), 1)
                return a
            Ry = np.arcsin(A[0,2])
            #Rx = np.arcsin(A[1,2]/np.cos(Ry))
            #Rz = np.arccos(A[0,1]/np.sin(Ry))

            if (abs(Ry)-np.pi/2)**2 < 1e-9:
                Rx = 0
                Rz = np.arctan2(-rang(A[1,0]), rang(-A[2,0]/A[0,2]))
            else:
                c  = np.cos(Ry)
                Rx = np.arctan2(rang(A[1,2]/c), rang(A[2,2]/c))
                Rz = np.arctan2(rang(A[0,1]/c), rang(A[0,0]/c))

            rotations = [Rx, Ry, Rz]
            translations = [A[0,3], A[1,3], A[2,3]]

            return rotations, translations


        motion_params = open(os.path.abspath('motion_parameters.par'),'w')
        for mat in flirt_out_mats:
            res = fsl.AvScale(mat_file = mat).run()
            A = np.asarray(res.outputs.rotation_translation_matrix)
            rotations, translations = get_params(A)
            for i in rotations+translations:
                motion_params.write('%f '%i)
            motion_params.write('\n')
        motion_params.close()
        motion_params = os.path.abspath('motion_parameters.par')
        return motion_params


    getmotion = pe.Node(niu.Function(input_names=["flirt_out_mats"],
        output_names=["motion_params"],
        function=get_flirt_motion_parameters),
        name="get_motion_parameters",iterfield="flirt_out_mats")

    wf.connect(flirt, "out_matrix_file", getmotion, "flirt_out_mats")

    from nipype.algorithms.rapidart import ArtifactDetect

    art = pe.Node(interface=ArtifactDetect(), name="art")
    art.inputs.use_differences = [True, True]
    art.inputs.save_plot=False
    art.inputs.use_norm = True
    art.inputs.norm_threshold = 3
    art.inputs.zintensity_threshold = 9
    art.inputs.mask_type = 'spm_global'
    art.inputs.parameter_source = 'FSL'

    wf.connect(getmotion, "motion_params", art, "realignment_parameters")
    wf.connect(outputspec, "dmri_corrected", art, "realigned_files")

    datasink = pe.Node(nio.DataSink(),name="sinker")
    datasink.inputs.base_directory = sink_dir
    datasink.inputs.substitutions = [("vol0000_flirt_merged.nii.gz", dwi_filename+'.nii.gz'),
                                     ("stats.vol0000_flirt_merged.txt", dwi_filename+".art.json"),
                                     ("motion_parameters.par", dwi_filename+".motion.txt"),
                                     ("_rotated.bvec", ".bvec"),
                                     ("aparc+aseg_warped_out", dwi_filename.replace("_dwi", "_aparc+aseg")),
                                     ("art.vol0000_flirt_merged_outliers.txt", dwi_filename+ ".outliers.txt"),
                                     ("vol0000_flirt_merged", dwi_filename),
                                     ("_roi_bbreg_freesurfer", "_register"),
                                     ("aparc+asegbin_warped_thresh", dwi_filename.replace("_dwi", "_mask")),
                                     ("derivatives/preafq", "derivatives/{}/preafq".format(bids_subject_name))]

    wf.connect(art, "statistic_files", datasink, "preafq.art.@artstat")
    wf.connect(art, "outlier_files", datasink, "preafq.art.@artoutlier")
    wf.connect(outputspec, "dmri_corrected", datasink, "preafq.dwi.@corrected")
    wf.connect(outputspec,"bvec_rotated", datasink, "preafq.dwi.@rotated")
    wf.connect(getmotion, "motion_params", datasink, "preafq.art.@motion")
    
    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "preafq.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "preafq.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "preafq.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "preafq.dti.@rd")
    wf.connect(get_tensor, "out_file", datasink, "preafq.dti.@scaled_tensor")

    wf.connect(bbreg, "min_cost_file", datasink, "preafq.reg.@mincost")
    wf.connect(bbreg,"out_fsl_file", datasink, "preafq.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "preafq.reg.@reg")
    wf.connect(threshold2, "binary_file", datasink, "preafq.anat.@mask")
    #wf.connect(vt2, "transformed_file", datasink, "dwi.@aparc_aseg")

    convert = pe.Node(fs.MRIConvert(out_type="niigz"), name="convert2nii")
    wf.connect(vt2, "transformed_file", convert, "in_file")
    wf.connect(convert, "out_file", datasink, "preafq.anat.@aparc_aseg")

    wf.base_dir = working_dir
    wf.run()

    from glob import glob 
    import os
    from shutil import copyfile

    copyfile(bval_file, os.path.join(sink_dir, bids_subject_name, "preafq", "dwi", os.path.split(bval_file)[1]))
    
    dmri_corrected = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.nii.gz'))[0]
    bvec_rotated = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.bvec'))[0]
    bval_file = glob(os.path.join(sink_dir, '*/preafq/dwi', '*.bval'))[0]
    art_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.art.json'))[0]
    motion_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.motion.txt'))[0]
    outlier_file = glob(os.path.join(sink_dir, '*/preafq/art', '*.outliers.txt'))[0]
    return dmri_corrected, bvec_rotated, art_file, motion_file, outlier_file