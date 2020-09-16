import circum.utils.math

import numpy as np


def test_rotate_x():
    positions = np.array([[0, 0, 0],
                          [1, 0, 1],
                          [0, 1, 1],
                          [1, 1, 1]])

    sensor_pose = np.array([[0],
                            [0],
                            [0],
                            [90],
                            [0],
                            [0]])

    expected = np.array([[0,  0,  0],  # noqa: E241
                         [0, -1, -1],
                         [1,  0,  1],  # noqa: E241
                         [1,  1,  1]])  # noqa: E241

    transformed = circum.utils.math.transform_positions(positions, sensor_pose)

    assert np.allclose(expected, transformed)


def test_rotate_y():
    positions = np.array([[1, 0, 1],
                          [0, 0, 0],
                          [0, 1, 1],
                          [1, 1, 1]])

    sensor_pose = np.array([[0],
                            [0],
                            [0],
                            [0],
                            [90],
                            [0]])

    expected = np.array([[0,  1,  1],  # noqa: E241
                         [0,  0,  0],  # noqa: E241
                         [-1, 0, -1],
                         [1,  1,  1]])  # noqa: E241

    transformed = circum.utils.math.transform_positions(positions, sensor_pose)

    assert np.allclose(expected, transformed)


def test_rotate_z():
    positions = np.array([[1, 0, 1],
                          [0, 1, 1],
                          [0, 0, 0],
                          [1, 1, 1]])

    sensor_pose = np.array([[0],
                            [0],
                            [0],
                            [0],
                            [0],
                            [90]])

    expected = np.array([[0, -1, -1],
                         [1,  0,  1],  # noqa: E241
                         [0,  0,  0],  # noqa: E241
                         [1,  1,  1]])  # noqa: E241

    transformed = circum.utils.math.transform_positions(positions, sensor_pose)

    assert np.allclose(expected, transformed)


def test_rotate_translate():
    positions = np.array([[1, 0, 0, 1],
                          [0, 1, 0, 1],
                          [0, 0, 1, 1],
                          [1, 1, 1, 1]])

    sensor_pose = np.array([[10],
                            [20],
                            [30],
                            [45],
                            [90],
                            [135]])

    expected = np.array([[10,  9, 10,  9],  # noqa: E241
                         [20, 20, 21, 21],
                         [29, 30, 30, 29],
                         [1,   1,  1,  1]])  # noqa: E241

    transformed = circum.utils.math.transform_positions(positions, sensor_pose)

    assert np.allclose(expected, transformed)
