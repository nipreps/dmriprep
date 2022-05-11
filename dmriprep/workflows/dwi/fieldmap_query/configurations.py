"""
Configurations for the "fieldmap_query" workflow.
"""
AVAILABLE_POLARITIES = {"FWD": "REV", "AP": "PA", "RL": "LR"}
PHASE_POLARS = AVAILABLE_POLARITIES.copy()
for key, val in AVAILABLE_POLARITIES.items():
    PHASE_POLARS[val] = key

INPUTNODE_FIELDS = ["dwi_file"]
