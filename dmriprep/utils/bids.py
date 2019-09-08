# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Utilities to handle BIDS inputs."""
import warnings


def get_bids_dict(layout, participant_label=None, session=None):
    def merge_dicts(x, y):
        """
        A function to merge two dictionaries, making it easier for us to make
        modality specific queries for dwi images (since they have variable
        extensions due to having an nii.gz, bval, and bvec file).
        """
        z = x.copy()
        z.update(y)
        return z

    # get all files matching the specific modality we are using
    if not participant_label:
        # list of all the subjects
        subjs = layout.get_subjects()
    else:
        # make it a list so we can iterate
        if not isinstance(participant_label, list):
            subjs = [participant_label]
            assert participant_label in subjs, "subject {} is not in the bids folder".format(participant_label)
        else:
            subjs = participant_label
            assert participant_label[0] in subjs, "subject {} is not in the bids folder".format(participant_label)

    print('\n')
    print("%s%s" % ('Subject:', subjs))
    for sub in subjs:
        if not session:
            seshs = layout.get_sessions(subject=sub, derivatives=False)
            # in case there are non-session level inputs
            seshs += [None]
        else:
            # make a list so we can iterate
            if not isinstance(session, list):
                seshs = [session]
                assert session in seshs, "session {} is not in the bids folder".format(session)
            else:
                seshs = session
                assert session[0] in seshs, "session {} is not in the bids folder".format(session)

        print("%s%s" % ('Sessions:', seshs))
        print('\n')
        # all the combinations of sessions and tasks that are possible
        bids_dict = dict()
        bids_dict[sub] = {}
        for ses in seshs:
            # the attributes for our modality img
            mod_attributes = [sub, ses]
            # the keys for our modality img
            mod_keys = ['subject', 'session']
            # our query we will use for each modality img
            mod_query = {'datatype': 'dwi'}
            for attr, key in zip(mod_attributes, mod_keys):
                if attr:
                    mod_query[key] = attr
                    
            dwi = layout.get(**merge_dicts(mod_query, {'extension': ['nii', 'nii.gz']}))
            bval = layout.get(**merge_dicts(mod_query, {'extension': 'bval'}))
            bvec = layout.get(**merge_dicts(mod_query, {'extension': 'bvec'}))
            jso = layout.get(**merge_dicts(mod_query, {'extension': 'json'}))

            bids_dict[sub][ses] = {}
            for acq_ix in range(1, len(dwi) + 1):
                bids_dict[sub][ses][acq_ix] = {}
                bids_dict[sub][ses][acq_ix]['dwi_file'] = dwi[acq_ix - 1].path
                bids_dict[sub][ses][acq_ix]['fbval'] = bval[acq_ix - 1].path
                bids_dict[sub][ses][acq_ix]['fbvec'] = bvec[acq_ix - 1].path
                bids_dict[sub][ses][acq_ix]['metadata'] = jso[acq_ix - 1].path
    return bids_dict


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


def collect_sessions(bids_dir, session=None, strict=False, bids_validate=True):
    """
    List the sessions under the BIDS root and checks that sessions
    designated with the participant_label argument exist in that folder.
    Returns the list of sessions to be finally processed.
    Requesting all sessions in a BIDS directory root:
    ...
    """
    from bids import BIDSLayout
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), validate=bids_validate)

    all_sessions = set(layout.get_sessions())

    # Error: bids_dir does not contain subjects
    if not all_sessions:
        raise BIDSError(
            'Could not find session. Please make sure the BIDS data '
            'structure is present and correct. Datasets can be validated online '
            'using the BIDS Validator (http://bids-standard.github.io/bids-validator/).\n'
            'If you are using Docker for Mac or Docker for Windows, you '
            'may need to adjust your "File sharing" preferences.', bids_dir)

    # No --participant-label was set, return all
    if not session:
        return sorted(all_sessions)

    if isinstance(session, int):
        session = [session]

    # Drop ses- prefixes
    session = [ses[4:] if ses.startswith('ses-') else ses for ses in session]
    # Remove duplicates
    session = sorted(set(session))
    # Remove labels not found
    found_label = sorted(set(session) & all_sessions)
    if not found_label:
        raise BIDSError('Could not find session [{}]'.format(
            ', '.join(session)), bids_dir)

    # Warn if some IDs were not found
    notfound_label = sorted(set(session) - all_sessions)
    if notfound_label:
        exc = BIDSError('Some sessions were not found: {}'.format(
            ', '.join(notfound_label)), bids_dir)
        if strict:
            raise exc
        warnings.warn(exc.msg, BIDSWarning)

    return found_label