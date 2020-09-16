import numpy as np

from scipy.linalg import inv


class KalmanFilter:
    """
      A class that predicts the next state of the system given sensor measurements
      using the Kalman Filter algorithm
    """

    def __init__(self, n):
        self.n = n
        self.I = np.eye(n)  # noqa: E741
        self.x = None
        self.P = None
        self.F = None
        self.Q = None

    def start(self, x: np.array, P: np.ndarray, F: np.ndarray, Q: np.ndarray):
        self.x = x
        self.P = P
        self.F = F
        self.Q = Q

    def set_Q(self, Q: np.ndarray):
        self.Q = Q

    def update_F(self, dt: float):
        self.F[0, 3], self.F[1, 4], self.F[2, 5] = dt, dt, dt

    def get_x(self):
        return self.x

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z: np.ndarray, H: np.ndarray, Hx: np.ndarray, R: np.ndarray):
        y = z - Hx
        PHt = self.P @ H.T
        S = H @ PHt + R
        K = PHt @ inv(S)

        self.x = self.x + K @ y
        self.P = (self.I - K @ H) @ self.P
