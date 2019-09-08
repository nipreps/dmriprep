Processing pipeline details
===========================

dMRIprep adapts its pipeline depending on what data and metadata are available
and are used as the input.

A (very) high-level view of the simplest pipeline is presented below.

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from collections import namedtuple, OrderedDict
    from dmriprep.workflows.base import init_single_subject_wf
    BIDSLayout = namedtuple('BIDSLayout', ['root'])
    wf = init_single_subject_wf(subject_id='test', session_list=[], name='single_subject_wf', layout=BIDSLayout, output_dir='.', work_dir='.', ignore=['fieldmaps'], b0_thresh=5, output_resolution=(1, 1, 1), bet_dwi=0.3, bet_mag=0.3, omp_nthreads=1, synb0_dir='')

T1w preprocessing
-----------------
:mod:`dmriprep.workflows.anatomical.init_anat_preproc_wf`

The T1w preprocessing workflow skull strips the T1w scan for later use in
tractography or susceptibility distortion correction if using ANTs or
BrainSuite. It uses ``init_brain_extraction_wf`` from
`niworkflows <https://github.com/poldracklab/niworkflows/blob/d5904a15201f99ce58a00774d1bfcdd9ea661371/niworkflows/anat/ants.py#L58>`_.

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from niworkflows.anat.ants import init_brain_extraction_wf
    wf = init_brain_extraction_wf()

DWI preprocessing
-----------------
:mod:`dmriprep.workflows.dwi.base.init_dwi_preproc_wf`

Preprocessing of DWI files is split into multiple sub-workflows described below.

.. workflow::
    :graph2use: orig
    :simple_form: yes

    from collections import namedtuple
    from dmriprep.workflows.dwi import init_dwi_preproc_wf
    BIDSLayout = namedtuple('BIDSLayout', ['root'])
    wf = init_dwi_preproc_wf(layout=BIDSLayout('.'), subject_id='dmripreptest', dwi_file='/madeup/path/sub-01_dwi.nii.gz', metadata={'PhaseEncodingDirection': 'j-', 'TotalReadoutTime': 0.05}, b0_thresh=5, output_resolution=(1, 1, 1), bet_dwi=0.3, bet_mag=0.3, omp_nthreads=1, ignore=['fieldmaps'], synb0_dir='')

Concatenating Scans
^^^^^^^^^^^^^^^^^^^
:mod:`dmriprep.workflows.dwi.util.init_dwi_concat_wf`

By default, each scan in the ``dwi`` folder will get preprocessed separately.
However, there are some cases where multiple scans should be concatenated before
head motion, eddy current distortion and susceptibility distortion correction
(eg. single-shell or multi-shell scan acquired in separate runs).

.. code-block:: console

    bids
    └── sub-01
      └── dwi
          ├── sub-01_acq-multishelldir30b1000_dwi.nii.gz
          ├── sub-01_acq-multishelldir30b3000_dwi.nii.gz
          ├── sub-01_acq-multishelldir30b4500_dwi.nii.gz
          └── sub-01_acq-singleshelldir60b1000_dwi.nii.gz

In the above example, the multi-shell scans should be concatenated and the
single-shell scan should be left alone. This is done by using the
``--concat_dwis`` flag as shown below:

``--concat_dwis multishelldir30b1000 multishelldir30b3000 multishelldir30b4500``

The unique ``acq`` entities are passed on so this pipeline knows which scans to
concatenate. The associated bvecs and bvals are also concatenated.

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.dwi import init_dwi_concat_wf
    wf = init_dwi_concat_wf(ref_file='/madeup/path/sub-01_dwi.nii.gz')

Artifact Removal
^^^^^^^^^^^^^^^^
:mod:`dmriprep.workflows.dwi.artifacts.init_dwi_artifacts_wf`

By default, dMRIPrep performs denoising and unringing on each dwi scan. These
steps can be skipped by passing ``--ignore denoising unringing`` in the command line.

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.dwi import init_dwi_artifacts_wf
    wf = init_dwi_artifacts_wf(ignore=[], output_resolution=(1, 1, 1))

Motion and Susceptibility Correction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:mod:`dmriprep.workflows.dwi.eddy.init_dwi_eddy_wf`

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.dwi import init_dwi_eddy_wf
    wf = init_dwi_eddy_wf(1, 'topup')

Tensor Estimates
^^^^^^^^^^^^^^^^
:mod:`dmriprep.workflows.dwi.tensor.init_dwi_tensor_wf`

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.dwi import init_dwi_tensor_wf
    wf = init_dwi_tensor_wf()

Susceptibility Distortion Correction (SDC)
------------------------------------------

Introduction
^^^^^^^^^^^^

Correction Methods
^^^^^^^^^^^^^^^^^^

1. topup
2. fieldmap
3. phasediff
4. phase1/phase2
5. nonlinear registration
6. synthetic b0

Topup
~~~~~
:mod:`dmriprep.workflows.fieldmap.pepolar.init_pepolar_wf`

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.fieldmap import init_pepolar_wf
    wf = init_pepolar_wf('dmripreptest', 0.3, ['/madeup/path/sub-01_dir-AP_epi.nii.gz', '/madeup/path/sub-01_dir-PA_epi.nii.gz'])

Fieldmap
~~~~~~~~
:mod:`dmriprep.workflows.fieldmap.fmap.init_fmap_wf`

All of the fieldmap-related workflows end with ``init_fmap_wf``. Depending on
the type of fieldmap, other upstream workflows are run. If a phasediff scan is
given, the phasediff is converted to a proper fieldmap using ``fsl_prepare_fieldmap``.
If phase1 and phase2 scans are given, they are first converted to a phasediff scan.
The code for this conversion was derived from `sdcflows <https://github.com/poldracklab/sdcflows/pull/30`_
and tested on the PNC dataset.

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.fieldmap import init_fmap_wf
    wf = init_fmap_wf(0.3)

Phasediff
~~~~~~~~~
:mod:`dmriprep.workflows.fieldmap.phasediff.init_phdiff_wf`

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.fieldmap import init_phdiff_wf
    wf = init_phdiff_wf(0.3)

Phase1/Phase2
~~~~~~~~~~~~~
:mod:`dmriprep.workflows.fieldmap.phasediff.init_phase_wf`

.. workflow::
    :graph2use: flat
    :simple_form: no

    from dmriprep.workflows.fieldmap import init_phase_wf
    wf = init_phase_wf(0.3)

Synthetic b0
~~~~~~~~~~~~
The synb0 method is based off of this `paper <https://www.sciencedirect.com/science/article/abs/pii/S0730725X18306179/>`_. It offers an alternative method of SDC by using deep learning on an anatomical image (T1).
You can use it in this pipeline by generating the synb0s for the subject(s) and
passing the bids-like directory containing them to the --synb0_dir parameter.
To find out how to generate the synb0s, you can visit our
`forked repo <https://github.com/TIGRLab/Synb0-DISCO>`_.
Once you have a directory of synb0s (recommended to place as derivatives of
bids folder, ex. bids/derivatives/synb0/sub-XX), then you are ready to run the
pipeline using them! Just run dmriprep as you usually would, with ``bids_dir``
and ``output_dir``, but now add ``--synb0_dir <your_synb0_directory>`` to your command.
The synb0 acquisition parameters for topup and eddy will be automatically generated in the
pipeline in the following format:

.. code-block:: console

    0 -1 0 <total_readout_time>
    0 1 0 0

If you want to overwrite the total_readout_time with one of your own,
simply add ``--total_readout <new_trt_time>`` to your command.
