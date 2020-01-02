import click
import circum.endpoint
import copy
import logging
import os

from threading import Semaphore, Thread
import importlib.machinery


logger = logging.getLogger(__name__)
tracking_semaphore = None
tracking_info = {"people": []}
vector_info = []
updated = False


def _get_targets(wlbt):
    appStatus, calibrationProcess = wlbt.GetStatus()
    # 5) Trigger: Scan(sense) according to profile and record signals
    # to be available for processing and retrieval.
    wlbt.Trigger()
    # 6) Get action: retrieve the last completed triggered recording
    targets = wlbt.GetTrackerTargets()
    rasterImage, _, _, sliceDepth, power = wlbt.GetRawImageSlice()
    return targets


def _update_thread(wlbt):
    global tracking_info
    global vector_info
    global updated

    while True:
        targets = _get_targets(wlbt)

        tracking_semaphore.acquire()

        if targets and targets is not None:
            tracking_info["people"] = \
                [{"x": target.xPosCm / 100, "y": target.yPosCm / 100, "z": target.zPosCm / 100} for target in targets]
            for i, target in enumerate(targets):
                logger.debug('Target #{}:\nx: {}\ny: {}\nz: {}\namplitude: {}\n'.format(
                    i + 1, target.xPosCm, target.yPosCm, target.zPosCm,
                    target.amplitude))
        else:
            tracking_info["people"] = []

        updated = True

        tracking_semaphore.release()
        # time.sleep(update_interval)


def run_walabot(simulator_args: {}) -> {}:
    global updated
    ret = None
    tracking_semaphore.acquire()
    if updated:
        ret = copy.deepcopy(tracking_info)
        updated = False
    tracking_semaphore.release()
    return ret


def _initialize_api(api_location: str):
    # dll_name = None

    # if os.name == 'nt':
    #     dll_name = 'bin/WalabotAPI.dll'
    # else
    #     dll_name = 'bin/libWalabotAPI.so'

    walabot_py = os.path.join(api_location, 'python/WalabotAPI.py')
    # walabot_dll = path.combine(walabot_api, dll_name)

    wlbt = importlib.machinery.SourceFileLoader('WalabotAPI', walabot_py).load_module()
    wlbt.Init()  # walabot_dll)

    wlbt.Initialize()

    return wlbt


def _connect_to_and_initialize_device(wlbt,
                                      min_r_cm: int = 30,
                                      max_r_cm: int = 200,
                                      res_r_cm: int = 3,
                                      min_theta_deg: int = -15,
                                      max_theta_deg: int = 15,
                                      res_theta_deg: int = 5,
                                      min_phi_deg: int = -60,
                                      max_phi_deg: int = 60,
                                      res_phi_deg: int = 5,
                                      mti_mode: bool = True,
                                      filter_thres: int = 30):
    # 1) Connect : Establish communication with walabot.
    wlbt.ConnectAny()
    # 2) Configure: Set scan profile and arena
    # Set Profile - to Tracker.
    wlbt.SetProfile(wlbt.PROF_TRACKER)
    # Set threshold
    wlbt.SetThreshold(filter_thres)
    # Setup arena - specify it by Cartesian coordinates.
    wlbt.SetArenaR(min_r_cm, max_r_cm, res_r_cm)
    # Sets polar range and resolution of arena (parameters in degrees).
    wlbt.SetArenaTheta(min_theta_deg, max_theta_deg, res_theta_deg)
    # Sets azimuth range and resolution of arena.(parameters in degrees).
    wlbt.SetArenaPhi(min_phi_deg, max_phi_deg, res_phi_deg)
    # Moving Target Identification: standard dynamic-imaging filter
    filterType = wlbt.FILTER_TYPE_MTI if mti_mode else wlbt.FILTER_TYPE_NONE
    wlbt.SetDynamicImageFilter(filterType)
    # 3) Start: Start the system in preparation for scanning.
    wlbt.Start()
    if not mti_mode:  # if MTI mode is not set - start calibrration
        # calibrates scanning to ignore or reduce the signals
        wlbt.StartCalibration()
        while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
            wlbt.Trigger()


@click.command()
@click.option('--api_location',
              required=False,
              type=str,
              default=None,
              help='Location Walabot API was installed in')
@click.pass_context
def walabot(ctx, api_location: str):
    global tracking_semaphore
    tracking_semaphore = Semaphore()
    if api_location is None:
        if os.name == "nt":
            api_location = 'C:/Program Files/Walabot/WalabotSDK/'
        else:
            api_location = '/usr/share/walabot/'
    logger.debug("using Walabot API at {}".format(api_location))

    wlbt = _initialize_api(api_location)

    _connect_to_and_initialize_device(wlbt)

    tracker_thread = Thread(target=_update_thread, args=[wlbt])
    tracker_thread.daemon = True
    tracker_thread.start()
    circum.endpoint.start_endpoint(ctx, "walabot", run_walabot)

    wlbt.Stop()
    wlbt.Disconnect()
    wlbt.Clean()
