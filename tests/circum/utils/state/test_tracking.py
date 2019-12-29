from circum.utils.state.tracking import TrackedObject, ObjectTracker
from datetime import datetime, timedelta
import numpy as np
from collections import OrderedDict
import copy
import mock


def test_TrackedObject_creation():
    time_thresh = timedelta(milliseconds=100)
    to = TrackedObject(np.array([0, 1, 2]))
    dt = datetime.now()
    assert np.array_equal(to.pos, np.array([0, 1, 2]))
    assert dt - to.last_seen < time_thresh
    assert to.id is None
    assert to.tracking_ctx is None
    assert dt - to.created < time_thresh
    assert to.history == []


def test_TrackedObject_equal():
    to1 = TrackedObject(np.array([0, 1, 2]))
    to2 = TrackedObject(np.array([0, 1, 2]))

    to1.id = 1
    to2.id = 1

    assert to1 == to2


def test_TrackedObject_notequal_different_ids():
    to1 = TrackedObject(np.array([0, 1, 2]))
    to2 = TrackedObject(np.array([0, 1, 2]))

    to1.id = 1
    to2.id = 2

    assert to1 != to2


def test_TrackedObject_notequal_different_types():
    to1 = TrackedObject(np.array([0, 1, 2]))
    to2 = object()

    assert to1 != to2


def test_ObjectTracker_creation():
    ot = ObjectTracker(5)
    assert isinstance(ot._objects, OrderedDict)
    assert len(ot._objects) == 0
    assert ot._next == 0
    assert ot._deletion_threshold == 5


def test_ObjectTracker_update():
    ot = ObjectTracker(5)
    tos = [TrackedObject(np.array([0, 1, 2]))]
    ot.update(tos)
    assert len(ot._objects) == 1
    assert ot._objects[0].id == 0


def test_ObjectTracker_update_multiple():
    ot = ObjectTracker(5)
    tos = [TrackedObject(np.array([0, 1, 2])), TrackedObject(np.array([0, 1, 2]))]
    ot.update(tos)
    assert len(ot._objects) == 2
    assert ot._objects[0].id == 0
    assert ot._objects[1].id == 1


def test_ObjectTracker_prune_too_old():
    dt = datetime.now()
    ot = ObjectTracker(5)
    tos = [TrackedObject(np.array([0, 1, 2])), TrackedObject(np.array([0, 1, 2]))]
    ot.update(tos)

    assert len(ot._objects) == 2

    ot._objects[1].created = dt - timedelta(seconds=100)
    ot._objects[1].last_seen = dt - timedelta(seconds=6)

    ot.update([])

    assert len(ot._objects) == 1


@mock.patch("circum.utils.state.tracking.ObjectTracker._now")
@mock.patch("circum.utils.state.tracking.TrackedObject._now")
def test_ObjectTracker_prune_too_invisible(object_now, tracker_now):
    now = datetime.now()

    object_now.side_effect = [
        now,  # create
        now,  # create
        now,  # create
        now,  # create
    ]

    tracker_now.side_effect = [
        # update 1
        now,  # _prune
        # update 2
        now + timedelta(seconds=10),  # _prune
    ]

    ot = ObjectTracker(5)
    tos = [TrackedObject(np.array([0, 1, 2])), TrackedObject(np.array([0, 1, 2]))]

    ot.update(copy.deepcopy(tos))
    assert len(ot._objects) == 2

    ot._objects[0].last_seen = now + timedelta(seconds=9)
    ot._objects[1].last_seen = now + timedelta(seconds=3.9)

    ot.update([])
    assert len(ot._objects) == 1
