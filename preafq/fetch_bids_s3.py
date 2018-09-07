# -*- coding: utf-8 -*-

"""Functions to fetch BIDS compliant data from S3"""

import copy
import json
import logging
import os.path as op
import re
from pathlib import Path

import boto3

from .base import InputFiles, InputFilesWithSession


mod_logger = logging.getLogger(__name__)


def get_s3_register(subject_id, site, raw_keys, deriv_keys):
    """Get the S3 keys for a single subject's input files

    Parameters
    ----------
    subject_id : string
        Subject ID on which to filter the s3 keys

    site : string
        Site ID from which to collect raw data

    raw_keys : sequence
        Sequence of raw data s3 keys to filter

    deriv_keys : sequence
        Sequence of derivative data s3 keys to filter

    Returns
    -------
    InputFiles namedtuple
        If all prerequisite s3 keys are present, return a namedtuple of
        s3 keys. Otherwise, use the default None values.
    """
    # Get only the s3 keys corresponding to this subject_id
    sub_dwi_files = [k for k in raw_keys if subject_id in k and '/dwi/' in k]
    sub_fmap_files = [k for k in raw_keys if subject_id in k and '/fmap/' in k]
    sub_deriv_files = [k for k in deriv_keys if subject_id in k]

    # Get the dwi files, bvec files, and bval files
    dwi = [f for f in sub_dwi_files
           if f.endswith('.nii.gz') and 'TRACEW' not in f]
    bvec = [f for f in sub_dwi_files if f.endswith('.bvec')]
    bval = [f for f in sub_dwi_files if f.endswith('.bval')]
    epi_nii = [f for f in sub_fmap_files if f.endswith('epi.nii.gz')
               and 'fMRI' not in f]
    epi_json = [f for f in sub_fmap_files if f.endswith('epi.json')
                and 'fMRI' not in f]
    t1w = [f for f in sub_deriv_files if f.endswith('/T1w.nii.gz')]
    freesurfer = [f for f in sub_deriv_files
                  if '/freesurfer/' in f]

    # Use truthiness of non-empty lists to verify that all
    # of the required prereq files exist in `s3_keys`
    # TODO: If some of the files are missing, look farther up in the directory
    # TODO: structure to see if there are files we should inherit
    if all([dwi, bval, bvec, epi_nii, epi_json, t1w, freesurfer]):
        return InputFiles(
            subject=subject_id,
            site=site,
            valid=True,
            files=dict(
                dwi=dwi,
                bvec=bvec,
                bval=bval,
                epi_nii=epi_nii,
                epi_json=epi_json,
                freesurfer=freesurfer,
                t1w=t1w,
            ),
            file_type='s3'
        )
    else:
        return InputFiles(
            subject=subject_id,
            site=site,
            valid=False,
            files=None,
            file_type='s3'
        )


def get_s3_keys(prefix, site, bucket='fcp-indi'):
    """Retrieve all keys in an S3 bucket that match the prefix and site ID

    Parameters
    ----------
    prefix : string
        S3 prefix designating the S3 "directory" in which to search.
        Do not include the site ID in the prefix.

    site : string
        Site ID from which to collect raw data

    bucket : string
        AWS S3 bucket in which to search

    Returns
    -------
    list
        All the keys matching the prefix and site in the S3 bucket
    """
    s3 = boto3.client('s3')

    # Avoid duplicate trailing slash in prefix
    prefix = prefix.rstrip('/')

    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix + '/' + site + '/',
    )

    try:
        keys = [d['Key'] for d in response.get('Contents')]
    except TypeError:
        raise ValueError(
            'There are no subject files in the S3 bucket with prefix '
            '{pfix:s} and site {site:s}'.format(pfix=prefix, site=site)
        )

    while response['IsTruncated']:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix + '/' + site + '/',
            ContinuationToken=response['NextContinuationToken']
        )

        keys += [d['Key'] for d in response.get('Contents')]

    return keys


def keys_to_subject_register(keys, prefix, site):
    """Filter S3 keys based on data availability and return

    Parameters
    ----------
    keys : sequence
        sequence of S3 keys

    prefix : string
        S3 prefix designating the S3 "directory" in which to search.
        Do not include the site ID in the prefix.

    site : string
        Site ID from which to collect raw data

    Returns
    -------
    list
        List of `InputFiles` namedtuples for each valid subject
    """
    def get_subject_id(key):
        match = re.search('/sub-[0-9a-zA-Z]*/', key)
        if match is not None:
            return match.group().strip('/')
        else:
            return None

    deriv_keys = [
        k for k in keys
        if k.startswith(prefix + '/' + site + '/derivatives/sub-')
    ]

    raw_keys = [
        k for k in keys
        if k.startswith(prefix + '/' + site + '/sub-')
    ]

    subs_with_dwi = {
        get_subject_id(k) for k in raw_keys
        if '/dwi/' in k
    }

    subs_with_epi_nii = {
        get_subject_id(k) for k in raw_keys
        if (
            k.endswith('epi.nii.gz')
            and '/fmap/' in k
            and 'fMRI' not in k
        )
    }

    subs_with_epi_json = {
        get_subject_id(k) for k in raw_keys
        if (
            k.endswith('epi.json')
            and '/fmap/' in k
            and 'fMRI' not in k
        )
    }

    subs_with_freesurfer = {
        get_subject_id(k) for k in deriv_keys
        if '/freesurfer/' in k
    }

    subs_with_t1w = {
        get_subject_id(k) for k in deriv_keys
        if k.endswith('T1w.nii.gz')
    }

    valid_subjects = (
            subs_with_dwi
            & subs_with_epi_nii
            & subs_with_epi_json
            & subs_with_freesurfer
            & subs_with_t1w
    )

    s3_registers = [
        get_s3_register(subject_id=s, site=site, raw_keys=raw_keys,
                        deriv_keys=deriv_keys)
        for s in valid_subjects
    ]

    s3_registers = list(filter(
        lambda sub: sub.valid,
        s3_registers
    ))

    return s3_registers


def download_register(subject_keys, bucket='fcp-indi', directory='./input'):
    """
    Parameters
    ----------
    subject_keys : InputFiles namedtuple
        Input s3 keys stored in namedtuple. Must have the fields
        'subject': subjectID,
        'site': siteID,
        'files': dictionary of S3 keys

    bucket : string
        S3 bucket from which to extract files

    directory : string
        Local directory to which to save files

    Returns
    -------
    files : InputFiles namedtuple
        Input file paths stored in namedtuple. Has the fields
        'subject': subjectID,
        'site' : siteID,
        'valid' : True,
        'files' : local file paths,
        'file_type' : 'local',
    """
    s3 = boto3.client('s3')
    subject = subject_keys.subject
    site = subject_keys.site

    input_files = InputFiles(
        subject=subject,
        site=site,
        valid=True,
        files={
            k: [op.abspath(op.join(
                directory, site, p.split('/' + site + '/')[-1]
            )) for p in v] for k, v in subject_keys.files.items()
        },
        file_type='local'
    )

    def download_from_s3(fname_, bucket_, key_):
        # Create the directory and file if necessary
        Path(op.dirname(fname_)).mkdir(parents=True, exist_ok=True)
        Path(fname_).touch(exist_ok=True)

        # Download the file
        s3.download_file(Bucket=bucket_, Key=key_, Filename=fname_)

    s3keys = subject_keys.files
    files = input_files.files
    for ftype in s3keys.keys():
        if isinstance(s3keys[ftype], str):
            download_from_s3(fname_=files[ftype],
                             bucket_=bucket,
                             key_=s3keys[ftype])
        elif all(isinstance(x, str) for x in s3keys[ftype]):
            for key, fname in zip(s3keys[ftype], files[ftype]):
                download_from_s3(fname_=fname, bucket_=bucket, key_=key)
        else:
            raise TypeError(
                'This subject {sub:s} has {ftype:s} S3 keys that are neither '
                'strings nor a sequence of strings. The S3 keys are {keys!s}'
                ''.format(sub=subject, ftype=ftype, keys=s3keys[ftype])
            )

    return input_files


def determine_directions(input_files,
                         input_type='s3',
                         bucket=None,
                         metadata_source='json',
                         json_key='PhaseEncodingDirection',
                         ap_value='j-', pa_value='j'):
    """Determine direction ['AP', 'PA'] of single subject's EPI nifty files

    Use either metadata in associated json file or filename

    Parameters
    ----------
    input_files : InputFiles namedtuple
        The local input files for the subject

    input_type : "s3" or "local", default="s3"
        The location of the input files, local or on S3

    bucket : string or None, default=None
        S3 Bucket where the input files are located.
        If input_type == 's3', then bucket must not be None

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
    InputFiles namedtuple
        An InputFiles namedtuple where all fields match the `input_files`
        namedtuple except that in the `files` field, the "epi_nii" and
        "epi_json" keys have been replaced with "epi_ap" and "epi_pa."
    """
    if metadata_source not in ['filename', 'json']:
        raise ValueError('metadata_source must be "filename" or "json".')

    if input_type not in ['s3', 'local']:
        raise ValueError('input_type must be "local" or "s3".')

    if input_type == 's3' and bucket is None:
        raise ValueError('If input_type is "s3," you must supply a bucket.')

    epi_files = input_files.files['epi_nii']
    json_files = input_files.files['epi_json']
    if metadata_source == 'filename':
        ap_files = [f for f in epi_files if 'dir-AP' in f]
        pa_files = [f for f in epi_files if 'dir-PA' in f]
    else:
        # Confirm that each nifty file has a corresponding json file.
        required_json = set([f.replace('.nii.gz', '.json') for f in epi_files])
        if set(json_files) != required_json:
            raise ValueError(
                'There are nifty files without corresponding json files. We '
                'failed to find the following expected files: {files!s}'
                ''.format(files=required_json - set(json_files))
            )

        s3 = boto3.client('s3')

        def get_json(json_file):
            if input_type == 'local':
                with open(json_file, 'r') as fp:
                    meta = json.load(fp)
            else:
                response = s3.get_object(
                    Bucket=bucket,
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
                    raise ValueError(
                        'The key {key:s} does not exist in file {jfile:s} and '
                        'the directionality could not be inferred from the '
                        'file name.'.format(key=json_key, jfile=jfile)
                    )
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
                    raise ValueError(
                        'The metadata for key {key:s} in file {jfile:s} does '
                        'not match the dir-PA or dir-AP values that you '
                        'provided. {key:s} = {val:s}. And the directionality '
                        'could not be inferred from the file name.'.format(
                            key=json_key,
                            jfile=jfile,
                            val=direction,
                        ))

    files = copy.deepcopy(input_files.files)
    del files['epi_nii']
    del files['epi_json']
    files['epi_ap'] = ap_files
    files['epi_pa'] = pa_files

    return InputFiles(
        subject=input_files.subject,
        site=input_files.site,
        valid=input_files.valid,
        files=files,
        file_type=input_files.file_type
    )


def separate_sessions(input_files, multiples_policy='sessions',
                      assign_empty_sessions=True):
    """Separate input file register into different sessions

    Parameters
    ----------
    input_files : InputFiles namedtuple

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
    list of InputFiles namedtuples
        List of InputFiles namedtuples for each session ID.
    """
    if multiples_policy not in ['sessions', 'concatenate']:
        raise ValueError('`multiples_policy` must be either "sessions" or '
                         '"concatenate"')

    # Take only the first of the T1W nifty files
    if len(input_files.files['t1w']) > 1:
        mod_logger.warning(
            'Found more than one T1W file for subject {sub:s} at site {site:s}'
            '. Discarding the others.\n\n'.format(sub=input_files.subject,
                                                  site=input_files.site)
        )

    t1w = input_files.files['t1w'][0]

    # Take only the first freesurfer directory
    freesurfer_dirs = {
        f.split('/freesurfer/')[0] for f in input_files.files['freesurfer']
    }

    if len(freesurfer_dirs) > 1:
        mod_logger.warning(
            'Found more than one freesurfer dir for subject {sub:s} at site '
            '{site:s}. Discarding the others.\n\n'.format(
                sub=input_files.subject, site=input_files.site
            )
        )

    freesurfer_dir = freesurfer_dirs.pop()
    freesurfer = [f for f in input_files.files['freesurfer']
                  if f.startswith(freesurfer_dir)]

    # Organize the files by session ID
    def get_sess_id(filename, fallback='null'):
        # Retrieve the session ID from a filename
        match = re.search('/sess-[0-9a-zA-Z]*/', filename)
        if match is not None:
            return match.group().strip('/')
        else:
            return fallback

    ftypes = ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']

    sess_ids = {ft: {get_sess_id(fn) for fn in input_files.files[ft]}
                for ft in ftypes}

    if not all([s == list(sess_ids.values())[0] for s in sess_ids.values()]):
        mod_logger.warning(
            'Session numbers are inconsistent for subject {sub:s} at site '
            '{site:s}. Sess-IDs: {sess_ids!s}.\nFiles: {files!s}\n\n'.format(
                sub=input_files.subject,
                site=input_files.site,
                sess_ids=sess_ids,
                files={k: (v) for k, v in input_files.files.items()
                       if k in ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']},
            )
        )
        return [InputFilesWithSession(
            subject=input_files.subject,
            site=input_files.site,
            session=None,
            files=None,
            file_type=None,
        )]

    # We just confirmed that all of the session ID sets are equal so we can
    # pop one set of session IDs off of `sess_ids` and use it from now on
    sess_ids = sess_ids[ftypes[0]]

    # Collect files by session ID and then file type
    files_by_session = {
        sess: {
            ft: [
                f for f in input_files.files[ft] if get_sess_id(f) == sess
            ]
            for ft in ftypes
        }
        for sess in sess_ids
    }

    output_files = []

    # Loop over each session ID
    for session, files in files_by_session.items():
        # Confirm that the subject has an equal number of each type of file
        n_files = {k: len(v) for k, v in files.items()
                   if k in ['dwi', 'bvec', 'bval', 'epi_ap', 'epi_pa']}

        if len(set(n_files.values())) != 1:
            mod_logger.warning(
                'The number of files is inconsistent for subject {sub:s} at '
                'site {site:s}. The file numbers are {n_files!s}\n\n'.format(
                    sub=input_files.subject,
                    site=input_files.site,
                    n_files=n_files
                )
            )
            output_files.append(InputFilesWithSession(
                subject=input_files.subject,
                site=input_files.site,
                session=None,
                files=None,
                file_type=None,
            ))
        elif len(set(n_files.values())) == 1:
            # There is only one set of files in this session. Append to output.
            if session == 'null':
                output_session = 'sess-01' if assign_empty_sessions else None
            else:
                output_session = session

            output_files.append(InputFilesWithSession(
                subject=input_files.subject,
                site=input_files.site,
                session=output_session,
                files=dict(
                    dwi=input_files.files['dwi'],
                    bvec=input_files.files['bvec'],
                    bval=input_files.files['bval'],
                    epi_ap=input_files.files['epi_ap'],
                    epi_pa=input_files.files['epi_pa'],
                    t1w=t1w,
                    freesurfer=freesurfer,
                ),
                file_type=input_files.file_type,
            ))
        else:
            # There are multiple copies of files for this one session ID.
            if multiples_policy == 'concatenate':
                # The multiple copies represent one session and should be
                # concatenated
                raise NotImplementedError('Concatenation of multiples not yet '
                                          'implemented.')
            else:
                # The multiple copies represent multiple sessions and
                # should be further subdivided into sessions
                raise NotImplementedError('Session subdivision not yet '
                                          'implemented.')

    return output_files


def get_all_s3_registers(prefix, sites, bucket='fcp-indi'):
    """

    Parameters
    ----------
    prefix : string
        S3 prefix designating the S3 "directory" in which to search.
        Do not include the site ID in the prefix.

    sites : sequence of strings
        Site IDs from which to collect raw data

    bucket : string
        AWS S3 bucket in which to search

    Returns
    -------
    dict
        dict where the keys are site IDs and the values are
        list of `InputFiles` namedtuples for each valid subject
        at that site
    """
    subjects = {}
    for site in sites:
        # Get all S3 keys
        keys = get_s3_keys(prefix=prefix, site=site, bucket='fcp-indi')

        # Get all registers (without the AP/PA directions)
        regs = keys_to_subject_register(keys=keys, prefix=prefix, site=site)

        # Assign the fmap files to either AP/PA
        regs_pa_ap = [
            determine_directions(input_files=reg,
                                 input_type='s3',
                                 bucket=bucket,
                                 metadata_source='json',
                                 json_key='PhaseEncodingDirection',
                                 ap_value='j-', pa_value='j')
            for reg in regs
        ]

        # Separate each subject register into different sessions
        regs_nested = [
            separate_sessions(reg,
                              multiples_policy='sessions',
                              assign_empty_sessions=True)
            for reg in regs_pa_ap
        ]

        # But `separate_sessions` returns a list of namedtuples
        # so `regs_nested` is nested and needs to be flattened
        regs_flat = [item for sublist in regs_nested for item in sublist]

        subjects[site] = [reg for reg in regs_flat if reg.files is not None]

    return subjects
