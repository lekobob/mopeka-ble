"""Parser for Mopeka BLE advertisements.


MIT License applies.
"""
from __future__ import annotations

import logging

from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo

_LOGGER = logging.getLogger(__name__)


class MopekaBluetoothDeviceData(BluetoothData):
    """Date update for ThermoBeacon Bluetooth devices."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing Mopeka BLE advertisement data: %s", service_info)
