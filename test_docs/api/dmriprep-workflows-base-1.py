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