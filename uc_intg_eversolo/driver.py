"""
Eversolo integration driver.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from ucapi_framework import BaseIntegrationDriver

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice
from uc_intg_eversolo.media_player import EversoloMediaPlayer
from uc_intg_eversolo.remote import create_remote
from uc_intg_eversolo.sensor import create_sensors
from uc_intg_eversolo.select import create_selects


class EversoloDriver(BaseIntegrationDriver[EversoloDevice, EversoloConfig]):

    def __init__(self):
        super().__init__(
            device_class=EversoloDevice,
            entity_classes=[
                EversoloMediaPlayer,
                lambda cfg, dev: create_remote(cfg, dev),
                lambda cfg, dev: create_sensors(cfg, dev),
                lambda cfg, dev: create_selects(cfg, dev),
            ],
            driver_id="eversolo",
        )
