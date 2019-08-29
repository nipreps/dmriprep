#!/usr/bin/env python

"""
dMRIprep base processing workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dmriprep_wf
.. autofunction:: init_single_subject_wf

"""

import os
from copy import deepcopy

from nipype.pipeline import engine as pe

from .utils.bids import collect_data
from .dwi import init_dwi_preproc_wf, init_dwi_derivatives_wf


def init_dmriprep_wf(
    subject_list,
    session_list,
    layout,
    output_dir,
    work_dir,
    ignore,
    concat_dwis,
    b0_thresh,
    output_resolution,
    bet_dwi,
    bet_mag,
    nthreads,
    omp_nthreads,
    synb0_dir
):
    """
    This workflow organizes the execusion of dMRIprep, with a sub-workflow for
    each subject.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

    from collections import namedtuple
    from dmriprep.workflows.base import init_dmriprep_wf
    BIDSLayout = namedtuple('BIDSLayout', ['root'])
    wf = init_dmriprep_wf(
      subject_list=['dmripreptest'],
      session_list=[],
      layout=BIDSLayout('.', validate=False),
      output_dir='.',
      work_dir='.',
      ignore=[],
      b0_thresh=5,
      output_resolution=(1, 1, 1),
      bet_dwi=0.3,
      bet_mag=0.3,
      nthreads=4,
      omp_nthreads=1,
      synb0_dir='.'
    )

    Parameters

        subject_list: list
            List of subject labels
        session_list: list
            List of session labels
        layout: BIDSLayout object
            BIDS dataset layout
        output_dir: str
            Directory in which to save derivatives
        work_dir: str
            Directory in which to store workflow execution state and temporary files
        ignore: list
            Preprocessing steps to skip (may include 'denoise', 'unring', 'fieldmaps')
        concat_dwis: list
            List of dwi images to concatenate (specified with the 'acq-') tag
        b0_thresh: int
            Threshold for identifying bval as a b0
        output_resolution: tuple
            Output resolution of dwi image in x, y and z axes
        bet_dwi: float
            Fractional intensity threshold for BET on dwi image
        bet_mag: float
            Fractional intensity threshold for BET on magnitude image
        nthreads: int
            Maximum number of threads to use
        omp_nthreads: int
            Maximum number of threads an individual process may use
        synb0_dir: str
            Direction in which synb0 derivatives are saved

    """
    dmriprep_wf = pe.Workflow(name='dmriprep_wf')
    dmriprep_wf.base_dir = work_dir

    for subject_id in subject_list:

        single_subject_wf = init_single_subject_wf(
            subject_id=subject_id,
            session_list=session_list,
            name='single_subject_' + subject_id + '_wf',
            layout=layout,
            output_dir=output_dir,
            work_dir=work_dir,
            ignore=ignore,
            concat_dwis=concat_dwis,
            b0_thresh=b0_thresh,
            output_resolution=output_resolution,
            bet_dwi=bet_dwi,
            bet_mag=bet_mag,
            omp_nthreads=omp_nthreads,
            synb0_dir=synb0_dir
        )

        single_subject_wf.config['execution']['crashdump_dir'] = os.path.join(
            output_dir, 'dmriprep', 'sub-' + subject_id, 'log'
        )
        single_subject_wf.config['execution']['remove_unnecessary_outputs'] = False
        single_subject_wf.config['execution']['keep_inputs'] = True
        single_subject_wf.config['execution']['crashfile_format'] = 'txt'

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)

        dmriprep_wf.add_nodes([single_subject_wf])

    return dmriprep_wf


def init_single_subject_wf(
    subject_id,
    session_list,
    name,
    layout,
    output_dir,
    work_dir,
    ignore,
    concat_dwis,
    b0_thresh,
    output_resolution,
    bet_dwi,
    bet_mag,
    omp_nthreads,
    synb0_dir
):
    """
    This workflow organizes the preprocessing pipeline for a single subject.
    It collects and reports information about the subject, and prepares
    sub-workflows to perform diffusion preprocessing.

    Diffusion preprocessing is performed using a separate workflow for each
    individual dwi series.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

    from collections import namedtuple
    from dmriprep.workflows.base import init_single_subject_wf
    BIDSLayout = namedtuple('BIDSLayout', ['root'])
    wf = init_single_subject_wf(
        subject_id='test',
        session_list=[],
        name='single_subject_wf',
        layout=BIDSLayout,
        output_dir='.',
        work_dir='.',
        ignore=[],
        b0_thresh=5,
        output_resolution=(1, 1, 1),
        bet_dwi=0.3,
        bet_mag=0.3,
        omp_nthreads=1,
        synb0_dir=''
    )

    Parameters

        subject_id: str
            Single subject label
        session_list: list
            List of sessions
        layout: BIDSLayout object
            BIDS dataset layout
        output_dir: str
            Directory in which to save derivatives
        work_dir: str
            Directory in which to store workflow execution state and temporary files
        ignore: list
            Preprocessing steps to skip (may include 'denoise', 'unring', 'fieldmaps')
        concat_dwis: list
            List of dwi images to concatenate (specified with the 'acq-') tag
        b0_thresh: int
            Threshold for identifying bval as a b0
        output_resolution: tuple
            Output resolution of dwi image in x, y and z axes
        bet_dwi: float
            Fractional intensity threshold for BET on dwi image
        bet_mag: float
            Fractional intensity threshold for BET on magnitude image
        omp_nthreads: int
            Maximum number of threads an individual process may use
        synb0_dir: str
            Directory in which synb0 derivatives are saved

    """
    # for documentation purposes
    if name in ('single_subject_wf', 'single_subject_dmripreptest_wf'):
        subject_data = {
            't1w': ['/madeup/path/sub-01_T1w.nii.gz'],
            'dwi': ['/madeup/path/sub-01_dwi.nii.gz']
        }
    else:
        subject_data = collect_data(layout, subject_id, session_list)

    if subject_data['dwi'] == []:
        raise Exception(
            'No dwi images found for participant {} in session {}. '
            'All workflows require dwi images'.format(
                subject_id, session_list if session_list else '<all>')
        )

    subject_wf = pe.Workflow(name=name)

    for dwi_file in dwi_files:
        entities = layout.parse_file_entities(dwi_file)
        if 'session' in entities:
            session_id = entities['session']
        else:
            session_id = None
        metadata = layout.get_metadata(dwi_file)
        dwi_preproc_wf = init_dwi_preproc_wf(
            subject_id=subject_id,
            dwi_file=dwi_file,
            metadata=metadata,
            layout=layout,
            output_dir=output_dir,
            work_dir=work_dir,
            ignore=ignore,
            b0_thresh=b0_thresh,
            output_resolution=output_resolution,
            bet_dwi=bet_dwi,
            bet_mag=bet_mag,
            omp_nthreads=omp_nthreads,
            synb0_dir=synb0_dir
        )
        datasink_wf = init_dwi_derivatives_wf(
            subject_id=subject_id,
            session_id=session_id,
            output_folder=output_dir
        )

        dwi_preproc_wf.base_dir = os.path.join(
            os.path.abspath(work_dir), subject_id
        )

        inputspec = dwi_preproc_wf.get_node('inputnode')
        inputspec.inputs.subject_id = subject_id
        inputspec.inputs.dwi_file = dwi_file
        inputspec.inputs.dwi_meta = metadata
        inputspec.inputs.bvec_file = layout.get_bvec(dwi_file)
        inputspec.inputs.bval_file = layout.get_bval(dwi_file)
        inputspec.inputs.out_dir = os.path.abspath(output_dir)

        ds_inputspec = datasink_wf.get_node('inputnode')
        ds_inputspec.inputs.subject_id = subject_id
        ds_inputspec.inputs.session_id = session_id
        ds_inputspec.inputs.output_folder = output_dir
        ds_inputspec.inputs.metadata = metadata

        if session_id:
            wf_name = 'sub_' + subject_id + '_ses_' + session_id + '_preproc_wf'
        else:
            wf_name = 'sub_' + subject_id + '_preproc_wf'
        full_wf = pe.Workflow(name=wf_name)

        full_wf.connect(
            [
                (
                    dwi_preproc_wf,
                    datasink_wf,
                    [
                        ('outputnode.out_dwi', 'inputnode.dwi'),
                        ('outputnode.out_bval', 'inputnode.bval'),
                        ('outputnode.out_bvec', 'inputnode.bvec'),
                        ('outputnode.index', 'inputnode.index'),
                        ('outputnode.acq_params', 'inputnode.acq_params'),
                        ('outputnode.out_mask', 'inputnode.mask'),
                        ('outputnode.out_b0_pre', 'inputnode.b0'),
                        ('outputnode.out_b0_mask_pre', 'inputnode.b0_mask'),
                        ('outputnode.out_eddy_quad_json', 'inputnode.eddy_quad_json'),
                        ('outputnode.out_eddy_quad_pdf', 'inputnode.eddy_quad_pdf'),
                        ('outputnode.out_dtifit_FA', 'inputnode.dtifit_FA'),
                        ('outputnode.out_dtifit_V1', 'inputnode.dtifit_V1'),
                        ('outputnode.out_dtifit_sse', 'inputnode.dtifit_sse'),
                        ('outputnode.out_noise', 'inputnode.noise')
                    ]
                )
            ]
        )

        subject_wf.add_nodes([full_wf])

    return subject_wf


def group_dwis(dwi_files, sessions, concat_dwis):

    all_dwis = []

    if sessions:
        session_dwi_groups = []
        for session in sessions:
            session_dwi_files = [img for img in dwi_files if 'ses-{}'.format(session) in img]
            for f in session_dwi_files:
                if any(acq in f for acq in concat_dwis):
                    session_dwi_groups.append(f)
                else:
                    all_dwis.append(f)
        all_dwis.append(session_dwi_groups)
    else:
        all_dwis.append(f)

    return all_dwis
