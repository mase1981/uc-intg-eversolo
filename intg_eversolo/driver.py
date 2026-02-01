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
from intg_eversolo.remote_a6 import EversoloRemoteA6
from intg_eversolo.remote_a8 import EversoloRemoteA8
from intg_eversolo.remote_a10 import EversoloRemoteA10
from intg_eversolo.select import (
    EversoloInputSelect,
    EversoloSpectrumModeSelect,
    EversoloVUModeSelect,
)
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
                lambda cfg, dev: (
                    EversoloRemoteA6(cfg, dev) if cfg.model == "DMP-A6" else
                    EversoloRemoteA8(cfg, dev) if cfg.model == "DMP-A8" else
                    EversoloRemoteA10(cfg, dev)
                ),
                lambda cfg, dev: [
                    EversoloStateSensor(cfg, dev),
                    EversoloSourceSensor(cfg, dev),
                    EversoloVolumeSensor(cfg, dev),
                    EversoloActiveOutputSensor(cfg, dev),
                ],
                lambda cfg, dev: [
                    EversoloInputSelect(cfg, dev),
                    EversoloVUModeSelect(cfg, dev),
                    EversoloSpectrumModeSelect(cfg, dev),
                ],
            ],
            driver_id="eversolo",
        )
