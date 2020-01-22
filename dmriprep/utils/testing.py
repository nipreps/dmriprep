#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Create empty BIDS data for testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""

from pathlib import Path
import json
import tempfile


def get_grouping_test_data():
    """Write a number of grouping test datasets to base_path."""

    dataset_desctiption = {
        "Acknowledgements": "",
        "Authors": [],
        "BIDSVersion": "1.0.2",
        "DatasetDOI": "",
        "Funding": "",
        "HowToAcknowledge": "",
        "License": "",
        "Name": "test_data",
        "ReferencesAndLinks": [],
        "template": "project"
    }

    base_dir = tempfile.mkdtemp()
    empty_bids_dir = Path(base_dir) / 'empty_bids'
    empty_bids_dir.mkdir(parents=True, exist_ok=True)

    def write_json(pth, content):
        with pth.open('w') as f:
            json.dump(content, f)

    def make_empty_bids(root, project_name):
        project_root = root / project_name
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / 'README').touch()
        write_json(project_root / 'dataset_description.json', dataset_desctiption)
        (project_root / 'sub-1' / 'dwi').mkdir(parents=True, exist_ok=True)
        (project_root / 'sub-1' / 'fmap').mkdir(parents=True, exist_ok=True)
        (project_root / 'sub-1' / 'anat').mkdir(parents=True, exist_ok=True)
        return project_root / 'sub-1'

    def write_test_bids(name, files_and_metas):
        test_bids = make_empty_bids(empty_bids_dir, name)
        for fname, meta in files_and_metas:
            _nifti = fname + ".nii.gz"
            _json = fname + '.json'
            (test_bids / _nifti).touch()
            write_json(test_bids / _json, meta)
        return test_bids.parent

    # One dwi, no fmaps
    easy = write_test_bids(
        'easy',
        [('dwi/sub-1_dwi', {'PhaseEncodingDirection': 'j'})])

    concat1 = write_test_bids(
        'concat1',
        [("dwi/sub-1_run-01_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_run-02_dwi", {'PhaseEncodingDirection': 'j'})]
    )

    opposite = write_test_bids(
        'opposite',
        [("dwi/sub-1_dir-AP_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-PA_dwi", {'PhaseEncodingDirection': 'j-'})])

    opposite_concat = write_test_bids(
        'opposite_concat',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-PA_run-1_dwi", {'PhaseEncodingDirection': 'j-'}),
         ("dwi/sub-1_dir-PA_run-2_dwi", {'PhaseEncodingDirection': 'j-'})])

    phasediff = write_test_bids(
        'phasediff',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_magnitude1", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_magnitude2", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_phasediff", {
             'PhaseEncodingDirection': 'j',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz',
                             'dwi/sub-1_dir-AP_run-2_dwi.nii.gz']})])

    epi = write_test_bids(
        'epi',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_dir-PA_epi", {
             'PhaseEncodingDirection': 'j-',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz',
                             'dwi/sub-1_dir-AP_run-2_dwi.nii.gz']})])

    separate_fmaps = write_test_bids(
        'separate_fmaps',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_dir-PA_run-1_epi", {
             'PhaseEncodingDirection': 'j-',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz']}),
         ("fmap/sub-1_dir-PA_run-2_epi", {
             'PhaseEncodingDirection': 'j-',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-2_dwi.nii.gz']}),
         ])

    mixed_fmaps = write_test_bids(
        'mixed_fmaps',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-PA_run-2_dwi", {'PhaseEncodingDirection': 'j-'}),
         ("fmap/sub-1_dir-PA_run-1_epi", {
             'PhaseEncodingDirection': 'j-',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz']}),
         ("fmap/sub-1_dir-AP_run-2_epi", {
             'PhaseEncodingDirection': 'j',
             'IntendedFor': ['dwi/sub-1_dir-PA_run-2_dwi.nii.gz']}),
         ])

    missing_info = write_test_bids(
        'missing_info',
        [("dwi/sub-1_dir-AP_run-1_dwi", {}),
         ("dwi/sub-1_dir-PA_run-2_dwi", {})]
    )

    wtf = write_test_bids(
        'wtf',
        [("dwi/sub-1_run-1_dwi", {}),
         ("dwi/sub-1_run-2_dwi", {}),
         ("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-PA_run-1_dwi", {'PhaseEncodingDirection': 'j-'}),
         ("dwi/sub-1_dir-PA_run-2_dwi", {'PhaseEncodingDirection': 'j-'}),
         ("dwi/sub-1_dir-IS_dwi", {'PhaseEncodingDirection': 'k-'}),
         ])

    appa_fmaps = write_test_bids(
        'appa_fmaps',
        [("dwi/sub-1_dir-AP_run-1_dwi", {'PhaseEncodingDirection': 'j'}),
         ("dwi/sub-1_dir-AP_run-2_dwi", {'PhaseEncodingDirection': 'j'}),
         ("fmap/sub-1_dir-PA_run-1_epi", {
             'PhaseEncodingDirection': 'j-',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz',
                             'dwi/sub-1_dir-AP_run-2_dwi.nii.gz']}),
         ("fmap/sub-1_dir-AP_run-2_epi", {
             'PhaseEncodingDirection': 'j',
             'IntendedFor': ['dwi/sub-1_dir-AP_run-1_dwi.nii.gz',
                             'dwi/sub-1_dir-AP_run-2_dwi.nii.gz']}),
         ])


    return empty_bids_dir
