import socket


def _advertise_server(name: str, type: str, ip: str, port: int):
    desc = {}

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