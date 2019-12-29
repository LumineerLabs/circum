from circum.utils.state.kalman.kalmanfilter import KalmanFilter
import numpy as np 
import datetime

class EKF:
    """
    A class that gets sensor measurements from class DataPoint 
    and predicts the next state of the system using an extended Kalman filter algorithm
    The state variables we are considering in this system are the position and velocity
    in x and y cartesian coordinates, in essence there are 4 variables we are tracking.
    """

    def __init__(self, d: {}):
        self.initialized = False
        self.timestamp = None
        self.n = d['number_of_states']
        self.P = d['initial_process_matrix']
        self.F = d['inital_state_transition_matrix']
        self.Q = d['initial_noise_matrix']
        self.R = d['covariance_matrix']
        self.H = d['transition_matrix']
        self.a = d['acceleration_noise']
        self.kalmanFilter = KalmanFilter(self.n)

    def updateQ(self, dt: int):
        dt2 = dt * dt
        dt3 = dt * dt2
        dt4 = dt * dt3
        
        # x, y = self.a

        ula = [dt4 * a_k / 4 for a_k in self.a]
        ura = [dt3 * a_k / 2 for a_k in self.a]
        lla = [dt3 * a_k / 2 for a_k in self.a]
        lra = [dt2 * a_k for a_k in self.a]

        half_n = int(self.n/2)

        ul = np.zeros((half_n, half_n))
        ur = np.zeros((half_n, half_n))
        ll = np.zeros((half_n, half_n))
        lr = np.zeros((half_n, half_n))

        np.fill_diagonal(ul, ula)
        np.fill_diagonal(ur, ura)
        np.fill_diagonal(ll, lla)
        np.fill_diagonal(lr, lra)

        Q = np.concatenate((np.concatenate((ul, ur), axis=1), np.concatenate((ll, lr), axis=1)))
        
        # r11 = dt4 * x / 4
        # r13 = dt3 * x / 2
        # r22 = dt4 * y / 4
        # r24 = dt3 * y / 2
        # r31 = dt3 * x / 2
        # r33 = dt2 * x
        # r42 = dt3 * y / 2
        # r44 = dt2 * y
        
        # Q = np.matrix([[r11,   0, r13,   0],
        #                [  0, r22,   0, r24],
        #                [r31,   0, r33,   0],
        #                [  0, r42,   0, r44]])

        Q = np.matrix(Q)
        
        self.kalmanFilter.set_Q(Q)

    def predict(self, timestamp: datetime.datetime):
        dt = (timestamp - self.timestamp) / datetime.timedelta(seconds=1)
        self.timestamp = timestamp

        self.kalmanFilter.update_F(dt)
        self.updateQ(dt)
        self.kalmanFilter.predict()

    def update(self, data: np.ndarray, timestamp: datetime.datetime):
        z = np.matrix(data).T
        x = self.kalmanFilter.get_x()

        Hx = self.H * x

        self.kalmanFilter.update(z, self.H, Hx, self.R)
        self.timestamp = timestamp

    def predict_update(self, data: np.ndarray, timestamp: datetime.datetime):
        self.predict(timestamp)
        self.update(data, timestamp)

    def start(self, data: np.ndarray, timestamp: datetime.datetime):
        self.timestamp = timestamp
        x = np.matrix(np.concatenate((data, np.array([0, 0, 0])))).T
        self.kalmanFilter.start(x, self.P, self.F, self.Q)
        self.initialized = True
        
    def process(self, data: (float, float), timestamp: int):
        
        if self.initialized: 
            self.update(data, timestamp)
        else:
            self.start(data, timestamp)

    def get(self):
        return self.kalmanFilter.get_x().T