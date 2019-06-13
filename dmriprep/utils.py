"""
Utility functions for other submodules

"""

import warnings
import itertools

import numpy as np
from bids.layout import BIDSLayout

mod_logger = logging.getLogger(__name__)


def is_hemispherical(vecs):
    """Test whether all points on a unit sphere lie in the same hemisphere.

    Parameters
    ----------
    vecs : numpy.ndarray
        2D numpy array with shape (N, 3) where N is the number of points.
        All points must lie on the unit sphere.

    Returns
    -------
    is_hemi : bool
        If True, one can find a hemisphere that contains all the points.
        If False, then the points do not lie in any hemisphere

    pole : numpy.ndarray
        If `is_hemi == True`, then pole is the "central" pole of the
        input vectors. Otherwise, pole is the zero vector.

    References
    ----------
    https://rstudio-pubs-static.s3.amazonaws.com/27121_a22e51b47c544980bad594d5e0bb2d04.html  # noqa
    """
    if vecs.shape[1] != 3:
        raise ValueError("Input vectors must be 3D vectors")
    if not np.allclose(1, np.linalg.norm(vecs, axis=1)):
        raise ValueError("Input vectors must be unit vectors")

    # Generate all pairwise cross products
    v0, v1 = zip(*[p for p in itertools.permutations(vecs, 2)])
    cross_prods = np.cross(v0, v1)

    # Normalize them
    cross_prods /= np.linalg.norm(cross_prods, axis=1)[:, np.newaxis]

    # `cross_prods` now contains all candidate vertex points for "the polygon"
    # in the reference. "The polygon" is a subset. Find which points belong to
    # the polygon using a dot product test with each of the original vectors
    angles = np.arccos(np.dot(cross_prods, vecs.transpose()))

    # And test whether it is orthogonal or less
    dot_prod_test = angles <= np.pi / 2.0

    # If there is at least one point that is orthogonal or less to each
    # input vector, then the points lie on some hemisphere
    is_hemi = len(vecs) in np.sum(dot_prod_test.astype(int), axis=1)

    if is_hemi:
        vertices = cross_prods[np.sum(dot_prod_test.astype(int), axis=1) == len(vecs)]
        pole = np.mean(vertices, axis=0)
        pole /= np.linalg.norm(pole)
    else:
        pole = np.array([0.0, 0.0, 0.0])
    return is_hemi, pole


class BIDSError(ValueError):
    def __init__(self, message, bids_root):
        indent = 10
        header = '{sep} BIDS root folder: "{bids_root}" {sep}'.format(
            bids_root=bids_root, sep=''.join(['-'] * indent))
        self.msg = '\n{header}\n{indent}{message}\n{footer}'.format(
            header=header, indent=''.join([' '] * (indent + 1)),
            message=message, footer=''.join(['-'] * len(header))
        )
        super(BIDSError, self).__init__(self.msg)
        self.bids_root = bids_root


class BIDSWarning(RuntimeWarning):
    pass


def collect_participants(bids_dir, participant_label=None, strict=False,
                         bids_validate=True):
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
    fmriprep.utils.bids.BIDSError:
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
            'Could not find participants. Please make sure the BIDS data '
            'structure is present and correct. Datasets can be validated online '
            'using the BIDS Validator (http://bids-standard.github.io/bids-validator/).\n'
            'If you are using Docker for Mac or Docker for Windows, you '
            'may need to adjust your "File sharing" preferences.', bids_dir)

    # No --participant-label was set, return all
    if not participant_label:
        return sorted(all_participants)

    if isinstance(participant_label, str):
        participant_label = [participant_label]

    # Drop sub- prefixes
    participant_label = [sub[4:] if sub.startswith('sub-') else sub for sub in participant_label]
    # Remove duplicates
    participant_label = sorted(set(participant_label))
    # Remove labels not found
    found_label = sorted(set(participant_label) & all_participants)
    if not found_label:
        raise BIDSError('Could not find participants [{}]'.format(
            ', '.join(participant_label)), bids_dir)

    # Warn if some IDs were not found
    notfound_label = sorted(set(participant_label) - all_participants)
    if notfound_label:
        exc = BIDSError('Some participants were not found: {}'.format(
            ', '.join(notfound_label)), bids_dir)
        if strict:
            raise exc
        warnings.warn(exc.msg, BIDSWarning)

    return found_label


def collect_data(bids_dir, participant_label, task=None, echo=None,
                 bids_validate=True):
    """
    Uses pybids to retrieve the input data for a given participant
    >>> bids_root, _ = collect_data(str(datadir / 'ds054'), '100185',
    ...                             bids_validate=False)
    >>> bids_root['fmap']  # doctest: +ELLIPSIS
    ['.../ds054/sub-100185/fmap/sub-100185_magnitude1.nii.gz', \
'.../ds054/sub-100185/fmap/sub-100185_magnitude2.nii.gz', \
'.../ds054/sub-100185/fmap/sub-100185_phasediff.nii.gz']
    >>> bids_root['bold']  # doctest: +ELLIPSIS
    ['.../ds054/sub-100185/func/sub-100185_task-machinegame_run-01_bold.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-02_bold.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-03_bold.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-04_bold.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-05_bold.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-06_bold.nii.gz']
    >>> bids_root['sbref']  # doctest: +ELLIPSIS
    ['.../ds054/sub-100185/func/sub-100185_task-machinegame_run-01_sbref.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-02_sbref.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-03_sbref.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-04_sbref.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-05_sbref.nii.gz', \
'.../ds054/sub-100185/func/sub-100185_task-machinegame_run-06_sbref.nii.gz']
    >>> bids_root['t1w']  # doctest: +ELLIPSIS
    ['.../ds054/sub-100185/anat/sub-100185_T1w.nii.gz']
    >>> bids_root['t2w']  # doctest: +ELLIPSIS
    []
    """
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), validate=bids_validate)

    queries = {
        'fmap': {'datatype': 'fmap'},
        't2w': {'datatype': 'anat', 'suffix': 'T2w'},
        't1w': {'datatype': 'anat', 'suffix': 'T1w'},
        'dwi': {'datatype': 'dwi', 'suffix': 'dwi'},
    }

    subj_data = {
        dtype: sorted(layout.get(return_type='file', subject=participant_label,
                                 extensions=['nii', 'nii.gz'], **query))
        for dtype, query in queries.items()}

    return subj_data, layout
