"""
Eversolo driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice
from intg_eversolo.media_player import EversoloMediaPlayer
from intg_eversolo.sensor import (
    EversoloSourceSensor,
    EversoloStateSensor,
    EversoloVolumeSensor,
)

_LOG = logging.getLogger(__name__)


class EversoloDriver(BaseIntegrationDriver[EversoloDevice, EversoloConfig]):
    """Eversolo integration driver."""

    def __init__(self):
        super().__init__(
            device_class=EversoloDevice,
            entity_classes=[
                EversoloMediaPlayer,
                # Sensors temporarily disabled due to framework subscription issues
                # TODO: Re-enable sensors once proper entity lifecycle pattern is identified
                # lambda cfg, dev: [
                #     EversoloStateSensor(cfg, dev),
                #     EversoloSourceSensor(cfg, dev),
                #     EversoloVolumeSensor(cfg, dev),
                # ],
            ],
            driver_id="eversolo",
        )
