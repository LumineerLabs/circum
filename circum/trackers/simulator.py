import click
import circum.endpoint
import copy
import logging
import numpy as np
import random
import time

from threading import Semaphore, Thread
from socket import socket


logger = logging.getLogger(__name__)
tracking_semaphore = None
tracking_info = {"people": []}
vector_info = []
updated = False


def _update_thread(update_interval: float):
    global tracking_info
    global vector_info
    global updated

    while True:
        tracking_semaphore.acquire()
        if len(vector_info) == 0:
            for i in range(1 + int(random.random() * 4)):
                # position
                x = random.random() * 10
                y = random.random() * 10
                z = random.random() * 3
                pos = np.array([x, y, z])

                # velocity
                dx = random.random()
                dy = random.random()
                vel = np.array([dx, dy, 0])
                mag = random.random() * 2
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
        tracking_info["people"] = [{"x": obj["pos"][0], "y": obj["pos"][1], "z": obj["pos"][2]} for obj in vector_info]
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
@click.pass_context
def simulator(ctx, update_interval: float):
    global tracking_semaphore
    tracking_semaphore = Semaphore()
    tracker_thread = Thread(target = _update_thread, args = [update_interval])
    tracker_thread.daemon = True
    tracker_thread.start()
    circum.endpoint.start_endpoint(ctx, "simulator", run_simulator)
