import logging
import socket
import sys
from ipaddress import AddressValueError, IPv4Address
from typing import List, Tuple

import ifaddr

from zeroconf import ServiceInfo, Zeroconf, get_all_addresses

logger = logging.getLogger(__name__)


def _advertise_server(name: str,
                      server_type: str,
                      ips: List[str],
                      port: int,
                      properties=b"") -> Tuple[Zeroconf, List[ServiceInfo]]:
    desc = properties

    service_type = f"_{server_type}._sub._circum._tcp.local."
    service_name = f"{name}.{service_type}"

    zeroconf = Zeroconf()
    infos = []

    logger.debug(f"registering {service_name} at {ips}:{port}")
    info = ServiceInfo(service_type,
                       service_name,
                       [socket.inet_aton(ip) for ip in ips], port, 0, 0,
                       desc)
    zeroconf.register_service(info)
    infos.append(info)

    print("Registered service, press Ctrl-C to exit...")
    return zeroconf, infos


def _open_server(ips: List[str],
                 port: int) -> List[socket.socket]:
    sockets = []
    socket_ips = []
    for ip in ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, port))
            s.listen()
            sockets.append(s)
            socket_ips.append(ip)
        except Exception:
            # not all ips on all interfaces will be bindable
            logger.warning("Unable to bind to address: {}".format(ip))
    return sockets, socket_ips


def _get_interface_ip(interface: str) -> List[str]:
    if interface is None:
        return get_all_addresses()

    # check if the interface was passed as an IP
    try:
        IPv4Address(interface)
        return [interface]
    except AddressValueError:
        pass

    # pyzeroconf only supports ipv4 so limit to that
    ipv4s = list({
        addr.ip
        for iface in ifaddr.get_adapters()
        for addr in iface.ips
        # Host only netmask 255.255.255.255
        if addr.is_IPv4 and iface.nice_name == interface and addr.network_prefix != 32
    })

    if len(ipv4s) == 0:
        raise Exception("unable to find an ipv4 address for interface")

    return ipv4s


def _set_keepalive(sock: socket.socket,
                   interval=1,
                   retries=5):
    platform = sys.platform
    if platform.startswith('linux'):
        # linux specific keepalive
        logger.debug("setting linux keepalive options")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, interval)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, retries)
    elif platform.startswith('win32'):
        # windows specific keepalive
        logger.debug("setting windows keepalive options")
        interval_ms = interval * 1000
        sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, interval_ms, interval_ms))
        # windows retry count is configured via registry value (max data retransmission attempts) and defaults to 5
    elif platform.startswith('darwin'):
        # osx specific keepalive
        logger.debug("setting OS X keepalive options")
        TCP_KEEPALIVE = 0x10
        TCP_KEEPINTVL = 0x101
        TCP_KEEPCNT = 0x102
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, interval)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPINTVL, interval)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPCNT, retries)
    # we'll leave the defaults on other os's


class ServiceListener:
    def __init__(self,
                 services: List[str]):
        self.sockets = {}
        self.services = services

    def remove_service(self, zeroconf, type_, name):
        logger.debug("Service {} removed".format(name))
        self.sockets.pop(name).close()

    def add_service(self, zeroconf, type_, name):
        info = zeroconf.get_service_info(type_, name)
        if len(self.services) > 0:
            if name not in self.services:
                logger.debug("Name doesn't match skipping {}, service info: {}".format(name, info))
                return
        logger.debug("Service {} added, service info: {}".format(name, info))
        if name not in self.sockets.keys():
            addresses = [str(IPv4Address(address)) for address in info.addresses]
            for address in addresses:
                try:
                    logger.debug("attempting to connects to ({}, {})".format(address, info.port))
                    service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    service_socket.connect((address, info.port))
                    _set_keepalive(service_socket)
                    self.sockets[name] = service_socket
                    logger.debug("connected")
                    break
                except Exception:
                    logger.warn("unable to create socket", exc_info=True)

    def remove(self, service_socket: socket.socket):
        for k, s in self.sockets.items():
            if s == service_socket:
                self.sockets.pop(k).close()
                return

    def get_sockets(self):
        return list(self.sockets.values())
