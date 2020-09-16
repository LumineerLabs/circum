import bson
import click
import logging
import select
import struct
import time
from threading import Semaphore, Thread

from circum.utils.network import ServiceListener
from matplotlib import pyplot as plt
from matplotlib import animation
from mpl_toolkits import mplot3d
from zeroconf import Zeroconf, ServiceBrowser

logger = logging.getLogger(__name__)
size_fmt = "!i"
size_data_len = struct.calcsize(size_fmt)

semaphore = Semaphore()
data = {"objects": []}

class RenderAnimation(animation.TimedAnimation):
    def __init__(self):
        self.fig = plt.figure()

        self.plt_3d = self.fig.add_subplot(221, projection="3d")
        self.plt_3d.set_title("3D")
        self.plt_3d.plot3D([], [], [], "bo", linestyle='None')

        self.plt_xz = self.fig.add_subplot(222)
        self.plt_xz.set_title("XZ")
        self.plt_xz.set_xlabel("X")
        self.plt_xz.set_ylabel("Z")
        self.data_xz = self.plt_xz.plot([], [], "bo", linestyle='None')

        self.plt_xy = self.fig.add_subplot(223)
        self.plt_xy.set_title("XY")
        self.plt_xy.set_xlabel("X")
        self.plt_xy.set_ylabel("Y")
        self.plt_xy.plot([], [], "bo", linestyle='None')

        self.plt_zy = self.fig.add_subplot(224)
        self.plt_zy.set_title("ZY")
        self.plt_zy.set_xlabel("Z")
        self.plt_zy.set_ylabel("Y")
        self.plt_zy.plot([], [], "bo", linestyle='None')

        self.xlim = [-1, 1]
        self.ylim = [-1, 1]
        self.zlim = [-1, 1]

        plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.5,
                            wspace=0.35)

        animation.TimedAnimation.__init__(self, self.fig, interval=10, blit=True)

    def _plot3d(self, subplt, datax, datay, dataz, ids):
        subplt.axes.set_xlim3d(self.xlim)
        subplt.axes.set_ylim3d(self.ylim)
        subplt.axes.set_zlim3d(self.zlim)

        for text in subplt.texts:
            text.remove()

        subplt.get_lines()[0].set_data(datax, datay)
        subplt.get_lines()[0].set_3d_properties(dataz)

        for i, datum in enumerate(zip(datax, datay, dataz)):
            subplt.text(datum[0], datum[1], datum[2], f' {ids[i]}', size=10, zorder=1, color='k')

    def _plot2d(self, subplt, data1, data2, ids, lim1, lim2):
        subplt.set_xlim(lim1)
        subplt.set_ylim(lim2)

        for text in subplt.texts:
            text.remove()

        subplt.get_lines()[0].set_data(data1, data2)

        for i, datum in enumerate(zip(data1, data2)):
            subplt.annotate(f' {ids[i]}', xy=datum, xycoords='data')

    def _draw_frame(self, _):
        global data
        semaphore.acquire()

        x = [person["x"] for person in data["objects"]]
        y = [person["y"] for person in data["objects"]]
        z = [person["z"] for person in data["objects"]]
        ids = [person["id"] for person in data["objects"]]
        semaphore.release()

        if len(x) > 0:
            minx = min(x)
            maxx = max(x)
            miny = min(y)
            maxy = max(y)
            minz = min(z)
            maxz = max(z)

            self.xlim = [min(self.xlim[0], minx - abs(.1 * minx)), max(self.xlim[1], maxx + abs(.1 * maxx))]
            self.ylim = [min(self.ylim[0], miny - abs(.1 * miny)), max(self.ylim[1], maxy + abs(.1 * maxy))]
            self.zlim = [min(self.zlim[0], minz - abs(.1 * minz)), max(self.zlim[1], maxz + abs(.1 * maxz))]

        self._plot3d(self.plt_3d, x, y, z, ids)
        self._plot2d(self.plt_xz, x, z, ids, self.xlim, self.zlim)
        self._plot2d(self.plt_xy, x, y, ids, self.xlim, self.ylim)
        self._plot2d(self.plt_zy, z, y, ids, self.zlim, self.ylim)

    def new_frame_seq(self):
        return iter(range(1))


def _listen_thread(listener: ServiceListener):
    global data

    service_sockets = []

    while True:
        service_sockets = listener.get_sockets()

        # service the sockets
        if len(service_sockets) > 0:
            ready, _, excepted = select.select(service_sockets, [], [])
            for ready_socket in ready:
                size_data = ready_socket.recv(size_data_len)
                size = struct.unpack(size_fmt, size_data)[0]
                bson_data = ready_socket.recv(size)
                update_data = bson.loads(bson_data)

                semaphore.acquire()
                data = update_data
                semaphore.release()
            for excepted_socket in excepted:
                listener.remove(excepted_socket)
        else:
            time.sleep(.01)


def _start_client(listener: ServiceListener):
    # start listener thread
    tracker_thread = Thread(target=_listen_thread, args=[listener])
    tracker_thread.daemon = True
    tracker_thread.start()

    ani = RenderAnimation()
    plt.show()

@click.command()
@click.option('--service',
              '-s',
              type=str,
              required=True,
              help='Names of the service to connect to.')
def cli(service: str):
    global logger
    logging.basicConfig(level="INFO")
    logger = logging.getLogger("demo_client")
    logger.setLevel("DEBUG")

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
