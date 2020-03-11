from collections import namedtuple
from niworkflows.utils.spaces import Reference, SpatialReferences
from dmriprep.workflows.base import init_single_subject_wf
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
    reportlets_dir='.',
    skull_strip_fixed_seed=False,
    skull_strip_template=Reference('OASIS30ANTs'),
    spaces=SpatialReferences(
        spaces=['MNI152Lin',
                ('fsaverage', {'density': '10k'}),
                'T1w',
                'fsnative'],
        checkpoint=True),
    subject_id='test',
    use_syn=True,
)