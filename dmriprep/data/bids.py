"""
This module contains the BIDS specification.
"""
#: Defalut BIDS patterns.
DEFAULT_PATTERNS = [
    "sub-{subject}[/ses-{session}]/{datatype<dwi>|dwi}/sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_res-{resolution}][_desc-{desc}][_part-{part}]_{suffix<dwi|dwiref|epiref|mask>}{extension<.bval|.bvec|.json|.nii.gz|.nii>|.nii.gz}",
    "sub-{subject}[/ses-{session}]/{datatype<anat>|anat}/sub-{subject}[_ses-{session}][_acq-{acquisition}][_ce-{ceagent}][_rec-{reconstruction}][_space-{space}][_res-{resolution}][_part-{part}]_{suffix<T1w|T2w|T1rho|T1map|T2map|T2star|FLAIR|FLASH|PDmap|PD|PDT2|inplaneT[12]|angio>}{extension<.nii|.nii.gz|.json>|.nii.gz}",
]

#: Opposite phase polarities
AVAILABLE_POLARITIES = {"FWD": "REV", "AP": "PA", "RL": "LR"}
PHASE_POLARS = AVAILABLE_POLARITIES.copy()
for key, val in AVAILABLE_POLARITIES.items():
    PHASE_POLARS[val] = key
