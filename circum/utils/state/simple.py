import datetime
import logging
import numpy as np
import scipy.spatial.distance as dist

from circum.utils.state.tracking import TrackedObject, ObjectTracker


logger = logging.getLogger(__name__)


class SimpleTracker(ObjectTracker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _track(self, objects: [TrackedObject]):
        now = datetime.datetime.now()
        tracked_objects = self.get_objects()

        if len(tracked_objects) == 0:
            for obj in objects:
                self._register(obj)
            return objects
        else:
            object_ids = [obj.id for obj in tracked_objects]
            object_positions = [obj.pos for obj in tracked_objects]
            new_positions = [obj.pos for obj in objects]

            distances = dist.cdist(np.asarray(object_positions), np.asarray(new_positions))

            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                id_ = object_ids[row]
                self._objects[id_].pos = new_positions[col]
                self._objects[id_].last_seen = now

                # indicate that we have examined each of the row and
                # column indexes, respectively
                used_rows.add(row)
                used_cols.add(col)

            if distances.shape[0] < distances.shape[1]:
                unused_cols = set(range(0, distances.shape[1])).difference(used_cols)
                return [objects[col] for col in unused_cols]
            else:
                return []
