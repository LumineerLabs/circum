#!/bin/python3

import bson
import click
import logging
import struct

import numpy as np

from circum.utils.network import _advertise_server, _open_server
from circum.utils.state.tracking import TrackedObject
from circum.utils.state.simple import SimpleTracker
from ipaddress import IPv4Address
from zeroconf import ServiceBrowser, Zeroconf


size_fmt = "!i"
size_data_len = struct.calcsize(size_fmt)
tracking_state = SimpleTracker()


class MyListener:
    def __init__(self):
        self.sockets = {}

    def remove_service(self, zeroconf, type, name):
        print("Endpoint %s removed" % (name,))
        sockets.pop(name).close()

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Endpoint %s added, service info: %s" % (name, info))
        if name not in self.sockets.keys():
            try:
                endpoint_socket = socket.socket((str(IPv4Address(info.address), info.port)))
                self.sockets[name] = endpoint_socket
            except Exception:
                pass

    def remove(self, service_socket: socket.socket):
        for k, s in self.sockets.iteritems():
            if s == service_socket:
                sockets.pop(k).close()
                return


def _update(update: {}, clients: [socket.socket]):
    people = [TrackedObject(np.ndarray([person["x"], person["y"], person["z"]])) for person in update["people"]]
    tracking_state.update(people)
    tracked = tracking_state.get_objects()
    update_dict = {
        "people", [{"x": person.pos[0], "y": person.pos[1], "z": person.pos[2], "id": person.id} for person in tracked]
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


def _run_service(server_socket: socket.socket, listener: ServiceBrowser):
    semaphore = Semaphore()
    clients = []
    endpoint_sockets = []

    while True:
        endpoint_sockets = listener.get_sockets()

        # service the sockets
        ready, _, excepted = select([server_socket] + endpoint_sockets, [], [], 1)
        for ready_socket in ready:
            if ready_socket == server_socket:
                conn, _ = server_socket.accept()
                semaphore.acquire()
                clients.append(conn)
                semaphore.release()
            elif ready_socket in endpoint_sockets:
                size_data = ready_socket.read(size_data_len)
                size = struct.unpack(size_fmt, size_data)
                data = ready_socket.read(size)
                update_data = bson.loads(data)
                _update(update_data)
        for excepted_socket in excepted:
            if excepted_socket != server_socket:
                listener.remove(excepted_socket)


def _start_endpoint(name: str, interface: str, port: int, listener: ServiceBrowser):
    
    ip = _get_interface_ip(interface)

    server_socket = _open_server(ip, port)

    zeroconf, info = _advertise_server(name, "service", ip, port)

    try:
        _run_service(server_socket, listener)
    except Exception:
        logging.error("Exception while running server", exc_info=True)
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()


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
def cli(name: str, interface: str, port: int):
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_endpoint._sub._circum._tcp.local.", listener)
    try:
        _start_endpoint(name, interface, port, listener)
    finally:
        zeroconf.close()


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger("circum_broker")
    cli(obj={})