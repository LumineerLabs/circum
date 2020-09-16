import copy
import logging
import random
import time
from threading import Semaphore, Thread

import click

import numpy as np


logger = logging.getLogger(__name__)
tracking_semaphore = None
tracking_info = {"objects": []}
vector_info = []
updated = False


def _update_thread(update_interval: float, num_objects: int):
    global tracking_info
    global vector_info
    global updated

    while True:
        tracking_semaphore.acquire()
        if len(vector_info) == 0:
            if num_objects == 0:
                num_objects = 1 + int(random.random() * 4)  # noqa S311
            for _ in range(num_objects):
                # position
                x = random.random() * 10  # noqa S311
                y = random.random() * 3  # noqa S311
                z = random.random() * 10  # noqa S311
                pos = np.array([x, y, z])

                # velocity
                dx = random.random()  # noqa S311
                dy = 0
                dz = random.random()  # noqa S311
                vel = np.array([dx, dy, dz])
                mag = random.random() * 2  # noqa S311
                vel = mag * vel / np.linalg.norm(vel)

                vector_info.append({"pos": pos, "vel": vel})
        else:
            # update
            for obj in vector_info:
                for i in range(len(obj["vel"])):
                    if obj["pos"][i] > 10 or obj["pos"][i] < 0:
                        obj["vel"][i] = -obj["vel"][i]
                obj["pos"] += obj["vel"]

        # track
        tracking_info["objects"] = [{"x": obj["pos"][0], "y": obj["pos"][1], "z": obj["pos"][2]} for obj in vector_info]
        updated = True

        tracking_semaphore.release()
        time.sleep(update_interval)


def run_simulator(simulator_args: {}) -> {}:
    global updated
    ret = None
    tracking_semaphore.acquire()
    if updated:
        ret = copy.deepcopy(tracking_info)
        updated = False
    tracking_semaphore.release()
    return ret


@click.command()
@click.option('--update_interval',
              required=False,
              type=float,
              default=.5,
              help='Rate to send updates.')
@click.option('--num_objects',
              required=False,
              type=int,
              default=4,
              help='Number of objects to simulate')
@click.pass_context
def simulator(ctx, update_interval: float, num_objects: int):
    import circum.endpoint
    global tracking_semaphore
    tracking_semaphore = Semaphore()
    logger.debug("simulating {} objects at {} Hz".format(num_objects, 1/update_interval))
    tracker_thread = Thread(target=_update_thread, args=[update_interval, num_objects])
    tracker_thread.daemon = True
    tracker_thread.start()
    circum.endpoint.start_endpoint(ctx, "simulator", run_simulator)
