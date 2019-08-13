"""
Utilities to handle BIDS inputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""

import warnings
import json
import sys

from bids.layout import BIDSLayout


class BIDSError(ValueError):
    def __init__(self, message, bids_root):
        indent = 10
        header = '{sep} BIDS root folder: "{bids_root}" {sep}'.format(
            bids_root=bids_root, sep="".join(["-"] * indent)
        )
        self.msg = "\n{header}\n{indent}{message}\n{footer}".format(
            header=header,
            indent="".join([" "] * (indent + 1)),
            message=message,
            footer="".join(["-"] * len(header)),
        )
        super(BIDSError, self).__init__(self.msg)
        self.bids_root = bids_root


class BIDSWarning(RuntimeWarning):
    pass


def collect_participants(
    bids_dir, participant_label=None, strict=False, bids_validate=True
):
    """
    List the participants under the BIDS root and checks that participants
    designated with the participant_label argument exist in that folder.
    Returns the list of participants to be finally processed.
    Requesting all subjects in a BIDS directory root:
    >>> collect_participants(str(datadir / 'ds114'), bids_validate=False)
    ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
    Requesting two subjects, given their IDs:
    >>> collect_participants(str(datadir / 'ds114'), participant_label=['02', '04'],
    ...                      bids_validate=False)
    ['02', '04']
    Requesting two subjects, given their IDs (works with 'sub-' prefixes):
    >>> collect_participants(str(datadir / 'ds114'), participant_label=['sub-02', 'sub-04'],
    ...                      bids_validate=False)
    ['02', '04']
    Requesting two subjects, but one does not exist:
    >>> collect_participants(str(datadir / 'ds114'), participant_label=['02', '14'],
    ...                      bids_validate=False)
    ['02']
    >>> collect_participants(
    ...     str(datadir / 'ds114'), participant_label=['02', '14'],
    ...     strict=True, bids_validate=False)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    dmriprep.utils.bids.BIDSError:
    ...
    """

    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), validate=bids_validate)

    all_participants = set(layout.get_subjects())

    # Error: bids_dir does not contain subjects
    if not all_participants:
        raise BIDSError(
            "Could not find participants. Please make sure the BIDS data "
            "structure is present and correct. Datasets can be validated online "
            "using the BIDS Validator (http://bids-standard.github.io/bids-validator/).\n"
            "If you are using Docker for Mac or Docker for Windows, you "
            'may need to adjust your "File sharing" preferences.',
            bids_dir,
        )

    # No --participant-label was set, return all
    if not participant_label:
        return sorted(all_participants)

    if isinstance(participant_label, str):
        participant_label = [participant_label]

    # Drop sub- prefixes
    participant_label = [
        sub[4:] if sub.startswith("sub-") else sub for sub in participant_label
    ]
    # Remove duplicates
    participant_label = sorted(set(participant_label))

    # Remove labels not found
    found_label = sorted(set(participant_label) & all_participants)
    if not found_label:
        raise BIDSError(
            "Could not find participants [{}]".format(", ".join(participant_label)),
            bids_dir,
        )

    # Warn if some IDs were not found
    notfound_label = sorted(set(participant_label) - all_participants)
    if notfound_label:
        exc = BIDSError(
            "Some participants were not found: {}".format(", ".join(notfound_label)),
            bids_dir,
        )
        if strict:
            raise exc
        warnings.warn(exc.msg, BIDSWarning)

    return all_participants, found_label


def validate_input_dir(bids_dir, all_subjects, subject_list):
    # Ignore issues and warnings that should not influence DMRIPREP
    import tempfile
    import subprocess

    validator_config_dict = {
        "ignore": [
            "EVENTS_COLUMN_ONSET",
            "EVENTS_COLUMN_DURATION",
            "TSV_EQUAL_ROWS",
            "TSV_EMPTY_CELL",
            "TSV_IMPROPER_NA",
            "INCONSISTENT_SUBJECTS",
            "INCONSISTENT_PARAMETERS",
            "PARTICIPANT_ID_COLUMN",
            "PARTICIPANT_ID_MISMATCH",
            "TASK_NAME_MUST_DEFINE",
            "PHENOTYPE_SUBJECTS_MISSING",
            "STIMULUS_FILE_MISSING",
            "BOLD_NOT_4D",
            "EVENTS_TSV_MISSING",
            "ACQTIME_FMT",
            "Participants age 89 or higher",
            "DATASET_DESCRIPTION_JSON_MISSING",
            "TASK_NAME_CONTAIN_ILLEGAL_CHARACTER",
            "FILENAME_COLUMN",
            "WRONG_NEW_LINE",
            "MISSING_TSV_COLUMN_CHANNELS",
            "MISSING_TSV_COLUMN_IEEG_CHANNELS",
            "MISSING_TSV_COLUMN_IEEG_ELECTRODES",
            "UNUSED_STIMULUS",
            "CHANNELS_COLUMN_SFREQ",
            "CHANNELS_COLUMN_LOWCUT",
            "CHANNELS_COLUMN_HIGHCUT",
            "CHANNELS_COLUMN_NOTCH",
            "CUSTOM_COLUMN_WITHOUT_DESCRIPTION",
            "ACQTIME_FMT",
            "SUSPICIOUSLY_LONG_EVENT_DESIGN",
            "SUSPICIOUSLY_SHORT_EVENT_DESIGN",
            "MISSING_TSV_COLUMN_EEG_ELECTRODES",
            "MISSING_SESSION",
        ],
        "error": ["NO_T1W"],
        "ignoredFiles": ["/dataset_description.json", "/participants.tsv"],
    }
    # Limit validation only to data from requested participants
    ignored_subjects = all_subjects.difference(subject_list)
    if ignored_subjects:
        for subject in ignored_subjects:
            validator_config_dict["ignoredFiles"].append("/sub-%s/**" % subject)
    with tempfile.NamedTemporaryFile("w+") as temp:
        temp.write(json.dumps(validator_config_dict))
        temp.flush()
        try:
            subprocess.check_call(["bids-validator", bids_dir, "-c", temp.name])
        except FileNotFoundError:
            print("bids-validator does not appear to be installed", file=sys.stderr)
