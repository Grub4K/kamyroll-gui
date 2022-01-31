from dataclasses import dataclass
from .locale import Locale


@dataclass
class Subtitle:
    locale: Locale
    url: str
    format: str
