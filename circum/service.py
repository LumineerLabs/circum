#!/bin/python3

import bson
import click
import logging
import select
import socket
import struct

import numpy as np

from circum.utils.network import _advertise_server, _open_server, _set_keepalive, _get_interface_ip, ServiceListener
from circum.utils.state.tracking import TrackedObject
from circum.utils.state.simple import SimpleTracker
from ipaddress import IPv4Address
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
from threading import Semaphore


logger = logging.getLogger(__name__)
size_fmt = "!i"
size_data_len = struct.calcsize(size_fmt)
tracking_state = SimpleTracker()


def _update(update: {}, clients: [socket.socket]):
    people = [TrackedObject(np.asarray([person["x"], person["y"], person["z"]])) for person in update["people"]]
    tracking_state.update(people)
    tracked = tracking_state.get_objects()
    update_dict = {
        "people": [{"x": person.pos[0], "y": person.pos[1], "z": person.pos[2], "id": person.id} for person in tracked]
    }
    logger.debug("update: {}".format(update_dict))
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


def _run_service(server_socket: socket.socket, listener: ServiceBrowser):
    semaphore = Semaphore()
    clients = []
    endpoint_sockets = []

    while True:
        endpoint_sockets = listener.get_sockets()

        # service the sockets
        ready, _, excepted = select.select([server_socket] + endpoint_sockets, [], [], 1)
        for ready_socket in ready:
            if ready_socket == server_socket:
                conn, _ = server_socket.accept()
                _set_keepalive(conn)
                semaphore.acquire()
                clients.append(conn)
                semaphore.release()
            elif ready_socket in endpoint_sockets:
                size_data = ready_socket.recv(size_data_len)
                size = struct.unpack(size_fmt, size_data)[0]
                data = ready_socket.recv(size)
                update_data = bson.loads(data)
                _update(update_data, clients)
        for excepted_socket in excepted:
            if excepted_socket != server_socket:
                listener.remove(excepted_socket)


def _start_service(name: str, interface: str, port: int, listener: ServiceBrowser):
    
    ip = _get_interface_ip(interface)

    logger.debug("opening server on ({},{})".format(ip, port))
    server_socket = _open_server(ip, port)

    zeroconf, info = _advertise_server(name, "service", ip, port)

    try:
        _run_service(server_socket, listener)
    except Exception:
        logging.error("Exception while running server", exc_info=True)
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()


@click.command()
@click.option('--name',
              '-n',
              required=True,
              help='The service name')
@click.option('--interface',
              '-i',
              required=False,
              default=None,
              help='The interface to bind to.')
@click.option('--port',
              '-p',
              required=False,
              default=8300,
              type=int,
              help='The port to bind to.')
@click.option('--endpoint',
              '-e',
              multiple=True,
              type=str,
              help='Names of endpoints to connect to. Can be specified multiple times. ' + 
                   'If no endpoints are specified, all available endpoints will be used.')
def cli(name: str, interface: str, port: int, endpoint: [str]):
    global logger
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger("circum_service")
    zeroconf = Zeroconf()
    endpoint_type = "_endpoint._sub._circum._tcp.local."
    listener = ServiceListener([name + "." + endpoint_type for name in endpoint])
    browser = ServiceBrowser(zeroconf, endpoint_type, listener)
    try:
        _start_service(name, interface, port, listener)
    finally:
        zeroconf.close()


if __name__ == "__main__":
    cli()