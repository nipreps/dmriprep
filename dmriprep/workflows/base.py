# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
dMRIPrep base processing workflows.

.. autofunction:: init_dmriprep_wf
.. autofunction:: init_single_subject_wf

"""

import sys
import os
from collections import OrderedDict
from copy import deepcopy

from nipype import __version__ as nipype_ver
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nilearn import __version__ as nilearn_ver

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.bids import (
    BIDSInfo, BIDSFreeSurferDir
)
from niworkflows.utils.misc import fix_multi_T1w_source_name
from smriprep.workflows.anatomical import init_anat_preproc_wf

from ..interfaces import DerivativesDataSink, BIDSDataGrabber
from ..interfaces.reports import SubjectSummary, AboutSummary
from ..utils.bids import collect_data
from ..__about__ import __version__
# from .dwi import init_dwi_preproc_wf


def init_dmriprep_wf(
    anat_only,
    debug,
    force_syn,
    freesurfer,
    hires,
    ignore,
    layout,
    longitudinal,
    low_mem,
    omp_nthreads,
    output_dir,
    output_spaces,
    run_uuid,
    skull_strip_fixed_seed,
    skull_strip_template,
    subject_list,
    use_syn,
    work_dir,
):
    """
    Create the base workflow.

    This workflow organizes the execution of *dMRIPrep*, with a sub-workflow for
    each subject. If FreeSurfer's recon-all is to be run, a FreeSurfer derivatives folder is
    created and populated with any needed template subjects.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        import os
        from collections import namedtuple, OrderedDict
        BIDSLayout = namedtuple('BIDSLayout', ['root'])
        from dmriprep.workflows.base import init_dmriprep_wf
        os.environ['FREESURFER_HOME'] = os.getcwd()
        wf = init_dmriprep_wf(
            anat_only=False,
            debug=False,
            force_syn=True,
            freesurfer=True,
            hires=True,
            ignore=[],
            layout=BIDSLayout('.'),
            longitudinal=False,
            low_mem=False,
            omp_nthreads=1,
            output_dir='.',
            output_spaces=OrderedDict([
                ('MNI152Lin', {}), ('fsaverage', {'density': '10k'}),
                ('T1w', {}), ('fsnative', {})]),
            run_uuid='X',
            skull_strip_fixed_seed=False,
            skull_strip_template=('OASIS30ANTs', {}),
            subject_list=['dmripreptest'],
            use_syn=True,
            work_dir='.',
        )


    Parameters
    ----------
        anat_only : bool
            Disable diffusion MRI workflows
        debug : bool
            Enable debugging outputs
        force_syn : bool
            **Temporary**: Always run SyN-based SDC
        freesurfer : bool
            Enable FreeSurfer surface reconstruction (may increase runtime)
        hires : bool
            Enable sub-millimeter preprocessing in FreeSurfer
        ignore : list
            Preprocessing steps to skip (may include "slicetiming", "fieldmaps")
        layout : BIDSLayout object
            BIDS dataset layout
        longitudinal : bool
            Treat multiple sessions as longitudinal (may increase runtime)
            See sub-workflows for specific differences
        low_mem : bool
            Write uncompressed .nii files in some cases to reduce memory usage
        omp_nthreads : int
            Maximum number of threads an individual process may use
        output_dir : str
            Directory in which to save derivatives
        output_spaces : OrderedDict
            Ordered dictionary where keys are TemplateFlow ID strings (e.g., ``MNI152Lin``,
            ``MNI152NLin6Asym``, ``MNI152NLin2009cAsym``, or ``fsLR``) strings designating
            nonstandard references (e.g., ``T1w`` or ``anat``, ``sbref``, ``run``, etc.),
            or paths pointing to custom templates organized in a TemplateFlow-like structure.
            Values of the dictionary aggregate modifiers (e.g., the value for the key ``MNI152Lin``
            could be ``{'resolution': 2}`` if one wants the resampling to be done on the 2mm
            resolution version of the selected template).
        run_uuid : str
            Unique identifier for execution instance
        skull_strip_template : tuple
            Name of target template for brain extraction with ANTs' ``antsBrainExtraction``,
            and corresponding dictionary of output-space modifiers.
        skull_strip_fixed_seed : bool
            Do not use a random seed for skull-stripping - will ensure
            run-to-run replicability when used with --omp-nthreads 1
        subject_list : list
            List of subject labels
        use_syn : bool
            **Experimental**: Enable ANTs SyN-based susceptibility distortion correction (SDC).
            If fieldmaps are present and enabled, this is not run, by default.
        work_dir : str
            Directory in which to store workflow execution state and temporary files

    """
    dmriprep_wf = Workflow(name='dmriprep_wf')
    dmriprep_wf.base_dir = work_dir

    if freesurfer:
        fsdir = pe.Node(
            BIDSFreeSurferDir(
                derivatives=output_dir,
                freesurfer_home=os.getenv('FREESURFER_HOME'),
                spaces=[s for s in output_spaces.keys() if s.startswith('fsaverage')] + [
                    'fsnative'] * ('fsnative' in output_spaces)),
            name='fsdir_run_' + run_uuid.replace('-', '_'), run_without_submitting=True)

    reportlets_dir = os.path.join(work_dir, 'reportlets')
    for subject_id in subject_list:
        single_subject_wf = init_single_subject_wf(
            anat_only=anat_only,
            debug=debug,
            force_syn=force_syn,
            freesurfer=freesurfer,
            hires=hires,
            ignore=ignore,
            layout=layout,
            longitudinal=longitudinal,
            low_mem=low_mem,
            name="single_subject_" + subject_id + "_wf",
            omp_nthreads=omp_nthreads,
            output_dir=output_dir,
            output_spaces=output_spaces,
            reportlets_dir=reportlets_dir,
            skull_strip_fixed_seed=skull_strip_fixed_seed,
            skull_strip_template=skull_strip_template,
            subject_id=subject_id,
            use_syn=use_syn,
        )

        single_subject_wf.config['execution']['crashdump_dir'] = (
            os.path.join(output_dir, "dmriprep", "sub-" + subject_id, 'log', run_uuid)
        )
        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)
        if freesurfer:
            dmriprep_wf.connect(fsdir, 'subjects_dir',
                                single_subject_wf, 'inputnode.subjects_dir')
        else:
            dmriprep_wf.add_nodes([single_subject_wf])

    return dmriprep_wf


def init_single_subject_wf(
    anat_only,
    debug,
    force_syn,
    freesurfer,
    hires,
    ignore,
    layout,
    longitudinal,
    low_mem,
    name,
    omp_nthreads,
    output_dir,
    output_spaces,
    reportlets_dir,
    skull_strip_fixed_seed,
    skull_strip_template,
    subject_id,
    use_syn,
):
    """
    Set-up the preprocessing pipeline for a single subject.

    It collects and reports information about the subject, and prepares
    sub-workflows to perform anatomical and diffusion MRI preprocessing.

    Anatomical preprocessing is performed in a single workflow, regardless of
    the number of sessions.
    Functional preprocessing is performed using a separate workflow for each
    individual BOLD series.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.base import init_single_subject_wf
        from collections import namedtuple, OrderedDict
        BIDSLayout = namedtuple('BIDSLayout', ['root'])
        wf = init_single_subject_wf(
            anat_only=False,
            debug=False,
            force_syn=True,
            freesurfer=True,
            hires=True,
            ignore=[],
            layout=BIDSLayout('.'),
            longitudinal=False,
            low_mem=False,
            name='single_subject_wf',
            omp_nthreads=1,
            output_dir='.',
            output_spaces=OrderedDict([
                ('MNI152Lin', {}), ('fsaverage', {'density': '10k'}),
                ('T1w', {}), ('fsnative', {})]),
            reportlets_dir='.',
            skull_strip_fixed_seed=False,
            skull_strip_template=('OASIS30ANTs', {}),
            subject_id='test',
            use_syn=True,
        )


    Parameters
    ----------
        anat_only : bool
            Disable diffusion MRI workflows
        debug : bool
            Enable debugging outputs
        force_syn : bool
            **Temporary**: Always run SyN-based SDC
        freesurfer : bool
            Enable FreeSurfer surface reconstruction (may increase runtime)
        hires : bool
            Enable sub-millimeter preprocessing in FreeSurfer
        ignore : list
            Preprocessing steps to skip (may include "slicetiming", "fieldmaps")
        layout : BIDSLayout object
            BIDS dataset layout
        longitudinal : bool
            Treat multiple sessions as longitudinal (may increase runtime)
            See sub-workflows for specific differences
        low_mem : bool
            Write uncompressed .nii files in some cases to reduce memory usage
        name : str
            Name of workflow
        omp_nthreads : int
            Maximum number of threads an individual process may use
        output_dir : str
            Directory in which to save derivatives
        output_spaces : OrderedDict
            Ordered dictionary where keys are TemplateFlow ID strings (e.g., ``MNI152Lin``,
            ``MNI152NLin6Asym``, ``MNI152NLin2009cAsym``, or ``fsLR``) strings designating
            nonstandard references (e.g., ``T1w`` or ``anat``, ``sbref``, ``run``, etc.),
            or paths pointing to custom templates organized in a TemplateFlow-like structure.
            Values of the dictionary aggregate modifiers (e.g., the value for the key ``MNI152Lin``
            could be ``{'resolution': 2}`` if one wants the resampling to be done on the 2mm
            resolution version of the selected template).
        reportlets_dir : str
            Directory in which to save reportlets
        skull_strip_fixed_seed : bool
            Do not use a random seed for skull-stripping - will ensure
            run-to-run replicability when used with --omp-nthreads 1
        skull_strip_template : tuple
            Name of target template for brain extraction with ANTs' ``antsBrainExtraction``,
            and corresponding dictionary of output-space modifiers.
        subject_id : str
            List of subject labels
        use_syn : bool
            **Experimental**: Enable ANTs SyN-based susceptibility distortion correction (SDC).
            If fieldmaps are present and enabled, this is not run, by default.


    Inputs

        subjects_dir
            FreeSurfer SUBJECTS_DIR

    """
    from ..config import NONSTANDARD_REFERENCES
    if name in ('single_subject_wf', 'single_subject_dmripreptest_wf'):
        # for documentation purposes
        subject_data = {
            't1w': ['/completely/made/up/path/sub-01_T1w.nii.gz'],
            'dwi': ['/completely/made/up/path/sub-01_task-nback_bold.nii.gz']
        }
    else:
        subject_data = collect_data(layout, subject_id)[0]

    # Make sure we always go through these two checks
    if not anat_only and subject_data['dwi'] == []:
        raise Exception("No DWI data found for participant {}. "
                        "All workflows require DWI images.".format(subject_id))

    if not subject_data['t1w']:
        raise Exception("No T1w images found for participant {}. "
                        "All workflows require T1w images.".format(subject_id))

    workflow = Workflow(name=name)
    workflow.__desc__ = """
Results included in this manuscript come from preprocessing
performed using *dMRIPrep* {dmriprep_ver}
(@dmriprep; RRID:SCR_017412),
which is based on *Nipype* {nipype_ver}
(@nipype1; @nipype2; RRID:SCR_002502).

""".format(dmriprep_ver=__version__, nipype_ver=nipype_ver)
    workflow.__postdesc__ = """

Many internal operations of *dMRIPrep* use
*Nilearn* {nilearn_ver} [@nilearn, RRID:SCR_001362],
mostly within the diffusion MRI processing workflow.
For more details of the pipeline, see [the section corresponding
to workflows in *dMRIPrep*'s documentation]\
(https://dmriprep.readthedocs.io/en/latest/workflows.html \
"dMRIPrep's documentation").


### Copyright Waiver

The above boilerplate text was automatically generated by dMRIPrep
with the express intention that users should copy and paste this
text into their manuscripts *unchanged*.
It is released under the [CC0]\
(https://creativecommons.org/publicdomain/zero/1.0/) license.

### References

""".format(nilearn_ver=nilearn_ver)

    # Filter out standard spaces to a separate dict
    std_spaces = OrderedDict([
        (key, modifiers) for key, modifiers in output_spaces.items()
        if key not in NONSTANDARD_REFERENCES])

    inputnode = pe.Node(niu.IdentityInterface(fields=['subjects_dir']),
                        name='inputnode')

    bidssrc = pe.Node(BIDSDataGrabber(subject_data=subject_data, anat_only=anat_only),
                      name='bidssrc')

    bids_info = pe.Node(BIDSInfo(
        bids_dir=layout.root, bids_validate=False), name='bids_info')

    summary = pe.Node(SubjectSummary(
        std_spaces=list(std_spaces.keys()),
        nstd_spaces=list(set(NONSTANDARD_REFERENCES).intersection(output_spaces.keys()))),
        name='summary', run_without_submitting=True)

    about = pe.Node(AboutSummary(version=__version__,
                                 command=' '.join(sys.argv)),
                    name='about', run_without_submitting=True)

    ds_report_summary = pe.Node(
        DerivativesDataSink(base_directory=reportlets_dir,
                            desc='summary', keep_dtype=True),
        name='ds_report_summary', run_without_submitting=True)

    ds_report_about = pe.Node(
        DerivativesDataSink(base_directory=reportlets_dir,
                            desc='about', keep_dtype=True),
        name='ds_report_about', run_without_submitting=True)

    # Preprocessing of T1w (includes registration to MNI)
    anat_preproc_wf = init_anat_preproc_wf(
        bids_root=layout.root,
        debug=debug,
        freesurfer=freesurfer,
        hires=hires,
        longitudinal=longitudinal,
        name="anat_preproc_wf",
        num_t1w=len(subject_data['t1w']),
        omp_nthreads=omp_nthreads,
        output_dir=output_dir,
        output_spaces=std_spaces,
        reportlets_dir=reportlets_dir,
        skull_strip_fixed_seed=skull_strip_fixed_seed,
        skull_strip_template=skull_strip_template,
    )

    workflow.connect([
        (inputnode, anat_preproc_wf, [('subjects_dir', 'inputnode.subjects_dir')]),
        (bidssrc, bids_info, [(('t1w', fix_multi_T1w_source_name), 'in_file')]),
        (inputnode, summary, [('subjects_dir', 'subjects_dir')]),
        (bidssrc, summary, [('t1w', 't1w'),
                            ('t2w', 't2w'),
                            ('dwi', 'dwi')]),
        (bids_info, summary, [('subject', 'subject_id')]),
        (bids_info, anat_preproc_wf, [(('subject', _prefix), 'inputnode.subject_id')]),
        (bidssrc, anat_preproc_wf, [('t1w', 'inputnode.t1w'),
                                    ('t2w', 'inputnode.t2w'),
                                    ('roi', 'inputnode.roi'),
                                    ('flair', 'inputnode.flair')]),
        (bidssrc, ds_report_summary, [(('t1w', fix_multi_T1w_source_name), 'source_file')]),
        (summary, ds_report_summary, [('out_report', 'in_file')]),
        (bidssrc, ds_report_about, [(('t1w', fix_multi_T1w_source_name), 'source_file')]),
        (about, ds_report_about, [('out_report', 'in_file')]),
    ])

    # Overwrite ``out_path_base`` of smriprep's DataSinks
    for node in workflow.list_node_names():
        if node.split('.')[-1].startswith('ds_'):
            workflow.get_node(node).interface.out_path_base = 'dmriprep'

    if anat_only:
        return workflow

    # for dwi_file in subject_data['dwi']:
    #     dwi_preproc_wf = init_dwi_preproc_wf(
    #         aroma_melodic_dim=aroma_melodic_dim,
    #         bold2t1w_dof=bold2t1w_dof,
    #         bold_file=bold_file,
    #         cifti_output=cifti_output,
    #         debug=debug,
    #         dummy_scans=dummy_scans,
    #         err_on_aroma_warn=err_on_aroma_warn,
    #         fmap_bspline=fmap_bspline,
    #         fmap_demean=fmap_demean,
    #         force_syn=force_syn,
    #         freesurfer=freesurfer,
    #         ignore=ignore,
    #         layout=layout,
    #         low_mem=low_mem,
    #         medial_surface_nan=medial_surface_nan,
    #         num_bold=len(subject_data['bold']),
    #         omp_nthreads=omp_nthreads,
    #         output_dir=output_dir,
    #         output_spaces=output_spaces,
    #         reportlets_dir=reportlets_dir,
    #         regressors_all_comps=regressors_all_comps,
    #         regressors_fd_th=regressors_fd_th,
    #         regressors_dvars_th=regressors_dvars_th,
    #         t2s_coreg=t2s_coreg,
    #         use_aroma=use_aroma,
    #         use_syn=use_syn,
    #     )

    #     workflow.connect([
    #         (anat_preproc_wf, dwi_preproc_wf,
    #          [(('outputnode.t1_preproc', _pop), 'inputnode.t1_preproc'),
    #           ('outputnode.t1_brain', 'inputnode.t1_brain'),
    #           ('outputnode.t1_mask', 'inputnode.t1_mask'),
    #           ('outputnode.t1_seg', 'inputnode.t1_seg'),
    #           ('outputnode.t1_aseg', 'inputnode.t1_aseg'),
    #           ('outputnode.t1_aparc', 'inputnode.t1_aparc'),
    #           ('outputnode.t1_tpms', 'inputnode.t1_tpms'),
    #           ('outputnode.template', 'inputnode.template'),
    #           ('outputnode.forward_transform', 'inputnode.anat2std_xfm'),
    #           ('outputnode.reverse_transform', 'inputnode.std2anat_xfm'),
    #           ('outputnode.joint_template', 'inputnode.joint_template'),
    #           ('outputnode.joint_forward_transform', 'inputnode.joint_anat2std_xfm'),
    #           ('outputnode.joint_reverse_transform', 'inputnode.joint_std2anat_xfm'),
    #           # Undefined if --no-freesurfer, but this is safe
    #           ('outputnode.subjects_dir', 'inputnode.subjects_dir'),
    #           ('outputnode.subject_id', 'inputnode.subject_id'),
    #           ('outputnode.t1_2_fsnative_forward_transform',
    #            'inputnode.t1_2_fsnative_forward_transform'),
    #           ('outputnode.t1_2_fsnative_reverse_transform',
    #            'inputnode.t1_2_fsnative_reverse_transform')]),
    #     ])

    return workflow


def _prefix(subid):
    if subid.startswith('sub-'):
        return subid
    return '-'.join(('sub', subid))


def _pop(inlist):
    if isinstance(inlist, (list, tuple)):
        return inlist[0]
    return inlist
