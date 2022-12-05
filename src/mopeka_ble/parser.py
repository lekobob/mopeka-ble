"""Parser for Mopeka BLE advertisements.


MIT License applies.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data.enum import StrEnum

_LOGGER = logging.getLogger(__name__)


class MopekaSensor(StrEnum):

    LEVEL = "level"
    BATTERY = "battery"
    TEMPERATURE = "temperature"
    QUALITY = "quality"
    SIGNAL_STRENGTH = "signal_strength"


@dataclass
class MopekaDevice:

    model: str
    name: str


DEVICE_TYPES = {
    0x03: MopekaDevice("Mopeka Pro Check", "Propane Tank"),
    0x04: MopekaDevice("Mopeka Air Space", "Tank"),
    0x05: MopekaDevice("Mopeka Pro Check Water", "Water Tank"),
}

# converting sensor value to height - contact Mopeka for other fluids/gases
MOPEKA_TANK_LEVEL_COEFFICIENTS_PROPANE = (0.573045, -0.002822, -0.00000535)

MFR_IDS = set(DEVICE_TYPES)

SERVICE_UUID = "0000fee5-0000-1000-8000-00805f9b34fb"


class MopekaBluetoothDeviceData(BluetoothData):
    """Date update for ThermoBeacon Bluetooth devices."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug(
            "Parsing Testing2 Mopeka BLE advertisement data: %s", service_info
        )
        if SERVICE_UUID not in service_info.service_uuids:
            return
        changed_manufacturer_data = self.changed_manufacturer_data(service_info)
        _LOGGER.debug("Passed UUID check")
        if not changed_manufacturer_data:
            return
        _LOGGER.debug("Passed Man Data check")
        last_id = list(changed_manufacturer_data)[-1]
        data = (
            int(last_id).to_bytes(2, byteorder="little")
            + changed_manufacturer_data[last_id]
        )
        """msg_length = len(data)
        if msg_length not in (20, 22):
            return"""
        device_id = data[2]
        device_type = DEVICE_TYPES[device_id]
        name = device_type.name
        self.set_precision(0)
        self.set_device_type(device_type.model)
        self.set_title(f"{name} {short_address(service_info.address)}")
        self.set_device_name(f"{name} {short_address(service_info.address)}")
        self.set_device_manufacturer("Mopeka")
        self._process_update(data)

    def _process_update(self, data: bytes) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing Mopka BLE advertisement data:%s", data.hex())
        if len(data) != 12:
            return
        """quality = data[6] >> 6
        self.update_predefined_sensor(SensorLibrary.COUNT__NONE, quality)"""
        self._raw_battery = data[3] & 0x7F
        self._raw_temp = data[4] & 0x7F
        self._raw_tank_level = ((int(data[6]) << 8) + data[5]) & 0x3FFF
        self.ReadingQualityStars = data[6] >> 6
        self.update_sensor(
            str(MopekaSensor.LEVEL), None, self.TankLevelInMM, None, "Level"
        )
        self.update_sensor(
            str(MopekaSensor.BATTERY), None, self.BatteryPercent, None, "Battery"
        )
        self.update_sensor(
            str(MopekaSensor.TEMPERATURE),
            None,
            self.TemperatureInCelsius,
            None,
            "Temperature",
        )
        self.update_sensor(
            str(MopekaSensor.QUALITY),
            None,
            self.ReadingQualityStars,
            None,
            "Quality",
        )

    @property
    def BatteryVoltage(self) -> float:
        """Battery reading in volts"""
        return self._raw_battery / 32.0

    @property
    def BatteryPercent(self) -> float:
        """Battery Percentage based on 3 volt CR2032 battery"""
        percent = ((self.BatteryVoltage - 2.2) / 0.65) * 100
        if percent > 100.0:
            return 100.0
        if percent < 0.0:
            return 0.0
        return round(percent, 1)

    @property
    def TemperatureInCelsius(self) -> int:
        """Temperature in Celsius
        Note: This temperature has not been characterized against ambient temperature
        """
        return self._raw_temp - 40

    @property
    def TankLevelInMM(self) -> int:
        """The tank level/depth in mm for propane gas"""
        return int(
            self._raw_tank_level
            * (
                MOPEKA_TANK_LEVEL_COEFFICIENTS_PROPANE[0]
                + (MOPEKA_TANK_LEVEL_COEFFICIENTS_PROPANE[1] * self._raw_temp)
                + (
                    MOPEKA_TANK_LEVEL_COEFFICIENTS_PROPANE[2]
                    * self._raw_temp
                    * self._raw_temp
                )
            )
        )
