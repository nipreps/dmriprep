"""
Configurations for *preprocessing* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["dwi_file", "merged_phasediff"]
OUTPUT_NODE_FIELDS = ["dwi_preproc"]

#: Keyword arguments
DWIDENOISE_KWARGS = dict()
INFER_PE_KWARGS = dict(input_names=["in_file"], output_names=["pe_dir"])
DWIFSLPREPROC_KWARGS = dict(
    rpe_options="pair",
    align_seepi=True,
    eddy_options=" --slm=linear",
)
BIASCORRECT_KWARGS = dict(use_ants=True)
