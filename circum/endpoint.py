#!/bin/python3

import bson
import click
import logging
import socket
import struct

from select import select
from threading import Semaphore, Thread
from typing import Callable
from circum.utils.network import _advertise_server, _open_server, _get_interface_ip, _set_keepalive
from circum.utils.math import transform_positions

# endpoint types
from circum.sensors.simulator import simulator
from circum.sensors.walabot import walabot
import numpy as np


logger = logging.getLogger(__name__)


def _transform_tracks(tracking_info: {}, pose: [float]):
    if tracking_info and len(tracking_info["people"]) > 0:
        positions = np.array([[float(obj["x"]), float(obj["y"]), float(obj["z"]), 1] for obj in tracking_info["people"]]).T
        positions = transform_positions(positions, pose).T

        for obj, pos in zip(tracking_info["people"], positions):
            obj["x"] = pos[0]
            obj["y"] = pos[1]
            obj["z"] = pos[2]

    return tracking_info


def _endpoint_thread(endpoint_func: Callable,
                     clients: [socket.socket],
                     semaphore: Semaphore,
                     pose: [float],
                     tracker_args: {}):
    while True:
        # update tracking info
        tracking_info = _transform_tracks(tracking_info=endpoint_func(tracker_args), pose=pose)
        if tracking_info is not None:
            bson_data = bson.dumps(tracking_info)
            size = len(bson_data)
            size_data = struct.pack("!i", size)
            data = size_data + bson_data

            # update clients
            semaphore.acquire()
            to_remove = []
            for client in clients:
                try:
                    client.sendall(data)
                except Exception:
                    logger.debug("transmit failure", exc_info=True)
                    to_remove.append(client)

            for sock in to_remove:
                clients.remove(sock)
            semaphore.release()


def _run_server(server_sockets: [socket.socket], reader, pose: [float], tracker_args):
    semaphore = Semaphore()
    clients = []

    # start thread
    tracker_thread = Thread(target=_endpoint_thread, args=(reader, clients, semaphore, pose, tracker_args))
    tracker_thread.daemon = True
    tracker_thread.start()

    # listen for connections
    while True:
        ready, _, _ = select(server_sockets, [], [], 1)
        for server_socket in ready:
            conn, addr = server_socket.accept()
            logger.debug("client connected: {}".format(addr))
            _set_keepalive(conn)
            semaphore.acquire()
            clients.append(conn)
            semaphore.release()


def _start_endpoint(name: str, interface: str, port: int, pose: [float], tracker_type: str, tracker, tracker_args):

    ips = _get_interface_ip(interface)

    logger.debug("opening server on ({},{})".format(ips, port))
    server_sockets, ips = _open_server(ips, port)

    zeroconf, infos = _advertise_server(name, "endpoint", ips, port, {"type": tracker_type})

    try:
        _run_server(server_sockets=server_sockets,
                    reader=tracker,
                    pose=pose,
                    tracker_args=tracker_args)
    except Exception:
        logging.error("Exception while running server", exc_info=True)
    finally:
        for info in infos:
            zeroconf.unregister_service(info)
        zeroconf.close()


def start_endpoint(ctx, tracker_type: str, tracker, tracker_args=None):
    _start_endpoint(ctx.obj["name"], ctx.obj["interface"], ctx.obj["port"], ctx.obj["pose"], tracker_type, tracker, tracker_args)


@click.group()
@click.option('--name',
              required=True,
              help='The service name')
@click.option('--interface',
              required=False,
              default=None,
              help='The interface to bind to.')
@click.option('--port',
              required=False,
              default=8300,
              type=int,
              help='The port to bind to.')
@click.option('--pose',
              required=False,
              default=[0, 0, 0, 0, 0, 0],
              type=float,
              nargs=6,
              help='The pose of the sensor. Expressed in x y z yaw(Rx) pitch(Ry) roll(Rz) order.\n'
                   'Units are meters and degrees. +Z is the direction of sensor view. X & Y follow the right hand rule.')
@click.pass_context
def cli(ctx, name: str, interface: str, port: int, pose: [float]):
    global logger
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger("circum_endpoint")
    ctx.ensure_object(dict)
    ctx.obj["name"] = name
    ctx.obj["interface"] = interface
    ctx.obj["port"] = port
    ctx.obj["pose"] = pose


# register endpoints
cli.add_command(simulator)
cli.add_command(walabot)


if __name__ == "__main__":
    cli(obj={})
