"""
Eversolo sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_eversolo.config import EversoloConfig
from uc_intg_eversolo.device import EversoloDevice

_LOG = logging.getLogger(__name__)


class EversoloStateSensor(SensorEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.state"
        super().__init__(
            entity_id,
            f"{device_config.name} State",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "Offline",
            })
            return
        state = self._device.get_state()
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: state,
        })


class EversoloSourceSensor(SensorEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.source"
        super().__init__(
            entity_id,
            f"{device_config.name} Source",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "Offline",
            })
            return
        current_source = self._device.get_current_source()
        self.update({
            sensor.Attributes.STATE: sensor.States.ON if current_source else sensor.States.UNAVAILABLE,
            sensor.Attributes.VALUE: current_source or "Unknown",
        })


class EversoloVolumeSensor(SensorEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.volume"
        super().__init__(
            entity_id,
            f"{device_config.name} Volume",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: "%"},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "0",
            })
            return
        volume = self._device.get_volume()
        self.update({
            sensor.Attributes.STATE: sensor.States.ON if volume is not None else sensor.States.UNAVAILABLE,
            sensor.Attributes.VALUE: str(volume) if volume is not None else "0",
        })


class EversoloOutputSensor(SensorEntity):

    def __init__(self, device_config: EversoloConfig, device: EversoloDevice):
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.output"
        super().__init__(
            entity_id,
            f"{device_config.name} Output",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if not self._device.device_reachable:
            self.update({
                sensor.Attributes.STATE: sensor.States.UNAVAILABLE,
                sensor.Attributes.VALUE: "Offline",
            })
            return
        current_output = self._device.get_current_output()
        self.update({
            sensor.Attributes.STATE: sensor.States.ON if current_output else sensor.States.UNAVAILABLE,
            sensor.Attributes.VALUE: current_output or "Unknown",
        })


def create_sensors(config: EversoloConfig, device: EversoloDevice) -> list:
    return [
        EversoloStateSensor(config, device),
        EversoloSourceSensor(config, device),
        EversoloVolumeSensor(config, device),
        EversoloOutputSensor(config, device),
    ]
