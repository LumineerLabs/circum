import numpy as np

from scipy.spatial import distance as dist
from datetime import datetime


class TrackedObject:
    def __init__(self, pos: np.ndarray):
        self.pos = pos
        self.last_seen = 0
        self.id = None

    def __eq__(self, other):
        if isinstance(other, TrackedObject):
            return self.id == other.id
        return False


class ObjectTracker:
    def __init__(self, deletion_threshold: int = 5):
        self._objects = OrderedDict()
        self._next = 0
        self._deletion_threshold = deletion_threshold

    def update(self, objects: [TrackedObject]):
        new_objs = self._track(objects)

        for obj in new_objs:
            self._add(obj)

        self._prune()

    def get_objects(self) -> [TrackedObject]:
        return self._objects

    def _prune(self):
        now = datetime.now()
        to_prune = []
        for obj in self._objects:
            if (obj.last_seen - now).total_seconds() > self._deletion_threshold:
                to_prune.append(obj)

        for obj in to_prune:
            self._objects.remove(obj)

    def _register(self, obj: TrackedObject):
        obj.id = self._next
        self._next += 1
        self._objects[obj.id] = obj

    def _track(self, objects: [TrackedObject]):
        pass
