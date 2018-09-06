# -*- coding: utf-8 -*-

"""Functions to fetch BIDS compliant data from HBN dataset"""

import os.path as op
import re

import boto3

from .base import InputS3Keys


def single_subject_s3_keys(subject, site, raw_keys, derivative_keys):
    """Get the S3 keys for a single subject's input files

    Parameters
    ----------
    subject : string
        Subject ID on which to filter the s3 keys

    site : string
        Site ID from which to collect raw data

    raw_keys : sequence
        Sequence of raw data s3 keys to filter

    derivative_keys : sequence
        Sequence of derivative data s3 keys to filter

    Returns
    -------
    InputS3Keys namedtuple
        If all prerequisite s3 keys are present, return a namedtuple of
        s3 keys. Otherwise, use the default None values.
    """
    # Get only the s3 keys corresponding to this subject
    sub_dwi_files = [k for k in raw_keys if subject in k and '/dwi/' in k]
    sub_fmap_files = [k for k in raw_keys if subject in k and '/fmap/' in k]
    sub_deriv_files = [k for k in derivative_keys if subject in k]

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
        return InputS3Keys(
            subject=subject,
            site=site,
            valid=True,
            s3_keys=dict(
                dwi=dwi,
                bvec=bvec,
                bval=bval,
                epi_nii=epi_nii,
                epi_json=epi_json,
                freesurfer=freesurfer,
                t1w=t1w,
            ),
        )
    else:
        return InputS3Keys(
            subject=subject,
            site=site,
            valid=False,
            s3_keys=None,
        )


def get_all_s3_keys(prefix, sites, bucket='fcp-indi'):
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
        A dictionary with keys corresponding to `sites` and values
        that are a list of `InputS3Keys` namedtuples
    """
    s3 = boto3.client('s3')
    subjects = {}

    # Avoid duplicate trailing slash in prefix
    prefix = prefix.rstrip('/')

    for site in sites:
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

        def get_subject_id(key):
            match = re.search('/sub-[0-9a-zA-Z]*/', key)
            if match is not None:
                return match.group().strip('/')
            else:
                return None

        derivative_keys = [
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
            get_subject_id(k) for k in derivative_keys
            if '/freesurfer/' in k
        }

        subs_with_t1w = {
            get_subject_id(k) for k in derivative_keys
            if k.endswith('T1w.nii.gz')
        }

        valid_subjects = (
                subs_with_dwi
                & subs_with_epi_nii
                & subs_with_epi_json
                & subs_with_freesurfer
                & subs_with_t1w
        )

        subject_s3_keys = [
            single_subject_s3_keys(s, site, raw_keys, derivative_keys)
            for s in valid_subjects
        ]

        subjects[site] = list(filter(
            lambda sub: sub.valid,
            subject_s3_keys
        ))

    return subjects
