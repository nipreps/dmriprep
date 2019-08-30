Processing pipeline details
===========================

dMRIprep adapts its pipeline depending on what data and metadata are available and are used as the input.

A (very) high-level view of the simplest pipeline is presented below.

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from collections import namedtuple, OrderedDict
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

T1w preprocessing
-----------------
:mod:`dmriprep.workflows.anatomical.init_anat_preproc_wf`

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from collections import OrderedDict
    from dmriprep.workflows.anatomical import init_anat_preproc_wf
    wf = init_anat_preproc_wf()

DWI preprocessing
-----------------
:mod:`dmriprep.workflows.dwi.base.init_dwi_preproc_wf`

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from collections import namedtuple
    from dmriprep.workflows.dwi import init_dwi_preproc_wf
    BIDSLayout = namedtuple('BIDSLayout', ['root'])
    wf = init_dwi_preproc_wf(
        subjectid='dmripreptest',
        dwi_file='/madeup/path/sub-01_dwi.nii.gz',
        metadata={},
        layout=BIDSLayout('.'),
        ignore=[],
        b0_thresh=5,
        output_resolution=(1, 1, 1),
        bet_dwi=0.3,
        bet_mag=0.3,
        nthreads=4,
        omp_nthreads=1,
        synb0_dir='.'
    )

Preprocessing of DWI files is split into multiple sub-workflows described below.
