import os
from collections import namedtuple, OrderedDict
BIDSLayout = namedtuple('BIDSLayout', ['root'])
from dmriprep.workflows.base import init_dmriprep_wf
from niworkflows.utils.spaces import Reference, SpatialReferences
os.environ['FREESURFER_HOME'] = os.getcwd()
wf = init_dmriprep_wf(
    anat_only=False,
    debug=False,
    force_syn=True,
    freesurfer=True,
    fs_subjects_dir=None,
    hires=True,
    ignore=[],
    layout=BIDSLayout('.'),
    longitudinal=False,
    low_mem=False,
    omp_nthreads=1,
    output_dir='.',
    run_uuid='X',
    skull_strip_fixed_seed=False,
    skull_strip_template=Reference('OASIS30ANTs'),
    spaces=SpatialReferences(
        spaces=['MNI152Lin',
                ('fsaverage', {'density': '10k'}),
                'T1w',
                'fsnative'],
        checkpoint=True),
    subject_list=['dmripreptest'],
    use_syn=True,
    work_dir='.',
)