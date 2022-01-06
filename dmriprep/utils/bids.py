# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2021 The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
"""Utilities to handle BIDS inputs."""
import json
import os
import sys
from pathlib import Path

from bids import BIDSLayout


def collect_data(
    bids_dir,
    participant_label,
    bids_validate=True,
    bids_filters=None,
):
    """
    Uses pybids to retrieve the input data for a given participant

    Examples
    --------
    >>> subject_data, bids_root = collect_data(str(datadir / 'BIDS_dataset'), '68',
    ... bids_validate=True,\
        bids_filter={"fmap":{"direction":"REV","acquisition":"dwi"},\
        "dwi":{"direction":"FWD"},"t1w":{"ceagent":"corrected"},\
        "t2w":{"ceagent":"corrected"}}) \
    >>> bids_root['fmap']  # doctest: +ELLIPSIS
    ['.../BIDS_dataset/sub-68/ses-202103221236/fmap/\
    sub-68_ses-202103221236_acq-dwi_dir-REV_epi.nii.gz'', \
    '.../BIDS_dataset/sub-68/ses-202105270937/fmap\
    /sub-68_ses-202105270937_acq-dwi_dir-REV_epi.nii.gz']
    >>> bids_root['bold']  # doctest: +ELLIPSIS
    ['.../BIDS_dataset/sub-68/ses-202103221236/dwi\
    /sub-68_ses-202103221236_dir-FWD_dwi.nii.gz', \
    '.../BIDS_dataset/sub-68/ses-202105270937/dwi\
    /sub-68_ses-202105270937_dir-FWD_dwi.nii.gz']
    >>> bids_root['t1w']  # doctest: +ELLIPSIS
    ['.../BIDS_dataset/sub-68/ses-202103221236/anat\
    /sub-68_ses-202103221236_ce-corrected_T1w.nii.gz', \
    '.../BIDS_dataset/sub-68/ses-202105270937/anat\
    /sub-68_ses-202105270937_ce-corrected_T1w.nii.gz']
    >>> bids_root['t2w']  # doctest: +ELLIPSIS
    ['.../BIDS_dataset/sub-68/ses-202103221236/anat\
    /sub-68_ses-202103221236_ce-corrected_T2w.nii.gz', \
    '.../BIDS_dataset/sub-68/ses-202105270937/anat\
    /sub-68_ses-202105270937_ce-corrected_T2w.nii.gz']
    """
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), validate=bids_validate)

    queries = {
        "fmap": {"datatype": "fmap"},
        "dwi": {"datatype": "dwi", "suffix": "dwi"},
        "flair": {"datatype": "anat", "suffix": "FLAIR"},
        "t2w": {"datatype": "anat", "suffix": "T2w"},
        "t1w": {"datatype": "anat", "suffix": "T1w"},
        "roi": {"datatype": "anat", "suffix": "roi"},
    }
    bids_filters = bids_filters or {}
    for acq, entities in bids_filters.items():
        queries[acq].update(entities)

    subj_data = {
        dtype: sorted(
            layout.get(
                return_type="file",
                subject=participant_label,
                extension=["nii", "nii.gz"],
                **query,
            )
        )
        for dtype, query in queries.items()
    }
    return subj_data, layout


def write_derivative_description(bids_dir, deriv_dir):
    from ..__about__ import DOWNLOAD_URL, __url__, __version__

    bids_dir = Path(bids_dir)
    deriv_dir = Path(deriv_dir)
    desc = {
        "Name": "dMRIPrep - dMRI PREProcessing workflow",
        "BIDSVersion": "1.1.1",
        "PipelineDescription": {
            "Name": "dMRIPrep",
            "Version": __version__,
            "CodeURL": DOWNLOAD_URL,
        },
        "CodeURL": __url__,
        "HowToAcknowledge": "Please cite https://doi.org/10.5281/zenodo.3392201.",
    }

    # Keys that can only be set by environment
    if "DMRIPREP_DOCKER_TAG" in os.environ:
        desc["DockerHubContainerTag"] = os.environ["DMRIPREP_DOCKER_TAG"]
    if "DMRIPREP_SINGULARITY_URL" in os.environ:
        singularity_url = os.environ["DMRIPREP_SINGULARITY_URL"]
        desc["SingularityContainerURL"] = singularity_url

        singularity_md5 = _get_shub_version(singularity_url)
        if singularity_md5 and singularity_md5 is not NotImplemented:
            desc["SingularityContainerMD5"] = _get_shub_version(
                singularity_url
            )

    # Keys deriving from source dataset
    orig_desc = {}
    fname = bids_dir / "dataset_description.json"
    if fname.exists():
        with fname.open() as fobj:
            orig_desc = json.load(fobj)

    if "DatasetDOI" in orig_desc:
        desc["SourceDatasetsURLs"] = [
            "https://doi.org/{}".format(orig_desc["DatasetDOI"])
        ]
    if "License" in orig_desc:
        desc["License"] = orig_desc["License"]

    with (deriv_dir / "dataset_description.json").open("w") as fobj:
        json.dump(desc, fobj, indent=4)


def validate_input_dir(exec_env, bids_dir, participant_label):
    # Ignore issues and warnings that should not influence dMRIPrep
    import subprocess
    import tempfile

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
            "TSV_IMPROPER_NA",
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
    if participant_label:
        all_subs = set([s.name[4:] for s in bids_dir.glob("sub-*")])
        selected_subs = set(
            [s[4:] if s.startswith("sub-") else s for s in participant_label]
        )
        bad_labels = selected_subs.difference(all_subs)
        if bad_labels:
            error_msg = (
                "Data for requested participant(s) label(s) not found. Could "
                "not find data for participant(s): %s. Please verify the requested "
                "participant labels."
            )
            if exec_env == "docker":
                error_msg += (
                    " This error can be caused by the input data not being "
                    "accessible inside the docker container. Please make sure all "
                    "volumes are mounted properly (see https://docs.docker.com/"
                    "engine/reference/commandline/run/#mount-volume--v---read-only)"
                )
            if exec_env == "singularity":
                error_msg += (
                    " This error can be caused by the input data not being "
                    "accessible inside the singularity container. Please make sure "
                    "all paths are mapped properly (see https://www.sylabs.io/"
                    "guides/3.0/user-guide/bind_paths_and_mounts.html)"
                )
            raise RuntimeError(error_msg % ",".join(bad_labels))

        ignored_subs = all_subs.difference(selected_subs)
        if ignored_subs:
            for sub in ignored_subs:
                validator_config_dict["ignoredFiles"].append(
                    "/sub-%s/**" % sub
                )
    with tempfile.NamedTemporaryFile("w+") as temp:
        temp.write(json.dumps(validator_config_dict))
        temp.flush()
        try:
            subprocess.check_call(
                ["bids-validator", bids_dir, "-c", temp.name]
            )
        except FileNotFoundError:
            print(
                "bids-validator does not appear to be installed",
                file=sys.stderr,
            )


def _get_shub_version(singularity_url):
    return NotImplemented
