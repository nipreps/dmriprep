"""
Functions to download example data from public repositories.

"""
import copy
import json
import logging
import os
import os.path as op
import re
import subprocess
from pathlib import Path

import pandas as pd
from dask import compute, delayed
from dask.diagnostics import ProgressBar
from tqdm.auto import tqdm


mod_logger = logging.getLogger(__name__)


def get_dataset(output_dir, source='HBN', subject_id='sub-NDARBA507GCT'):
    if source in ['HBN']:
        get_hbn_data(output_dir, subject_id)
    else:
        raise ValueError('Invalid dataset source')


def get_hbn_data(output_dir, subject_id):
    hbn_study = HBN(subjects=subject_id)
    subject = hbn_study.subjects[0]
    subject.download(directory=output_dir)
    # TODO: return a dict of subject ids and folder locations.
    return os.path.join(output_dir, subject_id)


def get_s3_client():
    """Return a boto3 s3 client

    Returns
    -------
    s3_client : boto3.client('s3')
    """
    import boto3
    from botocore import UNSIGNED
    from botocore.client import Config

    # Global s3 client to preserve anonymous config
    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    return s3_client


def _get_matching_s3_keys(bucket, prefix='', suffix=''):
    """Generate all the matching keys in an S3 bucket.

    Parameters
    ----------
    bucket : str
        Name of the S3 bucket

    prefix : str, optional
        Only fetch keys that start with this prefix

    suffix : str, optional
        Only fetch keys that end with this suffix

    Yields
    ------
    key : str
        S3 keys that match the prefix and suffix
    """
    s3 = get_s3_client()
    kwargs = {'Bucket': bucket, "MaxKeys": 1000}

    # If the prefix is a single string (not a tuple of strings), we can
    # do the filtering directly in the S3 API.
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix

    while True:
        # The S3 API response is a large blob of metadata.
        # 'Contents' contains information about the listed objects.
        resp = s3.list_objects_v2(**kwargs)

        try:
            contents = resp['Contents']
        except KeyError:
            return

        for obj in contents:
            key = obj['Key']
            if key.startswith(prefix) and key.endswith(suffix):
                yield key

        # The S3 API is paginated, returning up to 1000 keys at a time.
        # Pass the continuation token into the next response, until we
        # reach the final page (when this field is missing).
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


def _download_from_s3(fname, bucket, key, overwrite=False):
    """Download object from S3 to local file

    Parameters
    ----------
    fname : str
        File path to which to download the object

    bucket : str
        S3 bucket name

    key : str
        S3 key for the object to download

    overwrite : bool, default=False
        If True, overwrite file if it already exists.
        If False, skip download and return
    """
    # Create the directory and file if necessary
    s3 = get_s3_client()
    Path(op.dirname(fname)).mkdir(parents=True, exist_ok=True)
    try:
        Path(fname).touch(exist_ok=overwrite)

        # Download the file
        s3.download_file(Bucket=bucket, Key=key, Filename=fname)
    except FileExistsError:
        mod_logger.info(f'File {fname} already exists. Continuing...')
        pass


def _recursive_split_ext(path):
    """Recursively split pathname `path` into components.

    Parameters
    ----------
    path : path-like object

    Returns
    -------
    tuple :
        tuple of path parts. All parts except the first have a beginning
        period.

    """
    p0, p1 = op.splitext(path)
    if p1:
        return _recursive_split_ext(p0) + (p1,)
    else:
        return (p0,)


def _cumulative_paths(path_parts, add_ext=""):
    """Return all possible cumulative path names from a list of path parts

    For example, if `path_parts` = ["a", ".b", ".c", ".d"],
    this function will return ["a", "a.b", "a.b.c", "a.b.c.d"]

    Parameters
    ----------
    path_parts: sequence of strings
        The sequence of path substrings. All elements except the first must
        begin with a period.

    add_ext: str
        If provided, add this extension to each element of the result

    Returns
    -------
    list :
        List of cumulative path names
    """
    try:
        add_ext = add_ext if add_ext[0] == "." else "." + add_ext
    except IndexError:
        pass

    return [''.join(path_parts[:i+1]) + add_ext
            for i in range(len(path_parts))]


class Study:
    """A dMRI based study with a BIDS compliant directory structure"""
    def __init__(self, study_id, bucket, s3_prefix, subjects=None):
        """Initialize a Study instance

        Parameters
        ----------
        study_id : str
            An identifier string for the study

        bucket : str
            The S3 bucket that contains the study data

        s3_prefix : str
            The S3 prefix common to all of the study objects on S3

        subjects : str, sequence(str), int, or None
            If int, retrieve S3 keys for the first `subjects` subjects.
            If "all", retrieve all subjects.
            If str or sequence of strings, retrieve S3 keys for the specified
            subjects. If None, retrieve S3 keys for the first subject.
        """
        if not isinstance(study_id, str):
            raise TypeError("subject_id must be a string.")

        if not isinstance(bucket, str):
            raise TypeError("bucket must be a string.")

        if not isinstance(s3_prefix, str):
            raise TypeError("s3_prefix must be a string.")

        if not (subjects is None or
                isinstance(subjects, int) or
                isinstance(subjects, str) or
                all(isinstance(s, str) for s in subjects)):
            raise TypeError("subjects must be an int, string or a "
                            "sequence of strings.")

        if isinstance(subjects, int) and subjects < 1:
            raise ValueError("If subjects is an int, it must be "
                             "greater than 0.")

        self._study_id = study_id
        self._bucket = bucket
        self._s3_prefix = s3_prefix

        self._all_subjects = self.list_all_subjects()
        if subjects is None or subjects == 1:
            enter_validation_loop = True
            subjects = [sorted(self._all_subjects.keys())[0]]
            self._n_requested = 1
        elif isinstance(subjects, int) and subjects > 1:
            enter_validation_loop = True
            self._n_requested = subjects
            subjects = sorted(self._all_subjects.keys())[:subjects]
        elif subjects == "all":
            enter_validation_loop = False
            self._n_requested = len(self._all_subjects)
            subjects = list(self._all_subjects.keys())
        elif isinstance(subjects, str):
            enter_validation_loop = False
            self._n_requested = 1
            subjects = [subjects]
        else:
            enter_validation_loop = False
            self._n_requested = len(subjects)

        if not set(subjects) <= set(self._all_subjects.keys()):
            raise ValueError(
                f"The following subjects could not be found in the study: "
                f"{set(subjects) - set(self._all_subjects.keys())}"
            )

        subs = [
            delayed(self._get_subject)(s) for s in set(subjects)
        ]

        print("Retrieving subject S3 keys")
        with ProgressBar():
            subjects = list(compute(*subs, scheduler="threads"))

        self._subjects = [s for s in subjects if s.valid]

        if enter_validation_loop:
            # index of first uninspected subject
            idx_lo = self._n_requested
            while len(self._subjects) < self._n_requested:
                n_needed = self._n_requested - len(self._subjects)
                if n_needed == 1:
                    subjects = [sorted(self._all_subjects.keys())[idx_lo]]
                else:
                    subjects = sorted(
                        self._all_subjects.keys()
                    )[idx_lo:idx_lo + n_needed]

                idx_lo += n_needed

                subs = [
                    delayed(self._get_subject)(s) for s in set(subjects)
                ]

                with ProgressBar():
                    subjects = list(compute(*subs, scheduler="threads"))

                self._subjects += [s for s in subjects if s.valid]

            self._n_discarded = 0
        else:
            self._n_discarded = len([s for s in subjects if not s.valid])


    @property
    def study_id(self):
        """An identifier string for the study"""
        return self._study_id

    @property
    def bucket(self):
        """The S3 bucket that contains the study data"""
        return self._bucket

    @property
    def s3_prefix(self):
        """The S3 prefix common to all of the study objects on S3"""
        return self._s3_prefix

    @property
    def subjects(self):
        """A list of Subject instances for each requested subject"""
        return self._subjects

    def __repr__(self):
        return (f"{type(self).__name__}(study_id={self.study_id}, "
                f"bucket={self.bucket}, s3_prefix={self.s3_prefix})")

    def _get_subject(self, subject_id):
        """Return a Subject instance from a subject-ID"""
        return Subject(subject_id=subject_id,
                       site=self._all_subjects[subject_id],
                       study=self)

    def list_all_subjects(self):
        """Return a study-specific list of subjects.

        Returns
        -------
        dict
            dict with participant_id as keys and site_id as values
        """
        raise NotImplementedError

    def filter_keys(self, subject):
        """Study-specific S3 key filtering

        Parameters
        ----------
        subject : dmriprep.data.Subject
            subject instance
        """
        pass

    def postprocess(self, subject):
        """Study-specific postprocessing steps

        Parameters
        ----------
        subject : dmriprep.data.Subject
            subject instance
        """
        pass

    def download(self, directory, include_site=False, overwrite=False,
                 pbar=True):
        """Download files for each subject in the study

        Parameters
        ----------
        directory : str
            Directory to which to download subject files

        include_site : bool, default=False
            If True, include the site-ID in the download path

        overwrite : bool, default=False
            If True, overwrite files for each subject

        pbar : bool, default=True
            If True, include progress bar

        See Also
        --------
        dmriprep.data.Subject.download()
        """
        results = [delayed(sub.download)(
            directory=directory,
            include_site=include_site,
            overwrite=overwrite,
            pbar=pbar,
            pbar_idx=idx,
        ) for idx, sub in enumerate(self.subjects)]

        compute(*results, scheduler="threads")


class S3BidsStudy(Study):
    """

    """
    def __init__(self, study_id, bucket, s3_prefix=None,
                 subjects=None):
        """
        Initialize a study which is organized as BIDS compliant S3 bucket, or a
        sub-path of this bucket.

        Parameters
        ----------
        study_id : str An identifier string for the study

        bucket : str The S3 bucket that contains the study data

        s3_prefix : str, optional The S3 prefix common to all of the study
            objects on S3. Defaults to the root of the bucket.

        subjects : str, sequence(str), int, or None
            If int, retrieve S3 keys for the first `subjects` subjects.
            If str or sequence of strings, retrieve S3 keys for the specified
            subjects. If None, retrieve S3 keys for the first subject. If 'all',
            use all of the subjects in the study.
        """
        if s3_prefix is None:
            s3_prefix = ""
        super().__init__(
            study_id=study_id,
            bucket=bucket,
            s3_prefix=s3_prefix,
            subjects=subjects)

    def list_all_subjects(self):
        """
        Find the identifiers of all subjects
        """
        # XXX Ariel will figure this out.




class HBN(Study):
    """The HBN study

    See Also
    --------
    dmriprep.data.Study
    """
    def __init__(self, subjects=None):
        """Initialize the HBN instance

        Parameters
        ----------
        subjects : str, sequence(str), int, or None
            If int, retrieve S3 keys for the first `subjects` subjects.
            If str or sequence of strings, retrieve S3 keys for the specified
            subjects. If None, retrieve S3 keys for the first subject.
        """
        super().__init__(
            study_id="HBN",
            bucket="fcp-indi",
            s3_prefix="data/Projects/HBN/MRI",
            subjects=subjects
        )

    def list_all_subjects(self):
        """Return dict of HBN subjects

        Retrieve subjects from the participants.tsv files at each site

        Returns
        -------
        dict
            dict with participant_id as keys and site_id as values
        """
        def get_site_tsv_keys(site_id):
            pre = 'data/Projects/HBN/MRI/'
            raw = pre + f'{site_id}/participants.tsv'
            deriv = pre + f'{site_id}/derivatives/participants.tsv'
            return {'raw': raw, 'deriv': deriv}

        sites = ['Site-CBIC', 'Site-RU', 'Site-SI']
        tsv_keys = {site: get_site_tsv_keys(site) for site in sites}

        s3 = get_s3_client()

        def get_subs_from_tsv_key(s3_key):
            response = s3.get_object(
                Bucket=self.bucket,
                Key=s3_key
            )

            return set(pd.read_csv(
                response.get('Body')
            ).participant_id.values)

        subjects = {}
        for site, s3_keys in tsv_keys.items():
            site_subs = {k: get_subs_from_tsv_key(v)
                         for k, v in s3_keys.items()}
            subjects[site] = site_subs['raw'] & site_subs['deriv']

        all_subjects = {}
        for site, subs in subjects.items():
            for s in subs:
                all_subjects[s] = site

        return all_subjects

    def filter_keys(self, subject):
        """Filter S3 keys based on HBN specific vagaries

        HBN Site-CBIC has multiple anatomy folders due to
        motion correction software at the scanner level.
        If subject.site == "Site-CBIC" then choose only the
        anatomy files in the T1W_VNavNorm files

        Parameters
        ----------
        subject : dmriprep.data.Subject
            subject instance
        """
        if subject.site == "Site-CBIC":
            t1w_keys = subject.s3_keys['t1w']
            freesurfer_keys = subject.s3_keys['freesurfer']
            correct_dir = "T1w_VNavNorm"

            subject._s3_keys['t1w'] = list(filter(
                lambda x: correct_dir in x,
                t1w_keys
            ))

            subject._s3_keys['freesurfer'] = list(filter(
                lambda x: correct_dir in x,
                freesurfer_keys
            ))

    def postprocess(self, subject):
        """Move the T1 file back into the freesurfer directory.

        This step is specific to the HBN dataset where the T1 files
        are outside of the derivatives/sub-XXX/freesurfer directory,
        due to defacing protocols.

        Parameters
        ----------
        subject : dmriprep.data.Subject
            subject instance
        """
        for sess in subject.files.keys():
            t1_file = subject.files[sess]['t1w'][0]
            freesurfer_path = op.join(op.dirname(t1_file), 'freesurfer')

            convert_cmd = 'mri_convert {in_:s} {out_:s}'.format(
                in_=t1_file, out_=op.join(freesurfer_path, 'mri', 'orig.mgz')
            )

            fnull = open(os.devnull, 'w')
            subprocess.call(convert_cmd.split(),
                            stdout=fnull,
                            stderr=subprocess.STDOUT)

            # if the site is CBIC, then the freesurfer directory has an additional level.
            # move that level up by 1 (e.g. removing the T1w_VNavNorm folder
            if subject.site == 'Site-CBIC':
                newpath = freesurfer_path.replace('T1w_VNavNorm/', '')
                move_cmd = 'mv {oldpath} {newpath}'.format(oldpath=freesurfer_path, newpath=newpath)
                fnull1 = open(os.devnull, 'w')
                subprocess.call(move_cmd.split(),
                                stdout=fnull1,
                                stderr=subprocess.STDOUT)

            # now check that the AP/PA files are named correctly
            # eg it should look like "sub-{id}_dir-{dir}_acq-dwi_epi.nii.gz
            # but sometimes it looks like sub-{id}_acq-dwi_run-01_epi.nii.gz
            # which is silly. the direction should be in the filename.


class Subject:
    """A single dMRI study subject"""
    def __init__(self, subject_id, study, site=None):
        """Initialize a Subject instance

        Parameters
        ----------
        subject_id : str
            Subject-ID for this subject

        study : dmriprep.data.Study
            The Study for which this subject was a participant

        site : str, optional
            Site-ID for the site from which this subject's data was collected
        """
        if not isinstance(subject_id, str):
            raise TypeError("subject_id must be a string.")

        if not isinstance(study, Study):
            raise TypeError("study must be an instance of Study.")

        self._subject_id = subject_id
        self._study = study
        self._site = site
        self._valid = False
        self._organize_s3_keys()
        if self.valid:
            self.study.filter_keys(self)
            self._s3_keys = self._determine_directions(self._s3_keys)
            self._files = None

    @property
    def subject_id(self):
        """An identifier string for the subject"""
        return self._subject_id

    @property
    def study(self):
        """The study in which this subject participated"""
        return self._study

    @property
    def site(self):
        """The site at which this subject was a participant"""
        return self._site

    @property
    def valid(self):
        """If True, this subject has all the required MRI files"""
        return self._valid

    @property
    def s3_keys(self):
        """S3 keys for this subject's dMRI data

        The S3 keys are stored in a dict with following keys:
        - "dwi": Nifti file for DWI image
        - "bval": Bval file
        - "bvec": Bvec file
        - "epi_ap": Nifti EPI image (anterior to posterior)
        - "epi_pa": Nifti EPI image (posterior to anterior)
        - "freesurfer": Freesurfer structural files
        - "t1w": T1W Nifti file
        """
        return self._s3_keys

    @property
    def files(self):
        """Local files for this subject's dMRI data

        Before the call to subject.download(), this is None.
        Afterward, the files are stored in a dict with keys
        for each imaging session. The value for each session
        is itself a dict with the following keys:
        - "dwi": Nifti file for DWI image
        - "bval": Bval file
        - "bvec": Bvec file
        - "epi_ap": Nifti EPI image (anterior to posterior)
        - "epi_pa": Nifti EPI image (posterior to anterior)
        - "freesurfer": Freesurfer structural files
        - "t1w": T1W Nifti file
        """
        return self._files

    def __repr__(self):
        return (f"{type(self).__name__}(subject_id={self.subject_id}, "
                f"study_id={self.study.study_id}, site={self.site}, "
                f"valid={self.valid})")

    def _list_s3_keys(self):
        """Get all required S3 keys for this subject

        Returns
        -------
        s3_keys : dict
            S3 keys organized into "raw" and "deriv" lists
        """
        prefixes = {
            'raw': '/'.join([self.study.s3_prefix,
                             self.site,
                             self.subject_id]),
            'deriv': '/'.join([self.study.s3_prefix,
                               self.site,
                               'derivatives',
                               self.subject_id]),
        }

        s3_keys = {
            rd: list(_get_matching_s3_keys(
                bucket=self.study.bucket,
                prefix=prefix,
            )) for rd, prefix in prefixes.items()
        }

        return s3_keys

    def _organize_s3_keys(self):
        """Organize S3 keys into a dict

        The dict keys are "dwi," "bvec," "bval," "epi_nii," "epi_json,"
        "freesurfer," "t1w" and the values are the associated S3 object keys
        """
        # Retrieve and unpack the s3_keys
        s3_keys = self._list_s3_keys()
        dwi_keys = [k for k in s3_keys['raw'] if '/dwi/' in k]
        fmap_keys = [k for k in s3_keys['raw'] if '/fmap/' in k]
        deriv_keys = s3_keys['deriv']
        all_json_keys = [k for k in s3_keys['raw'] if k.endswith('.json')]

        # Get the dwi files, bvec files, and bval files
        dwi = [f for f in dwi_keys
               if f.endswith('.nii.gz') and 'TRACEW' not in f]
        bvec = [f for f in dwi_keys if f.endswith('.bvec')]
        bval = [f for f in dwi_keys if f.endswith('.bval')]
        epi_nii = [f for f in fmap_keys if f.endswith('epi.nii.gz')
                   and 'fMRI' not in f]
        epi_json = [f for f in fmap_keys if f.endswith('epi.json')
                    and 'fMRI' not in f]
        t1w = [f for f in deriv_keys if f.endswith('/T1w.nii.gz')]
        freesurfer = [f for f in deriv_keys
                      if '/freesurfer/' in f]

        json_keys = []
        for file_list in [dwi, bvec, bval, epi_nii, t1w]:
            for f in file_list:
                potential_keys = _cumulative_paths(_recursive_split_ext(f),
                                                   add_ext="json")
                json_keys += [k for k in potential_keys if k in all_json_keys]

        # Use truthiness of non-empty lists to verify that all
        # of the required prereq files exist in `s3_keys`
        # TODO: If some of the files are missing, look farther up in the directory
        # TODO: structure to see if there are files we should inherit
        if all([dwi, bval, bvec, epi_nii, epi_json, t1w, freesurfer]):
            self._valid = True
            self._s3_keys = dict(
                dwi=dwi,
                bvec=bvec,
                bval=bval,
                json=json_keys,
                epi_nii=epi_nii,
                epi_json=epi_json,
                freesurfer=freesurfer,
                t1w=t1w,
            )
        else:
            self._valid = False
            self._s3_keys = None

    def download(self, directory, include_site=False,
                 overwrite=False, pbar=True, pbar_idx=0):
        """Download files from S3

        Parameters
        ----------
        directory : str
            Directory to which to download subject files

        include_site : bool, default=False
            If True, include the site-ID in the download path

        overwrite : bool, default=False
            If True, overwrite files for each subject

        pbar : bool, default=True
            If True, include download progress bar

        pbar_idx : int, default=0
            Progress bar index for multithreaded progress bars
        """
        if not self.valid:
            mod_logger.warning(
                f"Subject {self.subject_id} is not a valid subject. "
                f"Skipping download."
            )
            return

        if include_site:
            directory = op.join(directory, self.site)

        files = {
            k: [op.abspath(op.join(
                directory, p.split('/' + self.site + '/')[-1]
            )) for p in v] for k, v in self.s3_keys.items()
        }

        # Generate list of (key, file) tuples
        key_file_pairs = []

        for ftype in self.s3_keys.keys():
            s3_keys = self.s3_keys[ftype]
            if isinstance(s3_keys, str):
                key_file_pairs.append((s3_keys, files[ftype]))
            elif all(isinstance(x, str) for x in s3_keys):
                for key, fname in zip(s3_keys, files[ftype]):
                    key_file_pairs.append((key, fname))
            else:
                raise TypeError(
                    f"This subject {self.subject_id} has {ftype} S3 keys that "
                    f"are neither strings nor a sequence of strings. The "
                    f"offending S3 keys are {s3_keys!s}"
                )

        try:
            files_by_session = self._separate_sessions(files)
            self._files = files_by_session
        except NotImplementedError:
            self._valid = False
            mod_logger.warning(
                f"Subject {self.subject_id} has inconsistent session numbers."
                f"Skipping download."
            )
            return

        if not files_by_session.keys():
            # There were no valid sessions
            self._valid = False
            mod_logger.warning(
                f"Subject {self.subject_id} is not a valid subject. "
                f"Skipping download."
            )
            return

        # Now iterate through the list and download each item
        if pbar:
            progress = tqdm(desc=f"Download {self.subject_id}",
                            position=pbar_idx,
                            total=len(key_file_pairs) + 1)

        for (key, fname) in key_file_pairs:
            _download_from_s3(fname=fname,
                              bucket=self.study.bucket,
                              key=key,
                              overwrite=overwrite)

            if pbar:
                progress.update()

        if pbar:
            progress.set_description(f"Postproc {self.subject_id}")

        self.study.postprocess(subject=self)

        if pbar:
            progress.update()
            progress.close()

    def _determine_directions(self,
                              input_files,
                              input_type='s3',
                              metadata_source='json',
                              json_key='PhaseEncodingDirection',
                              ap_value='j-', pa_value='j'):
        """Determine direction ['AP', 'PA'] of single subject's EPI nifty files

        Use either metadata in associated json file or filename

        Parameters
        ----------
        input_files : dict
            The local input files for the subject

        input_type : "s3" or "local", default="s3"
            The location of the input files, local or on S3

        metadata_source : "json" or "filename", default="json"
            If "filename," look for the direction in the filename,
            otherwise, use the json file and the other parameters

        json_key : string, default="PhaseEncodingDirection"
            The key that stores the direction information

        ap_value : string, default="j-"
            Metadata value to associate with dir-AP

        pa_value : string, default="j"
            Metadata value to associate with dir-PA

        Returns
        -------
        dict
            Filenames or S3 keys where all fields match self.files or
            self.s3_keys except that in the "epi_nii" and "epi_json" keys
            have been replaced with "epi_ap" and "epi_pa."
        """
        if metadata_source not in ['filename', 'json']:
            raise ValueError('metadata_source must be "filename" or "json".')

        if input_type not in ['s3', 'local']:
            raise ValueError('input_type must be "local" or "s3".')

        epi_files = input_files['epi_nii']
        json_files = input_files['epi_json']
        if metadata_source == 'filename':
            ap_files = [f for f in epi_files if 'dir-AP' in f]
            pa_files = [f for f in epi_files if 'dir-PA' in f]
        else:
            # Confirm that each nifty file has a corresponding json file.
            required_json = set([f.replace('.nii.gz', '.json') for f in epi_files])
            if set(json_files) != required_json:
                self._valid = False
                mod_logger.warning(
                    f'Subject {self.subject_id} does not have json files '
                    f'corresponding to its fmap NIFTI files. Failed to '
                    f'find the following expected files: '
                    f'{required_json - set(json_files)}. Subject deemed '
                    f'invalid.'
                )
                return input_files

            def get_json(json_file):
                if input_type == 'local':
                    with open(json_file, 'r') as fp:
                        meta = json.load(fp)
                else:
                    s3 = get_s3_client()
                    response = s3.get_object(
                        Bucket=self.study.bucket,
                        Key=json_file,
                    )
                    meta = json.loads(response.get('Body').read())

                return meta

            ap_files = []
            pa_files = []
            for jfile in json_files:
                metadata = get_json(jfile)

                direction = metadata.get(json_key)
                if direction == ap_value:
                    if 'dir-PA' in jfile:
                        mod_logger.warning(
                            'The key {key:s}={val:s} does not match the direction '
                            'suggested by the filename {fn:s}'.format(
                                key=json_key, val=direction, fn=jfile
                            )
                        )
                    ap_files.append(jfile.replace('.json', '.nii.gz'))
                elif direction == pa_value:
                    if 'dir-AP' in jfile:
                        mod_logger.warning(
                            'The key {key:s}={val:s} does not match the direction '
                            'suggested by the filename {fn:s}'.format(
                                key=json_key, val=direction, fn=jfile
                            )
                        )
                    pa_files.append(jfile.replace('.json', '.nii.gz'))
                elif direction is None:
                    mod_logger.warning(
                        'The key {key:s} does not exist in file {jfile:s}. '
                        'Falling back on filename to determine directionality.'
                        '\n\n'.format(key=json_key, jfile=jfile)
                    )
                    if 'dir-AP' in jfile:
                        ap_files.append(jfile.replace('.json', '.nii.gz'))
                    elif 'dir-PA' in jfile:
                        pa_files.append(jfile.replace('.json', '.nii.gz'))
                    else:
                        self._valid = False
                        mod_logger.warning(
                            f'Subject {self.subject_id} lacks the expected '
                            f'{json_key} key in file {jfile} and the '
                            f'directionality could not be inferred from the '
                            f'file name. Setting subject validity to False.'
                        )
                        return input_files
                else:
                    mod_logger.warning(
                        'The metadata in file {jfile:s} does not match the dir-PA '
                        'or dir-AP values that you provided. {key:s} = {val:s}. '
                        'Falling back on filename to determine directionality.\n\n'
                        ''.format(jfile=jfile, key=json_key, val=direction)
                    )
                    if 'dir-AP' in jfile:
                        ap_files.append(jfile.replace('.json', '.nii.gz'))
                    elif 'dir-PA' in jfile:
                        pa_files.append(jfile.replace('.json', '.nii.gz'))
                    else:
                        self._valid = False
                        mod_logger.warning(
                            'The metadata for key {key:s} in file {jfile:s} does '
                            'not match the dir-PA or dir-AP values that you '
                            'provided. {key:s} = {val:s}. And the directionality '
                            'could not be inferred from the file name.'.format(
                                key=json_key,
                                jfile=jfile,
                                val=direction,
                            ))
                        return input_files

        files = copy.deepcopy(input_files)
        del files['epi_nii']
        del files['epi_json']
        files['epi_ap'] = ap_files
        files['epi_pa'] = pa_files

        return files

    def _separate_sessions(self, input_files, multiples_policy='sessions',
                           assign_empty_sessions=True):
        """Separate input file register into different sessions

        Parameters
        ----------
        input_files : dict
            Dictionary of subject files

        multiples_policy : "sessions" or "concatenate"
            Flag that dictates how to handle multiple files in a session.
            If "sessions," treat multiples as different sessions and assign
            to new session IDs. If "concatenate," concatenate multiples into
            a single session

        assign_empty_sessions : bool
            If True, assign session IDs to files without a session ID in
            their path

        Returns
        -------
        dict of dicts
            Dict of Dicts of file names
        """
        if multiples_policy not in ['sessions', 'concatenate']:
            raise ValueError('`multiples_policy` must be either "sessions" or '
                             '"concatenate"')

        # Take only the first of the T1W nifty files
        if len(input_files['t1w']) > 1:
            mod_logger.warning(
                f"Found more than one T1W file for subject {self.subject_id} "
                f"at site {self.site}. Discarding the others.\n\n"
            )

        t1w = input_files['t1w']

        # Take only the first freesurfer directory
        freesurfer_dirs = {
            f.split('/freesurfer/')[0] for f in input_files['freesurfer']
        }

        if len(freesurfer_dirs) > 1:
            mod_logger.warning(
                f"Found more than one freesurfer directory for subject "
                f"{self.subject_id} at site {self.site}. Discarding the "
                f"others.\n\n"
            )

        freesurfer_dir = freesurfer_dirs.pop()
        freesurfer = [f for f in input_files['freesurfer']
                      if f.startswith(freesurfer_dir)]

        # Organize the files by session ID
        def get_sess_id(filename, fallback='null'):
            # Retrieve the session ID from a filename
            match = re.search('/ses-[0-9a-zA-Z]*/', filename)
            if match is not None:
                return match.group().strip('/')
            else:
                return fallback

        ftypes = ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']

        sess_ids = {ft: {get_sess_id(fn) for fn in input_files[ft]}
                    for ft in ftypes}

        if not all([s == list(sess_ids.values())[0]
                    for s in sess_ids.values()]):
            mod_logger.warning(
                "Session numbers are inconsistent for subject {sub:s} at site "
                "{site:s}. Ses-IDs: {sess_ids!s}.\n"
                "Files: {files!s}\n\n".format(
                    sub=self.subject_id,
                    site=self.site,
                    sess_ids=sess_ids,
                    files={
                        k: (v) for k, v in input_files.items()
                        if k in ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']
                    },
                )
            )
            return

        # We just confirmed that all of the session ID sets are equal so we can
        # pop one set of session IDs off of `sess_ids` and use it from now on
        sess_ids = sess_ids[ftypes[0]]

        # Collect files by session ID and then file type
        files_by_session = {
            sess: {
                ft: [
                    f for f in input_files[ft] if get_sess_id(f) == sess
                ]
                for ft in ftypes
            }
            for sess in sess_ids
        }

        output_files = {}

        # Loop over each session ID
        for session, files in files_by_session.items():
            # Confirm that the subject has an equal number of each type of file
            n_files = {k: len(v) for k, v in files.items()
                       if k in ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']}

            if len(set(n_files.values())) != 1:
                mod_logger.warning(
                    f"The number of files is inconsistent for subject "
                    f"{self.subject_id} at site {self.site}. The file numbers "
                    f"are {n_files!s}\n\n"
                )
            elif len(set(n_files.values())) == 1:
                # There is only one set of files in this session.
                # Append to output.
                if session == 'null':
                    output_session = 'ses-01' if assign_empty_sessions else None
                else:
                    output_session = session

                output_files[output_session] = dict(
                    dwi=input_files['dwi'],
                    bvec=input_files['bvec'],
                    bval=input_files['bval'],
                    epi_ap=input_files['epi_ap'],
                    epi_pa=input_files['epi_pa'],
                    json=input_files['json'],
                    t1w=t1w,
                    freesurfer=freesurfer,
                )
            else:
                # There are multiple copies of files for this one session ID.
                if multiples_policy == 'concatenate':
                    # The multiple copies represent one session and should be
                    # concatenated
                    raise NotImplementedError("Concatenation of multiples not "
                                              "yet implemented.")
                else:
                    # The multiple copies represent multiple sessions and
                    # should be further subdivided into sessions
                    raise NotImplementedError("Session subdivision not yet "
                                              "implemented.")

        return output_files
