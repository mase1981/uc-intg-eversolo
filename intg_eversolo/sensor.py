"""
Eversolo Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi.sensor import Attributes, DeviceClasses, Sensor, States
from ucapi_framework.entity import Entity

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloStateSensor(Sensor, Entity):
    """Eversolo playback state sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.state"

        super().__init__(
            entity_id,
            f"{device_config.name} State",
            [],  # features - no specific features needed
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: "Unknown",
            },
            device_class=None,
        )


class EversoloSourceSensor(Sensor, Entity):
    """Eversolo current source sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.source"

        super().__init__(
            entity_id,
            f"{device_config.name} Source",
            [],  # features - no specific features needed
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: "Unknown",
            },
            device_class=None,
        )


class EversoloVolumeSensor(Sensor, Entity):
    """Eversolo volume sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.volume"

        super().__init__(
            entity_id,
            f"{device_config.name} Volume",
            [],  # features - no specific features needed
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: 0,
                Attributes.UNIT: "%",
            },
            device_class=None,
        )


class EversoloActiveOutputSensor(Sensor, Entity):
    """Eversolo output sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.output"

        super().__init__(
            entity_id,
            f"{device_config.name} Output",
            [],  # features - no specific features needed
            {
                Attributes.STATE: States.UNAVAILABLE,
                Attributes.VALUE: "Unknown",
            },
            device_class=None,
        )
