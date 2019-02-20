"""
BIDS-functions to return inputs for the run.py functions.

"""
import os
import os.path as op
from glob import glob

import bids


def get_bids_subject_input_files(subject_id, bids_input_directory):
    """
    Function to return the needed files for dmriprep based on subject id and a bids directory.

    :param subject_id: string
    :param bids_input_directory: string to bids dir
    :return: dict of inputs
    """
    layout = bids.layout.BIDSLayout(bids_input_directory)
    subjects = layout.get_subjects()
    assert subject_id in subjects, "subject {} is not in the bids folder".format(subject_id)

    ap_file = layout.get(subject=subject_id,
                         datatype='fmap',
                         suffix='epi',
                         dir='AP',
                         extensions=['.nii', '.nii.gz'])
    assert len(ap_file) == 1, 'found {} ap fieldmap files and we need just 1'.format(len(ap_file))

    pa_file = layout.get(subject=subject_id,
                         datatype='fmap',
                         suffix='epi',
                         dir='PA',
                         extensions=['.nii', '.nii.gz'])
    assert len(pa_file) == 1, 'found {} pa fieldmap files and we need just 1'.format(len(pa_file))

    dwi_files = layout.get(subject=subject_id, datatype='dwi', suffix='dwi')
    valid_dwi_files = []

    for d in dwi_files:
        if d.path.startswith(op.abspath(op.join(bids_input_directory, 'sub-' + subject_id))):
            valid_dwi_files.append(d.path)

    dwi_file = [d for d in valid_dwi_files if d.endswith('.nii.gz') and not "TRACE" in d]
    assert len(dwi_file) == 1, 'found {} dwi files and we need just 1'.format(len(dwi_file))

    bval_file = [d for d in valid_dwi_files if d.endswith('.bval')]
    assert len(bval_file) == 1, 'found {} bval files and we need just 1'.format(len(bval_file))

    bvec_file = [d for d in valid_dwi_files if d.endswith('.bvec')]
    assert len(bvec_file) == 1, 'found {} bvec files and we need just 1'.format(len(bvec_file))

    subjects_dir = op.join(bids_input_directory, 'derivatives', 'sub-'+subject_id)

    if not op.exists(op.join(subjects_dir, 'freesurfer')):
        raise NotImplementedError('we have not yet implemented a version of dmriprep that runs freesurfer for you.'
                                  'please run freesurfer and try again'
                                  )

    outputs = dict(subject_id="sub-"+subject_id,
                   dwi_file=dwi_file[0],
                   dwi_file_AP=ap_file[0].path,
                   dwi_file_PA=pa_file[0].path,
                   bvec_file=bvec_file[0],
                   bval_file=bval_file[0],
                   subjects_dir=op.abspath(subjects_dir))
    return outputs


def get_bids_files(subject_id, bids_input_directory):
    """
    subject to get all bids files for am optional subject id and bids dir. if subject id is blank then all subjects
    are used.
    :param subject_id:
    :param bids_input_directory:
    :return:
    """
    if not subject_id:
        subjects = [s.split("/")[-1].replace("sub-", "") for s in glob(os.path.join(bids_input_directory, "sub-*"))]
        assert len(subjects), "No subject files found in bids directory"
        return [get_bids_subject_input_files(sub, bids_input_directory) for sub in subjects]
    else:
        return [get_bids_subject_input_files(subject_id, bids_input_directory)]
