"""
BIDS-functions to return inputs for the run.py functions.

"""
from glob import glob
import os

def get_BIDS_files(subject_id, bids_input_directory):
    if not subject_id:
        subjects = glob(os.path.join(bids_input_directory, "*"))
