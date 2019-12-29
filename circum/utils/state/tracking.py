import logging
import numpy as np

from datetime import datetime
from collections import OrderedDict


logger = logging.getLogger(__name__)


class TrackedObject:
    def __init__(self, pos: np.ndarray):
        self.pos = pos
        self.last_seen = self._now()
        self.id = None
        self.tracking_ctx = None
        self.created = self._now()
        self.history = []

    def __hash__(self):
        return int(id(self) / 16)

    def __eq__(self, other):
        if isinstance(other, TrackedObject):
            return self.id == other.id
        return False

    def __str__(self):
        return "Tracked Object {{id = {}, pos = {}, last_seen = {}}}".format(self.id, self.pos, self.last_seen)

    def _now(self):
        return datetime.now()


class ObjectTracker:
    def __init__(self, deletion_threshold: int = 5):
        self._objects = OrderedDict()
        self._next = 0
        self._deletion_threshold = deletion_threshold

    def update(self, objects: [TrackedObject]):
        new_objs = self._track(objects)

        for obj in new_objs:
            self._register(obj)

        self._prune()

    def get_objects(self) -> [TrackedObject]:
        return list(self._objects.values())

    def _prune(self):
        now = self._now()
        to_prune = []
        for obj in self._objects.values():
            time_since_last_seen = (now - obj.last_seen).total_seconds()
            time_since_created = (now - obj.created).total_seconds()
            if time_since_last_seen > self._deletion_threshold:
                # delete if it has been too long since we've seen the object
                to_prune.append(obj)
            elif time_since_created > self._deletion_threshold and time_since_last_seen / time_since_created > .6:
                # delete if we haven't seen most its life
                to_prune.append(obj)

        for obj in to_prune:
            self._objects.pop(obj.id)
            logger.debug("pruned: {}".format(obj))

    def _register(self, obj: TrackedObject):
        obj.id = self._get_next_object_id()
        self._objects[obj.id] = obj
        logger.debug("registered new object: {}".format(obj))

    def _track(self, objects: [TrackedObject]) -> [TrackedObject]:
        return objects

    def _get_next_object_id(self) -> int:
        id = self._next
        self._next += 1
        return id

    def _now(self) -> datetime:
        return datetime.now()
