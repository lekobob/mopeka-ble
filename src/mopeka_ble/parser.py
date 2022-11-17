"""Parser for Mopeka BLE advertisements.


MIT License applies.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo

_LOGGER = logging.getLogger(__name__)


@dataclass
class MopekaDevice:

    model: str
    name: str


DEVICE_TYPES = {
    0x03: MopekaDevice("3", "Mopeka Pro Check Propane"),
    0x04: MopekaDevice("4", "Mopeka Air Space"),
    0x05: MopekaDevice("5", "Mopeka Pro Check Water"),
}
MFR_IDS = set(DEVICE_TYPES)

SERVICE_UUID = "0000fee5-0000-1000-8000-00805f9b34fb"


class MopekaBluetoothDeviceData(BluetoothData):
    """Date update for ThermoBeacon Bluetooth devices."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing Mopeka BLE advertisement data: %s", service_info)
        if SERVICE_UUID not in service_info.service_uuids:
            return
        changed_manufacturer_data = self.changed_manufacturer_data(service_info)
        if not changed_manufacturer_data:
            return
        last_id = list(changed_manufacturer_data)[-1]
        data = (
            int(last_id).to_bytes(2, byteorder="little")
            + changed_manufacturer_data[last_id]
        )
        msg_length = len(data)
        if msg_length not in (20, 22):
            return
        device_id = data[0]
        device_type = DEVICE_TYPES[device_id]
        name = device_type.name
        self.set_precision(2)
        self.set_device_type(device_id)
        self.set_title(f"{name} {short_address(service_info.address)}")
        self.set_device_name(f"{name} {short_address(service_info.address)}")
        self.set_device_manufacturer("Mopeka")
        self._process_update(data)

    def _process_update(self, data: bytes) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug(
            "Parsing Mopka BLE advertisement data: %s Len: %d", data, len(data)
        )
