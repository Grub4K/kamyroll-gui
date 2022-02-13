from dataclasses import dataclass
from datetime import datetime

from .developer import Developer
from .locale import Locale
from .service import Service



@dataclass
class ConfigResponse:
    developers: list[Developer]
    services: list[Service]
    locales: list[Locale]
    resolution: list[int]
    updated: datetime
