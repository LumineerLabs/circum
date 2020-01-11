import bson
import click
import logging
import select
import struct
import time

from circum.utils.network import ServiceListener
from matplotlib import pyplot as plt
from zeroconf import Zeroconf, ServiceBrowser

logger = logging.getLogger(__name__)
size_fmt = "!i"
size_data_len = struct.calcsize(size_fmt)

fig = plt.figure()
ax = fig.add_subplot(111)

xlim = [1, 1]
ylim = [1, 1]


def _update(data: {}):
    global xlim
    global ylim

    x = [person["x"] for person in data["objects"]]
    y = [person["y"] for person in data["objects"]]
    ids = [person["id"] for person in data["objects"]]

    if len(x) > 0:
        minx = min(x)
        maxx = max(x)
        miny = min(y)
        maxy = max(x)

        ylim = [min(ylim[0], miny - abs(.1 * miny)), max(ylim[1], maxy + abs(.1 * maxy))]
        xlim = [min(xlim[0], minx - abs(.1 * minx)), max(xlim[1], maxx + abs(.1 * maxx))]

    ax.cla()

    axes = plt.gca()
    axes.set_xlim(xlim)
    axes.set_ylim(ylim)

    plt.plot(x, y, "bo", linestyle='None')
    for i, xy in enumerate(zip(x, y)):
        ax.annotate('{}'.format(ids[i]), xy=xy, textcoords='data')

    plt.grid()
    plt.draw()
    plt.pause(.01)


def _start_client(listener: ServiceListener):
    service_sockets = []

    while True:
        service_sockets = listener.get_sockets()

        # service the sockets
        if len(service_sockets) > 0:
            ready, _, excepted = select.select(service_sockets, [], [])
            for ready_socket in ready:
                size_data = ready_socket.recv(size_data_len)
                size = struct.unpack(size_fmt, size_data)[0]
                data = ready_socket.recv(size)
                update_data = bson.loads(data)
                _update(update_data)
            for excepted_socket in excepted:
                listener.remove(excepted_socket)
        else:
            time.sleep(.1)


@click.command()
@click.option('--service',
              '-s',
              type=str,
              required=True,
              help='Names of the service to connect to.')
def cli(service: str):
    global logger
    logging.basicConfig(level="DEBUG")
    logger = logging.getLogger("demo_client")

    zeroconf = Zeroconf()
    endpoint_type = "_service._sub._circum._tcp.local."
    listener = ServiceListener([service + "." + endpoint_type])
    browser = ServiceBrowser(zeroconf, endpoint_type, listener)  # noqa

    try:
        _start_client(listener)
    finally:
        zeroconf.close()


if __name__ == "__main__":
    cli()
