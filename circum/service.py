#!/bin/python3
import logging
import select
import socket
import struct
from threading import Semaphore

import bson

from circum.utils.network import ServiceListener, _advertise_server, _get_interface_ip, _open_server, _set_keepalive
from circum.utils.state.kalman_tracker import KalmanTracker as Tracker
from circum.utils.state.tracking import TrackedObject

import click

import numpy as np

from zeroconf import ServiceBrowser, Zeroconf


logger = logging.getLogger(__name__)
size_fmt = "!i"
size_data_len = struct.calcsize(size_fmt)
tracking_state = Tracker()


def _update(update: {}, clients: [socket.socket]):
    people = [TrackedObject(np.asarray([person["x"], person["y"], person["z"]])) for person in update]
    tracking_state.update(people)
    tracked = tracking_state.get_objects()
    update_dict = {
        "objects": [{"x": person.pos[0], "y": person.pos[1], "z": person.pos[2], "id": person.id} for person in tracked]
    }
    bson_data = bson.dumps(update_dict)
    length = len(bson_data)
    size_data = struct.pack(size_fmt, length)
    data = size_data + bson_data

    excepted = []

    for client in clients:
        try:
            client.sendall(data)
        except Exception:
            excepted.append(client)

    for client in excepted:
        clients.remove(client)


def _run_service(server_sockets: [socket.socket], listener: ServiceListener):
    semaphore = Semaphore()
    clients = []

    last_update = {}

    while True:
        endpoint_sockets = listener.get_sockets()

        removed_endpoints = set(last_update.keys()) - set(endpoint_sockets)
        for removed_endpoint in removed_endpoints:
            last_update.pop(removed_endpoint)

        # service the sockets
        ready, _, excepted = select.select(server_sockets + endpoint_sockets, [], [], 1)
        for ready_socket in ready:
            if ready_socket in server_sockets:
                conn, _ = ready_socket.accept()
                _set_keepalive(conn)
                semaphore.acquire()
                clients.append(conn)
                semaphore.release()
            elif ready_socket in endpoint_sockets:
                try:
                    size_data = ready_socket.recv(size_data_len)
                    size = struct.unpack(size_fmt, size_data)[0]
                    data = ready_socket.recv(size)
                    update_data = bson.loads(data)
                    last_update[ready_socket] = update_data["objects"]
                    _update([person for update in last_update.values() for person in update], clients)
                except OSError:
                    if ready_socket not in excepted:
                        excepted.append(ready_socket)
        for excepted_socket in excepted:
            if excepted_socket not in server_sockets:
                listener.remove(excepted_socket)


def _start_service(name: str, interface: str, port: int, listener: ServiceListener):
    ips = _get_interface_ip(interface)

    logger.debug("opening server on ({},{})".format(ips, port))
    server_sockets, ips = _open_server(ips, port)

    zeroconf, infos = _advertise_server(name, "service", ips, port)

    try:
        _run_service(server_sockets, listener)
    except Exception:
        logging.error("Exception while running server", exc_info=True)
    finally:
        for info in infos:
            zeroconf.unregister_service(info)
        zeroconf.close()


@click.command()
@click.option('--name',
              '-n',
              required=True,
              help='The service name. This must be provided.')
@click.option('--interface',
              '-i',
              required=False,
              default=None,
              help='The interface to bind to. Defaults to INADDR_ANY.')
@click.option('--port',
              '-p',
              required=False,
              default=8300,
              type=int,
              help='The port to bind to. Defaults 8300.')
@click.option('--endpoint',
              '-e',
              multiple=True,
              type=str,
              help='Names of endpoints to connect to. Can be specified multiple times. ' +
                   'If no endpoints are specified, all discovered endpoints will be used.')
def cli(name: str, interface: str, port: int, endpoint: [str]):
    global logger
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger("circum_service")
    zeroconf = Zeroconf()
    endpoint_type = "_endpoint._sub._circum._tcp.local."
    listener = ServiceListener([name + "." + endpoint_type for name in endpoint])
    browser = ServiceBrowser(zeroconf, endpoint_type, listener)  # noqa
    try:
        _start_service(name, interface, port, listener)
    finally:
        zeroconf.close()


if __name__ == "__main__":
    cli()
