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
from intg_eversolo.output_buttons import EversoloOutputButton
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
                lambda cfg, dev: [
                    EversoloStateSensor(cfg, dev),
                    EversoloSourceSensor(cfg, dev),
                    EversoloVolumeSensor(cfg, dev),
                ],
                self._create_output_buttons,
            ],
            driver_id="eversolo",
        )

    def _create_output_buttons(self, cfg: EversoloConfig, dev: EversoloDevice):
        """Create button entities for all possible Eversolo outputs."""
        # Common Eversolo outputs - buttons will work if device has them enabled
        all_outputs = {
            "rca": "RCA",
            "xlr": "XLR",
            "hdmi": "HDMI",
            "usb": "USB DAC",
            "spdif": "OPT/COAX",
            "xlrrca": "XLR/RCA",
        }

        buttons = []
        for tag, name in all_outputs.items():
            buttons.append(EversoloOutputButton(cfg, dev, tag, name))

        _LOG.debug(f"Created {len(buttons)} output button entities for {cfg.name}")
        return buttons
