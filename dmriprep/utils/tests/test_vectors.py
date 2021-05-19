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
"""Test vector utilities."""
import pytest
import numpy as np
import nibabel as nb
from dmriprep.utils import vectors as v
from collections import namedtuple


def test_corruption(tmpdir, dipy_test_data, monkeypatch):
    """Check whether b-value rescaling is operational."""
    tmpdir.chdir()

    bvals = dipy_test_data["bvals"]
    bvecs = dipy_test_data["bvecs"]

    dgt = v.DiffusionGradientTable(**dipy_test_data)
    affine = dgt.affine.copy()

    # Test vector hemisphere coverage
    assert np.all(dgt.pole == [0.0, 0.0, 0.0])

    dgt.to_filename("dwi.tsv")
    dgt = v.DiffusionGradientTable(rasb_file="dwi.tsv")
    assert dgt.normalized is False
    with pytest.raises(TypeError):
        dgt.to_filename("dwi", filetype="fsl")  # You can do this iff the affine is set.

    # check accessing obj.affine
    dgt = v.DiffusionGradientTable(dwi_file=namedtuple("Affine", ["affine"])(affine))
    assert np.all(dgt.affine == affine)
    dgt = v.DiffusionGradientTable(dwi_file=affine)
    assert np.all(dgt.affine == affine)

    # Perform various corruption checks using synthetic corrupted bval-bvec.
    dgt = v.DiffusionGradientTable()
    dgt.bvecs = bvecs
    with pytest.raises(ValueError):
        dgt.bvals = bvals[:-1]

    dgt = v.DiffusionGradientTable()
    dgt.bvals = bvals
    with pytest.raises(ValueError):
        dgt.bvecs = bvecs[:-1]

    # Missing b0
    bval_no_b0 = bvals.copy()
    bval_no_b0[0] = 51
    with pytest.raises(ValueError):
        dgt = v.DiffusionGradientTable(
            dwi_file=dipy_test_data["dwi_file"],
            bvals=bval_no_b0,
            bvecs=bvecs,
            raise_inconsistent=True,
        )
    bvec_no_b0 = bvecs.copy()
    bvec_no_b0[0] = np.array([1.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        dgt = v.DiffusionGradientTable(
            dwi_file=dipy_test_data["dwi_file"],
            bvals=bvals,
            bvecs=bvec_no_b0,
            raise_inconsistent=True,
        )

    # Corrupt b0 b-val
    bval_odd_b0 = bvals.copy()
    bval_odd_b0[bval_odd_b0 == 0] = 1e-8
    dgt = v.DiffusionGradientTable(
        dwi_file=dipy_test_data["dwi_file"], bvals=bval_odd_b0, bvecs=bvecs
    )
    assert dgt.bvals[0] == 0

    # Corrupt b0 b-vec
    bvec_odd_b0 = bvecs.copy()
    b0mask = np.all(bvec_odd_b0 == 0, axis=1)
    bvec_odd_b0[b0mask] = [10, 10, 10]
    dgt = v.DiffusionGradientTable(
        dwi_file=dipy_test_data["dwi_file"], bvals=bvals, bvecs=bvec_odd_b0
    )
    assert np.all(dgt.bvecs[b0mask] == [0.0, 0.0, 0.0])

    # Test normalization
    bvecs_factor = 2.0 * bvecs
    dgt = v.DiffusionGradientTable(
        dwi_file=dipy_test_data["dwi_file"], bvals=bvals, bvecs=bvecs_factor
    )
    assert -1.0 <= np.max(np.abs(dgt.gradients[..., :-1])) <= 1.0
    assert dgt.normalized is True

    def mock_func(*args, **kwargs):
        return "called!"

    with monkeypatch.context() as m:
        m.setattr(v, "normalize_gradients", mock_func)
        assert dgt.normalize() is None  # Test nothing is executed.

    with monkeypatch.context() as m:
        m.setattr(v, "bvecs2ras", mock_func)
        assert dgt.generate_vecval() is None  # Test nothing is executed.

    # Miscellaneous tests
    with pytest.raises(ValueError):
        dgt.to_filename("path", filetype="mrtrix")


def test_b0mask_from_data(tmp_path):
    """Check the estimation of bzeros using the dwi data."""

    highb = np.random.normal(100, 5, size=(40, 40, 40, 99))
    mask_file = tmp_path / "mask.nii.gz"

    # Test 1: no lowb
    dwi_file = tmp_path / "only_highb.nii.gz"
    nb.Nifti1Image(highb.astype(float), np.eye(4), None).to_filename(dwi_file)
    nb.Nifti1Image(np.ones((40, 40, 40), dtype=np.uint8), np.eye(4), None).to_filename(
        mask_file
    )

    assert v.b0mask_from_data(dwi_file, mask_file).sum() == 0

    # Test 1: one lowb
    lowb = np.random.normal(400, 50, size=(40, 40, 40, 1))
    dwi_file = tmp_path / "dwi.nii.gz"
    nb.Nifti1Image(
        np.concatenate((lowb, highb), axis=3).astype(float), np.eye(4), None
    ).to_filename(dwi_file)
    assert v.b0mask_from_data(dwi_file, mask_file).sum() == 1
