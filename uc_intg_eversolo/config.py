"""
Eversolo configuration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field


@dataclass
class EversoloConfig:
    identifier: str = ""
    name: str = ""
    host: str = ""
    port: int = 9529
    model: str = "DMP-A6"
    mac_address: str | None = field(default=None)
