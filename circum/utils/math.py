import math
from math import cos
from math import sin
from typing import List

import numpy as np


def transform_positions(positions: np.ndarray, sensor_pose: List[float]):
    translation_matrix = np.identity(4)
    translation_matrix[0][3] = sensor_pose[0]
    translation_matrix[1][3] = sensor_pose[1]
    translation_matrix[2][3] = sensor_pose[2]

    theta_x = math.radians(sensor_pose[3])
    theta_y = math.radians(sensor_pose[4])
    theta_z = math.radians(sensor_pose[5])

    rx = np.array([[1,     0,              0,       0],
                   [0, cos(theta_x), -sin(theta_x), 0],
                   [0, sin(theta_x),  cos(theta_x), 0],
                   [0,     0,              0,       1]])

    ry = np.array([[cos(theta_y),  0, sin(theta_y), 0],
                   [0,             1,       0,      0],
                   [-sin(theta_y), 0, cos(theta_y), 0],
                   [0,             0,       0,      1]])

    rz = np.array([[cos(theta_z), -sin(theta_z), 0, 0],
                   [sin(theta_z),  cos(theta_z), 0, 0],
                   [0,                   0,      1, 0],
                   [0,                   0,      0, 1]])

    # first rotate around the sensor's angles, these use the sensor location as the origin
    # then, translate, setting the positions' origin to the system's origin
    return translation_matrix @ (rz @ (ry @ (rx @ positions)))
