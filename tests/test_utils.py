#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dmripreproc` package."""

import numpy as np

from dmripreproc.utils import is_hemispherical


def uniform_points_on_sphere(npoints=1, hemisphere=True, rotate=(0, 0, 0)):
    """Generate random uniform points on a unit (hemi)sphere."""
    r = 1.0
    if hemisphere:
        theta = np.random.uniform(0, np.pi / 2, npoints)
    else:
        theta = np.random.uniform(0, np.pi, npoints)
    phi = np.random.uniform(0, 2 * np.pi, npoints)

    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)

    vecs = np.stack([x, y, z])

    rot_x = np.array([
        [1.0, 0.0, 0.0],
        [0.0, np.cos(rotate[0]), -np.sin(rotate[0])],
        [0.0, np.sin(rotate[0]), np.cos(rotate[0])]
    ])

    rot_y = np.array([
        [np.cos(rotate[1]), 0.0, np.sin(rotate[1])],
        [0.0, 1.0, 0.0],
        [-np.sin(rotate[1]), 0.0, np.cos(rotate[1])]
    ])

    rot_z = np.array([
        [np.cos(rotate[2]), -np.sin(rotate[2]), 0.0],
        [np.sin(rotate[2]), np.cos(rotate[2]), 0.0],
        [0.0, 0.0, 1.0]
    ])

    vecs = np.dot(rot_z, np.dot(rot_y, np.dot(rot_x, vecs)))

    return vecs.transpose()


def test_is_hemispherical():
    vecs = uniform_points_on_sphere(
        npoints=100,
        hemisphere=True,
        rotate=(np.random.uniform(0, np.pi),
                np.random.uniform(0, np.pi),
                np.random.uniform(0, np.pi))
    )

    assert is_hemispherical(vecs)[0]
    vecs = uniform_points_on_sphere(npoints=100, hemisphere=False)
    assert not is_hemispherical(vecs)[0]
