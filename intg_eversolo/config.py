"""
Eversolo configuration for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field
from typing import Optional
from ucapi_framework import BaseConfigManager


@dataclass
class EversoloConfig:
    """Eversolo device configuration."""

    identifier: str
    name: str
    host: str
    port: int = 9529
    mac_address: Optional[str] = field(default=None)

    def set_mac_address(self, mac: str) -> None:
        """Store MAC address for WakeOnLAN (survives reboots)."""
        self.mac_address = mac


class EversoloConfigManager(BaseConfigManager[EversoloConfig]):
    """Configuration manager with automatic JSON persistence."""

    pass
