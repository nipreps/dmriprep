from os.path import abspath

from dmriprep.run_1 import run_dmriprep

output = run_dmriprep(
    abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.nii.gz"),
    abspath("./sub-NDARBA507GCT/fmap/"
            "sub-NDARBA507GCT_dir-AP_acq-dwi_epi.nii.gz"),
    abspath("./sub-NDARBA507GCT/fmap/"
            "sub-NDARBA507GCT_dir-PA_acq-dwi_epi.nii.gz"),
    abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.bvec"),
    abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.bval"),
    abspath("./derivatives/sub-NDARBA507GCT"),
    abspath("./scratch2"),
    abspath("./derivatives")
)

print(output)
