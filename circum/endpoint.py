#!/bin/python3

import logging
import socket
import struct
import uuid
from select import select
from threading import Semaphore, Thread
from typing import Callable, Dict, List

import bson

from circum.utils.math import transform_positions
from circum.utils.network import _advertise_server, _get_interface_ip, _open_server, _set_keepalive

import click

import numpy as np

import pkg_resources


logger = logging.getLogger(__name__)
circum_sensors = []
circum_pose_providers = {}


# register pose providers
pose_providers = {entry_point.name: entry_point.load() for
                  entry_point in
                  pkg_resources.iter_entry_points('circum.pose_providers')}


def _transform_tracks(tracking_info: Dict[str, float], pose: List[float]):
    if tracking_info and len(tracking_info["objects"]) > 0:
        positions = np.array(
            [[float(obj["x"]), float(obj["y"]), float(obj["z"]), 1] for obj in tracking_info["objects"]]).T
        positions = transform_positions(positions, pose).T

        for obj, pos in zip(tracking_info["objects"], positions):
            obj["x"] = pos[0]
            obj["y"] = pos[1]
            obj["z"] = pos[2]

    return tracking_info


def _endpoint_thread(endpoint_func: Callable,
                     clients: List[socket.socket],
                     semaphore: Semaphore,
                     pose: List[float],
                     tracker_args: Dict):
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


def _run_server(server_sockets: List[socket.socket],
                reader,
                pose: List[float],
                tracker_args: Dict):
    semaphore = Semaphore()
    clients = []

    # TODO: connect to pose provider service

    # start sensor thread
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


def _start_endpoint(name: str,
                    interface: str,
                    port: int,
                    pose: List[float],
                    tracker_type: str,
                    tracker,
                    tracker_args):

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


def start_endpoint(ctx,
                   tracker_type: str,
                   tracker,
                   tracker_args=None):
    _start_endpoint(ctx.obj["name"],
                    ctx.obj["interface"],
                    ctx.obj["port"],
                    ctx.obj["pose"],
                    tracker_type,
                    tracker,
                    tracker_args)


random_default_name = uuid.uuid1()


@click.group()
@click.option('--name',
              required=False,
              default=str(random_default_name),
              help='The service name. Defaults to a random UUID.')
@click.option('--interface',
              required=False,
              default=None,
              help='The interface to bind to. Defaults to INADDR_ANY')
@click.option('--port',
              required=False,
              default=8301,
              type=int,
              help='The port to bind to. Defaults to 8301')
@click.option('--pose',
              required=False,
              default=None,
              type=float,
              nargs=6,
              help='The pose of the sensor. Expressed in x y z yaw(Rx) pitch(Ry) roll(Rz) order.\n'
                   'Units are meters and degrees.\n'
                   ' +Z is the direction of sensor view. X & Y follow the right hand rule.\n'
                   'If a pose provider is installed, this will override it. Defaults to [0, 0, 0, 0, 0, 0]')
@click.option('--pose-provider',
              required=False,
              default=None,
              type=click.Choice(list(pose_providers.keys()), case_sensitive=False),
              help='The pose provider to use for automatically determining the sensor pose. Defaults to static pose.\n'
                   'NOTE: this is currently unsupported')
@click.option('--debug',
              required=False,
              default=False,
              help='Print debug messages.')
@click.pass_context
def cli(ctx,
        name: str,
        interface: str,
        port: int,
        pose: List[float],
        pose_provider: str,
        debug: bool):

    global logger
    logger = logging.getLogger("circum_endpoint")

    if debug:
        logger.setLevel("DEBUG")

    logger.debug("Loaded Plugins: {}".format(circum_sensors))

    if len(pose) > 0 and pose_provider:
        raise Exception("--pose and --pose-provider cannot both be specified")

    if len(pose) == 0 and pose_provider is None:
        pose = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    ctx.ensure_object(dict)
    ctx.obj["name"] = name
    ctx.obj["interface"] = interface
    ctx.obj["port"] = port
    ctx.obj["pose"] = pose
    ctx.obj["pose_provider"] = pose_provider


# register sensors
for entry_point in pkg_resources.iter_entry_points('circum.sensors'):
    circum_sensors.append(entry_point.name)
    cli.add_command(entry_point.load())


if __name__ == "__main__":
    cli(obj={})
