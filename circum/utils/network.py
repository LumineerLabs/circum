import socket
import sys

from zeroconf import Zeroconf, ServiceInfo


def _advertise_server(name: str, type: str, ip: str, port: int, properties=b""):
    desc = properties

    service_type = "_{}._sub._circum._tcp.local.".format(type)
    service_name = "{}.{}".format(name, service_type)

    print("registering ({} {})".format(service_type, service_name))

    info = ServiceInfo(service_type,
                       service_name,
                       socket.inet_aton(ip), port, 0, 0,
                       desc, "{}.local.".format(name))

    zeroconf = Zeroconf()
    print("Registration of a service, press Ctrl-C to exit...")
    zeroconf.register_service(info)

    return zeroconf, info


def _open_server(ip: str, port: int) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen()
    return s


def _get_interface_ip(interface: str) -> str:
    if interface is None:
        # INADDR_ANY
        return "0.0.0.0"

    # pyzeroconf only supports ipv4 so limit to that
    ipv4s = [ip.ip for ip in ifaddr.get_adapters()[interface].ips if isinistance(ip.ip, str)]

    if len(ipv4s) == 0:
        raise Exception("unable to find an ipv4 address for interface")

    return ipv4s[0]


def _set_keepalive(sock: socket.socket, interval=1, retries=5):
    platform = sys.platform
    if platform.startswith('linux'):
        # linux specific keepalive
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, interval)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, retries)
    elif platform.startswith('win32'):
        # windows specific keepalive
        interval_ms = interval * 1000
        sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, interval_ms, interval_ms))
        # windows retry count is configured via registry value (max data retransmission attempts) and defaults to 5
    elif platform.startswith('darwin'):
        # osx specific keepalive
        TCP_KEEPALIVE = 0x10
        TCP_KEEPINTVL = 0x101
        TCP_KEEPCNT = 0x102
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, interval)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPINTVL, interval)
        sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPCNT, retries)
    # we'll leave the defaults on other os's