from pykalman import KalmanFilter

import datetime
import datetime
import logging
import numpy as np
import scipy.spatial.distance as dist

from circum.utils.state.tracking import TrackedObject, ObjectTracker
from circum.utils.state.kalman.ekf import EKF
from munkres import Munkres


logger = logging.getLogger(__name__)


class KalmanContext:
    def __init__(self):
        num_states = 6
        half_num_states = int(num_states/2)
        R = np.zeros([half_num_states, half_num_states])
        np.fill_diagonal(R, 0.01)
        R = np.matrix(R)
        # [[0.01,    0,    0],
        #  [   0, 0.01,    0],
        #  [   0,    0, 0.01]])


        H = np.zeros((half_num_states, num_states))
        np.fill_diagonal(H, 1)
        H = np.matrix(H)
            # [[1, 0, 0, 0],
            #  [0, 1, 0, 0]])

        P_vals = [1 for i in range(half_num_states)] + [1000 for i in range(half_num_states)]
        P = np.zeros([num_states, num_states])
        np.fill_diagonal(P, P_vals)
        P = np.matrix(P)
        # [[1, 0,    0,    0],
        #  [0, 1,    0,    0],
        #  [0, 0, 1000,    0],
        #  [0, 0,    0, 1000]])

        Q = np.matrix(np.zeros([num_states, num_states]))
        F = np.matrix(np.eye(num_states))

        d = {
            'number_of_states': 6,
            'initial_process_matrix': P,
            'covariance_matrix': R, 
            'transition_matrix': H,
            'inital_state_transition_matrix': F,
            'initial_noise_matrix': Q, 
            'acceleration_noise': (5, 5, 5)
        }

        self.kf = EKF(d)


class KalmanTracker(ObjectTracker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _associate(self, detected: [TrackedObject], threshold: float = 10) -> ([(TrackedObject, TrackedObject)], [TrackedObject], [TrackedObject]):
        tracked_objects = self.get_objects()
        object_positions = [obj.pos for obj in tracked_objects]
        new_positions = [obj.pos for obj in detected]
        if len(tracked_objects) == 0:
            return [], detected, []
        if len(detected) == 0:
            return [], [], tracked_objects
        distances = dist.cdist(np.asarray(new_positions), np.asarray(object_positions))

        m = Munkres()
        indexes = m.compute(distances)

        associations = []
        associated_detections = [detected[detected_index] for detected_index, _ in indexes]
        associated_tracked = [tracked_objects[tracked_index] for _, tracked_index in indexes]
        unassociated_detections = set(detected) - set(associated_detections)
        unassociated_tracked = set(tracked_objects) - set(associated_tracked)

        # unassociate anything that jumped too far
        for row, column in indexes:
            if distances[row][column] < threshold:
                associations.append((tracked_objects[column], detected[row]))
            else:
                unassociated_detections.add(detected[row])
                unassociated_tracked.add(tracked_objects[column])

        return associations, unassociated_detections, unassociated_tracked

    def _predict(self):
        # update all of the currently tracked objects with their predictions
        tracked_objects = self.get_objects()
        now = self._now()
        for tracked_object in tracked_objects:
            tracked_object.tracking_ctx.kf.predict(now)
            tracked_object.pos =\
                np.array(tracked_object.tracking_ctx.kf.get()[0, 0:int(tracked_object.tracking_ctx.kf.n / 2)])[0]

    def _track(self, objects: [TrackedObject]) -> [TrackedObject]:
        # predict
        self._predict()
    
        associations, unassociated_detections, unassociated_tracked = self._associate(objects)

        now = self._now()

        # add context to new objects
        for detection in unassociated_detections:
            detection.tracking_ctx = KalmanContext()
            detection.tracking_ctx.kf.start(detection.pos, now)

        # predict/update
        for tracked, detection in associations:
            tracked.tracking_ctx.kf.update(detection.pos, now)
            tracked.pos = np.array(tracked.tracking_ctx.kf.get()[0, 0:int(tracked.tracking_ctx.kf.n / 2)])[0]

        return unassociated_detections
