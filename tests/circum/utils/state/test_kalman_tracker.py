import copy
import datetime

from circum.utils.state.kalman_tracker import KalmanTracker
from circum.utils.state.tracking import TrackedObject

import mock

import numpy as np


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_kalman_update(object_now, tracker_now):
    now = datetime.datetime.now()

    object_now.side_effect = [
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
    ]

    tracker_now.side_effect = [
        now + datetime.timedelta(seconds=1),  # _predict
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
    ]

    objects = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    tracker = KalmanTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects))

    tracked_objects = tracker.get_objects()

    assert len(tracked_objects) == len(objects)

    for i in range(len(objects)):
        assert any(np.array_equal(obj.pos, objects[i].pos) for obj in tracked_objects)


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_kalman_update_stable_association(object_now, tracker_now):
    now = datetime.datetime.now()

    object_now.side_effect = [
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
    ]

    tracker_now.side_effect = [
        now + datetime.timedelta(seconds=1),  # _predict
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=2),  # _predict
        now + datetime.timedelta(seconds=2),  # _track
        now + datetime.timedelta(seconds=2),  # _prune
    ]

    objects = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    tracker = KalmanTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects))

    tracked_objects1 = copy.deepcopy(tracker.get_objects())

    tracker.update(copy.deepcopy(objects))

    tracked_objects2 = copy.deepcopy(tracker.get_objects())

    assert len(tracked_objects1) == len(tracked_objects2)

    obj_map = {obj.id: obj for obj in tracked_objects1}

    for i in range(len(objects)):
        assert np.array_equal(tracked_objects2[i].pos, obj_map[tracked_objects2[i].id].pos)


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_kalman_update_10_pct_delta(object_now, tracker_now):
    '''
    This tests the case where an update is closer to the a different object in the previous test_kalman_update
    '''
    now = datetime.datetime.now()

    object_now.side_effect = [
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
        now,  # create
    ]

    tracker_now.side_effect = [
        now + datetime.timedelta(seconds=1),  # _predict
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=2),  # _predict
        now + datetime.timedelta(seconds=2),  # _track
        now + datetime.timedelta(seconds=2),  # _prune
    ]

    objects1 = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    objects2 = [
        TrackedObject(np.array([0.1, 0, 0])),
        TrackedObject(np.array([0.9, 0, 0])),
        TrackedObject(np.array([0.1, 1, 0])),
        TrackedObject(np.array([0.9, 1, 0]))
    ]

    tracker = KalmanTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects1))

    tracked_objects1 = copy.deepcopy(tracker.get_objects())

    tracker.update(copy.deepcopy(objects2))

    tracked_objects2 = copy.deepcopy(tracker.get_objects())

    assert len(tracked_objects1) == len(tracked_objects2)

    obj_map = {obj.id: obj for obj in tracked_objects2}

    for i in range(len(objects1)):
        assert np.linalg.norm(tracked_objects1[i].pos - obj_map[tracked_objects1[i].id].pos) < .2


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_kalman_update_crossover_tricky(object_now, tracker_now):
    now = datetime.datetime.now()

    object_now.side_effect = [
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
    ]

    tracker_now.side_effect = [
        now + datetime.timedelta(seconds=1),  # _predict
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=2),  # _predict
        now + datetime.timedelta(seconds=2),  # _track
        now + datetime.timedelta(seconds=2),  # _prune
        now + datetime.timedelta(seconds=3),  # _predict
        now + datetime.timedelta(seconds=3),  # _track
        now + datetime.timedelta(seconds=3),  # _prune
    ]

    objects1 = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    objects2 = [
        TrackedObject(np.array([0, .3, 0])),
        TrackedObject(np.array([1, .3, 0])),
        TrackedObject(np.array([0, .7, 0])),
        TrackedObject(np.array([1, .7, 0]))
    ]

    objects3 = [
        TrackedObject(np.array([0, .6, 0])),
        TrackedObject(np.array([1, .6, 0])),
        TrackedObject(np.array([0, .4, 0])),
        TrackedObject(np.array([1, .4, 0]))
    ]

    tracker = KalmanTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects1))

    tracked_objects_start = copy.deepcopy(tracker.get_objects())

    tracker.update(copy.deepcopy(objects2))

    tracker.update(copy.deepcopy(objects3))

    tracked_objects_final = copy.deepcopy(tracker.get_objects())

    assert len(tracked_objects_start) == len(tracked_objects_final)

    index_map = {}

    for obj in tracked_objects_start:
        index = [i for i, elem in enumerate(objects1) if np.array_equal(elem.pos, obj.pos)][0]
        index_map[obj.id] = index

    for obj in tracked_objects_final:
        index = index_map[obj.id]
        assert np.all(abs(objects3[index].pos - obj.pos) < .001)


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_kalman_update_predictive_tracking(object_now, tracker_now):
    now = datetime.datetime.now()

    object_now.side_effect = [
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now,  # create 1
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=1),  # create 2
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
        now + datetime.timedelta(seconds=2),  # create 3
    ]

    tracker_now.side_effect = [
        now + datetime.timedelta(seconds=1),  # _predict
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=2),  # _predict
        now + datetime.timedelta(seconds=2),  # _track
        now + datetime.timedelta(seconds=2),  # _prune
        now + datetime.timedelta(seconds=3),  # _predict
        now + datetime.timedelta(seconds=3),  # _track
        now + datetime.timedelta(seconds=3),  # _prune
    ]

    objects1 = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    objects2 = [
        TrackedObject(np.array([0, .3, 0])),
        TrackedObject(np.array([1, .3, 0])),
        TrackedObject(np.array([0, .7, 0])),
        TrackedObject(np.array([1, .7, 0]))
    ]

    objects3 = [
        TrackedObject(np.array([0, .6, 0])),
        TrackedObject(np.array([1, .6, 0])),
        TrackedObject(np.array([0, .4, 0])),
        TrackedObject(np.array([1, .4, 0]))
    ]

    tracker = KalmanTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects1))

    tracked_objects_start = copy.deepcopy(tracker.get_objects())

    tracker.update(copy.deepcopy(objects2))

    tracker.update([])

    tracked_objects_final = copy.deepcopy(tracker.get_objects())

    assert len(tracked_objects_start) == len(tracked_objects_final)

    index_map = {}

    for obj in tracked_objects_start:
        index = [i for i, elem in enumerate(objects1) if np.array_equal(elem.pos, obj.pos)][0]
        index_map[obj.id] = index

    for obj in tracked_objects_final:
        index = index_map[obj.id]
        assert np.all(abs(objects3[index].pos - obj.pos) < .001)
