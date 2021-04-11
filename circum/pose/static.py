import logging
from typing import Dict, List

from circum.pose.provider import PoseProvider

import click


logger = logging.getLogger(__name__)


class StaticPoseProvider(PoseProvider):
    def __init__(self,
                 x: float=0,
                 y: float=0,
                 z: float=0,
                 yaw: float=0,
                 pitch: float=0,
                 roll: float=0):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def get_pose(self) -> List[float]:
        return [
            self.x,
            self.y,
            self.z,
            self.yaw,
            self.pitch,
            self.roll
        ]

@click.command()
@click.option('--pose',
              required=False,
              default=None,
              type=float,
              nargs=6,
              help='The pose of the sensor. Expressed in x y z yaw(Rx) pitch(Ry) roll(Rz) order.\n'
                   'Units are meters and degrees.\n'
                   ' +Z is the direction of sensor view. X & Y follow the right hand rule.\n'
                   'If a pose provider is installed, this will override it. Defaults to [0, 0, 0, 0, 0, 0]')
@click.pass_context
def static_pose(ctx,
                pose: List[float]):
    if "pose_provider" in ctx.obj:
        logger.error("A pose provider was already specified. Only one pose provider can be specified")
        exit(1)

    ctx.obj["pose_provider"] = StaticPoseProvider(*pose)
