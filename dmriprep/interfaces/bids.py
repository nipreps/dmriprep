# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright The NiPreps Developers <nipreps@gmail.com>
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
"""BIDS-related interfaces."""

from pathlib import Path

from bids.utils import listify
from nipype.interfaces.base import (
    DynamicTraitedSpec,
    File,
    SimpleInterface,
    TraitedSpec,
    isdefined,
    traits,
)
from nipype.interfaces.io import add_traits
from nipype.interfaces.utility.base import _ravel


class _BIDSURIInputSpec(DynamicTraitedSpec):
    dataset_links = traits.Dict(mandatory=True, desc='Dataset links')
    out_dir = traits.Str(mandatory=True, desc='Output directory')


class _BIDSURIOutputSpec(TraitedSpec):
    out = traits.List(
        traits.Str,
        desc='BIDS URI(s) for file',
    )


class BIDSURI(SimpleInterface):
    """Convert input filenames to BIDS URIs, based on links in the dataset.

    This interface can combine multiple lists of inputs.
    """

    input_spec = _BIDSURIInputSpec
    output_spec = _BIDSURIOutputSpec

    def __init__(self, numinputs=0, **inputs):
        super().__init__(**inputs)
        self._numinputs = numinputs
        if numinputs >= 1:
            input_names = [f'in{i + 1}' for i in range(numinputs)]
        else:
            input_names = []
        add_traits(self.inputs, input_names)

    def _run_interface(self, runtime):
        inputs = [getattr(self.inputs, f'in{i + 1}') for i in range(self._numinputs)]
        in_files = listify(inputs)
        in_files = _ravel(in_files)
        # Remove undefined inputs
        in_files = [f for f in in_files if isdefined(f)]
        # Convert the dataset links to BIDS URI prefixes
        updated_keys = {f'bids:{k}:': Path(v) for k, v in self.inputs.dataset_links.items()}
        updated_keys['bids::'] = Path(self.inputs.out_dir)
        # Convert the paths to BIDS URIs
        out = [_find_nearest_path(updated_keys, f) for f in in_files]
        self._results['out'] = out

        return runtime


class _BIDSSourceFileInputSpec(TraitedSpec):
    bids_info = traits.Dict(
        mandatory=True,
        desc='BIDS information dictionary',
    )
    precomputed = traits.Dict({}, usedefault=True, desc='Precomputed BIDS information')
    sessionwise = traits.Bool(False, usedefault=True, desc='Keep session information')
    anat_type = traits.Enum('t1w', 't2w', usedefault=True, desc='Anatomical reference type')


class _BIDSSourceFileOutputSpec(TraitedSpec):
    source_file = File(desc='Source file')


class BIDSSourceFile(SimpleInterface):
    input_spec = _BIDSSourceFileInputSpec
    output_spec = _BIDSSourceFileOutputSpec

    def _run_interface(self, runtime):
        src = self.inputs.bids_info[self.inputs.anat_type]

        if not src and self.inputs.precomputed.get(f'{self.inputs.anat_type}_preproc'):
            src = self.inputs.bids_info['dwi']
            self._results['source_file'] = _create_multi_source_file(src)
            return runtime

        self._results['source_file'] = _create_multi_source_file(
            src,
            sessionwise=self.inputs.sessionwise,
        )
        return runtime


class _CreateFreeSurferIDInputSpec(TraitedSpec):
    subject_id = traits.Str(mandatory=True, desc='BIDS Subject ID')
    session_id = traits.Str(desc='BIDS session ID')


class _CreateFreeSurferIDOutputSpec(TraitedSpec):
    subject_id = traits.Str(desc='FreeSurfer subject ID')


class CreateFreeSurferID(SimpleInterface):
    input_spec = _CreateFreeSurferIDInputSpec
    output_spec = _CreateFreeSurferIDOutputSpec

    def _run_interface(self, runtime):
        self._results['subject_id'] = _create_fs_id(
            self.inputs.subject_id,
            self.inputs.session_id or None,
        )
        return runtime


def _create_multi_source_file(in_files, sessionwise=False):
    """
    Create a generic source name from multiple input files.

    If sessionwise is True, session information from the first file is retained in the name.

    Examples
    --------
    >>> _create_multi_source_file([
    ...     '/path/to/sub-045_ses-test_T1w.nii.gz',
    ...     '/path/to/sub-045_ses-retest_T1w.nii.gz'])
    '/path/to/sub-045_T1w.nii.gz'
    >>> _create_multi_source_file([
    ...     '/path/to/sub-045_ses-1_run-1_T1w.nii.gz',
    ...     '/path/to/sub-045_ses-1_run-2_T1w.nii.gz'],
    ...     sessionwise=True)
    '/path/to/sub-045_ses-1_T1w.nii.gz'
    """
    import re
    from pathlib import Path

    from nipype.utils.filemanip import filename_to_list

    if not isinstance(in_files, tuple | list):
        return in_files
    elif len(in_files) == 1:
        return in_files[0]

    p = Path(filename_to_list(in_files)[0])
    try:
        subj = re.search(r'(?<=^sub-)[a-zA-Z0-9]*', p.name).group()
        suffix = re.search(r'(?<=_)\w+(?=\.)', p.name).group()
    except AttributeError as e:
        raise AttributeError('Could not extract BIDS information') from e

    prefix = f'sub-{subj}'

    if sessionwise:
        ses = re.search(r'(?<=_ses-)[a-zA-Z0-9]*', p.name)
        if ses:
            prefix += f'_ses-{ses.group()}'
    return str(p.parent / f'{prefix}_{suffix}.nii.gz')


def _create_fs_id(subject_id, session_id=None):
    """
    Create FreeSurfer subject ID.

    Examples
    --------
    >>> _create_fs_id('01')
    'sub-01'
    >>> _create_fs_id('sub-01')
    'sub-01'
    >>> _create_fs_id('01', 'pre')
    'sub-01_ses-pre'
    """

    if not subject_id.startswith('sub-'):
        subject_id = f'sub-{subject_id}'

    if session_id:
        ses_str = session_id
        if isinstance(session_id, list):
            from smriprep.utils.misc import stringify_sessions

            ses_str = stringify_sessions(session_id)
        if not ses_str.startswith('ses-'):
            ses_str = f'ses-{ses_str}'
        subject_id += f'_{ses_str}'
    return subject_id


def _find_nearest_path(path_dict, input_path):
    """Find the nearest relative path from an input path to a dictionary of paths.

    If ``input_path`` is not relative to any of the paths in ``path_dict``,
    the absolute path string is returned.

    If ``input_path`` is already a BIDS-URI, then it will be returned unmodified.

    Parameters
    ----------
    path_dict : dict of (str, Path)
        A dictionary of paths.
    input_path : Path
        The input path to match.

    Returns
    -------
    matching_path : str
        The nearest relative path from the input path to a path in the dictionary.
        This is either the concatenation of the associated key from ``path_dict``
        and the relative path from the associated value from ``path_dict`` to ``input_path``,
        or the absolute path to ``input_path`` if no matching path is found from ``path_dict``.

    Examples
    --------
    >>> from pathlib import Path
    >>> path_dict = {
    ...     'bids::': Path('/data/derivatives/dmriprep'),
    ...     'bids:raw:': Path('/data'),
    ...     'bids:deriv-0:': Path('/data/derivatives/source-1'),
    ... }
    >>> input_path = Path('/data/derivatives/source-1/sub-01/dwi/sub-01_dir-AP_dwi.nii.gz')
    >>> _find_nearest_path(path_dict, input_path)  # match to 'bids:deriv-0:'
    'bids:deriv-0:sub-01/dwi/sub-01_dir-AP_dwi.nii.gz'
    >>> input_path = Path('/out/sub-01/dwi/sub-01_dir-AP_dwi.nii.gz')
    >>> _find_nearest_path(path_dict, input_path)  # no match- absolute path
    '/out/sub-01/dwi/sub-01_dir-AP_dwi.nii.gz'
    >>> input_path = Path('/data/sub-01/dwi/sub-01_dir-AP_dwi.nii.gz')
    >>> _find_nearest_path(path_dict, input_path)  # match to 'bids:raw:'
    'bids:raw:sub-01/dwi/sub-01_dir-AP_dwi.nii.gz'
    >>> input_path = 'bids::sub-01/dwi/sub-01_dir-AP_dwi.nii.gz'
    >>> _find_nearest_path(path_dict, input_path)  # already a BIDS-URI
    'bids::sub-01/dwi/sub-01_dir-AP_dwi.nii.gz'

    """
    # Don't modify BIDS-URIs
    if isinstance(input_path, str) and input_path.startswith('bids:'):
        return input_path

    # Calculate all distances and sort by distance
    input_path = Path(input_path)
    matching_paths = sorted(
        [
            (len(input_path.relative_to(path).parts), f'{key}{input_path.relative_to(path)}')
            for key, path in path_dict.items()
            if input_path.is_relative_to(path)
        ]
    )
    return str(input_path.absolute()) if not matching_paths else matching_paths[0][1]
