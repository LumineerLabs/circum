from circum.utils.state.tracking import TrackedObject, ObjectTracker

class SimpleTracker(ObjectTracker):
    def __init__(self, *args, **kwargs):
        super(SimpleTracker, self).__init__(self, *args, **kwargs)

    def _track(self, objects: [TrackedObject]):
        now = datetime.now()
        object_ids = [obj.id for obj in self._objects.keys()]
        object_positions = [obj.pos for obj in self._objects.values()]

        new_positions = [obj.pos for obj in self._objects.values()]

        distances = dist.cdist(np.array(object_positions), np.array(new_positions))

        rows = distances.min(axis=1).argsort()
        cols = distances.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            id = object_ids[row]
            self._objects[id].pos = new_positions[col]
            self._objects[id].last_seen = now

            # indicate that we have examined each of the row and
            # column indexes, respectively
            used_rows.add(row)
            used_cols.add(col)
