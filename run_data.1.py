from run_1 import *
import os
output = run_preAFQ(os.path.abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.nii.gz"), 
           os.path.abspath("./sub-NDARBA507GCT/fmap/sub-NDARBA507GCT_dir-AP_acq-dwi_epi.nii.gz"), 
           os.path.abspath("./sub-NDARBA507GCT/fmap/sub-NDARBA507GCT_dir-PA_acq-dwi_epi.nii.gz"),
           os.path.abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.bvec"), 
           os.path.abspath("./sub-NDARBA507GCT/dwi/sub-NDARBA507GCT_acq-64dir_dwi.bval"), 
           os.path.abspath("./derivatives/sub-NDARBA507GCT"), 
           os.path.abspath("./scratch1"),
           os.path.abspath("./derivatives"))
print(output)