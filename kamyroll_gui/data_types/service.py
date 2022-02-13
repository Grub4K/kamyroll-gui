import re

from dataclasses import dataclass



@dataclass
class Service:
    id: str
    name: str
    regex: re.Pattern
    active: bool
    bypass: bool
