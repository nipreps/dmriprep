from dmriprep.workflows.dwi import init_dwi_preproc_wf
from collections import namedtuple
BIDSLayout = namedtuple('BIDSLayout', ['root'])
wf = init_dwi_preproc_wf(
    dwi_file='/completely/made/up/path/sub-01_dwi.nii.gz',
    debug=False,
    force_syn=True,
    ignore=[],
    low_mem=False,
    omp_nthreads=1,
    output_dir='.',
    reportlets_dir='.',
    use_syn=True,
    layout=BIDSLayout('.'),
    num_dwi=1,
)