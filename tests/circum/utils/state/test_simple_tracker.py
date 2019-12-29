from circum.utils.state.simple_tracker import SimpleTracker
from circum.utils.state.tracking import TrackedObject
import copy
import numpy as np
import mock
import datetime


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_simple_update(object_now, tracker_now):
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
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
    ]

    objects = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    tracker = SimpleTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects))

    tracked_objects = tracker.get_objects()

    assert len(tracked_objects) == len(objects)

    for i in range(len(objects)):
        assert any(np.array_equal(obj.pos, objects[i].pos) for obj in tracked_objects)


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_simple_update_stable_association(object_now, tracker_now):
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
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
    ]

    objects = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    tracker = SimpleTracker(deletion_threshold=5)

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
def test_simple_update_10_pct_delta(object_now, tracker_now):
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
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
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

    tracker = SimpleTracker(deletion_threshold=5)

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
def test_simple_update_permanence(object_now, tracker_now):
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
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
        now + datetime.timedelta(seconds=1),  # _track
        now + datetime.timedelta(seconds=1),  # _prune
    ]

    objects = [
        TrackedObject(np.array([0, 0, 0])),
        TrackedObject(np.array([1, 0, 0])),
        TrackedObject(np.array([0, 1, 0])),
        TrackedObject(np.array([1, 1, 0]))
    ]

    tracker = SimpleTracker(deletion_threshold=5)

    tracker.update(copy.deepcopy(objects))

    tracked_objects1 = copy.deepcopy(tracker.get_objects())

    tracker.update([])

    tracked_objects2 = copy.deepcopy(tracker.get_objects())

    assert len(tracked_objects1) == len(tracked_objects2)

    obj_map = {obj.id: obj for obj in tracked_objects1}

    for i in range(len(objects)):
        assert np.array_equal(tracked_objects2[i].pos, obj_map[tracked_objects2[i].id].pos)