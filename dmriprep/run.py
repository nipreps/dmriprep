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


def run_dmriprep_pe(subject_id, dwi_file, dwi_file_AP, dwi_file_PA, bvec_file, bval_file,
                    subjects_dir, working_dir, out_dir):

    wf = get_dmriprep_pe_workflow(working_dir)
    wf.base_dir = op.join(op.abspath(working_dir), subject_id)

    inputspec = wf.get_node('inputspec')
    inputspec.inputs.subject_id = subject_id
    inputspec.inputs.dwi_file = dwi_file
    inputspec.inputs.dwi_file_ap = dwi_file_AP
    inputspec.inputs.dwi_file_pa = dwi_file_PA
    inputspec.inputs.bvec_file = bvec_file
    inputspec.inputs.bval_file = bval_file
    inputspec.inputs.subjects_dir = subjects_dir
    inputspec.inputs.out_dir = op.abspath(out_dir)

    wf.run()


def get_dmriprep_pe_workflow(working_dir):
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

    inputspec = pe.Node(niu.IdentityInterface(fields=[
        'subject_id',
        'dwi_file',
        'dwi_file_ap',
        'dwi_file_pa',
        'bvec_file',
        'bval_file',
        'subjects_dir',
        'out_dir'
    ]), name="inputspec")

    # inputspec.inputs.subject_id = subject_id
    # inputspec.inputs.dwi_file = dwi_file
    # inputspec.inputs.dwi_file_ap = dwi_file_AP
    # inputspec.inputs.dwi_file_pa = dwi_file_PA
    # inputspec.inputs.bvec_file = bvec_file
    # inputspec.inputs.bval_file = bval_file
    # inputspec.inputs.subjects_dir = subjects_dir
    # inputspec.inputs.out_dir = op.abspath(out_dir)
    #
    # # some bookkeeping (getting the filename, getting the BIDS subject name)
    # dwi_fname = op.split(dwi_file)[1].split(".nii.gz")[0]
    # bids_sub_name = subject_id
    # assert bids_sub_name.startswith("sub-")

    # Grab the preprocessing all_fsl_pipeline
    # AK: watch out, other datasets might be encoded LR
    epi_AP = {'echospacing': 66.5e-3, 'enc_dir': 'y-'}
    epi_PA = {'echospacing': 66.5e-3, 'enc_dir': 'y'}
    prep = all_fsl_pipeline(epi_params=epi_AP, altepi_params=epi_PA)

    # initialize an overall workflow
    wf = pe.Workflow(name="dmriprep")

    #prep.inputs.inputnode.in_file = dwi_file
    #prep.inputs.inputnode.in_bvec = bvec_file
    #prep.inputs.inputnode.in_bval = bval_file

    wf.connect(inputspec, 'dwi_file', prep, 'inputnode.in_file')
    wf.connect(inputspec, 'bvec_file', prep, 'inputnode.in_bvec')
    wf.connect(inputspec, 'bval_file', prep, 'inputnode.in_bval')

    eddy = prep.get_node('fsl_eddy')
    eddy.inputs.repol = True
    eddy.inputs.niter = 1  # TODO: make this a parameter to the function with default 5

    def id_outliers_fn(outlier_report, threshold, dwi_file):
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

        dwi_file: string
            Path to nii dwi file to determine total number of slices

        Returns
        -------
        drop_scans: numpy.ndarray
            List of scan indices to drop
        """
        import nibabel as nib
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

        if 0 < threshold < 1:
            threshold *= nib.load(dwi_file).shape[2]

        drop_scans = np.array([
            s for s in scans
            if num_outliers(s, outliers) > threshold
        ])

        outpath = op.abspath("dropped_scans.txt")
        np.savetxt(outpath, drop_scans, fmt="%d")

        return drop_scans, outpath

    id_outliers_node = pe.Node(niu.Function(
        input_names=["outlier_report", "threshold", "dwi_file"],
        output_names=["drop_scans", "outpath"],
        function=id_outliers_fn),
        name="id_outliers_node"
    )

    # TODO: make this a parameter to the function
    id_outliers_node.inputs.threshold = 0.02
    wf.connect(inputspec, 'dwi_file', id_outliers_node, 'dwi_file')
    # id_outliers_node.inputs.dwi_file = dwi_file
    wf.connect(prep, "fsl_eddy.out_outlier_report",
               id_outliers_node, "outlier_report")

    listMerge = pe.Node(niu.Merge(numinputs=2), name="listMerge")
    wf.connect(inputspec, 'dwi_file_ap', listMerge, 'in1')
    wf.connect(inputspec, 'dwi_file_pa', listMerge, 'in2')

    merge = pe.Node(fsl.Merge(dimension='t'), name="mergeAPPA")
    # merge.inputs.in_files = [dwi_file_AP, dwi_file_PA]
    wf.connect(merge, 'merged_file', prep, 'inputnode.alt_file')
    wf.connect(listMerge, 'out', merge, 'in_files')

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi")
    wf.connect(prep, "outputnode.out_file", fslroi, "in_file")

    bbreg = pe.Node(fs.BBRegister(contrast_type="t2", init="coreg",
                                  out_fsl_file=True,
                                  #subjects_dir=subjects_dir,
                                  epi_mask=True),
                    name="bbreg")
    bbreg.inputs.subject_id = 'freesurfer'  # bids_sub_name
    wf.connect(fslroi, "roi_file", bbreg, "source_file")
    wf.connect(inputspec, 'subjects_dir', bbreg, 'subjects_dir')

    def drop_outliers_fn(in_file, in_bval, in_bvec, drop_scans):
        """Drop outlier volumes from dwi file

        Parameters
        ----------
        in_file: string
            Path to nii dwi file to drop outlier volumes from

        in_bval: string
            Path to bval file to drop outlier volumes from

        in_bvec: string
            Path to bvec file to drop outlier volumes from

        drop_scans: numpy.ndarray
            List of scan indices to drop

        Returns
        -------
        out_file: string
            Path to "thinned" output dwi file

        out_bval: string
            Path to "thinned" output bval file

        out_bvec: string
            Path to "thinned" output bvec file
        """
        import nibabel as nib
        import numpy as np
        import os.path as op
        from nipype.utils.filemanip import fname_presuffix

        img = nib.load(op.abspath(in_file))
        img_data = img.get_fdata()
        img_data_thinned = np.delete(img_data, drop_scans, axis=3)
        img_thinned = nib.Nifti1Image(img_data_thinned.astype(np.float64), img.affine)

        root, ext1 = op.splitext(in_file)
        root, ext0 = op.splitext(root)
        out_file = fname_presuffix(in_file, suffix="_thinned", newpath=op.abspath('.')) #''.join([root + "_thinned", ext0, ext1])
        nib.save(img_thinned, op.abspath(out_file))

        bval = np.loadtxt(in_bval)
        bval_thinned = np.delete(bval, drop_scans, axis=0)
        out_bval = fname_presuffix(in_bval, suffix="_thinned", newpath=op.abspath('.'))
        np.savetxt(out_bval, bval_thinned)

        bvec = np.loadtxt(in_bvec)
        bvec_thinned = np.delete(bvec, drop_scans, axis=1)
        out_bvec = fname_presuffix(in_bvec, suffix="_thinned", newpath=op.abspath('.'))
        np.savetxt(out_bvec, bvec_thinned)

        return out_file, out_bval, out_bvec

    drop_outliers_node = pe.Node(niu.Function(
        input_names=["in_file", "in_bval", "in_bvec", "drop_scans"],
        output_names=["out_file", "out_bval", "out_bvec"],
        function=drop_outliers_fn),
        name="drop_outliers_node"
    )


    # Align the output of drop_outliers_node & also the eddy corrected version to the anatomical space
    # without resampling. and then for aparc+aseg & the mask, resample to the larger voxel size of the B0 image from
    # fslroi. Also we need to apply the transformation to both bvecs (dropped & eddied) and I think we can just load
    # the affine from bbreg (sio.loadmat) and np.dot(coord, aff) for each coord in bvec

    def get_orig(subjects_dir, sub='freesurfer'):
        import os.path as op
        return op.join(subjects_dir, sub, "mri", "orig.mgz")

    # transform the dropped volume version to anat space w/ out resampling
    voltransform = pe.Node(fs.ApplyVolTransform(no_resample=True),
                           iterfield=['source_file', 'reg_file'],
                           name='transform')
    #voltransform.inputs.subjects_dir = subjects_dir
    wf.connect(inputspec, 'subjects_dir', voltransform, 'subjects_dir')
    #voltransform.inputs.target_file = get_orig(subjects_dir, 'freesurfer')
    wf.connect(inputspec, ('subjects_dir', get_orig), voltransform, 'target_file')
    wf.connect(prep, "outputnode.out_file", voltransform, "source_file")
    wf.connect(bbreg, "out_reg_file", voltransform, "reg_file")

    def func_applyTransformToBvecs(bvec_file, reg_mat_file):
        import numpy as np
        import nipype.utils.filemanip as fm
        import os
        aff = np.loadtxt(reg_mat_file)
        bvecs = np.loadtxt(bvec_file)
        bvec_trans = []
        for bvec in bvecs.T:
            coord = np.hstack((bvec, [1]))
            coord_trans = np.dot(coord, aff)[:-1]
            bvec_trans.append(coord_trans)
        out_bvec = fm.fname_presuffix(bvec_file, suffix="anat_space", newpath=os.path.abspath('.'))
        np.savetxt(out_bvec, np.asarray(bvec_trans).T)
        return out_bvec

    node_applyTransformToBvecs = pe.Node(niu.Function(input_names=['bvec_file', 'reg_mat_file'],
                                                      output_names=['out_bvec'],
                                                      function=func_applyTransformToBvecs),
                                         name="applyTransformToBvecs")
    wf.connect(bbreg, 'out_fsl_file', node_applyTransformToBvecs, 'reg_mat_file')
    wf.connect(prep, 'outputnode.out_bvec', node_applyTransformToBvecs, 'bvec_file')

    # ok cool, now lets do the thresholding.

    wf.connect(id_outliers_node, "drop_scans", drop_outliers_node, "drop_scans")
    wf.connect(voltransform, "transformed_file", drop_outliers_node, "in_file")
    wf.connect(inputspec, 'bval_file', drop_outliers_node, 'in_bval')
    # drop_outliers_node.inputs.in_bval = bval_file
    wf.connect(node_applyTransformToBvecs, "out_bvec", drop_outliers_node, "in_bvec")

    # lets compute the tensor on both the dropped volume scan
    # and also the original, eddy corrected one.
    get_tensor = pe.Node(DTI(), name="dipy_tensor")
    wf.connect(drop_outliers_node, "out_file", get_tensor, "in_file")
    wf.connect(drop_outliers_node, "out_bval", get_tensor, "in_bval")
    wf.connect(drop_outliers_node, "out_bvec", get_tensor, "in_bvec")

    get_tensor_eddy = get_tensor.clone('dipy_tensor_eddy')
    wf.connect(voltransform, 'transformed_file', get_tensor_eddy, "in_file")
    wf.connect(node_applyTransformToBvecs, 'out_bvec', get_tensor_eddy, "in_bvec")
    wf.connect(inputspec, 'bval_file', get_tensor_eddy, 'in_bval')
    # get_tensor_eddy.inputs.in_bval = bval_file

    # AK: What is this, some vestigal node from a previous workflow?
    # I'm not sure why the tensor gets scaled. but i guess lets scale it for
    # both the dropped & eddy corrected versions.
    scale_tensor = pe.Node(name='scale_tensor', interface=fsl.BinaryMaths())
    scale_tensor.inputs.operation = 'mul'
    scale_tensor.inputs.operand_value = 1000
    wf.connect(get_tensor, 'out_file', scale_tensor, 'in_file')

    scale_tensor_eddy = scale_tensor.clone('scale_tensor_eddy')
    wf.connect(get_tensor_eddy, 'out_file', scale_tensor_eddy, 'in_file')


    # OK now that anatomical stuff (segmentation & mask)
    # We'll need:
    # 1. the B0 image in anat space (fslroi the 'transformed file' of voltransform
    # 2. the aparc aseg resampled-like the B0 image (mri_convert)
    # 3. the resample aparc_aseg binarized to be the mask image.

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

    def get_aparc_aseg(subjects_dir, sub='freesurfer'):
        import os.path as op
        return op.join(subjects_dir, sub, "mri", "aparc+aseg.mgz")

    getB0Anat = fslroi.clone('getB0Anat')
    wf.connect(voltransform, 'transformed_file', getB0Anat, 'in_file')

    # reslice the anat-space aparc+aseg to the DWI resolution
    resliceToDwi = pe.Node(fs.MRIConvert(resample_type="nearest"),
                            name="resampleToDWI")
    wf.connect(getB0Anat, 'roi_file', resliceToDwi, 'reslice_like')
    wf.connect(inputspec, ('subjects_dir', get_aparc_aseg), resliceToDwi, 'in_file')

    # also reslice the orig i suppose
    resliceOrigToDwi = resliceToDwi.clone('resliceT1wToDwi')
    wf.connect(inputspec, ('subjects_dir', get_orig), resliceOrigToDwi, 'in_file')
    # resliceOrigToDwi.inputs.in_file = get_orig(subjects_dir, 'freesurfer')
    resliceOrigToDwi.inputs.out_type = 'niigz'
    wf.connect(getB0Anat, 'roi_file', resliceOrigToDwi, 'reslice_like')

    # we assume the freesurfer is the output of BIDS
    # so the freesurfer output is in /path/to/derivatives/sub-whatever/freesurfer
    # which means the subject_dir is /path/to/derivatives/sub-whatever
    # resliceToDwi.inputs.in_file = get_aparc_aseg(subjects_dir, 'freesurfer')

    # now we have a nice aparc+aseg still in anat space but resliced like the dwi file
    # lets create a mask file from it.

    wf.connect(resliceToDwi, 'out_file', create_mask, 'aparc_aseg')

    # save all the things
    datasink = pe.Node(nio.DataSink(), name="sinker")
    wf.connect(inputspec, 'out_dir', datasink, 'base_directory')
    wf.connect(inputspec, 'subject_id', datasink, 'container')
    # datasink.inputs.base_directory = op.join(op.abspath(out_dir), subject_id)
    # datasink.inputs.container = subject_id

    wf.connect(drop_outliers_node, "out_file", datasink, "dmriprep.dwi.@thinned")
    wf.connect(drop_outliers_node, "out_bval", datasink, "dmriprep.dwi.@bval_thinned")
    wf.connect(drop_outliers_node, "out_bvec", datasink, "dmriprep.dwi.@bvec_thinned")

    # eddy corrected files
    wf.connect(prep, "outputnode.out_file", datasink, "dmriprep.dwi_eddy.@corrected")
    wf.connect(prep, "outputnode.out_bvec", datasink, "dmriprep.dwi_eddy.@rotated")
    wf.connect(inputspec, 'bval_file', datasink, 'dmriprep.dwi_eddy.@bval')

    # all the eddy stuff except the corrected files
    wf.connect(prep, "fsl_eddy.out_movement_rms",
               datasink, "dmriprep.qc.@eddyparamsrms")
    wf.connect(prep, "fsl_eddy.out_outlier_report",
               datasink, "dmriprep.qc.@eddyparamsreport")
    wf.connect(prep, "fsl_eddy.out_restricted_movement_rms",
               datasink, "dmriprep.qc.@eddyparamsrestrictrms")
    wf.connect(prep, "fsl_eddy.out_shell_alignment_parameters",
               datasink, "dmriprep.qc.@eddyparamsshellalign")
    wf.connect(prep, "fsl_eddy.out_parameter",
               datasink, "dmriprep.qc.@eddyparams")

    # the file that told us which volumes to trop
    wf.connect(id_outliers_node, "outpath", datasink, "dmriprep.qc.@droppedscans")

    # the tensors of the dropped volumes dwi
    wf.connect(get_tensor, "out_file", datasink, "dmriprep.dti.@tensor")
    wf.connect(get_tensor, "fa_file", datasink, "dmriprep.dti.@fa")
    wf.connect(get_tensor, "md_file", datasink, "dmriprep.dti.@md")
    wf.connect(get_tensor, "ad_file", datasink, "dmriprep.dti.@ad")
    wf.connect(get_tensor, "rd_file", datasink, "dmriprep.dti.@rd")
    wf.connect(get_tensor, "color_fa_file", datasink, "dmriprep.dti.@colorfa")
    wf.connect(scale_tensor, "out_file", datasink, "dmriprep.dti.@scaled_tensor")

    # the tensors of the eddied volumes dwi
    wf.connect(get_tensor_eddy, "out_file", datasink, "dmriprep.dti_eddy.@tensor")
    wf.connect(get_tensor_eddy, "fa_file", datasink, "dmriprep.dti_eddy.@fa")
    wf.connect(get_tensor_eddy, "md_file", datasink, "dmriprep.dti_eddy.@md")
    wf.connect(get_tensor_eddy, "ad_file", datasink, "dmriprep.dti_eddy.@ad")
    wf.connect(get_tensor_eddy, "rd_file", datasink, "dmriprep.dti_eddy.@rd")
    wf.connect(get_tensor_eddy, "color_fa_file", datasink, "dmriprep.dti_eddy.@colorfa")
    wf.connect(scale_tensor_eddy, "out_file", datasink, "dmriprep.dti_eddy.@scaled_tensor")

    # anatomical registration stuff
    wf.connect(bbreg, "min_cost_file", datasink, "dmriprep.reg.@mincost")
    wf.connect(bbreg, "out_fsl_file", datasink, "dmriprep.reg.@fslfile")
    wf.connect(bbreg, "out_reg_file", datasink, "dmriprep.reg.@reg")

    # anatomical files resliced
    wf.connect(resliceToDwi, 'out_file', datasink, 'dmriprep.anat.@segmentation')
    wf.connect(create_mask, 'outfile', datasink, 'dmriprep.anat.@mask')
    wf.connect(resliceOrigToDwi, 'out_file', datasink, 'dmriprep.anat.@T1w')

    def reportNodeFunc(dwi_corrected_file, eddy_rms, eddy_report,
                       color_fa_file, anat_mask_file, outlier_indices):
        from dmriprep.qc import create_report_json

        report = create_report_json(dwi_corrected_file, eddy_rms, eddy_report,
                                    color_fa_file, anat_mask_file, outlier_indices)
        return report

    reportNode = pe.Node(niu.Function(
        input_names=['dwi_corrected_file', 'eddy_rms',
                     'eddy_report', 'color_fa_file',
                     'anat_mask_file', 'outlier_indices'],
        output_names=['report'],
        function=reportNodeFunc
    ), name="reportJSON")

    # for the report, lets show the eddy corrected (full volume) image
    wf.connect(voltransform, "transformed_file", reportNode, 'dwi_corrected_file')

    # add the rms movement output from eddy
    wf.connect(prep, "fsl_eddy.out_movement_rms", reportNode, 'eddy_rms')
    wf.connect(prep, "fsl_eddy.out_outlier_report", reportNode, 'eddy_report')
    wf.connect(id_outliers_node, 'drop_scans', reportNode, 'outlier_indices')

    # the mask file to check our registration, and the colorFA file go in the report
    wf.connect(create_mask, "outfile", reportNode, 'anat_mask_file')
    wf.connect(get_tensor, "color_fa_file", reportNode, 'color_fa_file')

    # save that report!
    wf.connect(reportNode, 'report', datasink, 'dmriprep.report.@report')

    # this part is done last, to get the filenames *just right*
    # its super annoying.
    def name_files_nicely(dwi_file, subject_id):
        import os.path as op
        dwi_fname = op.split(dwi_file)[1].split(".nii.gz")[0]
        substitutions = [
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
            ("aparc+aseg_outbin", dwi_fname.replace("_dwi", "_mask")),
            ("aparc+aseg_out", dwi_fname.replace("_dwi", "_aparc+aseg")),
            ("art.eddy_corrected_outliers", dwi_fname.replace("dwi", "outliers")),
            ("color_fa", "colorfa"),
            ("orig_out", dwi_fname.replace("_dwi", "_T1w")),
            # ("eddy_corrected_", dwi_fname.replace("dwi", "")),
            ("stats.eddy_corrected", dwi_fname.replace("dwi", "artStats")),
            ("eddy_corrected.eddy_parameters", dwi_fname+".eddy_parameters"),
            ("qc/eddy_corrected", "qc/"+dwi_fname),
            ("derivatives/dmriprep", "derivatives/{}/dmriprep".format(subject_id)),
            ("_rotatedanat_space_thinned", ""),
            ("_thinned", ""),
            ("eddy_corrected", dwi_fname),
            ("_warped", ""),
            ("_maths", "_scaled"),
            ("dropped_scans", dwi_fname.replace("_dwi", "_dwi_dropped_scans")),
            ("report.json", dwi_fname.replace("_dwi", "_dwi_report.json"))
        ]
        return substitutions

    node_name_files_nicely = pe.Node(niu.Function(input_names=['dwi_file', 'subject_id'],
                                                  output_names=['substitutions'],
                                                  function=name_files_nicely),
                                     name="name_files_nicely"
                                     )
    wf.connect(inputspec, 'dwi_file', node_name_files_nicely, 'dwi_file')
    wf.connect(inputspec, 'subject_id', node_name_files_nicely, 'subject_id')
    wf.connect(node_name_files_nicely, 'substitutions', datasink, 'substitutions')

    # write the graph (this is saved to the working dir)
    wf.write_graph()

    return wf
