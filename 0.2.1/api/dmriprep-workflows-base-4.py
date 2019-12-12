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