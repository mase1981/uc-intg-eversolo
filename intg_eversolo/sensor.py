"""
Eversolo Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi.sensor import Attributes, DeviceClasses, Sensor, States
from ucapi_framework import DeviceEvents

from intg_eversolo.config import EversoloConfig
from intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloStateSensor(Sensor):
    """Eversolo playback state sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_state"

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

        # Subscribe to device updates
        try:
            self._device.events.on(DeviceEvents.UPDATE, self._on_device_update)
        except Exception as err:
            _LOG.warning(f"[{entity_id}] Could not subscribe to device events: {err}")

    def _on_device_update(self, update: dict[str, Any] | None = None, **kwargs) -> None:
        """Handle device update events."""
        state = self._device.get_state()

        if state == "UNKNOWN":
            self.attributes[Attributes.STATE] = States.UNAVAILABLE
            self.attributes[Attributes.VALUE] = "Unknown"
        else:
            self.attributes[Attributes.STATE] = States.ON
            self.attributes[Attributes.VALUE] = state


class EversoloSourceSensor(Sensor):
    """Eversolo current source sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_source"

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

        # Subscribe to device updates
        try:
            self._device.events.on(DeviceEvents.UPDATE, self._on_device_update)
        except Exception as err:
            _LOG.warning(f"[{entity_id}] Could not subscribe to device events: {err}")

    def _on_device_update(self, update: dict[str, Any] | None = None, **kwargs) -> None:
        """Handle device update events."""
        source = self._device.get_current_source()

        if source:
            self.attributes[Attributes.STATE] = States.ON
            self.attributes[Attributes.VALUE] = source
        else:
            self.attributes[Attributes.STATE] = States.UNAVAILABLE
            self.attributes[Attributes.VALUE] = "Unknown"


class EversoloVolumeSensor(Sensor):
    """Eversolo volume sensor."""

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        """Initialize sensor."""
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_volume"

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

        # Subscribe to device updates
        try:
            self._device.events.on(DeviceEvents.UPDATE, self._on_device_update)
        except Exception as err:
            _LOG.warning(f"[{entity_id}] Could not subscribe to device events: {err}")

    def _on_device_update(self, update: dict[str, Any] | None = None, **kwargs) -> None:
        """Handle device update events."""
        volume = self._device.get_volume()

        if volume is not None:
            self.attributes[Attributes.STATE] = States.ON
            self.attributes[Attributes.VALUE] = volume
        else:
            self.attributes[Attributes.STATE] = States.UNAVAILABLE
            self.attributes[Attributes.VALUE] = 0
