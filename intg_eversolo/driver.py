"""
Eversolo driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice
from intg_eversolo.light import EversoloDisplayBrightnessLight, EversoloKnobBrightnessLight
from intg_eversolo.media_player import EversoloMediaPlayer
from intg_eversolo.remote import EversoloRemote
from intg_eversolo.sensor import (
    EversoloActiveOutputSensor,
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
                EversoloRemote,
                lambda cfg, dev: [
                    EversoloStateSensor(cfg, dev),
                    EversoloSourceSensor(cfg, dev),
                    EversoloVolumeSensor(cfg, dev),
                    EversoloActiveOutputSensor(cfg, dev),
                ],
                lambda cfg, dev: [
                    EversoloDisplayBrightnessLight(cfg, dev),
                    EversoloKnobBrightnessLight(cfg, dev),
                ],
            ],
            driver_id="eversolo",
        )
