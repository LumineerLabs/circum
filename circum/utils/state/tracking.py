import logging
import numpy as np

from scipy.spatial import distance as dist
from datetime import datetime
from collections import OrderedDict


logger = logging.getLogger(__name__)


class TrackedObject:
    def __init__(self, pos: np.ndarray):
        self.pos = pos
        self.last_seen = datetime.now()
        self.id = None

    def __eq__(self, other):
        if isinstance(other, TrackedObject):
            return self.id == other.id
        return False

    def __str__(self):
        return "Tracked Object {{id = {}, pos = {}, last_seen = {}}}".format(self.id, self.pos, self.last_seen)


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
        return self._objects.values()

    def _prune(self):
        now = datetime.now()
        to_prune = []
        for obj in self._objects.values():
            if (obj.last_seen - now).total_seconds() > self._deletion_threshold:
                to_prune.append(obj)

        for obj in to_prune:
            self._objects.pop(obj.id)
            logger.debug("pruned: {}".format(obj))

    def _register(self, obj: TrackedObject):
        obj.id = self._next
        self._next += 1
        self._objects[obj.id] = obj
        logger.debug("registered new object: {}".format(obj))

    def _track(self, objects: [TrackedObject]):
        pass
