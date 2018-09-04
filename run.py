def run_preAFQ(dwi_file, bvec_file, bval_file, working_dir, sink_dir):
    import nipype.interfaces.fsl as fsl
    from nipype.interfaces.fsl.utils import AvScale
    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as niu
    import nipype.interfaces.io as nio
    from nipype.workflows.dmri.fsl.epi import create_dmri_preprocessing
    from nipype.interfaces.dipy import DTI
    from nipype.utils.filemanip import fname_presuffix
    import os

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
                                     ("_rotated.bvec ", ".bvec"),
                                     ("derivatives/dwi", "derivatives/{}/dwi".format(bids_subject_name))]

    wf.connect(art, "statistic_files", datasink, "dwi.@artstat")
    wf.connect(outputspec, "dmri_corrected", datasink, "dwi.@corrected")
    wf.connect(outputspec,"bvec_rotated", datasink, "dwi.@rotated")
    wf.connect(getmotion, "motion_params", datasink, "dwi.@motion")

    wf.base_dir = working_dir
    wf.run()

    from glob import glob 
    import os
    from shutil import copyfile

    copyfile(bval_file, os.path.join(sink_dir, bids_subject_name, "dwi", os.path.split(bval_file)[1]))
    
    dmri_corrected = glob(os.path.join(sink_dir, '*/dwi', '*.nii.gz'))[0]
    bvec_rotated = glob(os.path.join(sink_dir, '*/dwi', '*.bvec'))[0]
    bval_file = glob(os.path.join(sink_dir, '*/dwi', '*.bval'))[0]
    art_file = glob(os.path.join(sink_dir, '*/dwi', '*.art.json'))[0]
    motion_file = glob(os.path.join(sink_dir, '*/dwi', '*.motion.txt'))[0]
    return dmri_corrected, bvec_rotated, art_file, motion_file