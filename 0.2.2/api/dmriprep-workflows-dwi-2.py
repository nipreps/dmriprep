from dmriprep.workflows.dwi.util import init_dwi_reference_wf
wf = init_dwi_reference_wf(omp_nthreads=1)
wf.inputs.inputnode.b0_ixs=[0]